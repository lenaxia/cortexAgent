"""WebSocket API for CortexAgent integration."""
from __future__ import annotations

import logging
import voluptuous as vol
from typing import Any, Callable, Dict, List, Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.components import websocket_api
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.const import ERR_NOT_FOUND

from .const import (
    DOMAIN,
    DATA_AGENT,
    DATA_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)

# Signal constants
SIGNAL_CONVERSATION_UPDATED = f"{DOMAIN}_conversation_updated"
SIGNAL_TOOLS_UPDATED = f"{DOMAIN}_tools_updated"
SIGNAL_MCP_SERVERS_UPDATED = f"{DOMAIN}_mcp_servers_updated"


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register WebSocket commands."""
    websocket_api.async_register_command(hass, ws_get_conversations)
    websocket_api.async_register_command(hass, ws_get_conversation_history)
    websocket_api.async_register_command(hass, ws_clear_conversation)
    websocket_api.async_register_command(hass, ws_get_tools)
    websocket_api.async_register_command(hass, ws_get_mcp_servers)
    websocket_api.async_register_command(hass, ws_get_agent_status)
    websocket_api.async_register_command(hass, ws_subscribe_events)


@websocket_api.websocket_command({
    vol.Required("type"): "cortex_agent/get_conversations",
    vol.Required("entry_id"): str,
})
@callback
async def ws_get_conversations(
    hass: HomeAssistant, connection: ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Get all conversations for an agent."""
    entry_id = msg["entry_id"]
    
    if entry_id not in hass.data.get(DOMAIN, {}):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Agent not found")
        return
        
    agent_data = hass.data[DOMAIN][entry_id]
    agent = agent_data.get(DATA_AGENT)
    
    if not agent or not hasattr(agent, "conversation_manager"):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Conversation manager not found")
        return
    
    # Get all conversation IDs and metadata
    conversations = []
    for conversation_id in agent.conversation_manager.get_conversation_ids():
        # Get first and last message for preview
        history = agent.conversation_manager.get_conversation(conversation_id)
        
        first_message = history[0].content if history else ""
        last_message = history[-1].content if history else ""
        
        conversations.append({
            "id": conversation_id,
            "first_message": first_message[:100] + "..." if len(first_message) > 100 else first_message,
            "last_message": last_message[:100] + "..." if len(last_message) > 100 else last_message,
            "message_count": len(history),
            "created_at": agent.conversation_manager.get_conversation_metadata(conversation_id).get("created_at"),
            "updated_at": agent.conversation_manager.get_conversation_metadata(conversation_id).get("updated_at"),
        })
    
    connection.send_result(msg["id"], {"conversations": conversations})


