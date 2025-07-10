"""The Cortex Agent integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    DATA_AGENT,
    DATA_COORDINATOR,
    CONF_MCP_SERVERS,
    CONF_PROVIDER,
    CONF_MODEL_ID,
    CONF_API_KEY,
    CONF_SYSTEM_PROMPT,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    CONF_MEMORY_ENABLED,
)
from .websocket_api import async_register_websocket_commands
from .frontend import async_register_frontend, CortexAgentFrontendView

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Cortex Agent component."""
    import voluptuous as vol
    from .services import (
        async_reload_service,
        async_connect_mcp_server_service,
        async_disconnect_mcp_server_service,
        async_add_tool_service,
        async_remove_tool_service,
        async_clear_conversation_service
    )
    
    hass.data.setdefault(DOMAIN, {})
    
    # Register WebSocket API commands
    async_register_websocket_commands(hass)
    
    # Register frontend resources
    async_register_frontend(hass)
    
    # Register frontend view
    hass.http.register_view(CortexAgentFrontendView(hass))

    # Register services
    hass.services.async_register(
        DOMAIN,
        "reload",
        async_reload_service
    )
    hass.services.async_register(
        DOMAIN,
        "connect_mcp_server",
        async_connect_mcp_server_service,
        schema=vol.Schema({
            vol.Required("name"): str,
            vol.Required("url"): str,
            vol.Required("server_type"): vol.In(["local", "remote"]),
            vol.Optional("auth_token"): str
        })
    )
    hass.services.async_register(
        DOMAIN,
        "disconnect_mcp_server",
        async_disconnect_mcp_server_service,
        schema=vol.Schema({
            vol.Required("name"): str
        })
    )
    hass.services.async_register(
        DOMAIN,
        "add_tool",
        async_add_tool_service,
        schema=vol.Schema({
            vol.Required("name"): str,
            vol.Required("config"): dict
        })
    )
    hass.services.async_register(
        DOMAIN,
        "remove_tool",
        async_remove_tool_service,
        schema=vol.Schema({
            vol.Required("name"): str
        })
    )
    hass.services.async_register(
        DOMAIN,
        "clear_conversation",
        async_clear_conversation_service
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cortex Agent from a config entry."""
    from .conversation import CortexAgent
    from .conversation_manager import ConversationManager
    from .tool_registry import ToolRegistry
    from .model_provider import create_model_provider
    from .memory_handler import MemoryHandler
    from .mcp_connector import MCPConnector
    
    hass.data.setdefault(DOMAIN, {})
    
    # Initialize components
    try:
        # Create model provider
        provider_type = entry.data[CONF_PROVIDER]
        model_provider = await create_model_provider(
            provider_type=provider_type,
            config=entry.data,
            hass=hass,
        )
        
        # Create conversation manager
        conversation_manager = ConversationManager(
            hass=hass,
            entry_id=entry.entry_id,
        )
        await conversation_manager.async_load()
        
        # Create tool registry
        tool_registry = ToolRegistry(hass=hass)
        
        # Create memory handler if enabled
        memory_handler = None
        if entry.options.get(CONF_MEMORY_ENABLED, True):
            memory_handler = MemoryHandler(
                hass=hass,
                entry_id=entry.entry_id,
            )
            await memory_handler.async_load()
        
        # Create MCP connector
        mcp_connector = MCPConnector(hass=hass, entry=entry)
        await mcp_connector.async_setup()
        
        # Create agent
        agent = CortexAgent(
            hass=hass,
            entry=entry,
            model_provider=model_provider,
            conversation_manager=conversation_manager,
            tool_registry=tool_registry,
            memory_handler=memory_handler,
            mcp_connector=mcp_connector,
        )
        
        # Register the agent as a conversation agent
        conversation_id = await hass.components.conversation.async_register(agent)
        
        # Store components in hass.data
        hass.data[DOMAIN][entry.entry_id] = {
            DATA_AGENT: agent,
            "conversation_id": conversation_id,
            "model_provider": model_provider,
            "conversation_manager": conversation_manager,
            "tool_registry": tool_registry,
            "memory_handler": memory_handler,
            "mcp_connector": mcp_connector,
        }
        
        _LOGGER.info("CortexAgent integration set up successfully")
        return True
        
    except Exception as ex:
        _LOGGER.error("Error setting up CortexAgent integration: %s", ex)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id not in hass.data[DOMAIN]:
        return True
        
    entry_data = hass.data[DOMAIN][entry.entry_id]
    
    # Unregister the conversation agent
    conversation_id = entry_data.get("conversation_id")
    if conversation_id:
        await hass.components.conversation.async_unregister(conversation_id)
    
    # Unload components
    agent = entry_data.get(DATA_AGENT)
    if agent:
        await agent.async_unload()
    
    # Clean up MCP connector
    mcp_connector = entry_data.get("mcp_connector")
    if mcp_connector:
        for server_name in mcp_connector.get_connected_servers():
            await mcp_connector.async_disconnect(server_name)
    
    # Clean up memory handler
    memory_handler = entry_data.get("memory_handler")
    if memory_handler:
        await memory_handler.async_save()
    
    # Clean up conversation manager
    conversation_manager = entry_data.get("conversation_manager")
    if conversation_manager:
        await conversation_manager.async_save()
    
    # Remove data
    hass.data[DOMAIN].pop(entry.entry_id)
    
    return True