"""Tool registry for the Cortex Agent integration."""
from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from .models import ToolMetadata

_LOGGER = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for tools that can be used by the agent."""

    def __init__(self, hass: Any) -> None:
        """Initialize the tool registry."""
        self.hass = hass
        self._tools: dict[str, dict[str, Any]] = {}
        self._categories: dict[str, list[str]] = {}

    def register_tool(
        self,
        tool_id: str | None = None,
        tool_fn: Callable | None = None,
        metadata: ToolMetadata | None = None,
        **kwargs
    ) -> None:
        """Register a tool with the registry.

        Can be called in two ways:
        1. register_tool(tool_id, tool_fn, metadata)
        2. register_tool(name="tool_name", function=tool_fn, description="desc", ...)
        """
        # Handle the case where it's called with named parameters
        if kwargs:
            # Extract parameters from kwargs
            name = kwargs.get("name", tool_id)
            function = kwargs.get("function", tool_fn)
            description = kwargs.get("description", "")
            category = kwargs.get("category", "uncategorized")
            parameters = kwargs.get("parameters", {})
            permissions = kwargs.get("permissions", [])
            examples = kwargs.get("examples", [])

            # Create metadata from kwargs
            metadata = ToolMetadata(
                name=name,
                description=description,
                category=category,
                parameters=parameters,
                permissions=permissions,
                examples=examples
            )

            # Use name as tool_id and function as tool_fn
            tool_id = name
            tool_fn = function

        if tool_id is None or tool_fn is None:
            raise ValueError("Tool ID and function are required")

        if tool_id in self._tools:
            _LOGGER.warning("Tool %s already registered, overwriting", tool_id)

        # Create default metadata if not provided
        if metadata is None:
            # Extract description from docstring if available
            description = "No description available."
            if tool_fn.__doc__:
                # Get first line of docstring
                description = tool_fn.__doc__.strip().split('\n')[0]
                if not description.endswith('.'):
                    description += '.'

            metadata = ToolMetadata(
                name=tool_id,
                description=description
            )

        category = metadata.category

        # Store the tool
        self._tools[tool_id] = {
            "function": tool_fn,
            "metadata": metadata
        }

        # Add to category
        if category not in self._categories:
            self._categories[category] = []

        # Remove from old category if it was already registered
        for cat, tools in list(self._categories.items()):
            if tool_id in tools and cat != category:
                tools.remove(tool_id)
                # Clean up empty categories
                if not tools:
                    del self._categories[cat]
                break

        # Add to new category
        if category not in self._categories:
            self._categories[category] = []

        if tool_id not in self._categories[category]:
            self._categories[category].append(tool_id)

        _LOGGER.info("Registered tool %s in category %s", tool_id, category)

    def unregister_tool(self, tool_id: str) -> bool:
        """Unregister a tool from the registry."""
        if tool_id not in self._tools:
            return False

        # Remove from tools
        del self._tools[tool_id]

        # Remove from category
        for cat, tools in list(self._categories.items()):
            if tool_id in tools:
                tools.remove(tool_id)

                # Clean up empty category
                if not tools:
                    del self._categories[cat]

        _LOGGER.info("Unregistered tool %s", tool_id)
        return True

    def get_tool(self, tool_id: str) -> Callable | None:
        """Get a tool by ID."""
        tool_data = self._tools.get(tool_id)
        return tool_data["function"] if tool_data else None

    def get_all_tools(self) -> list[Callable]:
        """Get all registered tools."""
        return [tool_data["function"] for tool_data in self._tools.values()]

    def get_tools_by_category(self, category: str) -> list[Callable]:
        """Get all tools in a category."""
        tool_ids = self._categories.get(category, [])
        return [self._tools[tool_id]["function"] for tool_id in tool_ids if tool_id in self._tools]

    def get_tool_metadata(self, tool_id: str) -> ToolMetadata | None:
        """Get metadata for a tool."""
        tool_data = self._tools.get(tool_id)
        return tool_data["metadata"] if tool_data else None

    def get_categories(self) -> list[str]:
        """Get all registered categories."""
        return list(self._categories.keys())

    def get_category_tools(self, category: str) -> list[str]:
        """Get all tool IDs in a category."""
        return self._categories.get(category, [])

    def get_tool_count(self) -> int:
        """Get the total number of registered tools."""
        return len(self._tools)

    def get_tools_info(self) -> dict[str, list[dict[str, Any]]]:
        """Get information about all tools organized by category."""
        tools_info: dict[str, list[dict[str, Any]]] = {}

        for category in self.get_categories():
            tools_info[category] = []
            tool_ids = self._categories.get(category, [])

            for tool_id in tool_ids:
                if tool_id in self._tools:
                    metadata = self._tools[tool_id]["metadata"]
                    tools_info[category].append({
                        "id": tool_id,
                        "name": metadata.name,
                        "description": metadata.description,
                        "permissions": metadata.permissions,
                        "examples": metadata.examples,
                        "parameters": metadata.parameters
                    })

        return tools_info

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._categories.clear()
        _LOGGER.info("Cleared all registered tools")


def register_tool(
    registry: ToolRegistry, metadata: ToolMetadata | None = None, **kwargs
) -> Callable[[Callable], Callable]:
    """Decorator to register a tool with the registry."""
    def decorator(func: Callable) -> Callable:
        # Use function name as tool ID if not specified in metadata or kwargs
        if metadata and metadata.name:
            tool_id = metadata.name
        else:
            tool_id = kwargs.get("name", func.__name__)

        # Register the tool
        if kwargs:
            # If kwargs are provided, pass them along with the function
            kwargs["function"] = func
            registry.register_tool(**kwargs)
        else:
            # Otherwise use the traditional method
            registry.register_tool(tool_id, func, metadata)
        return func
    return decorator
