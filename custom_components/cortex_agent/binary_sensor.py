"""Binary sensor platform for cortexAgent integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import CortexAgentCoordinator
from .entity import CortexAgentEntity, CortexAgentServerEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up cortexAgent binary sensor based on a config entry."""
    # Get the agent and coordinator from hass.data
    if entry.entry_id not in hass.data[DOMAIN]:
        return

    entry_data = hass.data[DOMAIN][entry.entry_id]

    # Create a coordinator if it doesn't exist
    coordinator = entry_data.get("coordinator")
    if coordinator is None:
        coordinator = CortexAgentCoordinator(hass, entry)
        entry_data["coordinator"] = coordinator
        # Fetch data for the first time
        await coordinator.async_config_entry_first_refresh()

    # Create entities
    entities = [
        CortexAgentAvailableBinarySensor(coordinator, entry),
        CortexAgentMemoryEnabledBinarySensor(coordinator, entry),
    ]

    # Add MCP server connection binary sensors
    if coordinator.data and "servers" in coordinator.data:
        entities.extend(
            CortexAgentServerConnectionBinarySensor(
                coordinator,
                entry,
                server_name,
            )
            for server_name in coordinator.data["servers"]
        )

    async_add_entities(entities)


class CortexAgentAvailableBinarySensor(CortexAgentEntity, BinarySensorEntity):
    """Binary sensor to indicate if the agent is available."""

    def __init__(
        self,
        coordinator: CortexAgentCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)

        self._attr_name = f"{entry.title} Available"
        self._attr_icon = "mdi:robot"
        self._attr_unique_id = f"{entry.entry_id}_available"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

        self._attr_has_entity_name = True
        self._attr_translation_key = "available"

    @property
    def is_on(self) -> bool:
        """Return true if the agent is available."""
        if not self.coordinator.data:
            return False

        status = self.coordinator.data.get("status", "unknown")
        return status == "active"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class CortexAgentMemoryEnabledBinarySensor(CortexAgentEntity, BinarySensorEntity):
    """Binary sensor to indicate if memory is enabled."""

    def __init__(
        self,
        coordinator: CortexAgentCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)

        self._attr_name = f"{entry.title} Memory Enabled"
        self._attr_icon = "mdi:memory"
        self._attr_unique_id = f"{entry.entry_id}_memory_enabled"

        self._attr_has_entity_name = True
        self._attr_translation_key = "memory_enabled"

    @property
    def is_on(self) -> bool:
        """Return true if memory is enabled."""
        if not self.coordinator.data:
            return False

        return self.coordinator.data.get("memory_enabled", False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class CortexAgentServerConnectionBinarySensor(CortexAgentServerEntity, BinarySensorEntity):
    """Binary sensor to indicate if an MCP server is connected."""

    def __init__(
        self,
        coordinator: CortexAgentCoordinator,
        entry: ConfigEntry,
        server_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry, server_name)

        self._attr_name = f"MCP Server {server_name} Connected"
        self._attr_icon = "mdi:server-network"
        self._attr_unique_id = f"{entry.entry_id}_server_{server_name}_connected"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

        self._attr_has_entity_name = True
        self._attr_translation_key = f"server_{server_name}_connected"

    @property
    def is_on(self) -> bool:
        """Return true if the server is connected."""
        if not self.coordinator.data or "servers" not in self.coordinator.data:
            return False

        if self._server_name in self.coordinator.data["servers"]:
            status = self.coordinator.data["servers"][self._server_name].get("status", "unknown")
            return status == "connected"

        return False

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
