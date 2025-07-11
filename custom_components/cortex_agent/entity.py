"""Entity definitions for the CortexAgent integration."""
from __future__ import annotations

from typing import Any, Dict

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import CortexAgentCoordinator


class CortexAgentEntity(CoordinatorEntity[CortexAgentCoordinator]):
    """Representation of a Cortex Agent entity."""

    _attr_has_entity_name = True
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # First check the parent class availability (coordinator.last_update_success)
        if not super().available:
            return False
            
        # Check if the coordinator has data
        if not self.coordinator.data:
            return False
            
        # Check if the agent is initialized
        if not self.coordinator._agent:
            return False
            
        return True

    def __init__(
        self,
        coordinator: CortexAgentCoordinator,
        entry: ConfigEntry,
        description: EntityDescription = None,
    ) -> None:
        """Initialize the entity.
        
        Args:
            coordinator: Data update coordinator
            entry: Config entry
            description: Entity description
        """
        super().__init__(coordinator)
        
        self.entry = entry
        
        if description is not None:
            self.entity_description = description
            self._attr_translation_key = description.key
            
        self._attr_unique_id = f"{entry.entry_id}_{self.__class__.__name__}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=DEFAULT_NAME,
            model="AI Assistant",
            sw_version=coordinator.data.get("version", "0.1.0") if coordinator.data else "0.1.0",
        )

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
            
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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class CortexAgentServerEntity(CortexAgentEntity):
    """Representation of a Cortex Agent server entity."""
    
    def __init__(
        self,
        coordinator: CortexAgentCoordinator,
        entry: ConfigEntry,
        server_name: str,
        description: EntityDescription = None,
    ) -> None:
        """Initialize the entity.
        
        Args:
            coordinator: Data update coordinator
            entry: Config entry
            server_name: Name of the server
            description: Entity description
        """
        super().__init__(coordinator, entry, description)
        self._server_name = server_name
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # First check the parent class availability
        if not super().available:
            return False
            
        # Check if the server exists in the coordinator data
        if not self.coordinator.data or "servers" not in self.coordinator.data:
            return False
            
        # Check if the server is in the list of servers
        if self._server_name not in self.coordinator.data["servers"]:
            return False
            
        return True