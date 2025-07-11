"""Event listener for the CortexAgent integration."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from homeassistant.const import (
    EVENT_STATE_CHANGED,
    EVENT_CALL_SERVICE,
)

# Define constants for events not available in the current Home Assistant version
EVENT_AUTOMATION_TRIGGERED = "automation_triggered"
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_utc_time_change,
)

_LOGGER = logging.getLogger(__name__)


class EventListener:
    """Listens for Home Assistant events and stores them for agent context."""

    def __init__(self, hass: HomeAssistant, coordinator: Any):
        """Initialize the event listener.
        
        Args:
            hass: Home Assistant instance
            coordinator: Data update coordinator
        """
        self.hass = hass
        self.coordinator = coordinator
        self.agent_id = coordinator.agent_id
        self._listeners = []

    async def async_start(self) -> None:
        """Start listening for events."""
        # Listen for state changes
        self._listeners.append(
            self.hass.bus.async_listen(EVENT_STATE_CHANGED, self._handle_state_changed_event)
        )
        
        # Listen for service calls
        self._listeners.append(
            self.hass.bus.async_listen(EVENT_CALL_SERVICE, self._handle_service_call_event)
        )
        
        # Listen for automation triggers
        self._listeners.append(
            self.hass.bus.async_listen(EVENT_AUTOMATION_TRIGGERED, self._handle_automation_triggered_event)
        )
        
        _LOGGER.debug("Event listener started for agent %s", self.agent_id)

    async def async_stop(self) -> None:
        """Stop listening for events."""
        for listener in self._listeners:
            listener()
        self._listeners = []
        _LOGGER.debug("Event listener stopped for agent %s", self.agent_id)

    async def _handle_state_changed_event(self, event: Event) -> None:
        """Handle state changed events.
        
        Args:
            event: The state changed event
        """
        if not self.coordinator.memory_handler:
            return
            
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        
        # Skip if entity_id is missing
        if not entity_id:
            return
            
        # Create a human-readable description of the state change
        if old_state and new_state:
            content = f"Entity {entity_id} changed from {old_state.state} to {new_state.state}"
            if new_state.attributes:
                content += f" with attributes: {json.dumps(dict(new_state.attributes), default=str)}"
        elif new_state:
            content = f"Entity {entity_id} was created with state {new_state.state}"
            if new_state.attributes:
                content += f" with attributes: {json.dumps(dict(new_state.attributes), default=str)}"
        elif old_state:
            content = f"Entity {entity_id} was removed (previous state was {old_state.state})"
        else:
            return  # Skip if we don't have any state information
            
        # Store the event in memory
        try:
            await self.coordinator.memory_handler.store(
                agent_id=self.agent_id,
                content=content,
                metadata={
                    "type": "state_changed",
                    "entity_id": entity_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as ex:
            _LOGGER.error("Failed to store state change event: %s", ex)

    async def _handle_service_call_event(self, event: Event) -> None:
        """Handle service call events.
        
        Args:
            event: The service call event
        """
        if not self.coordinator.memory_handler:
            return
            
        domain = event.data.get("domain")
        service = event.data.get("service")
        service_data = event.data.get("service_data", {})
        target = event.data.get("target", {})
        
        # Skip if domain or service is missing
        if not domain or not service:
            return
            
        # Create a human-readable description of the service call
        content = f"Service {domain}.{service} was called"
        
        if target:
            if "entity_id" in target:
                entities = target["entity_id"]
                if isinstance(entities, list):
                    content += f" on entities: {', '.join(entities)}"
                else:
                    content += f" on entity: {entities}"
            elif "device_id" in target:
                devices = target["device_id"]
                if isinstance(devices, list):
                    content += f" on devices: {', '.join(devices)}"
                else:
                    content += f" on device: {devices}"
                    
        if service_data:
            content += f" with data: {json.dumps(service_data, default=str)}"
            
        # Store the event in memory
        try:
            await self.coordinator.memory_handler.store(
                agent_id=self.agent_id,
                content=content,
                metadata={
                    "type": "service_call",
                    "domain": domain,
                    "service": service,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as ex:
            _LOGGER.error("Failed to store service call event: %s", ex)

    async def _handle_automation_triggered_event(self, event: Event) -> None:
        """Handle automation triggered events.
        
        Args:
            event: The automation triggered event
        """
        if not self.coordinator.memory_handler:
            return
            
        name = event.data.get("name")
        entity_id = event.data.get("entity_id")
        
        # Skip if both name and entity_id are missing
        if not name and not entity_id:
            return
            
        # Create a human-readable description of the automation trigger
        if name and entity_id:
            content = f"Automation '{name}' ({entity_id}) was triggered"
        elif name:
            content = f"Automation '{name}' was triggered"
        else:
            content = f"Automation {entity_id} was triggered"
            
        # Store the event in memory
        try:
            await self.coordinator.memory_handler.store(
                agent_id=self.agent_id,
                content=content,
                metadata={
                    "type": "automation_triggered",
                    "entity_id": entity_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as ex:
            _LOGGER.error("Failed to store automation triggered event: %s", ex)


# Keep the old class name for backward compatibility
AgentEventListener = EventListener


async def async_setup_event_listener(hass: HomeAssistant, coordinator: Any) -> EventListener:
    """Set up and start the event listener.
    
    Args:
        hass: Home Assistant instance
        coordinator: Data update coordinator
        
    Returns:
        The event listener instance
    """
    listener = EventListener(hass, coordinator)
    await listener.async_start()
    return listener