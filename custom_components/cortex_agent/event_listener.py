"""Event listener for the CortexAgent integration."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_state_change,
    async_track_time_pattern,
)

_LOGGER = logging.getLogger(__name__)


class AgentEventListener:
    """Listens for Home Assistant events and triggers agent actions."""

    def __init__(self, hass: HomeAssistant, agent_manager: Any):
        """Initialize the event listener.
        
        Args:
            hass: Home Assistant instance
            agent_manager: Agent manager instance
        """
        self.hass = hass
        self.agent_manager = agent_manager
        self._listeners = []
        self._subscribed_events = set()

    async def async_setup(self) -> None:
        """Set up event listeners based on configuration."""
        # Get configuration
        config = self.agent_manager.entry.options

        # Set up state change listeners
        if config.get("listen_states", []):
            for entity_config in config["listen_states"]:
                self._setup_state_listener(entity_config)

        # Set up time pattern listeners
        if config.get("time_patterns", []):
            for pattern_config in config["time_patterns"]:
                self._setup_time_pattern_listener(pattern_config)

        # Set up event listeners
        if config.get("events", []):
            for event_config in config["events"]:
                self._setup_event_listener(event_config)

    def _setup_state_listener(self, config: Dict) -> None:
        """Set up a state change listener.
        
        Args:
            config: State change configuration
        """
        entity_id = config["entity_id"]
        from_state = config.get("from")
        to_state = config.get("to")

        @callback
        def state_changed(event: Event) -> None:
            """Handle state changed event."""
            # Check if this is the entity we're interested in
            if event.data["entity_id"] != entity_id:
                return

            # Check state transitions if specified
            old_state = event.data.get("old_state")
            new_state = event.data.get("new_state")

            if old_state is None or new_state is None:
                return

            if from_state is not None and old_state.state != from_state:
                return

            if to_state is not None and new_state.state != to_state:
                return

            # Process the event with the agent
            self.hass.async_create_task(
                self._process_event(
                    "state_changed",
                    {
                        "entity_id": entity_id,
                        "old_state": old_state.state,
                        "new_state": new_state.state,
                        "attributes": dict(new_state.attributes),
                    },
                )
            )

        # Register the listener
        self._listeners.append(async_track_state_change(self.hass, entity_id, state_changed))

    def _setup_time_pattern_listener(self, config: Dict) -> None:
        """Set up a time pattern listener.
        
        Args:
            config: Time pattern configuration
        """
        pattern = config["pattern"]

        @callback
        def time_pattern_fired(now: datetime) -> None:
            """Handle time pattern event."""
            self.hass.async_create_task(
                self._process_event(
                    "time_pattern",
                    {"pattern": pattern, "time": now.isoformat()},
                )
            )

        # Register the listener
        self._listeners.append(async_track_time_pattern(self.hass, time_pattern_fired, **pattern))

    def _setup_event_listener(self, config: Dict) -> None:
        """Set up an event listener.
        
        Args:
            config: Event configuration
        """
        event_type = config["event_type"]
        event_data = config.get("event_data")

        @callback
        def event_fired(event: Event) -> None:
            """Handle fired event."""
            # Check event data if specified
            if event_data:
                for key, value in event_data.items():
                    if event.data.get(key) != value:
                        return

            # Process the event with the agent
            self.hass.async_create_task(
                self._process_event(event_type, dict(event.data))
            )

        # Register the listener
        self._subscribed_events.add(event_type)
        self._listeners.append(self.hass.bus.async_listen(event_type, event_fired))

    async def _process_event(self, event_type: str, event_data: Dict) -> None:
        """Process an event with the agent.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        # Create a prompt for the agent
        prompt = f"Event: {event_type}\nData: {json.dumps(event_data, indent=2)}"

        # Process with agent
        try:
            result = await self.agent_manager.async_process_event(prompt, event_data)

            # Log the result
            _LOGGER.debug("Agent processed event %s with result: %s", event_type, result)
        except Exception as err:
            _LOGGER.error("Error processing event with agent: %s", str(err))

    def async_unload(self) -> None:
        """Unload all listeners."""
        for listener in self._listeners:
            listener()
        self._listeners = []
        self._subscribed_events.clear()