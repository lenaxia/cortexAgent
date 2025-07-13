"""Diagnostics support for Cortex Agent."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .const import CONF_MODEL_ID, CONF_PROVIDER, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Keys to redact in the diagnostics data
TO_REDACT = {CONF_API_KEY, "auth_token", "token", "password", "secret"}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = {
        "entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
            "source": entry.source,
        },
        "provider": entry.data.get(CONF_PROVIDER),
        "model_id": entry.data.get(CONF_MODEL_ID),
    }

    # Get components from hass.data
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        entry_data = hass.data[DOMAIN][entry.entry_id]

        # Add conversation statistics
        conversation_manager = entry_data.get("conversation_manager")
        if conversation_manager:
            data["conversations"] = {
                "count": len(conversation_manager.conversations),
                "ids": conversation_manager.get_conversation_ids(),
                "summaries": [
                    {
                        "id": conv_id,
                        "metadata": conversation_manager.get_conversation_metadata(conv_id)
                    }
                    for conv_id in conversation_manager.get_conversation_ids()
                ]
            }

        # Add MCP server information
        mcp_connector = entry_data.get("mcp_connector")
        if mcp_connector:
            data["mcp_servers"] = {
                "connected_servers": mcp_connector.get_connected_servers(),
                "connection_status": mcp_connector.get_connection_status(),
                "tools_count": {
                    server: len(tools)
                    for server, tools in mcp_connector.tools_cache.items()
                }
            }

        # Add tool registry information
        tool_registry = entry_data.get("tool_registry")
        if tool_registry:
            data["tools"] = {
                "count": tool_registry.get_tool_count(),
                "names": [tool["id"] for category, tools in tool_registry.get_tools_info().items()
                         for tool in tools]
            }

        # Add memory handler information
        memory_handler = entry_data.get("memory_handler")
        if memory_handler and hasattr(memory_handler, "get_stats"):
            data["memory"] = memory_handler.get_stats()

    # Redact sensitive information
    return dict(async_redact_data(data, TO_REDACT))
