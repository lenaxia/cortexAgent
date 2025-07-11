"""Service implementations for CortexAgent."""
from __future__ import annotations

import logging
import asyncio
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_MCP_SERVERS, CONF_CUSTOM_TOOLS

_LOGGER = logging.getLogger(__name__)

async def async_reload_service(service: ServiceCall) -> None:
    """Handle reload service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    
    # Handle both async and non-async get_entry methods for testing
    get_entry_method = hass.config_entries.async_get_entry
    if asyncio.iscoroutinefunction(get_entry_method):
        entry = await get_entry_method(entry_id)
    else:
        entry = get_entry_method(entry_id)

    if not entry:
        _LOGGER.error("Config entry not found")
        return

    if entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("Agent not found")
        return

    try:
        # Handle both async and non-async reload methods for testing
        reload_method = hass.config_entries.async_reload
        if asyncio.iscoroutinefunction(reload_method):
            result = await reload_method(entry.entry_id)
        else:
            result = reload_method(entry.entry_id)
            
        if not result:
            _LOGGER.error("Failed to reload config entry %s", entry_id)
    except Exception as ex:
        _LOGGER.error("Error reloading config entry %s: %s", entry_id, ex)
        raise

async def async_connect_mcp_server_service(service: ServiceCall) -> None:
    """Handle connect_mcp_server service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    
    # Handle both async and non-async get_entry methods for testing
    get_entry_method = hass.config_entries.async_get_entry
    if asyncio.iscoroutinefunction(get_entry_method):
        entry = await get_entry_method(entry_id)
    else:
        entry = get_entry_method(entry_id)
    
    if not entry:
        _LOGGER.error("Config entry not found")
        return
    
    if entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("Agent not found")
        return
        
    # Get the MCP connector
    mcp_connector = hass.data[DOMAIN][entry.entry_id].get("mcp_connector")
    if not mcp_connector:
        _LOGGER.error("MCP connector not available")
        return
        
    # Create server config
    server_config = {
        "name": service.data["name"],
        "url": service.data["url"],
        "server_type": service.data["server_type"],
        "auth_token": service.data.get("auth_token")
    }
    
    # Connect to the server
    try:
        result = await mcp_connector.async_connect(server_config)
        if not result:
            _LOGGER.error("Failed to connect to MCP server %s", server_config["name"])
            return
    except Exception as ex:
        _LOGGER.error("Error connecting to MCP server %s: %s", server_config["name"], ex)
        raise
        
    # Update config entry with new server
    new_options = {**entry.options}
    mcp_servers = new_options.get(CONF_MCP_SERVERS, [])
    
    # Add or update server
    server_exists = False
    for i, server in enumerate(mcp_servers):
        if server["name"] == service.data["name"]:
            mcp_servers[i] = server_config
            server_exists = True
            break
            
    if not server_exists:
        mcp_servers.append(server_config)
        
    new_options[CONF_MCP_SERVERS] = mcp_servers
    
    # Handle both async and non-async update_entry methods for testing
    update_entry_method = hass.config_entries.async_update_entry
    if asyncio.iscoroutinefunction(update_entry_method):
        await update_entry_method(entry, options=new_options)
    else:
        update_entry_method(entry, options=new_options)

