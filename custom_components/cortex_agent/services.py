"""Service implementations for CortexAgent."""
from __future__ import annotations

import logging
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
    entry = await hass.config_entries.async_get_entry(entry_id)

    if not entry:
        _LOGGER.error("Config entry not found")
        return

    if entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("Agent not found")
        return

    await hass.config_entries.async_reload(entry.entry_id)

async def async_connect_mcp_server_service(service: ServiceCall) -> None:
    """Handle connect_mcp_server service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    entry = hass.config_entries.async_get_entry(entry_id)
    
    if not entry:
        _LOGGER.error("Config entry not found")
        return
        
    # Update config entry with new server
    new_options = {**entry.options}
    mcp_servers = new_options.get(CONF_MCP_SERVERS, [])
    
    # Add or update server
    server_exists = False
    for i, server in enumerate(mcp_servers):
        if server["name"] == service.data["name"]:
            mcp_servers[i] = {
                "name": service.data["name"],
                "url": service.data["url"],
                "server_type": service.data["server_type"],
                "auth_token": service.data.get("auth_token")
            }
            server_exists = True
            break
            
    if not server_exists:
        mcp_servers.append({
            "name": service.data["name"],
            "url": service.data["url"],
            "server_type": service.data["server_type"],
            "auth_token": service.data.get("auth_token")
        })
        
    new_options[CONF_MCP_SERVERS] = mcp_servers
    hass.config_entries.async_update_entry(entry, options=new_options)

async def async_disconnect_mcp_server_service(service: ServiceCall) -> None:
    """Handle disconnect_mcp_server service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    entry = hass.config_entries.async_get_entry(entry_id)
    
    if not entry:
        _LOGGER.error("Config entry not found")
        return
        
    # Update config entry to remove server
    new_options = {**entry.options}
    mcp_servers = new_options.get(CONF_MCP_SERVERS, [])
    
    new_options[CONF_MCP_SERVERS] = [
        s for s in mcp_servers if s["name"] != service.data["name"]
    ]
    hass.config_entries.async_update_entry(entry, options=new_options)

async def async_add_tool_service(service: ServiceCall) -> None:
    """Handle add_tool service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    entry = hass.config_entries.async_get_entry(entry_id)
    
    if not entry:
        _LOGGER.error("Config entry not found")
        return
        
    # Update config entry with new tool
    new_options = {**entry.options}
    custom_tools = new_options.get(CONF_CUSTOM_TOOLS, [])
    
    # Add or update tool
    tool_exists = False
    for i, tool in enumerate(custom_tools):
        if tool["name"] == service.data["name"]:
            custom_tools[i] = {
                "name": service.data["name"],
                "description": service.data["description"],
                "type": service.data["type"],
                "code": service.data.get("code"),
                "path": service.data.get("path")
            }
            tool_exists = True
            break
            
    if not tool_exists:
        custom_tools.append({
            "name": service.data["name"],
            "description": service.data["description"],
            "type": service.data["type"],
            "code": service.data.get("code"),
            "path": service.data.get("path")
        })
        
    new_options[CONF_CUSTOM_TOOLS] = custom_tools
    hass.config_entries.async_update_entry(entry, options=new_options)

async def async_remove_tool_service(service: ServiceCall) -> None:
    """Handle remove_tool service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    entry = hass.config_entries.async_get_entry(entry_id)
    
    if not entry:
        _LOGGER.error("Config entry not found")
        return
        
    # Update config entry to remove tool
    new_options = {**entry.options}
    custom_tools = new_options.get(CONF_CUSTOM_TOOLS, [])
    
    new_options[CONF_CUSTOM_TOOLS] = [
        t for t in custom_tools if t["name"] != service.data["name"]
    ]
    hass.config_entries.async_update_entry(entry, options=new_options)

async def async_clear_conversation_service(service: ServiceCall) -> None:
    """Handle clear_conversation service calls."""
    hass = service.hass
    entry_id = service.data["entity_id"].split(".")[1]
    
    # Get config entry first to validate
    entry = await hass.config_entries.async_get_entry(entry_id)
    if not entry or entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("Agent not found")
        return
        
    agent = hass.data[DOMAIN][entry_id]["agent"]
    conversation_id = service.data.get("conversation_id")
    
    if conversation_id:
        await agent.conversation_manager.clear_conversation(conversation_id)
    else:
        await agent.conversation_manager.clear_all_conversations()
    
    await agent.conversation_manager.async_save()