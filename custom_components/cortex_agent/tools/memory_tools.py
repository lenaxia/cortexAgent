"""Memory tools for the CortexAgent integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant

from ..tool_registry import ToolMetadata, ToolRegistry, register_tool

_LOGGER = logging.getLogger(__name__)

# Get the tool registry instance
tool_registry = ToolRegistry(HomeAssistant)


@register_tool(
    registry=tool_registry,
    metadata=ToolMetadata(
        name="store_memory",
        description="Store information in memory for later retrieval",
        category="memory",
        permissions=["write"],
        examples=[
            "Remember that I prefer window seats on flights",
            "Store that my favorite color is blue"
        ],
        parameters={
            "content": {
                "type": "string",
                "description": "The information to store in memory",
                "required": True
            },
            "metadata": {
                "type": "object",
                "description": "Optional metadata to associate with the memory",
                "required": False
            }
        }
    )
)
async def store_memory(hass: HomeAssistant, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Store information in memory for later retrieval.
    
    Args:
        hass: Home Assistant instance
        content: The information to store
        metadata: Optional metadata to associate with the memory
        
    Returns:
        A dictionary with the result
    """
    try:
        # Get the memory handler from the agent
        memory_handler = None
        for entry_data in hass.data.get("cortex_agent", {}).values():
            agent = entry_data.get("agent")
            if agent and hasattr(agent, "memory_handler"):
                memory_handler = agent.memory_handler
                break
                
        if not memory_handler:
            return {"success": False, "error": "Memory handler not found"}
            
        # Store the memory
        result = await memory_handler.async_store(content, metadata)
        
        return result
    except Exception as err:
        _LOGGER.error("Error storing memory: %s", str(err))
        return {"success": False, "error": str(err)}


@register_tool(
    registry=tool_registry,
    metadata=ToolMetadata(
        name="retrieve_memory",
        description="Retrieve information from memory based on a query",
        category="memory",
        permissions=["read"],
        examples=[
            "What do I prefer for flights?",
            "What's my favorite color?"
        ],
        parameters={
            "query": {
                "type": "string",
                "description": "The query to search for in memory",
                "required": True
            }
        }
    )
)
async def retrieve_memory(hass: HomeAssistant, query: str) -> Dict[str, Any]:
    """Retrieve information from memory based on a query.
    
    Args:
        hass: Home Assistant instance
        query: The query to search for
        
    Returns:
        A dictionary with the result
    """
    try:
        # Get the memory handler from the agent
        memory_handler = None
        for entry_data in hass.data.get("cortex_agent", {}).values():
            agent = entry_data.get("agent")
            if agent and hasattr(agent, "memory_handler"):
                memory_handler = agent.memory_handler
                break
                
        if not memory_handler:
            return {"success": False, "error": "Memory handler not found"}
            
        # Retrieve the memory
        result = await memory_handler.async_retrieve(query)
        
        return result
    except Exception as err:
        _LOGGER.error("Error retrieving memory: %s", str(err))
        return {"success": False, "error": str(err)}


@register_tool(
    registry=tool_registry,
    metadata=ToolMetadata(
        name="list_memories",
        description="List all stored memories",
        category="memory",
        permissions=["read"],
        examples=[
            "What do you remember about me?",
            "List all memories"
        ]
    )
)
async def list_memories(hass: HomeAssistant) -> Dict[str, Any]:
    """List all stored memories.
    
    Args:
        hass: Home Assistant instance
        
    Returns:
        A dictionary with the result
    """
    try:
        # Get the memory handler from the agent
        memory_handler = None
        for entry_data in hass.data.get("cortex_agent", {}).values():
            agent = entry_data.get("agent")
            if agent and hasattr(agent, "memory_handler"):
                memory_handler = agent.memory_handler
                break
                
        if not memory_handler:
            return {"success": False, "error": "Memory handler not found"}
            
        # List all memories
        result = await memory_handler.async_list_all()
        
        return result
    except Exception as err:
        _LOGGER.error("Error listing memories: %s", str(err))
        return {"success": False, "error": str(err)}


@register_tool(
    registry=tool_registry,
    metadata=ToolMetadata(
        name="clear_memories",
        description="Clear all stored memories",
        category="memory",
        permissions=["write"],
        examples=[
            "Forget everything you know about me",
            "Clear all memories"
        ]
    )
)
async def clear_memories(hass: HomeAssistant) -> Dict[str, Any]:
    """Clear all stored memories.
    
    Args:
        hass: Home Assistant instance
        
    Returns:
        A dictionary with the result
    """
    try:
        # Get the memory handler from the agent
        memory_handler = None
        for entry_data in hass.data.get("cortex_agent", {}).values():
            agent = entry_data.get("agent")
            if agent and hasattr(agent, "memory_handler"):
                memory_handler = agent.memory_handler
                break
                
        if not memory_handler:
            return {"success": False, "error": "Memory handler not found"}
            
        # Clear all memories
        result = await memory_handler.async_clear()
        
        return result
    except Exception as err:
        _LOGGER.error("Error clearing memories: %s", str(err))
        return {"success": False, "error": str(err)}