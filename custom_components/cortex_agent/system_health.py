"""System health for cortexAgent integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

API_ENDPOINTS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "google": "https://generativelanguage.googleapis.com",
    "aws": "https://bedrock-runtime.{region}.amazonaws.com",
    "azure": "{base_url}",
}


@callback  # type: ignore[misc]
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the info page."""
    info = {}

    # Get the agent from hass.data
    if DOMAIN not in hass.data:
        return {
            "agent_status": "not_configured",
            "model_provider_status": "not_configured",
            "memory_status": "not_configured",
        }

    # Get all config entries for the domain
    entries = hass.data.get(DOMAIN, {})
    if not entries:
        return {
            "agent_status": "not_configured",
            "model_provider_status": "not_configured",
            "memory_status": "not_configured",
        }

    # Use the first entry for system health
    for _, entry_data in entries.values():
        agent = entry_data.get("agent")
        if agent:
            # Agent status
            info["agent_status"] = "active" if agent else "inactive"

            # Model provider status
            if hasattr(agent, "model_provider"):
                provider_name = getattr(agent.model_provider, "name", "unknown")
                info["model_provider_status"] = provider_name

                # API connectivity check
                if provider_name in API_ENDPOINTS:
                    api_url = API_ENDPOINTS[provider_name]

                    # Handle AWS region and Azure base URL
                    if provider_name == "aws" and hasattr(agent.model_provider, "region"):
                        api_url = api_url.format(region=agent.model_provider.region)
                    elif provider_name == "azure" and hasattr(agent.model_provider, "base_url"):
                        api_url = api_url.format(base_url=agent.model_provider.base_url)

                    info["can_reach_provider_api"] = await system_health.async_check_can_reach_url(
                        hass, api_url
                    )

            # Memory status
            if hasattr(agent, "memory_handler"):
                info["memory_status"] = "enabled" if agent.memory_handler else "disabled"
            else:
                info["memory_status"] = "not_available"

            # Conversation count
            if hasattr(agent, "conversation_manager") and hasattr(agent.conversation_manager, "conversations"):
                info["conversation_count"] = str(len(agent.conversation_manager.conversations))

            # Tool count
            if DOMAIN in hass.data and "tools" in hass.data[DOMAIN]:
                info["tool_count"] = str(len(hass.data[DOMAIN]["tools"]))

            # MCP servers
            if "mcp_connector" in entry_data:
                mcp_connector = entry_data["mcp_connector"]
                if hasattr(mcp_connector, "get_connected_servers"):
                    servers = mcp_connector.get_connected_servers()
                    info["mcp_servers_connected"] = str(len(servers))

            # Only process the first active agent
            break

    return info
