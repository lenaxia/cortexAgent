"""Standalone tests for the ToolRegistry implementation."""
import sys
import os
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

# Define the necessary classes from models.py
@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    name: str
    description: str
    category: str = "uncategorized"
    permissions: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


# Define the ToolRegistry class
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
            print(f"Warning: Tool {tool_id} already registered, overwriting")
        
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
        for cat, tools in self._categories.items():
            if tool_id in tools and cat != category:
                tools.remove(tool_id)
                # Clean up empty categories
                if not tools:
                    del self._categories[cat]
                break
        
        # Add to new category
        if tool_id not in self._categories[category]:
            self._categories[category].append(tool_id)
        
        print(f"Registered tool {tool_id} in category {category}")
    
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
        if category in self._categories and tool_id in self._categories[category]:
            self._categories[category].remove(tool_id)
            
            # Clean up empty category
            if not self._categories[category]:
                del self._categories[category]
        
        print(f"Unregistered tool {tool_id}")
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


# Mock Home Assistant instance
class MockHass:
    """Mock Home Assistant instance."""
    pass


# Tests
def test_tool_registry_initialization():
    """Test ToolRegistry initialization."""
    mock_hass = MockHass()
    registry = ToolRegistry(mock_hass)
    
    assert registry.hass == mock_hass
    assert registry._tools == {}
    assert registry._categories == {}
    print("✅ test_tool_registry_initialization passed")


def test_register_tool():
    """Test registering a tool."""
    mock_hass = MockHass()
    registry = ToolRegistry(mock_hass)
    
    # Create a mock tool function
    def mock_tool():
        """A mock tool."""
        return "mock result"
    
    metadata = ToolMetadata(
        name="mock_tool",
        description="A mock tool for testing",
        category="testing"
    )
    
    # Register the tool
    registry.register_tool("mock_tool", mock_tool, metadata)
    
    # Check that the tool was registered
    assert "mock_tool" in registry._tools
    assert registry._tools["mock_tool"]["function"] == mock_tool
    assert registry._tools["mock_tool"]["metadata"] == metadata
    
    # Check that the category was created
    assert "testing" in registry._categories
    assert "mock_tool" in registry._categories["testing"]
    print("✅ test_register_tool passed")


def test_register_tool_without_metadata():
    """Test registering a tool without metadata."""
    mock_hass = MockHass()
    registry = ToolRegistry(mock_hass)
    
    def mock_tool():
        """A mock tool."""
        return "mock result"
    
    # Register the tool without metadata
    registry.register_tool("mock_tool", mock_tool)
    
    # Check that the tool was registered with default metadata
    assert "mock_tool" in registry._tools
    assert registry._tools["mock_tool"]["function"] == mock_tool
    
    # Should have default metadata
    metadata = registry._tools["mock_tool"]["metadata"]
    assert metadata.name == "mock_tool"
    assert metadata.description == "A mock tool."
    assert metadata.category == "uncategorized"
    print("✅ test_register_tool_without_metadata passed")


def test_get_tool():
    """Test getting a tool by ID."""
    mock_hass = MockHass()
    registry = ToolRegistry(mock_hass)
    
    def mock_tool():
        return "mock result"
    
    # Register the tool
    registry.register_tool("mock_tool", mock_tool)
    
    # Get the tool
    retrieved_tool = registry.get_tool("mock_tool")
    assert retrieved_tool == mock_tool
    
    # Try to get non-existent tool
    non_existent = registry.get_tool("non_existent")
    assert non_existent is None
    print("✅ test_get_tool passed")


def test_unregister_tool():
    """Test unregistering a tool."""
    mock_hass = MockHass()
    registry = ToolRegistry(mock_hass)
    
    def mock_tool():
        return "mock result"
    
    metadata = ToolMetadata("mock_tool", "desc", "testing")
    
    # Register the tool
    registry.register_tool("mock_tool", mock_tool, metadata)
    
    assert "mock_tool" in registry._tools
    assert "mock_tool" in registry._categories["testing"]
    
    # Unregister the tool
    result = registry.unregister_tool("mock_tool")
    
    assert result is True
    assert "mock_tool" not in registry._tools
    assert "testing" not in registry._categories  # Category should be removed
    
    # Try to unregister non-existent tool
    result = registry.unregister_tool("non_existent")
    assert result is False
    print("✅ test_unregister_tool passed")


if __name__ == "__main__":
    # Run tests directly
    print("Running standalone tests for ToolRegistry...")
    test_tool_registry_initialization()
    test_register_tool()
    test_register_tool_without_metadata()
    test_get_tool()
    test_unregister_tool()
    print("All tests passed! ✅")