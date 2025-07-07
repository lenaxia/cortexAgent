"""Tests for the commands module."""
import pytest
from unittest.mock import patch, MagicMock

from unified_agent.models import CommandResult, MCPServerConfig, MCPServerType, MemoryConfig
from unified_agent.commands import (
    HelpCommand, ConnectCommand, DisconnectCommand, 
    ListServersCommand, ListToolsCommand, RememberCommand,
    RecallCommand, MemoriesCommand, ConfigCommand, ReloadCommand
)


class TestHelpCommand:
    """Tests for the HelpCommand class."""
    
    def test_execute(self):
        """Test executing the help command."""
        # Initialize command
        command = HelpCommand()
        
        # Execute command
        result = command.execute([])
        
        # Check that result is correct
        assert result.success is True
        assert "Help Information" in result.message
        assert "Available Commands" in result.data
        assert "/help" in result.data
        assert "/connect" in result.data


class TestConnectCommand:
    """Tests for the ConnectCommand class."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        mcp_connector = MagicMock()
        mcp_connector.connect.return_value = True
        
        config_manager = MagicMock()
        config_manager.add_mcp_server.return_value = True
        
        agent_manager = MagicMock()
        agent_manager.reload_agent.return_value = True
        
        return {
            "mcp_connector": mcp_connector,
            "config_manager": config_manager,
            "agent_manager": agent_manager
        }
    
    def test_execute_success(self, mock_dependencies):
        """Test executing the connect command successfully."""
        # Initialize command
        command = ConnectCommand(
            mock_dependencies["mcp_connector"],
            mock_dependencies["config_manager"],
            mock_dependencies["agent_manager"]
        )
        
        # Execute command
        result = command.execute(["https://example.com/mcp", "sse", "test-server"])
        
        # Check that dependencies were called correctly
        mock_dependencies["mcp_connector"].connect.assert_called_once()
        server_config = mock_dependencies["mcp_connector"].connect.call_args[0][0]
        assert server_config.name == "test-server"
        assert server_config.url == "https://example.com/mcp"
        assert server_config.server_type == MCPServerType.SSE
        
        mock_dependencies["config_manager"].add_mcp_server.assert_called_once_with(server_config)
        mock_dependencies["agent_manager"].reload_agent.assert_called_once()
        
        # Check that result is correct
        assert result.success is True
        assert "Connected to MCP server" in result.message
    
    def test_execute_missing_url(self, mock_dependencies):
        """Test executing the connect command with missing URL."""
        # Initialize command
        command = ConnectCommand(
            mock_dependencies["mcp_connector"],
            mock_dependencies["config_manager"],
            mock_dependencies["agent_manager"]
        )
        
        # Execute command
        result = command.execute([])
        
        # Check that result is correct
        assert result.success is False
        assert "Usage" in result.message
    
    def test_execute_invalid_server_type(self, mock_dependencies):
        """Test executing the connect command with invalid server type."""
        # Initialize command
        command = ConnectCommand(
            mock_dependencies["mcp_connector"],
            mock_dependencies["config_manager"],
            mock_dependencies["agent_manager"]
        )
        
        # Execute command
        result = command.execute(["https://example.com/mcp", "invalid"])
        
        # Check that result is correct
        assert result.success is False
        assert "Invalid server type" in result.message
    
    def test_execute_connection_failure(self, mock_dependencies):
        """Test executing the connect command when connection fails."""
        # Set up mock to return False
        mock_dependencies["mcp_connector"].connect.return_value = False
        
        # Initialize command
        command = ConnectCommand(
            mock_dependencies["mcp_connector"],
            mock_dependencies["config_manager"],
            mock_dependencies["agent_manager"]
        )
        
        # Execute command
        result = command.execute(["https://example.com/mcp", "sse", "test-server"])
        
        # Check that result is correct
        assert result.success is False
        assert "Failed to connect" in result.message


class TestDisconnectCommand:
    """Tests for the DisconnectCommand class."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        mcp_connector = MagicMock()
        mcp_connector.disconnect.return_value = True
        
        config_manager = MagicMock()
        config_manager.remove_mcp_server.return_value = True
        
        agent_manager = MagicMock()
        agent_manager.reload_agent.return_value = True
        
        return {
            "mcp_connector": mcp_connector,
            "config_manager": config_manager,
            "agent_manager": agent_manager
        }
    
    def test_execute_success(self, mock_dependencies):
        """Test executing the disconnect command successfully."""
        # Initialize command
        command = DisconnectCommand(
            mock_dependencies["mcp_connector"],
            mock_dependencies["config_manager"],
            mock_dependencies["agent_manager"]
        )
        
        # Execute command
        result = command.execute(["test-server"])
        
        # Check that dependencies were called correctly
        mock_dependencies["mcp_connector"].disconnect.assert_called_once_with("test-server")
        mock_dependencies["config_manager"].remove_mcp_server.assert_called_once_with("test-server")
        mock_dependencies["agent_manager"].reload_agent.assert_called_once()
        
        # Check that result is correct
        assert result.success is True
        assert "Disconnected from MCP server" in result.message
    
    def test_execute_missing_name(self, mock_dependencies):
        """Test executing the disconnect command with missing name."""
        # Initialize command
        command = DisconnectCommand(
            mock_dependencies["mcp_connector"],
            mock_dependencies["config_manager"],
            mock_dependencies["agent_manager"]
        )
        
        # Execute command
        result = command.execute([])
        
        # Check that result is correct
        assert result.success is False
        assert "Usage" in result.message
    
    def test_execute_disconnect_failure(self, mock_dependencies):
        """Test executing the disconnect command when disconnect fails."""
        # Set up mock to return False
        mock_dependencies["mcp_connector"].disconnect.return_value = False
        
        # Initialize command
        command = DisconnectCommand(
            mock_dependencies["mcp_connector"],
            mock_dependencies["config_manager"],
            mock_dependencies["agent_manager"]
        )
        
        # Execute command
        result = command.execute(["test-server"])
        
        # Check that result is correct
        assert result.success is False
        assert "Failed to disconnect" in result.message


