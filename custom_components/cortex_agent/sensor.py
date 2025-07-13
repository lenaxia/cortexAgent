"""Sensor platform for cortexAgent integration."""
from __future__ import annotations

import logging
from typing import Any, Final

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DATA_AGENT, DOMAIN
from .coordinator import CortexAgentCoordinator
from .entity import CortexAgentEntity, CortexAgentServerEntity

_LOGGER = logging.getLogger(__name__)

# Define sensor types
SENSOR_TYPES: Final = {
    "status": {
        "name": "Status",
        "icon": "mdi:robot",
        "device_class": None,
    },
    "provider": {
        "name": "Provider",
        "icon": "mdi:cloud",
        "device_class": None,
    },
    "model": {
        "name": "Model",
        "icon": "mdi:brain",
        "device_class": None,
    },
    "conversation_count": {
        "name": "Conversation Count",
        "icon": "mdi:message-text",
        "device_class": None,
    },
    "tool_count": {
        "name": "Tool Count",
        "icon": "mdi:tools",
        "device_class": None,
    },
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up cortexAgent sensor based on a config entry."""
    # Get the agent and coordinator from hass.data
    if entry.entry_id not in hass.data[DOMAIN]:
        return

    entry_data = hass.data[DOMAIN][entry.entry_id]
    # Agent is retrieved but not used, removing assignment
    entry_data.get(DATA_AGENT)

    # Create a coordinator if it doesn't exist
    coordinator = entry_data.get("coordinator")
    if coordinator is None:
        coordinator = CortexAgentCoordinator(hass, entry)
        entry_data["coordinator"] = coordinator
        # Fetch data for the first time
        await coordinator.async_config_entry_first_refresh()

    # Create entities
    entities = []
    for sensor_type, sensor_info in SENSOR_TYPES.items():
        entities.append(
            CortexAgentSensor(
                coordinator,
                entry,
                sensor_type,
                sensor_info,
            )
        )

    # Add MCP server status sensors
    if coordinator.data and "servers" in coordinator.data:
        # Use list comprehension for better performance
        entities.extend(
            CortexAgentServerSensor(coordinator, entry, server_name)
            for server_name in coordinator.data["servers"]
        )

    async_add_entities(entities)


class CortexAgentSensor(CortexAgentEntity, SensorEntity):
    """Representation of a cortexAgent sensor."""

    def __init__(
        self,
        coordinator: CortexAgentCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
        sensor_info: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)

        self._sensor_type = sensor_type
        self._attr_name = f"{entry.title} {sensor_info['name']}"
        self._attr_icon = sensor_info["icon"]
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"

        if sensor_info["device_class"]:
            self._attr_device_class = sensor_info["device_class"]

        self._attr_has_entity_name = True
        self._attr_translation_key = sensor_type

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        if self._sensor_type == "status":
            return self.coordinator.data.get("status", "unknown")
        if self._sensor_type in self.coordinator.data:
            return self.coordinator.data.get(self._sensor_type)
        if self._sensor_type in self.coordinator.data.get("tools", {}):
            return self.coordinator.data["tools"].get(self._sensor_type)

        # Check in extra_state_attributes of the base entity
        for key, value in self.extra_state_attributes.items():
            if key == self._sensor_type:
                return value

        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class CortexAgentServerSensor(CortexAgentServerEntity, SensorEntity):
    """Representation of a cortexAgent MCP server sensor."""

    def __init__(
        self,
        coordinator: CortexAgentCoordinator,
        entry: ConfigEntry,
        server_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, server_name)

        self._attr_name = f"MCP Server {server_name}"
        self._attr_icon = "mdi:server-network"
        self._attr_unique_id = f"{entry.entry_id}_server_{server_name}"

        self._attr_has_entity_name = True
        self._attr_translation_key = f"server_{server_name}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or "servers" not in self.coordinator.data:
            return None

        if self._server_name in self.coordinator.data["servers"]:
            return self.coordinator.data["servers"][self._server_name].get("status", "unknown")

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {}

        if not self.coordinator.data or "servers" not in self.coordinator.data:
            return attrs

        if self._server_name in self.coordinator.data["servers"]:
            server_data = self.coordinator.data["servers"][self._server_name]
            attrs["last_seen"] = server_data.get("last_seen")
            attrs["tools"] = server_data.get("tools", 0)

        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
