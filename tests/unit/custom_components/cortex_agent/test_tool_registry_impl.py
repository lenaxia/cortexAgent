"""Tests for the ToolRegistry implementation."""
import pytest
from unittest.mock import MagicMock

from custom_components.cortex_agent.models import ToolMetadata
from custom_components.cortex_agent.tool_registry import ToolRegistry


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MagicMock()


def test_tool_registry_init(mock_hass):
    """Test ToolRegistry initialization."""
    registry = ToolRegistry(mock_hass)
    
    assert registry.hass == mock_hass
    assert registry._tools == {}
    assert registry._categories == {}


def test_tool_registry_register_tool(mock_hass):
    """Test registering a tool."""
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


def test_tool_registry_register_tool_without_metadata(mock_hass):
    """Test registering a tool without metadata."""
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


def test_tool_registry_register_tool_overwrite(mock_hass):
    """Test overwriting an existing tool."""
    registry = ToolRegistry(mock_hass)
    
    def mock_tool_1():
        return "result 1"
    
    def mock_tool_2():
        return "result 2"
    
    # Register first tool
    registry.register_tool("test_tool", mock_tool_1)
    assert registry._tools["test_tool"]["function"] == mock_tool_1
    
    # Register second tool with same name (should overwrite)
    registry.register_tool("test_tool", mock_tool_2)
    assert registry._tools["test_tool"]["function"] == mock_tool_2


def test_tool_registry_get_tool(mock_hass):
    """Test getting a tool by ID."""
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


def test_tool_registry_get_all_tools(mock_hass):
    """Test getting all registered tools."""
    registry = ToolRegistry(mock_hass)
    
    def tool_1():
        return "result 1"
    
    def tool_2():
        return "result 2"
    
    # Register tools
    registry.register_tool("tool_1", tool_1)
    registry.register_tool("tool_2", tool_2)
    
    # Get all tools
    all_tools = registry.get_all_tools()
    
    assert len(all_tools) == 2
    assert tool_1 in all_tools
    assert tool_2 in all_tools


def test_tool_registry_get_tools_by_category(mock_hass):
    """Test getting tools by category."""
    registry = ToolRegistry(mock_hass)
    
    def tool_1():
        return "result 1"
    
    def tool_2():
        return "result 2"
    
    def tool_3():
        return "result 3"
    
    # Register tools in different categories
    registry.register_tool("tool_1", tool_1, ToolMetadata("tool_1", "desc", "category_a"))
    registry.register_tool("tool_2", tool_2, ToolMetadata("tool_2", "desc", "category_a"))
    registry.register_tool("tool_3", tool_3, ToolMetadata("tool_3", "desc", "category_b"))
    
    # Get tools by category
    category_a_tools = registry.get_tools_by_category("category_a")
    category_b_tools = registry.get_tools_by_category("category_b")
    non_existent_tools = registry.get_tools_by_category("non_existent")
    
    assert len(category_a_tools) == 2
    assert tool_1 in category_a_tools
    assert tool_2 in category_a_tools
    
    assert len(category_b_tools) == 1
    assert tool_3 in category_b_tools
    
    assert len(non_existent_tools) == 0


def test_tool_registry_get_tool_metadata(mock_hass):
    """Test getting tool metadata."""
    registry = ToolRegistry(mock_hass)
    
    def mock_tool():
        return "mock result"
    
    metadata = ToolMetadata(
        name="mock_tool",
        description="A mock tool",
        category="testing",
        permissions=["read"],
        examples=["example usage"]
    )
    
    # Register the tool
    registry.register_tool("mock_tool", mock_tool, metadata)
    
    # Get metadata
    retrieved_metadata = registry.get_tool_metadata("mock_tool")
    
    assert retrieved_metadata == metadata
    assert retrieved_metadata.name == "mock_tool"
    assert retrieved_metadata.description == "A mock tool"
    assert retrieved_metadata.category == "testing"
    assert retrieved_metadata.permissions == ["read"]
    assert retrieved_metadata.examples == ["example usage"]
    
    # Try to get metadata for non-existent tool
    non_existent_metadata = registry.get_tool_metadata("non_existent")
    assert non_existent_metadata is None


def test_tool_registry_get_categories(mock_hass):
    """Test getting all categories."""
    registry = ToolRegistry(mock_hass)
    
    def tool_1():
        return "result 1"
    
    def tool_2():
        return "result 2"
    
    def tool_3():
        return "result 3"
    
    # Register tools in different categories
    registry.register_tool("tool_1", tool_1, ToolMetadata("tool_1", "desc", "category_a"))
    registry.register_tool("tool_2", tool_2, ToolMetadata("tool_2", "desc", "category_b"))
    registry.register_tool("tool_3", tool_3, ToolMetadata("tool_3", "desc", "category_a"))
    
    # Get categories
    categories = registry.get_categories()
    
    assert len(categories) == 2
    assert "category_a" in categories
    assert "category_b" in categories


def test_tool_registry_unregister_tool(mock_hass):
    """Test unregistering a tool."""
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
    assert "mock_tool" not in registry._categories["testing"]
    
    # Try to unregister non-existent tool
    result = registry.unregister_tool("non_existent")
    assert result is False


def test_tool_registry_unregister_tool_cleans_empty_category(mock_hass):
    """Test that unregistering the last tool in a category removes the category."""
    registry = ToolRegistry(mock_hass)
    
    def mock_tool():
        return "mock result"
    
    metadata = ToolMetadata("mock_tool", "desc", "testing")
    
    # Register the tool
    registry.register_tool("mock_tool", mock_tool, metadata)
    
    assert "testing" in registry._categories
    
    # Unregister the tool
    registry.unregister_tool("mock_tool")
    
    # Category should be removed since it's empty
    assert "testing" not in registry._categories


def test_tool_registry_get_tool_count(mock_hass):
    """Test getting the total number of registered tools."""
    registry = ToolRegistry(mock_hass)
    
    assert registry.get_tool_count() == 0
    
    def tool_1():
        return "result 1"
    
    def tool_2():
        return "result 2"
    
    # Register tools
    registry.register_tool("tool_1", tool_1)
    registry.register_tool("tool_2", tool_2)
    
    assert registry.get_tool_count() == 2
    
    # Unregister one tool
    registry.unregister_tool("tool_1")
    
    assert registry.get_tool_count() == 1