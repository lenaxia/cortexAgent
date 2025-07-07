"""Integration tests for the unified agent."""
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from unified_agent.models import AgentConfig, MCPServerConfig, MemoryConfig, MCPServerType
from unified_agent.config_manager import ConfigManager
from unified_agent.mcp_connector import MCPConnector
from unified_agent.memory_handler import MemoryHandler
from unified_agent.agent_manager import AgentManager
from unified_agent.command_registry import CommandRegistry
from unified_agent.commands import (
    HelpCommand, ConnectCommand, DisconnectCommand, 
    ListServersCommand, ListToolsCommand, RememberCommand,
    RecallCommand, MemoriesCommand, ConfigCommand, ReloadCommand
)
from unified_agent.cli_interface import CLIInterface
from unified_agent.main import create_application


class TestIntegration:
    """Integration tests for the unified agent."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            f.write(b'{"name": "Test Agent", "system_prompt": "You are a test agent", "mcp_servers": [], "memory": {"enabled": true, "user_id": "test-user"}, "http_enabled": true}')
            temp_path = f.name
        
        yield temp_path
        
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def test_config_manager_mcp_connector_integration(self, temp_config_file):
        """Test integration between ConfigManager and MCPConnector."""
        # Initialize components
        config_manager = ConfigManager(temp_config_file)
        mcp_connector = MCPConnector()
        
        # Add a server to the configuration
        server_config = MCPServerConfig(
            name="test-server",
            url="https://example.com/mcp",
            server_type=MCPServerType.SSE
        )
        
        # Add server to config
        result = config_manager.add_mcp_server(server_config)
        assert result is True
        
        # Connect to server
        result = mcp_connector.connect(server_config)
        assert result is True
        
        # Check that server is connected
        connected_servers = mcp_connector.get_connected_servers()
        assert "test-server" in connected_servers
        
        # Get tools
        tools = mcp_connector.get_all_tools()
        assert len(tools) > 0
        
        # Disconnect from server
        result = mcp_connector.disconnect("test-server")
        assert result is True
        
        # Check that server is disconnected
        connected_servers = mcp_connector.get_connected_servers()
        assert "test-server" not in connected_servers
    
    def test_memory_handler_integration(self):
        """Test integration with MemoryHandler."""
        # Initialize components
        memory_config = MemoryConfig(
            enabled=True,
            user_id="test-user"
        )
        memory_handler = MemoryHandler(memory_config)
        
        # Store information
        result = memory_handler.store("Test memory")
        assert result["success"] is True
        
        # Retrieve information
        result = memory_handler.retrieve("Test")
        assert result["success"] is True
        assert "memories" in result["result"]
        
        # List all memories
        result = memory_handler.list_all()
        assert result["success"] is True
        assert "memories" in result["result"]
    
    @patch("unified_agent.agent_manager.Agent")
    def test_agent_manager_integration(self, mock_agent_class, temp_config_file):
        """Test integration with AgentManager."""
        # Set up mock agent
        mock_agent = MagicMock()
        mock_agent.return_value = "Mock agent response"
        mock_agent_class.return_value = mock_agent
        
        # Initialize components
        config_manager = ConfigManager(temp_config_file)
        mcp_connector = MCPConnector()
        memory_handler = MemoryHandler(config_manager.config.memory)
        agent_manager = AgentManager(
            config_manager.config,
            mcp_connector,
            memory_handler
        )
        
        # Process input
        result = agent_manager.process_input("Hello, agent")
        assert result["success"] is True
        assert "response" in result
        
        # Reload agent
        result = agent_manager.reload_agent()
        assert result is True
    
    def test_command_registry_integration(self):
        """Test integration with CommandRegistry."""
        # Initialize components
        config_manager = MagicMock()
        mcp_connector = MagicMock()
        memory_handler = MagicMock()
        agent_manager = MagicMock()
        
        # Create command registry
        command_registry = CommandRegistry()
        
        # Register commands
        command_registry.register("help", HelpCommand())
        command_registry.register("connect", ConnectCommand(
            mcp_connector, config_manager, agent_manager
        ))
        
        # Execute help command
        result = command_registry.execute("help", [])
        assert result.success is True
        assert "Help Information" in result.message
        
        # Execute connect command
        mcp_connector.connect.return_value = True
        config_manager.add_mcp_server.return_value = True
        agent_manager.reload_agent.return_value = True
        
        result = command_registry.execute("connect", ["https://example.com/mcp", "sse", "test-server"])
        assert result.success is True
        assert "Connected to MCP server" in result.message
    
    @patch("builtins.input")
    @patch("builtins.print")
    def test_cli_interface_integration(self, mock_print, mock_input):
        """Test integration with CLIInterface."""
        # Set up mocks
        mock_input.side_effect = ["/help", "exit"]
        
        # Initialize components
        command_registry = CommandRegistry()
        command_registry.register("help", HelpCommand())
        
        agent_manager = MagicMock()
        
        # Create CLI interface
        cli_interface = CLIInterface(command_registry, agent_manager)
        
        # Run interface
        cli_interface.run()
        
        # Check that help command was executed
        mock_print.assert_any_call("\n✅ Help Information")
    
    @patch("unified_agent.main.ConfigManagerFactory")
    @patch("unified_agent.main.MCPConnectorFactory")
    @patch("unified_agent.main.MemoryHandlerFactory")
    @patch("unified_agent.main.AgentManagerFactory")
    def test_application_creation(self, mock_agent_manager_factory, mock_memory_handler_factory, 
                                 mock_mcp_connector_factory, mock_config_manager_factory, temp_config_file):
        """Test creating the application."""
        # Set up mocks
        mock_config_manager = MagicMock()
        mock_config_manager.config = AgentConfig(
            name="Test Agent",
            system_prompt="You are a test agent",
            mcp_servers=[],
            memory=MemoryConfig(
                enabled=True,
                user_id="test-user"
            ),
            http_enabled=True
        )
        mock_config_manager_factory.create.return_value = mock_config_manager
        
        mock_mcp_connector = MagicMock()
        mock_mcp_connector_factory.create.return_value = mock_mcp_connector
        
        mock_memory_handler = MagicMock()
        mock_memory_handler_factory.create.return_value = mock_memory_handler
        
        mock_agent_manager = MagicMock()
        mock_agent_manager_factory.create.return_value = mock_agent_manager
        
        # Create application
        app = create_application(temp_config_file)
        
        # Check that application was created
        assert isinstance(app, CLIInterface)