class TestListServersCommand:
    """Tests for the ListServersCommand class."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        config_manager = MagicMock()
        config_manager.config.mcp_servers = [
            MCPServerConfig(
                name="test-server-1",
                url="https://example.com/mcp1",
                server_type=MCPServerType.SSE,
                enabled=True
            ),
            MCPServerConfig(
                name="test-server-2",
                url="https://example.com/mcp2",
                server_type=MCPServerType.STREAMABLE_HTTP,
                enabled=False
            )
        ]
        
        mcp_connector = MagicMock()
        mcp_connector.get_connected_servers.return_value = ["test-server-1"]
        
        return {
            "config_manager": config_manager,
            "mcp_connector": mcp_connector
        }
    
    def test_execute_with_servers(self, mock_dependencies):
        """Test executing the list-servers command with servers configured."""
        # Initialize command
        command = ListServersCommand(
            mock_dependencies["config_manager"],
            mock_dependencies["mcp_connector"]
        )
        
        # Execute command
        result = command.execute([])
        
        # Check that result is correct
        assert result.success is True
        assert "MCP Servers" in result.message
        assert "test-server-1" in result.data
        assert "test-server-2" in result.data
        assert "Connected" in result.data
        assert "Disconnected" in result.data
    
    def test_execute_no_servers(self, mock_dependencies):
        """Test executing the list-servers command with no servers configured."""
        # Set up mock to return empty list
        mock_dependencies["config_manager"].config.mcp_servers = []
        
        # Initialize command
        command = ListServersCommand(
            mock_dependencies["config_manager"],
            mock_dependencies["mcp_connector"]
        )
        
        # Execute command
        result = command.execute([])
        
        # Check that result is correct
        assert result.success is True
        assert "No MCP servers configured" in result.message


class TestRememberCommand:
    """Tests for the RememberCommand class."""
    
    @pytest.fixture
    def mock_memory_handler(self):
        """Create a mock memory handler."""
        memory_handler = MagicMock()
        memory_handler.store.return_value = {
            "success": True,
            "result": {"status": "success"}
        }
        return memory_handler
    
    def test_execute_success(self, mock_memory_handler):
        """Test executing the remember command successfully."""
        # Initialize command
        command = RememberCommand(mock_memory_handler)
        
        # Execute command
        result = command.execute(["This", "is", "a", "test", "memory"])
        
        # Check that memory handler was called correctly
        mock_memory_handler.store.assert_called_once_with("This is a test memory")
        
        # Check that result is correct
        assert result.success is True
        assert "Information stored in memory" in result.message
    
    def test_execute_missing_text(self, mock_memory_handler):
        """Test executing the remember command with missing text."""
        # Initialize command
        command = RememberCommand(mock_memory_handler)
        
        # Execute command
        result = command.execute([])
        
        # Check that result is correct
        assert result.success is False
        assert "Usage" in result.message
    
    def test_execute_store_failure(self, mock_memory_handler):
        """Test executing the remember command when store fails."""
        # Set up mock to return failure
        mock_memory_handler.store.return_value = {
            "success": False,
            "error": "Test error"
        }
        
        # Initialize command
        command = RememberCommand(mock_memory_handler)
        
        # Execute command
        result = command.execute(["This", "is", "a", "test", "memory"])
        
        # Check that result is correct
        assert result.success is False
        assert "Test error" in result.message
