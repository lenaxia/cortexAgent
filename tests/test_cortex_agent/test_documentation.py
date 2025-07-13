"""Tests for the CortexAgent documentation component."""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from homeassistant.core import HomeAssistant, ServiceCall

from custom_components.cortex_agent.documentation import (
    ToolDocumentation,
)
from custom_components.cortex_agent.const import (
    DOMAIN,
    ATTR_ENTITY_ID,
    ATTR_FORMAT,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.bus = MagicMock()
    hass.bus.async_fire = AsyncMock()
    hass.services = MagicMock()
    hass.services.async_register = AsyncMock()
    return hass


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry."""
    registry = MagicMock()
    registry.get_categories = MagicMock(return_value=["category1", "category2"])
    registry.get_category_tools = MagicMock(side_effect=lambda category: {
        "category1": ["tool1", "tool2"],
        "category2": ["tool3"],
    }.get(category, []))
    registry._categories = {
        "category1": ["tool1", "tool2"],
        "category2": ["tool3"],
    }
    
    # Define tool data
    tool_data = {
        "tool1": {
            "metadata": {
                "name": "Tool 1",
                "description": "Description of Tool 1",
                "parameters": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter 1",
                        "required": True,
                    },
                    "param2": {
                        "type": "integer",
                        "description": "Parameter 2",
                        "required": False,
                    },
                },
                "examples": ["Example 1", "Example 2"],
            }
        },
        "tool2": {
            "metadata": {
                "name": "Tool 2",
                "description": "Description of Tool 2",
                "parameters": {},
                "examples": [],
            }
        },
        "tool3": {
            "metadata": {
                "name": "Tool 3",
                "description": "Description of Tool 3",
                "parameters": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter 1",
                        "required": True,
                    },
                },
                "examples": ["Example 1"],
            }
        },
    }
    
    # Set up get_tool to return the appropriate tool data
    registry.get_tool = MagicMock(side_effect=lambda tool_id: tool_data.get(tool_id))
    return registry


@pytest.fixture
def tool_documentation(mock_hass, mock_tool_registry):
    """Create a ToolDocumentation instance."""
    return ToolDocumentation(mock_hass, mock_tool_registry)


class TestToolDocumentation:
    """Test the ToolDocumentation class."""

    def test_init(self, mock_hass, mock_tool_registry):
        """Test initialization."""
        doc = ToolDocumentation(mock_hass, mock_tool_registry)
        
        assert doc.hass == mock_hass
        assert doc.tool_registry == mock_tool_registry

    def test_generate_markdown(self, tool_documentation):
        """Test generating markdown documentation."""
        markdown = tool_documentation.generate_markdown()
        
        # Check that the markdown contains the expected content
        assert "# Available Agent Tools" in markdown
        assert "## Table of Contents" in markdown
        assert "- [Category1](#category1)" in markdown
        assert "- [Category2](#category2)" in markdown
        assert "## Category1" in markdown
        assert "## Category2" in markdown
        assert "### Tool 1" in markdown
        assert "### Tool 2" in markdown
        assert "### Tool 3" in markdown
        assert "Description of Tool 1" in markdown
        assert "Description of Tool 2" in markdown
        assert "Description of Tool 3" in markdown
        assert "#### Parameters" in markdown
        assert "| Name | Type | Description | Required |" in markdown
        assert "| `param1` | `string` | Parameter 1 | Yes |" in markdown
        assert "| `param2` | `integer` | Parameter 2 | No |" in markdown
        assert "#### Examples" in markdown
        assert "- Example 1" in markdown
        assert "- Example 2" in markdown

    def test_generate_html(self, tool_documentation):
        """Test generating HTML documentation."""
        with patch("markdown.markdown") as mock_markdown:
            mock_markdown.return_value = "<h1>Available Agent Tools</h1>"
            
            html = tool_documentation.generate_html()
            
            # Check that markdown was converted to HTML
            mock_markdown.assert_called_once()
            
            # Check that the HTML contains the expected content
            assert "<h1>Available Agent Tools</h1>" in html
            assert "<style>" in html
            assert "</style>" in html
            assert "<body>" in html
            assert "</body>" in html

    def test_generate_html_without_markdown_module(self, tool_documentation):
        """Test generating HTML documentation without markdown module."""
        with patch("markdown.markdown", side_effect=ImportError("No module named 'markdown'")):
            html = tool_documentation.generate_html()
            
            # Check that the HTML contains the raw markdown
            assert "<pre>" in html
            assert "</pre>" in html
            assert "# Available Agent Tools" in html

    async def test_async_register_services(self, tool_documentation):
        """Test registering services."""
        # Register services
        await tool_documentation.async_register_services()
        
        # Check that services were registered
        tool_documentation.hass.services.async_register.assert_called_once()
        
        # Check service name - it's the second positional argument
        service_name = tool_documentation.hass.services.async_register.call_args[0][1]
        assert service_name == "generate_tool_documentation"

    async def test_handle_generate_documentation_markdown(self, tool_documentation):
        """Test handling generate_tool_documentation service call with markdown format."""
        # Create service call
        service_call = MagicMock(spec=ServiceCall)
        service_call.domain = DOMAIN
        service_call.service = "generate_tool_documentation"
        service_call.data = {
            ATTR_ENTITY_ID: "cortex_agent.test",
            ATTR_FORMAT: "markdown",
        }
        
        # Mock generate_markdown
        tool_documentation.generate_markdown = MagicMock(return_value="# Markdown Content")
        
        # Handle service call
        await tool_documentation._handle_generate_documentation(service_call)
        
        # Check that event was fired
        tool_documentation.hass.bus.async_fire.assert_called_once()
        
        # Check event data - the second positional argument is the event data
        event_data = tool_documentation.hass.bus.async_fire.call_args[0][1]
        assert event_data[ATTR_ENTITY_ID] == "cortex_agent.test"
        assert event_data["content"] == "# Markdown Content"
        assert event_data["format"] == "markdown"

    async def test_handle_generate_documentation_html(self, tool_documentation):
        """Test handling generate_tool_documentation service call with HTML format."""
        # Create service call
        service_call = MagicMock(spec=ServiceCall)
        service_call.domain = DOMAIN
        service_call.service = "generate_tool_documentation"
        service_call.data = {
            ATTR_ENTITY_ID: "cortex_agent.test",
            ATTR_FORMAT: "html",
        }
        
        # Mock generate_html
        tool_documentation.generate_html = MagicMock(return_value="<html>HTML Content</html>")
        
        # Handle service call
        await tool_documentation._handle_generate_documentation(service_call)
        
        # Check that event was fired
        tool_documentation.hass.bus.async_fire.assert_called_once()
        
        # Check event data - the second positional argument is the event data
        event_data = tool_documentation.hass.bus.async_fire.call_args[0][1]
        assert event_data[ATTR_ENTITY_ID] == "cortex_agent.test"
        assert event_data["content"] == "<html>HTML Content</html>"
        assert event_data["format"] == "html"