"""Data update coordinator for CortexAgent."""
from __future__ import annotations

import asyncio
import logging
import random
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)

class CortexAgentCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the agent."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        retry_attempts: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 5.0
    ) -> None:
        """Initialize global CortexAgent data updater."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL
        )
        
        self.entry = entry
        self.retry_attempts = retry_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from agent and connected MCP servers."""
        data = {
            "status": "active",
            "last_update": dt_util.utcnow().isoformat(),
            "servers": {},
            "tools": {}
        }

        # Get connected MCP servers and tools from hass data
        if DOMAIN in self.hass.data:
            domain_data = self.hass.data[DOMAIN]
            # Include all registered tools in response
            data["tools"] = domain_data.get("tools", {})
            
            # Track server statuses with retry logic
            for server_name, server in domain_data.get("servers", {}).items():
                last_error = None
                status = "error"
                tools = []
                
                # Initialize server entry
                data["servers"][server_name] = {
                    "status": status,
                    "last_seen": dt_util.utcnow().isoformat(),
                    "tools": 0
                }

                # First try status check with retries
                status_attempt = 0
                while status_attempt < self.retry_attempts:
                    status_attempt += 1
                    delay = min(
                        self.base_delay * (2 ** (status_attempt - 1)),
                        self.max_delay
                    ) * (0.5 + random.random())
                    
                    if status_attempt > 1:
                        _LOGGER.debug(
                            "Retrying status check for server %s in %.2f seconds (attempt %d/%d)",
                            server_name,
                            delay,
                            status_attempt,
                            self.retry_attempts
                        )
                        await asyncio.sleep(delay)
                    
                    try:
                        if hasattr(server, 'get_status'):
                            status = await server.get_status()
                            break
                        else:
                            status = "error"
                            break
                    except Exception as err:
                        last_error = err
                        _LOGGER.warning(
                            "Error checking server %s status (attempt %d/%d): %s",
                            server_name,
                            status_attempt,
                            self.retry_attempts,
                            err
                        )
                        if status_attempt == self.retry_attempts:
                            status = "error"
                
                # Only proceed to tools fetch if status check succeeded
                if status == "connected":
                    tools_attempt = 0
                    tools = []
                    while tools_attempt < self.retry_attempts:
                        tools_attempt += 1
                        delay = min(
                            self.base_delay * (2 ** (tools_attempt - 1)),
                            self.max_delay
                        ) * (0.5 + random.random())
                        
                        if tools_attempt > 1:
                            _LOGGER.debug(
                                "Retrying tools fetch for server %s in %.2f seconds (attempt %d/%d)",
                                server_name,
                                delay,
                                tools_attempt,
                                self.retry_attempts
                            )
                            await asyncio.sleep(delay)
                        
                        try:
                            if hasattr(server, 'get_tools'):
                                tools = await server.get_tools()
                                break
                        except Exception as err:
                            last_error = err
                            _LOGGER.warning(
                                "Error getting tools for server %s (attempt %d/%d): %s",
                                server_name,
                                tools_attempt,
                                self.retry_attempts,
                                err
                            )
                            if tools_attempt == self.retry_attempts:
                                tools = []

                    # Update server entry
                    data["servers"][server_name] = {
                        "status": status,
                        "last_seen": dt_util.utcnow().isoformat(),
                        "tools": len(tools) if tools else (
                            len(server.tools) if hasattr(server, 'tools') else 0
                        )
                    }
                else:
                    # Update server entry with failed status
                    data["servers"][server_name] = {
                        "status": status,
                        "last_seen": dt_util.utcnow().isoformat(),
                        "tools": 0
                    }

        return data