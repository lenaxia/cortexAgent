"""System health support for the CortexAgent integration."""
from __future__ import annotations

from typing import Any, Dict

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DATA_AGENT, DOMAIN


@callback
async def async_register(hass: HomeAssistant) -> None:
    """Register system health callbacks.
    
    Args:
        hass: Home Assistant instance
    """
    system_health.async_register_info(hass, DOMAIN, system_health_info)


async def system_health_info(hass: HomeAssistant) -> Dict[str, Any]:
    """Get system health information.
    
    Args:
        hass: Home Assistant instance
        
    Returns:
        System health information
    """
    # Count active agents
    active_agents = 0
    total_conversations = 0
    total_tools = 0

    for entry_id, data in hass.data.get(DOMAIN, {}).items():
        agent = data.get(DATA_AGENT)
        if agent and getattr(agent, "_setup_done", False):
            active_agents += 1

            # Count conversations if available
            if hasattr(agent, "conversation_manager"):
                total_conversations += len(agent.conversation_manager.conversations)

            # Count tools if available
            if hasattr(agent, "tool_registry"):
                total_tools += len(agent.tool_registry._tools)

    # Get version
    version = "0.1.0"  # Replace with actual version detection

    return {
        "version": version,
        "active_agents": active_agents,
        "total_conversations": total_conversations,
        "total_tools": total_tools,
    }