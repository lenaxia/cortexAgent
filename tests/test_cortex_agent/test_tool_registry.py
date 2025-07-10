"""Tests for the CortexAgent tool registry."""
from unittest.mock import patch, MagicMock
import pytest

from homeassistant.core import HomeAssistant

from custom_components.cortex_agent.tool_registry import (
    ToolRegistry,
    register_tool,
)
from custom_components.cortex_agent.models import ToolMetadata


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MagicMock(spec=HomeAssistant)


@pytest.fixture
def tool_registry(mock_hass):
    """Create a tool registry."""
    return ToolRegistry(mock_hass)


@pytest.fixture
def sample_tool_function():
    """Sample tool function."""
    def sample_tool(hass, arg1=None, arg2=None):
        """Sample tool for testing."""
        return {"result": f"Processed {arg1} and {arg2}"}
    return sample_tool


@pytest.fixture
def sample_tool_metadata():
    """Sample tool metadata."""
    return ToolMetadata(
        name="sample_tool",
        description="A sample tool for testing",
        category="test",
        permissions=["read"],
        examples=["Example usage"],
        parameters={"arg1": {"type": "string"}, "arg2": {"type": "number"}}
    )


class TestToolRegistry:
    """Test the tool registry."""

    def test_init(self, mock_hass):
        """Test initialization."""
        registry = ToolRegistry(mock_hass)
        
        assert registry.hass == mock_hass
        assert registry._tools == {}
        assert registry._categories == {}

    def test_register_tool_with_metadata(self, tool_registry, sample_tool_function, sample_tool_metadata):
        """Test registering a tool with metadata."""
        tool_registry.register_tool(
            "sample_tool",
            sample_tool_function,
            sample_tool_metadata
        )
        
        assert "sample_tool" in tool_registry._tools
        assert tool_registry._tools["sample_tool"]["function"] == sample_tool_function
        assert tool_registry._tools["sample_tool"]["metadata"] == sample_tool_metadata
        
        # Check category registration
        assert "test" in tool_registry._categories
        assert "sample_tool" in tool_registry._categories["test"]

    def test_register_tool_without_metadata(self, tool_registry, sample_tool_function):
        """Test registering a tool without metadata."""
        tool_registry.register_tool("sample_tool", sample_tool_function)
        
        assert "sample_tool" in tool_registry._tools
        assert tool_registry._tools["sample_tool"]["function"] == sample_tool_function
        
        # Check that default metadata was created
        metadata = tool_registry._tools["sample_tool"]["metadata"]
        assert metadata.name == "sample_tool"
        assert "Sample tool for testing" in metadata.description
        assert metadata.category == "uncategorized"
        
        # Check category registration
        assert "uncategorized" in tool_registry._categories
        assert "sample_tool" in tool_registry._categories["uncategorized"]

    def test_register_tool_overwrite(self, tool_registry, sample_tool_function, sample_tool_metadata):
        """Test overwriting an existing tool."""
        # Register first tool
        tool_registry.register_tool(
            "sample_tool",
            sample_tool_function,
            sample_tool_metadata
        )
        
        # Create a new function and metadata
        new_function = lambda hass, x: x * 2
        new_metadata = ToolMetadata(
            name="sample_tool",
            description="New description",
            category="new_category"
        )
        
        # Register with same ID
        tool_registry.register_tool(
            "sample_tool",
            new_function,
            new_metadata
        )
        
        # Check that tool was overwritten
        assert tool_registry._tools["sample_tool"]["function"] == new_function
        assert tool_registry._tools["sample_tool"]["metadata"] == new_metadata
        
        # Check that category was updated
        assert "test" not in tool_registry._categories  # Category should be removed when empty
        assert "sample_tool" in tool_registry._categories["new_category"]

    def test_unregister_tool(self, tool_registry, sample_tool_function, sample_tool_metadata):
        """Test unregistering a tool."""
        # Register tool
        tool_registry.register_tool(
            "sample_tool",
            sample_tool_function,
            sample_tool_metadata
        )
        
        # Unregister tool
        result = tool_registry.unregister_tool("sample_tool")
        
        # Check result
        assert result is True
        assert "sample_tool" not in tool_registry._tools
        assert "test" not in tool_registry._categories  # Category should be removed when empty

    def test_unregister_nonexistent_tool(self, tool_registry):
        """Test unregistering a tool that doesn't exist."""
        result = tool_registry.unregister_tool("nonexistent_tool")
        assert result is False

    def test_get_tool(self, tool_registry, sample_tool_function, sample_tool_metadata):
        """Test getting a tool by ID."""
        # Register tool
        tool_registry.register_tool(
            "sample_tool",
            sample_tool_function,
            sample_tool_metadata
        )
        
        # Get tool
        tool = tool_registry.get_tool("sample_tool")
        
        # Check result
        assert tool == sample_tool_function

    def test_get_nonexistent_tool(self, tool_registry):
        """Test getting a tool that doesn't exist."""
        tool = tool_registry.get_tool("nonexistent_tool")
        assert tool is None

    def test_get_all_tools(self, tool_registry, sample_tool_function):
        """Test getting all tools."""
        # Register multiple tools
        tool_registry.register_tool("tool1", sample_tool_function)
        tool_registry.register_tool("tool2", lambda hass: "tool2")
        
        # Get all tools
        tools = tool_registry.get_all_tools()
        
        # Check result
        assert len(tools) == 2
        assert sample_tool_function in tools

    def test_get_tools_by_category(self, tool_registry, sample_tool_function):
        """Test getting tools by category."""
        # Register tools in different categories
        tool_registry.register_tool(
            "tool1",
            sample_tool_function,
            ToolMetadata(name="tool1", description="Tool 1", category="category1")
        )
        tool_registry.register_tool(
            "tool2",
            lambda hass: "tool2",
            ToolMetadata(name="tool2", description="Tool 2", category="category1")
        )
        tool_registry.register_tool(
            "tool3",
            lambda hass: "tool3",
            ToolMetadata(name="tool3", description="Tool 3", category="category2")
        )
        
        # Get tools by category
        category1_tools = tool_registry.get_tools_by_category("category1")
        category2_tools = tool_registry.get_tools_by_category("category2")
        
        # Check results
        assert len(category1_tools) == 2
        assert len(category2_tools) == 1
        assert sample_tool_function in category1_tools

    def test_get_tool_metadata(self, tool_registry, sample_tool_function, sample_tool_metadata):
        """Test getting tool metadata."""
        # Register tool
        tool_registry.register_tool(
            "sample_tool",
            sample_tool_function,
            sample_tool_metadata
        )
        
        # Get metadata
        metadata = tool_registry.get_tool_metadata("sample_tool")
        
        # Check result
        assert metadata == sample_tool_metadata

    def test_get_categories(self, tool_registry):
        """Test getting all categories."""
        # Register tools in different categories
        tool_registry.register_tool(
            "tool1",
            lambda hass: "tool1",
            ToolMetadata(name="tool1", description="Tool 1", category="category1")
        )
        tool_registry.register_tool(
            "tool2",
            lambda hass: "tool2",
            ToolMetadata(name="tool2", description="Tool 2", category="category2")
        )
        
        # Get categories
        categories = tool_registry.get_categories()
        
        # Check result
        assert len(categories) == 2
        assert "category1" in categories
        assert "category2" in categories

    def test_get_tool_count(self, tool_registry):
        """Test getting tool count."""
        # Register tools
        tool_registry.register_tool("tool1", lambda hass: "tool1")
        tool_registry.register_tool("tool2", lambda hass: "tool2")
        
        # Get count
        count = tool_registry.get_tool_count()
        
        # Check result
        assert count == 2

    def test_get_tools_info(self, tool_registry, sample_tool_function, sample_tool_metadata):
        """Test getting tools info."""
        # Register tools in different categories
        tool_registry.register_tool(
            "tool1",
            sample_tool_function,
            sample_tool_metadata
        )
        tool_registry.register_tool(
            "tool2",
            lambda hass: "tool2",
            ToolMetadata(name="tool2", description="Tool 2", category="category2")
        )
        
        # Get tools info
        tools_info = tool_registry.get_tools_info()
        
        # Check result
        assert "test" in tools_info
        assert "category2" in tools_info
        assert len(tools_info["test"]) == 1
        assert tools_info["test"][0]["id"] == "tool1"
        assert tools_info["test"][0]["name"] == "sample_tool"

    def test_clear(self, tool_registry):
        """Test clearing all tools."""
        # Register tools
        tool_registry.register_tool("tool1", lambda hass: "tool1")
        tool_registry.register_tool("tool2", lambda hass: "tool2")
        
        # Clear registry
        tool_registry.clear()
        
        # Check result
        assert tool_registry._tools == {}
        assert tool_registry._categories == {}
        assert tool_registry.get_tool_count() == 0