@websocket_api.websocket_command({
    vol.Required("type"): "cortex_agent/get_conversation_history",
    vol.Required("entry_id"): str,
    vol.Required("conversation_id"): str,
})
@callback
async def ws_get_conversation_history(
    hass: HomeAssistant, connection: ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Get conversation history."""
    entry_id = msg["entry_id"]
    conversation_id = msg["conversation_id"]
    
    if entry_id not in hass.data.get(DOMAIN, {}):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Agent not found")
        return
        
    agent_data = hass.data[DOMAIN][entry_id]
    agent = agent_data.get(DATA_AGENT)
    
    if not agent or not hasattr(agent, "conversation_manager"):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Conversation manager not found")
        return
    
    # Get conversation history
    history = agent.conversation_manager.get_conversation(conversation_id)
    if not history:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Conversation not found")
        return
    
    # Convert to serializable format
    messages = []
    for message in history:
        messages.append({
            "role": message.role.value,
            "content": message.content,
            "timestamp": message.timestamp.isoformat() if hasattr(message, "timestamp") else None,
        })
    
    metadata = agent.conversation_manager.get_conversation_metadata(conversation_id)
    
    connection.send_result(msg["id"], {
        "conversation_id": conversation_id,
        "messages": messages,
        "metadata": metadata,
    })


@websocket_api.websocket_command({
    vol.Required("type"): "cortex_agent/clear_conversation",
    vol.Required("entry_id"): str,
    vol.Optional("conversation_id"): str,
})
@callback
async def ws_clear_conversation(
    hass: HomeAssistant, connection: ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Clear a conversation or all conversations."""
    entry_id = msg["entry_id"]
    conversation_id = msg.get("conversation_id")
    
    if entry_id not in hass.data.get(DOMAIN, {}):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Agent not found")
        return
        
    agent_data = hass.data[DOMAIN][entry_id]
    agent = agent_data.get(DATA_AGENT)
    
    if not agent or not hasattr(agent, "conversation_manager"):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Conversation manager not found")
        return
    
    try:
        if conversation_id:
            # Clear specific conversation
            await agent.conversation_manager.clear_conversation(conversation_id)
        else:
            # Clear all conversations
            await agent.conversation_manager.clear_all_conversations()
            
        # Save changes
        await agent.conversation_manager.async_save()
        
        connection.send_result(msg["id"], {"success": True})
    except Exception as ex:
        _LOGGER.error("Error clearing conversation: %s", ex)
        connection.send_error(msg["id"], "server_error", str(ex))


@websocket_api.websocket_command({
    vol.Required("type"): "cortex_agent/get_tools",
    vol.Required("entry_id"): str,
    vol.Optional("category"): str,
})
@callback
async def ws_get_tools(
    hass: HomeAssistant, connection: ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Get available tools."""
    entry_id = msg["entry_id"]
    category = msg.get("category")
    
    if entry_id not in hass.data.get(DOMAIN, {}):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Agent not found")
        return
        
    agent_data = hass.data[DOMAIN][entry_id]
    agent = agent_data.get(DATA_AGENT)
    
    if not agent or not hasattr(agent, "tool_registry"):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Tool registry not found")
        return
    
    # Get tools
    if category:
        tools = agent.tool_registry.get_tools_by_category(category)
    else:
        tools = agent.tool_registry.get_all_tools()
    
    # Convert to serializable format
    tool_list = []
    for tool in tools:
        tool_list.append({
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"],
            "category": tool["category"],
        })
    
    connection.send_result(msg["id"], {"tools": tool_list})


@websocket_api.websocket_command({
    vol.Required("type"): "cortex_agent/get_mcp_servers",
    vol.Required("entry_id"): str,
})
@callback
async def ws_get_mcp_servers(
    hass: HomeAssistant, connection: ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Get connected MCP servers."""
    entry_id = msg["entry_id"]
    
    if entry_id not in hass.data.get(DOMAIN, {}):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Agent not found")
        return
        
    agent_data = hass.data[DOMAIN][entry_id]
    mcp_connector = agent_data.get("mcp_connector")
    
    if not mcp_connector:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "MCP connector not found")
        return
    
    # Get connected servers
    server_names = mcp_connector.get_connected_servers()
    
    # Get tools for each server
    servers = []
    for server_name in server_names:
        tools = await mcp_connector.async_get_server_tools(server_name)
        
        # Convert tools to serializable format
        tool_list = []
        for tool in tools:
            tool_list.append({
                "name": tool.tool_name,
                "description": tool.description,
                "parameters": tool.parameters,
            })
        
        servers.append({
            "name": server_name,
            "tools": tool_list,
            "tool_count": len(tool_list),
        })
    
    connection.send_result(msg["id"], {"servers": servers})


@websocket_api.websocket_command({
    vol.Required("type"): "cortex_agent/get_agent_status",
    vol.Required("entry_id"): str,
})
@callback
async def ws_get_agent_status(
    hass: HomeAssistant, connection: ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Get agent status."""
    entry_id = msg["entry_id"]
    
    if entry_id not in hass.data.get(DOMAIN, {}):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Agent not found")
        return
        
    agent_data = hass.data[DOMAIN][entry_id]
    agent = agent_data.get(DATA_AGENT)
    
    if not agent:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Agent not found")
        return
    
    # Get status information
    status = {
        "provider": agent.model_provider.__class__.__name__,
        "model_id": agent.entry.data.get("model_id", "unknown"),
        "conversation_count": len(agent.conversation_manager.get_conversation_ids()) if hasattr(agent, "conversation_manager") else 0,
        "tool_count": len(agent.tool_registry.get_all_tools()) if hasattr(agent, "tool_registry") else 0,
        "memory_enabled": agent.memory_handler is not None,
        "memory_count": len(await agent.memory_handler.get_all_memories()) if agent.memory_handler else 0,
        "mcp_server_count": len(agent.mcp_connector.get_connected_servers()) if agent.mcp_connector else 0,
    }
    
    connection.send_result(msg["id"], {"status": status})


@websocket_api.websocket_command({
    vol.Required("type"): "cortex_agent/subscribe_events",
    vol.Required("entry_id"): str,
})
@callback
def ws_subscribe_events(
    hass: HomeAssistant, connection: ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Subscribe to events."""
    entry_id = msg["entry_id"]
    
    if entry_id not in hass.data.get(DOMAIN, {}):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Agent not found")
        return
    
    @callback
    def forward_conversation_events(event_data: Dict[str, Any]) -> None:
        """Forward conversation events to websocket."""
        connection.send_message({
            "id": msg["id"],
            "type": "event",
            "event": {
                "type": "conversation_updated",
                "data": event_data,
            },
        })
    
    @callback
    def forward_tools_events(event_data: Dict[str, Any]) -> None:
        """Forward tools events to websocket."""
        connection.send_message({
            "id": msg["id"],
            "type": "event",
            "event": {
                "type": "tools_updated",
                "data": event_data,
            },
        })
    
    @callback
    def forward_mcp_events(event_data: Dict[str, Any]) -> None:
        """Forward MCP server events to websocket."""
        connection.send_message({
            "id": msg["id"],
            "type": "event",
            "event": {
                "type": "mcp_servers_updated",
                "data": event_data,
            },
        })
    
    # Subscribe to events
    unsub_conversation = async_dispatcher_connect(
        hass, f"{SIGNAL_CONVERSATION_UPDATED}_{entry_id}", forward_conversation_events
    )
    unsub_tools = async_dispatcher_connect(
        hass, f"{SIGNAL_TOOLS_UPDATED}_{entry_id}", forward_tools_events
    )
    unsub_mcp = async_dispatcher_connect(
        hass, f"{SIGNAL_MCP_SERVERS_UPDATED}_{entry_id}", forward_mcp_events
    )
    
    # Register unsubscribe function
    connection.subscriptions[msg["id"]] = lambda: [
        unsub_conversation(),
        unsub_tools(),
        unsub_mcp(),
    ]
    
    connection.send_result(msg["id"])