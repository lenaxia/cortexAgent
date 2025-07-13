"""Data update coordinator for CortexAgent."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any, TypeVar

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)
TIMEOUT = 10

T = TypeVar("T", bound=dict[str, Any])

class CortexAgentCoordinator(DataUpdateCoordinator[T]):
    """Class to manage fetching data from the agent."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        retry_attempts: int = 3,
    ) -> None:
        """Initialize global CortexAgent data updater."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DEFAULT_NAME} Data",
            update_interval=UPDATE_INTERVAL,
            config_entry=entry,
            always_update=False,  # Only update if data has changed
        )

        self.entry = entry
        self.retry_attempts = retry_attempts
        self._agent = None
        self._mcp_connector = None

    async def _async_setup(self) -> None:
        """Set up the coordinator.

        This is called automatically during async_config_entry_first_refresh.
        """
        if DOMAIN in self.hass.data and self.entry.entry_id in self.hass.data[DOMAIN]:
            entry_data = self.hass.data[DOMAIN][self.entry.entry_id]
            self._agent = entry_data.get("agent")
            self._mcp_connector = entry_data.get("mcp_connector")

            _LOGGER.debug("Coordinator setup complete with agent: %s", self._agent is not None)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from agent and connected MCP servers."""
        try:
            async with asyncio.timeout(TIMEOUT):
                data = {
                    "status": "active",
                    "last_update": dt_util.utcnow().isoformat(),
                    "version": getattr(self._agent, "version", "0.1.0") if self._agent else "0.1.0",
                    "servers": {},
                    "tools": {},
                    "provider": None,
                    "model": None,
                    "memory_enabled": False,
                    "http_enabled": False,
                    "conversation_count": 0,
                    "tool_count": 0,
                }

                # Get agent data if available
                if self._agent:
                    data["provider"] = getattr(self._agent.model_provider, "name", None) if hasattr(self._agent, "model_provider") else None
                    data["model"] = getattr(self._agent.model_provider, "model_id", None) if hasattr(self._agent, "model_provider") else None
                    data["memory_enabled"] = getattr(self._agent, "memory_handler", None) is not None
                    data["conversation_count"] = len(getattr(self._agent.conversation_manager, "conversations", {})) if hasattr(self._agent, "conversation_manager") else 0

                # Get connected MCP servers and tools from hass data
                if DOMAIN in self.hass.data:
                    domain_data = self.hass.data[DOMAIN]
                    # Include all registered tools in response
                    tools = domain_data.get("tools", {})
                    data["tools"] = tools
                    data["tool_count"] = len(tools)

                    # Get MCP server data
                    if self._mcp_connector:
                        try:
                            servers = self._mcp_connector.get_connected_servers()
                            for server_name in servers:
                                server_info = await self._get_server_info(server_name)
                                if server_info:
                                    data["servers"][server_name] = server_info
                        except (ConnectionError, TimeoutError, ValueError, AttributeError) as err:
                            _LOGGER.debug("Error getting MCP server data: %s", err)

                return data
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout error fetching data: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error updating coordinator data")
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def _get_server_info(self, server_name: str) -> dict[str, Any]:
        """Get information about an MCP server with retry logic."""
        if not self._mcp_connector:
            return None

        server = self._mcp_connector.get_server(server_name)
        if not server:
            return None

        status = "error"
        tools = []

        # Try to get server status
        for attempt in range(self.retry_attempts):
            try:
                if hasattr(server, 'get_status'):
                    status = await server.get_status()
                    break
                status = "error"
                break
            except (ConnectionError, TimeoutError, ValueError, AttributeError) as err:
                _LOGGER.debug(
                    "Error checking server %s status (attempt %d/%d): %s",
                    server_name,
                    attempt + 1,
                    self.retry_attempts,
                    err
                )
                if attempt == self.retry_attempts - 1:
                    status = "error"

        # Only proceed to tools fetch if status check succeeded
        if status == "connected":
            try:
                if hasattr(server, 'get_tools'):
                    tools = await server.get_tools()
            except (ConnectionError, TimeoutError, ValueError, AttributeError) as err:
                _LOGGER.debug("Error getting tools for server %s: %s", server_name, err)

        return {
            "status": status,
            "last_seen": dt_util.utcnow().isoformat(),
            "tools": len(tools) if tools else (
                len(server.tools) if hasattr(server, 'tools') else 0
            )
        }
