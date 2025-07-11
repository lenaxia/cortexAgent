"""Tests for the CortexAgent MCP connector."""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.cortex_agent.mcp_connector import (
    MCPConnector,
    MCPServerConfig,
    MCPTool,
)
from custom_components.cortex_agent.const import (
    CONF_MCP_SERVERS,
    SERVER_TYPE_SSE,
    SERVER_TYPE_STREAMABLE_HTTP,
    SERVER_TYPE_STDIO,
)
from custom_components.cortex_agent.exceptions import NetworkError


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock()
    return hass


@pytest.fixture
def mock_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.options = {
        CONF_MCP_SERVERS: [
            {
                "name": "test-server",
                "url": "http://localhost:8000/mcp",
                "server_type": SERVER_TYPE_SSE,
                "enabled": True,
            }
        ]
    }
    return entry


@pytest.fixture
def mock_sse_client():
    """Mock SSE client."""
    with patch("custom_components.cortex_agent.mcp_connector.sse_client") as mock:
        yield mock


@pytest.fixture
def mock_streamablehttp_client():
    """Mock Streamable HTTP client."""
    with patch("custom_components.cortex_agent.mcp_connector.streamablehttp_client") as mock:
        yield mock


@pytest.fixture
def mock_stdio_client():
    """Mock Stdio client."""
    with patch("custom_components.cortex_agent.mcp_connector.stdio_client") as mock:
        yield mock


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client."""
    with patch("strands.tools.mcp.mcp_client.MCPClient") as mock_class:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=None)
        mock_instance.list_tools_sync = MagicMock(return_value=[])
        mock_class.return_value = mock_instance
        yield mock_class


class TestMCPConnector:
    """Test the MCP connector."""

    def test_init(self, mock_hass, mock_entry):
        """Test initialization."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        assert connector.hass == mock_hass
        assert connector.entry == mock_entry
        assert connector.clients == {}
        assert connector.tools_cache == {}

    async def test_async_setup(
        self, mock_hass, mock_entry, mock_sse_client, mock_mcp_client
    ):
        """Test setup from config."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Mock the connect method
        connector.async_connect = AsyncMock(return_value=True)
        
        # Call setup
        await connector.async_setup()
        
        # Check that connect was called with the server config
        connector.async_connect.assert_called_once_with(
            mock_entry.options[CONF_MCP_SERVERS][0]
        )

    async def test_async_connect_sse(
        self, mock_hass, mock_entry, mock_sse_client, mock_mcp_client
    ):
        """Test connecting to an SSE server."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Create server config
        server_config = {
            "name": "test-server",
            "url": "http://localhost:8000/mcp",
            "server_type": SERVER_TYPE_SSE,
            "auth_token": "test-token",
        }
        
        # Call connect
        result = await connector.async_connect(server_config)
        
        # Check result
        assert result is True
        
        # Check that SSE client was created
        mock_sse_client.assert_called_once()
        assert "test-server" in connector.clients
        
        # Check that tools were cached
        mock_hass.async_add_executor_job.assert_called_once()

    async def test_async_connect_streamable_http(
        self, mock_hass, mock_entry, mock_streamablehttp_client, mock_mcp_client
    ):
        """Test connecting to a Streamable HTTP server."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Create server config
        server_config = {
            "name": "test-server",
            "url": "http://localhost:8000/mcp",
            "server_type": SERVER_TYPE_STREAMABLE_HTTP,
        }
        
        # Call connect
        result = await connector.async_connect(server_config)
        
        # Check result
        assert result is True
        
        # Check that Streamable HTTP client was created
        mock_streamablehttp_client.assert_called_once()
        assert "test-server" in connector.clients

    async def test_async_connect_stdio(
        self, mock_hass, mock_entry, mock_stdio_client, mock_mcp_client
    ):
        """Test connecting to a Stdio server."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Create server config
        server_config = {
            "name": "test-local-server",
            "url": "/usr/local/bin/mcp-server",
            "server_type": SERVER_TYPE_STDIO,
            "command_args": ["--debug", "--no-auth"],
        }
        
        # Call connect
        result = await connector.async_connect(server_config)
        
        # Check result
        assert result is True
        
        # Check that Stdio client was created
        mock_stdio_client.assert_called_once_with("/usr/local/bin/mcp-server", ["--debug", "--no-auth"])
        assert "test-local-server" in connector.clients

    async def test_async_connect_unsupported_type(self, mock_hass, mock_entry):
        """Test connecting with an unsupported server type."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Create server config
        server_config = {
            "name": "test-server",
            "url": "http://localhost:8000/mcp",
            "server_type": "unsupported",
        }
        
        # Call connect
        result = await connector.async_connect(server_config)
        
        # Check result
        assert result is False

    async def test_async_connect_already_connected(
        self, mock_hass, mock_entry, mock_sse_client, mock_mcp_client
    ):
        """Test connecting to a server that's already connected."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Add a client to simulate already being connected
        connector.clients["test-server"] = MagicMock()
        
        # Create server config
        server_config = {
            "name": "test-server",
            "url": "http://localhost:8000/mcp",
            "server_type": SERVER_TYPE_SSE,
        }
        
        # Mock disconnect
        connector.async_disconnect = AsyncMock(return_value=True)
        
        # Call connect
        result = await connector.async_connect(server_config)
        
        # Check result
        assert result is True
        
        # Check that disconnect was called
        connector.async_disconnect.assert_called_once_with("test-server")

    async def test_async_connect_import_error(self, mock_hass, mock_entry):
        """Test connecting with import error."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Create server config
        server_config = {
            "name": "test-server",
            "url": "http://localhost:8000/mcp",
            "server_type": SERVER_TYPE_SSE,
        }
        
        # Mock import error
        with patch(
            "custom_components.cortex_agent.mcp_connector.sse_client",
            side_effect=ImportError("Module not found")
        ):
            # Call connect
            with pytest.raises(NetworkError):
                await connector.async_connect(server_config)

    async def test_async_disconnect(self, mock_hass, mock_entry):
        """Test disconnecting from a server."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Add a client to disconnect
        mock_client = MagicMock()
        connector.clients["test-server"] = mock_client
        connector.tools_cache["test-server"] = [MagicMock()]
        
        # Call disconnect
        result = await connector.async_disconnect("test-server")
        
        # Check result
        assert result is True
        assert "test-server" not in connector.clients
        assert "test-server" not in connector.tools_cache

    async def test_async_disconnect_not_connected(self, mock_hass, mock_entry):
        """Test disconnecting from a server that's not connected."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Call disconnect
        result = await connector.async_disconnect("nonexistent-server")
        
        # Check result
        assert result is False

    def test_update_tools_cache(self, mock_hass, mock_entry, mock_mcp_client):
        """Test updating the tools cache."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Create a mock tool
        mock_tool = MagicMock()
        mock_tool.tool_name = "test-tool"
        mock_tool.description = "Test tool"
        mock_tool.parameters = {"param1": {"type": "string"}}
        
        # Add a client
        mock_client = MagicMock()
        mock_client.list_tools_sync.return_value = [mock_tool]
        connector.clients["test-server"] = mock_client
        
        # Update tools cache
        connector._update_tools_cache("test-server")
        
        # Check result
        assert "test-server" in connector.tools_cache
        assert len(connector.tools_cache["test-server"]) == 1
        assert connector.tools_cache["test-server"][0].tool_name == "test-tool"
        assert connector.tools_cache["test-server"][0].server_name == "test-server"

    def test_update_tools_cache_error(self, mock_hass, mock_entry):
        """Test updating the tools cache with an error."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Add a client that raises an exception
        mock_client = MagicMock()
        mock_client.list_tools_sync.side_effect = Exception("Test error")
        connector.clients["test-server"] = mock_client
        
        # Update tools cache
        connector._update_tools_cache("test-server")
        
        # Check result
        assert "test-server" in connector.tools_cache
        assert connector.tools_cache["test-server"] == []

    async def test_async_get_all_tools(self, mock_hass, mock_entry, mock_mcp_client):
        """Test getting all tools."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Add clients
        connector.clients = {
            "server1": MagicMock(),
            "server2": MagicMock(),
        }
        
        # Add tools to cache
        connector.tools_cache = {
            "server1": [
                MCPTool(server_name="server1", tool_name="tool1", description="Tool 1"),
            ],
            "server2": [
                MCPTool(server_name="server2", tool_name="tool2", description="Tool 2"),
            ],
        }
        
        # Mock update_tools_cache
        connector._update_tools_cache = MagicMock()
        
        # Get all tools
        tools = await connector.async_get_all_tools()
        
        # Check result
        assert len(tools) == 2
        assert tools[0].server_name == "server1"
        assert tools[1].server_name == "server2"
        
        # Check that update_tools_cache was called for each server
        assert connector._update_tools_cache.call_count == 2

    async def test_async_get_server_tools(self, mock_hass, mock_entry, mock_mcp_client):
        """Test getting tools for a specific server."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Add client
        connector.clients["test-server"] = MagicMock()
        
        # Add tools to cache
        connector.tools_cache["test-server"] = [
            MCPTool(server_name="test-server", tool_name="tool1", description="Tool 1"),
        ]
        
        # Mock update_tools_cache
        connector._update_tools_cache = MagicMock()
        
        # Get server tools
        tools = await connector.async_get_server_tools("test-server")
        
        # Check result
        assert len(tools) == 1
        assert tools[0].server_name == "test-server"
        
        # Check that update_tools_cache was called
        connector._update_tools_cache.assert_called_once_with("test-server")

    def test_get_connected_servers(self, mock_hass, mock_entry):
        """Test getting connected servers."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Add clients
        connector.clients = {
            "server1": MagicMock(),
            "server2": MagicMock(),
        }
        
        # Get connected servers
        servers = connector.get_connected_servers()
        
        # Check result
        assert len(servers) == 2
        assert "server1" in servers
        assert "server2" in servers

    def test_get_client(self, mock_hass, mock_entry):
        """Test getting a client."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Add client
        mock_client = MagicMock()
        connector.clients["test-server"] = mock_client
        
        # Get client
        client = connector.get_client("test-server")
        
        # Check result
        assert client == mock_client

    def test_get_nonexistent_client(self, mock_hass, mock_entry):
        """Test getting a client that doesn't exist."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Get client
        client = connector.get_client("nonexistent-server")
        
        # Check result
        assert client is None

    async def test_async_execute_tool(self, mock_hass, mock_entry, mock_mcp_client):
        """Test executing a tool."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Add client
        mock_client = MagicMock()
        connector.clients["test-server"] = mock_client
        
        # Add tool to cache
        connector.tools_cache["test-server"] = [
            MCPTool(
                server_name="test-server",
                tool_name="test-tool",
                description="Test tool",
                parameters={"param1": {"type": "string"}}
            )
        ]
        
        # Mock validation and sanitization methods
        connector._validate_tool_arguments = MagicMock()
        connector._sanitize_result = MagicMock(return_value={"result": "success"})
        
        # Mock execute_tool_sync
        connector._execute_tool_sync = MagicMock(return_value={"result": "success"})
        
        # Execute tool
        result = await connector.async_execute_tool(
            "test-server", "test-tool", {"param1": "value1"}
        )
        
        # Check result
        assert result == {"result": "success"}
        
        # Check that execute_tool_sync was called
        connector._execute_tool_sync.assert_called_once_with(
            mock_client, "test-tool", {"param1": "value1"}
        )
        
        # Check that validation and sanitization methods were called
        connector._validate_tool_arguments.assert_called_once()
        connector._sanitize_result.assert_called_once_with({"result": "success"})

    async def test_async_execute_tool_not_connected(self, mock_hass, mock_entry):
        """Test executing a tool on a server that's not connected."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Execute tool
        with pytest.raises(NetworkError):
            await connector.async_execute_tool(
                "nonexistent-server", "test-tool", {"param1": "value1"}
            )

    def test_execute_tool_sync(self, mock_hass, mock_entry):
        """Test executing a tool synchronously."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Create mock client
        mock_client = MagicMock()
        mock_client.execute_tool_sync.return_value = {"result": "success"}
        
        # Execute tool
        result = connector._execute_tool_sync(
            mock_client, "test-tool", {"param1": "value1"}
        )
        
        # Check result
        assert result == {"result": "success"}
        
        # Check that client method was called
        mock_client.execute_tool_sync.assert_called_once_with(
            "test-tool", {"param1": "value1"}
        )

    def test_execute_tool_sync_no_method(self, mock_hass, mock_entry):
        """Test executing a tool on a client without the method."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Create mock client without execute_tool_sync
        mock_client = MagicMock()
        del mock_client.execute_tool_sync
        
        # Execute tool
        with pytest.raises(NetworkError):
            connector._execute_tool_sync(
                mock_client, "test-tool", {"param1": "value1"}
            )

    def test_register_execution_callback(self, mock_hass, mock_entry):
        """Test registering an execution callback."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Create callback
        callback = MagicMock()
        
        # Register callback
        connector.register_execution_callback("test-server", callback)
        
        # Check result
        assert "test-server" in connector._execution_callbacks
        assert connector._execution_callbacks["test-server"] == callback

    def test_unregister_execution_callback(self, mock_hass, mock_entry):
        """Test unregistering an execution callback."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Add callback
        connector._execution_callbacks["test-server"] = MagicMock()
        
        # Unregister callback
        connector.unregister_execution_callback("test-server")
        
        # Check result
        assert "test-server" not in connector._execution_callbacks
        
    def test_is_valid_identifier(self, mock_hass, mock_entry):
        """Test validating identifiers."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Test valid identifiers
        assert connector._is_valid_identifier("valid_identifier") is True
        assert connector._is_valid_identifier("valid-identifier") is True
        assert connector._is_valid_identifier("valid123") is True
        
        # Test invalid identifiers
        assert connector._is_valid_identifier("invalid identifier") is False  # Contains space
        assert connector._is_valid_identifier("invalid;identifier") is False  # Contains semicolon
        assert connector._is_valid_identifier("invalid/identifier") is False  # Contains slash
        assert connector._is_valid_identifier("") is False  # Empty string
        
    def test_validate_tool_arguments(self, mock_hass, mock_entry):
        """Test validating tool arguments."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Create a test tool
        tool = MCPTool(
            server_name="test-server",
            tool_name="test-tool",
            description="Test tool",
            parameters={
                "required_string": {"type": "string", "required": True},
                "optional_number": {"type": "number"},
                "boolean_param": {"type": "boolean"},
                "array_param": {"type": "array"},
                "object_param": {"type": "object"},
            }
        )
        
        # Test valid arguments
        valid_args = {
            "required_string": "test",
            "optional_number": 42,
            "boolean_param": True,
            "array_param": [1, 2, 3],
            "object_param": {"key": "value"}
        }
        # Should not raise an exception
        connector._validate_tool_arguments(tool, valid_args)
        
        # Test missing required parameter
        missing_required = {
            "optional_number": 42
        }
        with pytest.raises(ValueError, match="Missing required parameter"):
            connector._validate_tool_arguments(tool, missing_required)
            
        # Test unknown parameter
        unknown_param = {
            "required_string": "test",
            "unknown_param": "value"
        }
        with pytest.raises(ValueError, match="Unknown parameter"):
            connector._validate_tool_arguments(tool, unknown_param)
            
        # Test invalid parameter types
        invalid_types = {
            "required_string": 123,  # Should be string
            "optional_number": "not a number",  # Should be number
            "boolean_param": "not a boolean",  # Should be boolean
            "array_param": "not an array",  # Should be array
            "object_param": "not an object"  # Should be object
        }
        
        # Test each invalid type separately
        for param, value in invalid_types.items():
            with pytest.raises(ValueError, match=f"Parameter {param} must be"):
                connector._validate_tool_arguments(tool, {
                    "required_string": "test" if param != "required_string" else value,
                    param: value
                })
                
    def test_sanitize_result(self, mock_hass, mock_entry):
        """Test sanitizing tool execution results."""
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Test sanitizing a simple result
        simple_result = {"key": "value"}
        sanitized = connector._sanitize_result(simple_result)
        assert sanitized == simple_result
        
        # Test sanitizing a nested result
        nested_result = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "nested": {
                "key": "value"
            },
            "array": [
                {"item": 1},
                {"item": 2}
            ]
        }
        sanitized = connector._sanitize_result(nested_result)
        assert sanitized == nested_result
        
        # Test sanitizing a non-dict result
        non_dict = "not a dict"
        sanitized = connector._sanitize_result(non_dict)
        assert sanitized == non_dict