async def async_disconnect_mcp_server_service(service: ServiceCall) -> None:
    """Handle disconnect_mcp_server service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    
    # Handle both async and non-async get_entry methods for testing
    get_entry_method = hass.config_entries.async_get_entry
    if asyncio.iscoroutinefunction(get_entry_method):
        entry = await get_entry_method(entry_id)
    else:
        entry = get_entry_method(entry_id)
    
    if not entry:
        _LOGGER.error("Config entry not found")
        return
    
    if entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("Agent not found")
        return
        
    # Get the MCP connector
    mcp_connector = hass.data[DOMAIN][entry.entry_id].get("mcp_connector")
    if not mcp_connector:
        _LOGGER.error("MCP connector not available")
        return
        
    server_name = service.data["name"]
    
    # Disconnect from the server
    try:
        result = await mcp_connector.async_disconnect(server_name)
        if not result:
            _LOGGER.error("Failed to disconnect from MCP server %s", server_name)
            return
    except Exception as ex:
        _LOGGER.error("Error disconnecting from MCP server %s: %s", server_name, ex)
        raise
        
    # Update config entry to remove server
    new_options = {**entry.options}
    mcp_servers = new_options.get(CONF_MCP_SERVERS, [])
    
    new_options[CONF_MCP_SERVERS] = [
        s for s in mcp_servers if s["name"] != server_name
    ]
    
    # Handle both async and non-async update_entry methods for testing
    update_entry_method = hass.config_entries.async_update_entry
    if asyncio.iscoroutinefunction(update_entry_method):
        await update_entry_method(entry, options=new_options)
    else:
        update_entry_method(entry, options=new_options)

async def async_add_tool_service(service: ServiceCall) -> None:
    """Handle add_tool service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    
    # Handle both async and non-async get_entry methods for testing
    get_entry_method = hass.config_entries.async_get_entry
    if asyncio.iscoroutinefunction(get_entry_method):
        entry = await get_entry_method(entry_id)
    else:
        entry = get_entry_method(entry_id)
    
    if not entry:
        _LOGGER.error("Config entry not found")
        return
        
    if entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("Agent not found")
        return
        
    # Update config entry with new tool
    new_options = {**entry.options}
    custom_tools = new_options.get(CONF_CUSTOM_TOOLS, [])
    
    # Create tool config
    tool_config = {
        "name": service.data["name"],
        "description": service.data["description"],
        "type": service.data["type"],
        "code": service.data.get("code"),
        "path": service.data.get("path")
    }
    
    # Add or update tool
    tool_exists = False
    for i, tool in enumerate(custom_tools):
        if tool["name"] == service.data["name"]:
            custom_tools[i] = tool_config
            tool_exists = True
            break
            
    if not tool_exists:
        custom_tools.append(tool_config)
        
    new_options[CONF_CUSTOM_TOOLS] = custom_tools
    
    # Handle both async and non-async update_entry methods for testing
    update_entry_method = hass.config_entries.async_update_entry
    if asyncio.iscoroutinefunction(update_entry_method):
        await update_entry_method(entry, options=new_options)
    else:
        update_entry_method(entry, options=new_options)

async def async_remove_tool_service(service: ServiceCall) -> None:
    """Handle remove_tool service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    
    # Handle both async and non-async get_entry methods for testing
    get_entry_method = hass.config_entries.async_get_entry
    if asyncio.iscoroutinefunction(get_entry_method):
        entry = await get_entry_method(entry_id)
    else:
        entry = get_entry_method(entry_id)
    
    if not entry:
        _LOGGER.error("Config entry not found")
        return
        
    if entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("Agent not found")
        return
        
    # Get the tool registry
    agent = hass.data[DOMAIN][entry.entry_id].get("agent")
    if not agent or not hasattr(agent, "tool_registry"):
        _LOGGER.error("Tool registry not available")
        return
        
    tool_name = service.data["name"]
    
    # Remove the tool from the registry if it exists
    try:
        if agent.tool_registry.unregister_tool(tool_name):
            _LOGGER.info("Tool %s removed from registry", tool_name)
    except Exception as ex:
        _LOGGER.error("Error removing tool %s from registry: %s", tool_name, ex)
        raise
        
    # Update config entry to remove tool
    new_options = {**entry.options}
    custom_tools = new_options.get(CONF_CUSTOM_TOOLS, [])
    
    new_options[CONF_CUSTOM_TOOLS] = [
        t for t in custom_tools if t["name"] != tool_name
    ]
    
    # Handle both async and non-async update_entry methods for testing
    update_entry_method = hass.config_entries.async_update_entry
    if asyncio.iscoroutinefunction(update_entry_method):
        await update_entry_method(entry, options=new_options)
    else:
        update_entry_method(entry, options=new_options)

async def async_clear_conversation_service(service: ServiceCall) -> None:
    """Handle clear_conversation service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    
    # Handle both async and non-async get_entry methods for testing
    get_entry_method = hass.config_entries.async_get_entry
    if asyncio.iscoroutinefunction(get_entry_method):
        entry = await get_entry_method(entry_id)
    else:
        entry = get_entry_method(entry_id)
        
    if not entry or entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("Agent not found")
        return
        
    agent = hass.data[DOMAIN][entry_id]["agent"]
    conversation_id = service.data.get("conversation_id")
    
    # Handle both async and non-async conversation manager methods for testing
    if conversation_id:
        clear_method = agent.conversation_manager.clear_conversation
        if asyncio.iscoroutinefunction(clear_method):
            await clear_method(conversation_id)
        else:
            clear_method(conversation_id)
    else:
        clear_all_method = agent.conversation_manager.clear_all_conversations
        if asyncio.iscoroutinefunction(clear_all_method):
            await clear_all_method()
        else:
            clear_all_method()
    
    # Handle both async and non-async save method for testing
    save_method = agent.conversation_manager.async_save
    if asyncio.iscoroutinefunction(save_method):
        await save_method()
    else:
        save_method()