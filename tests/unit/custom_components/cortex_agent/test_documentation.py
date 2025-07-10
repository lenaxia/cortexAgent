"""Tests for the CortexAgent documentation module."""
from unittest.mock import MagicMock, patch, mock_open

import pytest

from custom_components.cortex_agent.documentation import (
    DocumentationGenerator,
    generate_markdown_documentation,
    generate_tool_documentation,
    generate_model_documentation,
    generate_mcp_server_documentation,
)
from custom_components.cortex_agent.model_provider import ModelProviderType
from custom_components.cortex_agent.mcp_connector import MCPServerType


@pytest.fixture
def mock_hass():
    """Fixture to provide a mock hass instance."""
    return MagicMock()


@pytest.fixture
def mock_coordinator():
    """Fixture to provide a mock coordinator."""
    coordinator = MagicMock()
    coordinator.agent_id = "test_agent"
    coordinator.name = "Test Agent"
    
    # Set up the coordinator data
    coordinator.data = MagicMock()
    coordinator.data.model_provider_connected = True
    coordinator.data.model_provider_name = "OpenAI"
    coordinator.data.model_provider_model = "gpt-4"
    coordinator.data.mcp_servers = [
        {
            "server_id": "server_123",
            "name": "Test Server",
            "server_type": "remote",
            "connected": True,
        },
    ]
    coordinator.data.memory_count = 10
    coordinator.data.conversation_history_length = 5
    coordinator.data.available_tools = ["tool1", "tool2"]
    
    return coordinator


def test_documentation_generator_init(mock_hass, mock_coordinator):
    """Test the initialization of DocumentationGenerator."""
    # Create a documentation generator
    generator = DocumentationGenerator(mock_hass, mock_coordinator)
    
    # Check the generator properties
    assert generator.hass == mock_hass
    assert generator.coordinator == mock_coordinator
    assert generator.agent_id == "test_agent"
    assert generator.name == "Test Agent"


def test_documentation_generator_generate_markdown(mock_hass, mock_coordinator):
    """Test the generate_markdown method of DocumentationGenerator."""
    # Create a documentation generator
    generator = DocumentationGenerator(mock_hass, mock_coordinator)
    
    # Set up the mock coordinator
    mock_coordinator.model_provider.provider_type = ModelProviderType.OPENAI
    mock_coordinator.model_provider.name = "OpenAI"
    mock_coordinator.model_provider.model = "gpt-4"
    
    mock_coordinator.mcp_connector.list_servers.return_value = [
        {
            "server_id": "server_123",
            "name": "Test Server",
            "server_type": "remote",
            "url": "https://example.com/mcp",
            "description": "A test MCP server",
            "connected": True,
            "tools": [
                {
                    "tool_id": "tool_123",
                    "name": "Test Tool",
                    "description": "A test tool",
                    "parameters": [
                        {
                            "name": "param1",
                            "description": "A test parameter",
                            "type": "string",
                            "required": True,
                        },
                    ],
                },
            ],
            "resources": [
                {
                    "uri": "resource://test",
                    "description": "A test resource",
                },
            ],
        },
    ]
    
    mock_coordinator.tool_manager.list_tools.return_value = [
        {
            "name": "tool1",
            "description": "Tool 1",
            "parameters": [
                {
                    "name": "param1",
                    "description": "Parameter 1",
                    "type": "string",
                    "required": True,
                },
            ],
        },
        {
            "name": "tool2",
            "description": "Tool 2",
            "parameters": [],
        },
    ]
    
    # Generate markdown
    markdown = generator.generate_markdown()
    
    # Check the markdown
    assert "# Test Agent" in markdown
    assert "## Model" in markdown
    assert "OpenAI" in markdown
    assert "gpt-4" in markdown
    assert "## MCP Servers" in markdown
    assert "Test Server" in markdown
    assert "## Tools" in markdown
    assert "tool1" in markdown
    assert "tool2" in markdown


def test_documentation_generator_save_to_file(mock_hass, mock_coordinator):
    """Test the save_to_file method of DocumentationGenerator."""
    # Create a documentation generator
    generator = DocumentationGenerator(mock_hass, mock_coordinator)
    
    # Set up the mock generate_markdown method
    generator.generate_markdown = MagicMock(return_value="# Test Agent\n\nThis is a test.")
    
    # Mock open
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        # Save to file
        generator.save_to_file("/path/to/file.md")
    
    # Check that open was called with the right arguments
    mock_file.assert_called_once_with("/path/to/file.md", "w")
    
    # Check that write was called with the right arguments
    mock_file().write.assert_called_once_with("# Test Agent\n\nThis is a test.")


