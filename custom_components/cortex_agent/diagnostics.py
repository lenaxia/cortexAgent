"""Diagnostics support for the CortexAgent integration."""
from __future__ import annotations

from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_AGENT, DATA_COORDINATOR, DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> Dict[str, Any]:
    """Return diagnostics for a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        Diagnostics data
    """
    # Get coordinator
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    # Get agent
    agent = hass.data[DOMAIN][entry.entry_id][DATA_AGENT]

    # Get metrics if available
    metrics = {}
    if hasattr(agent, "metrics"):
        metrics = agent.metrics.get_metrics()

    # Create diagnostics data
    diagnostics = {
        "entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": {
                k: "***" if k in ["api_key", "auth_token"] else v
                for k, v in entry.data.items()
            },
            "options": {
                k: "***" if k in ["api_key", "auth_token"] else v
                for k, v in entry.options.items()
            },
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_update": coordinator.last_update.isoformat()
            if coordinator.last_update
            else None,
            "data": coordinator.data,
        },
        "agent": {
            "setup_done": agent._setup_done if hasattr(agent, "_setup_done") else False,
            "conversation_count": len(agent.conversation_manager.conversations)
            if hasattr(agent, "conversation_manager")
            else 0,
            "tool_count": len(agent.tool_registry._tools)
            if hasattr(agent, "tool_registry")
            else 0,
        },
        "metrics": metrics,
    }

    return diagnostics