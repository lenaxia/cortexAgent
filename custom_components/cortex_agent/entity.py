"""Entity definitions for the CortexAgent integration."""
from __future__ import annotations

from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .coordinator import CortexAgentCoordinator


class CortexAgentEntity(Entity):
    """Representation of a Cortex Agent entity."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator: CortexAgentCoordinator):
        """Initialize the entity.
        
        Args:
            hass: Home Assistant instance
            entry: Config entry
            coordinator: Data update coordinator
        """
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._attr_name = entry.title
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Cortex Agent",
            "model": "AI Assistant",
            "sw_version": "0.1.0",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def state(self) -> str:
        """Return the state of the entity."""
        return self.coordinator.data.get("status", "unknown")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        return {
            "provider": self.coordinator.data.get("provider"),
            "model": self.coordinator.data.get("model"),
            "last_activity": self.coordinator.data.get("last_activity"),
            "memory_enabled": self.coordinator.data.get("memory_enabled"),
            "http_enabled": self.coordinator.data.get("http_enabled"),
            "mcp_servers": self.coordinator.data.get("mcp_servers"),
            "custom_tools": self.coordinator.data.get("custom_tools"),
            "conversation_count": self.coordinator.data.get("conversation_count", 0),
            "tool_count": self.coordinator.data.get("tool_count", 0),
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()