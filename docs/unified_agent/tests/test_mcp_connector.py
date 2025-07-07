"""Tests for the mcp_connector module."""
import pytest
from unittest.mock import patch, MagicMock, call

from unified_agent.models import MCPServerConfig, MCPServerType, MCPTool
from unified_agent.mcp_connector import MCPConnector


class TestMCPConnector:
    """Tests for the MCPConnector class."""
    
    @pytest.fixture
    def server_config(self):
        """Create a server configuration for testing."""
        return MCPServerConfig(
            name="test-server",
            url="https://example.com/mcp",
            server_type=MCPServerType.SSE,
            auth_token="test-token",
            enabled=True
        )
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create a mock MCP client."""
        mock_client = MagicMock()
        mock_client.connect = MagicMock()
        mock_client.disconnect = MagicMock()
        mock_client.list_tools_sync = MagicMock(return_value=[
            MagicMock(
                tool_name="test-tool",
                description="A test tool",
                parameters={"param1": "string"}
            )
        ])
        return mock_client
    
    @patch("unified_agent.mcp_connector.MCPClient")
    @patch("unified_agent.mcp_connector.sse_client")
    def test_connect_sse(self, mock_sse_client, mock_mcp_client_class, server_config, mock_mcp_client):
        """Test connecting to an SSE server."""
        # Set up mocks
        mock_mcp_client_class.return_value = mock_mcp_client
        mock_sse_client.return_value = "mock_transport"
        
        # Initialize connector
        connector = MCPConnector()
        
        # Connect to server
        result = connector.connect(server_config)
        
        # Check that connection was successful
        assert result is True
        
        # Check that sse_client was called correctly
        mock_sse_client.assert_called_once_with(
            "https://example.com/mcp",
            auth_token="test-token"
        )
        
        # Check that MCPClient was created correctly
        mock_mcp_client_class.assert_called_once()
        
        # Check that client was connected
        mock_mcp_client.connect.assert_called_once()
        
        # Check that client was stored
        assert "test-server" in connector.clients
        assert connector.clients["test-server"] == mock_mcp_client
        
        # Check that tools were cached
        assert "test-server" in connector.tools_cache
        assert len(connector.tools_cache["test-server"]) == 1
        assert connector.tools_cache["test-server"][0].tool_name == "test-tool"
    
    @patch("unified_agent.mcp_connector.MCPClient")
    @patch("unified_agent.mcp_connector.streamablehttp_client")
    def test_connect_streamable_http(self, mock_streamablehttp_client, mock_mcp_client_class, mock_mcp_client):
        """Test connecting to a streamable HTTP server."""
        # Set up mocks
        mock_mcp_client_class.return_value = mock_mcp_client
        mock_streamablehttp_client.return_value = "mock_transport"
        
        # Create server config
        server_config = MCPServerConfig(
            name="test-server",
            url="https://example.com/mcp",
            server_type=MCPServerType.STREAMABLE_HTTP,
            auth_token="test-token",
            enabled=True
        )
        
        # Initialize connector
        connector = MCPConnector()
        
        # Connect to server
        result = connector.connect(server_config)
        
        # Check that connection was successful
        assert result is True
        
        # Check that streamablehttp_client was called correctly
        mock_streamablehttp_client.assert_called_once_with(
            "https://example.com/mcp",
            auth_token="test-token"
        )
    
    @patch("unified_agent.mcp_connector.MCPClient")
    def test_connect_unsupported_type(self, mock_mcp_client_class):
        """Test connecting to a server with an unsupported type."""
        # Create server config with unsupported type
        server_config = MCPServerConfig(
            name="test-server",
            url="https://example.com/mcp",
            server_type=MCPServerType.WEBSOCKET,
            enabled=True
        )
        
        # Initialize connector
        connector = MCPConnector()
        
        # Connect to server
        result = connector.connect(server_config)
        
        # Check that connection failed
        assert result is False
        
        # Check that MCPClient was not created
        mock_mcp_client_class.assert_not_called()
    
    @patch("unified_agent.mcp_connector.MCPClient")
    @patch("unified_agent.mcp_connector.sse_client")
    def test_connect_exception(self, mock_sse_client, mock_mcp_client_class, server_config):
        """Test connecting to a server when an exception is raised."""
        # Set up mocks
        mock_mcp_client = MagicMock()
        mock_mcp_client.connect.side_effect = Exception("Test error")
        mock_mcp_client_class.side_effect = Exception("Test error")

        # Initialize connector
        connector = MCPConnector()

        # Connect to server
        result = connector.connect(server_config)

        # Check that connection failed
        assert result is False
    
    @patch("unified_agent.mcp_connector.MCPClient")
    @patch("unified_agent.mcp_connector.sse_client")
    def test_disconnect(self, mock_sse_client, mock_mcp_client_class, server_config, mock_mcp_client):
        """Test disconnecting from a server."""
        # Set up mocks
        mock_mcp_client_class.return_value = mock_mcp_client
        
        # Initialize connector
        connector = MCPConnector()
        
        # Connect to server
        connector.connect(server_config)
        
        # Disconnect from server
        result = connector.disconnect("test-server")
        
        # Check that disconnect was successful
        assert result is True
        
        # Check that client was disconnected
        mock_mcp_client.disconnect.assert_called_once()
        
        # Check that client was removed
        assert "test-server" not in connector.clients
        assert "test-server" not in connector.tools_cache
    
    def test_disconnect_not_connected(self):
        """Test disconnecting from a server that is not connected."""
        # Initialize connector
        connector = MCPConnector()
        
        # Disconnect from server
        result = connector.disconnect("nonexistent")
        
        # Check that disconnect failed
        assert result is False
    
    @patch("unified_agent.mcp_connector.MCPClient")
    @patch("unified_agent.mcp_connector.sse_client")
    def test_disconnect_exception(self, mock_sse_client, mock_mcp_client_class, server_config, mock_mcp_client):
        """Test disconnecting from a server when an exception is raised."""
        # Set up mocks
        mock_mcp_client.disconnect.side_effect = Exception("Test error")
        mock_mcp_client_class.return_value = mock_mcp_client

        # Initialize connector
        connector = MCPConnector()

        # Connect to server
        connector.connect(server_config)
        
        # Create a custom class that raises an exception when accessed
        class ExceptionClient:
            def __getattribute__(self, name):
                raise Exception("Test error")
        
        # Replace the client with our custom class
        connector.clients["test-server"] = ExceptionClient()

        # Disconnect from server
        result = connector.disconnect("test-server")

        # Check that disconnect failed
        assert result is False
    
    @patch("unified_agent.mcp_connector.MCPClient")
    @patch("unified_agent.mcp_connector.sse_client")
    def test_get_all_tools(self, mock_sse_client, mock_mcp_client_class, server_config, mock_mcp_client):
        """Test getting all tools."""
        # Set up mocks
        mock_mcp_client_class.return_value = mock_mcp_client
        
        # Initialize connector
        connector = MCPConnector()
        
        # Connect to server
        connector.connect(server_config)
        
        # Get all tools
        tools = connector.get_all_tools()
        
        # Check that tools were returned
        assert len(tools) == 1
        assert tools[0].server_name == "test-server"
        assert tools[0].tool_name == "test-tool"
    
    @patch("unified_agent.mcp_connector.MCPClient")
    @patch("unified_agent.mcp_connector.sse_client")
    def test_get_connected_servers(self, mock_sse_client, mock_mcp_client_class, server_config, mock_mcp_client):
        """Test getting connected servers."""
        # Set up mocks
        mock_mcp_client_class.return_value = mock_mcp_client
        
        # Initialize connector
        connector = MCPConnector()
        
        # Connect to server
        connector.connect(server_config)
        
        # Get connected servers
        servers = connector.get_connected_servers()
        
        # Check that servers were returned
        assert len(servers) == 1
        assert servers[0] == "test-server"