def test_generate_markdown_documentation(mock_hass, mock_coordinator):
    """Test the generate_markdown_documentation function."""
    # Set up the mock coordinator
    mock_coordinator.model_provider.provider_type = ModelProviderType.OPENAI
    mock_coordinator.model_provider.name = "OpenAI"
    mock_coordinator.model_provider.model = "gpt-4"
    
    mock_coordinator.mcp_connector.list_servers.return_value = [
        {
            "server_id": "server_123",
            "name": "Test Server",
            "server_type": "remote",
            "url": "https://example.com/mcp",
            "description": "A test MCP server",
            "connected": True,
            "tools": [
                {
                    "tool_id": "tool_123",
                    "name": "Test Tool",
                    "description": "A test tool",
                    "parameters": [
                        {
                            "name": "param1",
                            "description": "A test parameter",
                            "type": "string",
                            "required": True,
                        },
                    ],
                },
            ],
            "resources": [
                {
                    "uri": "resource://test",
                    "description": "A test resource",
                },
            ],
        },
    ]
    
    mock_coordinator.tool_manager.list_tools.return_value = [
        {
            "name": "tool1",
            "description": "Tool 1",
            "parameters": [
                {
                    "name": "param1",
                    "description": "Parameter 1",
                    "type": "string",
                    "required": True,
                },
            ],
        },
        {
            "name": "tool2",
            "description": "Tool 2",
            "parameters": [],
        },
    ]
    
    # Generate markdown
    markdown = generate_markdown_documentation(mock_coordinator)
    
    # Check the markdown
    assert "# Test Agent" in markdown
    assert "## Model" in markdown
    assert "OpenAI" in markdown
    assert "gpt-4" in markdown
    assert "## MCP Servers" in markdown
    assert "Test Server" in markdown
    assert "## Tools" in markdown
    assert "tool1" in markdown
    assert "tool2" in markdown


def test_generate_tool_documentation():
    """Test the generate_tool_documentation function."""
    # Create a tool
    tool = {
        "name": "test_tool",
        "description": "A test tool",
        "parameters": [
            {
                "name": "param1",
                "description": "A test parameter",
                "type": "string",
                "required": True,
            },
            {
                "name": "param2",
                "description": "Another test parameter",
                "type": "number",
                "required": False,
                "default": 42,
            },
        ],
    }
    
    # Generate markdown
    markdown = generate_tool_documentation(tool)
    
    # Check the markdown
    assert "### test_tool" in markdown
    assert "A test tool" in markdown
    assert "#### Parameters" in markdown
    assert "param1" in markdown
    assert "A test parameter" in markdown
    assert "string" in markdown
    assert "Required" in markdown
    assert "param2" in markdown
    assert "Another test parameter" in markdown
    assert "number" in markdown
    assert "Optional" in markdown
    assert "Default: 42" in markdown


def test_generate_model_documentation():
    """Test the generate_model_documentation function."""
    # Create model info
    model_info = {
        "provider_type": ModelProviderType.OPENAI,
        "name": "OpenAI",
        "model": "gpt-4",
        "connected": True,
    }
    
    # Generate markdown
    markdown = generate_model_documentation(model_info)
    
    # Check the markdown
    assert "## Model" in markdown
    assert "Provider: OpenAI" in markdown
    assert "Model: gpt-4" in markdown
    assert "Status: Connected" in markdown


def test_generate_model_documentation_not_connected():
    """Test the generate_model_documentation function with a disconnected model."""
    # Create model info
    model_info = {
        "provider_type": ModelProviderType.OPENAI,
        "name": "OpenAI",
        "model": "gpt-4",
        "connected": False,
    }
    
    # Generate markdown
    markdown = generate_model_documentation(model_info)
    
    # Check the markdown
    assert "## Model" in markdown
    assert "Provider: OpenAI" in markdown
    assert "Model: gpt-4" in markdown
    assert "Status: Disconnected" in markdown


def test_generate_mcp_server_documentation():
    """Test the generate_mcp_server_documentation function."""
    # Create a server
    server = {
        "server_id": "server_123",
        "name": "Test Server",
        "server_type": "remote",
        "url": "https://example.com/mcp",
        "description": "A test MCP server",
        "connected": True,
        "tools": [
            {
                "tool_id": "tool_123",
                "name": "Test Tool",
                "description": "A test tool",
                "parameters": [
                    {
                        "name": "param1",
                        "description": "A test parameter",
                        "type": "string",
                        "required": True,
                    },
                ],
            },
        ],
        "resources": [
            {
                "uri": "resource://test",
                "description": "A test resource",
            },
        ],
    }
    
    # Generate markdown
    markdown = generate_mcp_server_documentation(server)
    
    # Check the markdown
    assert "### Test Server" in markdown
    assert "Type: Remote" in markdown
    assert "URL: https://example.com/mcp" in markdown
    assert "Description: A test MCP server" in markdown
    assert "Status: Connected" in markdown
    assert "#### Tools" in markdown
    assert "Test Tool" in markdown
    assert "A test tool" in markdown
    assert "#### Resources" in markdown
    assert "resource://test" in markdown
    assert "A test resource" in markdown


def test_generate_mcp_server_documentation_not_connected():
    """Test the generate_mcp_server_documentation function with a disconnected server."""
    # Create a server
    server = {
        "server_id": "server_123",
        "name": "Test Server",
        "server_type": "local",
        "url": "stdio://path/to/server",
        "description": "A test MCP server",
        "connected": False,
        "tools": [],
        "resources": [],
    }
    
    # Generate markdown
    markdown = generate_mcp_server_documentation(server)
    
    # Check the markdown
    assert "### Test Server" in markdown
    assert "Type: Local" in markdown
    assert "URL: stdio://path/to/server" in markdown
    assert "Description: A test MCP server" in markdown
    assert "Status: Disconnected" in markdown
    assert "No tools available" in markdown
    assert "No resources available" in markdown