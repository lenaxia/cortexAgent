"""Tool registry for CortexAgent."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import asdict

from .models import ToolMetadata

_LOGGER = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for tools that can be used by the agent."""
    
    def __init__(self, hass):
        """Initialize the tool registry."""
        self.hass = hass
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register_tool(
        self,
        tool_id: str,
        tool_fn: Callable,
        metadata: Optional[ToolMetadata] = None
    ) -> None:
        """Register a tool with the registry."""
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
        
        # Get the tool's category
        metadata = self._tools[tool_id]["metadata"]
        category = metadata.category
        
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
    
    def get_tool(self, tool_id: str) -> Optional[Callable]:
        """Get a tool by ID."""
        tool_data = self._tools.get(tool_id)
        return tool_data["function"] if tool_data else None
    
    def get_all_tools(self) -> List[Callable]:
        """Get all registered tools."""
        return [tool_data["function"] for tool_data in self._tools.values()]
    
    def get_tools_by_category(self, category: str) -> List[Callable]:
        """Get all tools in a category."""
        tool_ids = self._categories.get(category, [])
        return [self._tools[tool_id]["function"] for tool_id in tool_ids if tool_id in self._tools]
    
    def get_tool_metadata(self, tool_id: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool."""
        tool_data = self._tools.get(tool_id)
        return tool_data["metadata"] if tool_data else None
    
    def get_categories(self) -> List[str]:
        """Get all registered categories."""
        return list(self._categories.keys())
    
    def get_tool_count(self) -> int:
        """Get the total number of registered tools."""
        return len(self._tools)
    
    def get_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all tools organized by category."""
        tools_info = {}
        
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


def register_tool(registry: ToolRegistry, metadata: Optional[ToolMetadata] = None):
    """Decorator to register a tool with the registry."""
    def decorator(func):
        # Use function name as tool ID if not specified in metadata
        tool_id = metadata.name if metadata and metadata.name else func.__name__
        
        # Register the tool
        registry.register_tool(tool_id, func, metadata)
        return func
    return decorator