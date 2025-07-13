"""Memory tools for the CortexAgent integration."""
from __future__ import annotations

import logging
from typing import Any

from custom_components.cortex_agent.tool_registry import ToolRegistry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

def register_memory_tools(tool_registry: ToolRegistry) -> None:
    """Register memory tools with the tool registry."""
    # Register store_memory tool
    tool_registry.register_tool(
        name="store_memory",
        description="Store information in memory for later retrieval",
        function=store_memory,
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

    # Register retrieve_memory tool
    tool_registry.register_tool(
        name="retrieve_memory",
        description="Retrieve information from memory based on a query",
        function=retrieve_memory,
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

    # Register list_memories tool
    tool_registry.register_tool(
        name="list_memories",
        description="List all stored memories",
        function=list_memories,
        category="memory",
        permissions=["read"],
        examples=[
            "What do you remember about me?",
            "List all memories"
        ]
    )

    # Register clear_memories tool
    tool_registry.register_tool(
        name="clear_memories",
        description="Clear all stored memories",
        function=clear_memories,
        category="memory",
        permissions=["write"],
        examples=[
            "Forget everything you know about me",
            "Clear all memories"
        ]
    )
async def store_memory(hass: HomeAssistant, content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
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
        return await memory_handler.async_store(content, metadata)
    except HomeAssistantError as err:
        # Catch Home Assistant specific errors
        _LOGGER.error("Home Assistant error storing memory: %s", str(err))
        return {"success": False, "error": str(err)}
    except ValueError as err:
        # Catch validation errors
        _LOGGER.error("Validation error storing memory: %s", str(err))
        return {"success": False, "error": str(err)}
    except Exception as err:  # pylint: disable=broad-except
        # We need to catch all exceptions to ensure the tool doesn't fail completely
        _LOGGER.exception("Unexpected error storing memory")
        return {"success": False, "error": str(err)}


async def retrieve_memory(hass: HomeAssistant, query: str) -> dict[str, Any]:
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
        return await memory_handler.async_retrieve(query)
    except HomeAssistantError as err:
        # Catch Home Assistant specific errors
        _LOGGER.error("Home Assistant error retrieving memory: %s", str(err))
        return {"success": False, "error": str(err)}
    except ValueError as err:
        # Catch validation errors
        _LOGGER.error("Validation error retrieving memory: %s", str(err))
        return {"success": False, "error": str(err)}
    except Exception as err:  # pylint: disable=broad-except
        # We need to catch all exceptions to ensure the tool doesn't fail completely
        _LOGGER.exception("Unexpected error retrieving memory")
        return {"success": False, "error": str(err)}


async def list_memories(hass: HomeAssistant) -> dict[str, Any]:
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
        return await memory_handler.async_list_all()
    except HomeAssistantError as err:
        # Catch Home Assistant specific errors
        _LOGGER.error("Home Assistant error listing memories: %s", str(err))
        return {"success": False, "error": str(err)}
    except ValueError as err:
        # Catch validation errors
        _LOGGER.error("Validation error listing memories: %s", str(err))
        return {"success": False, "error": str(err)}
    except Exception as err:  # pylint: disable=broad-except
        # We need to catch all exceptions to ensure the tool doesn't fail completely
        _LOGGER.exception("Unexpected error listing memories")
        return {"success": False, "error": str(err)}


async def clear_memories(hass: HomeAssistant) -> dict[str, Any]:
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
        return await memory_handler.async_clear()
    except HomeAssistantError as err:
        # Catch Home Assistant specific errors
        _LOGGER.error("Home Assistant error clearing memories: %s", str(err))
        return {"success": False, "error": str(err)}
    except ValueError as err:
        # Catch validation errors
        _LOGGER.error("Validation error clearing memories: %s", str(err))
        return {"success": False, "error": str(err)}
    except Exception as err:  # pylint: disable=broad-except
        # We need to catch all exceptions to ensure the tool doesn't fail completely
        _LOGGER.exception("Unexpected error clearing memories")
        return {"success": False, "error": str(err)}