class TestRegisterToolDecorator:
    """Test the register_tool decorator."""

    def test_decorator(self, tool_registry):
        """Test using the decorator to register a tool."""
        # Define a function with the decorator
        @register_tool(tool_registry, ToolMetadata(
            name="decorated_tool",
            description="A tool registered with a decorator",
            category="decorated"
        ))
        def decorated_tool(hass, arg1=None):
            """Decorated tool function."""
            return {"result": arg1}
        
        # Check that the tool was registered
        assert "decorated_tool" in tool_registry._tools
        assert tool_registry._tools["decorated_tool"]["function"] == decorated_tool
        assert tool_registry._tools["decorated_tool"]["metadata"].name == "decorated_tool"
        assert "decorated" in tool_registry._categories

    def test_decorator_without_metadata(self, tool_registry):
        """Test using the decorator without metadata."""
        # Define a function with the decorator
        @register_tool(tool_registry)
        def simple_tool(hass, arg1=None):
            """Simple tool function."""
            return {"result": arg1}
        
        # Check that the tool was registered with default metadata
        assert "simple_tool" in tool_registry._tools
        assert tool_registry._tools["simple_tool"]["function"] == simple_tool
        assert tool_registry._tools["simple_tool"]["metadata"].name == "simple_tool"
        assert "Simple tool function." in tool_registry._tools["simple_tool"]["metadata"].description