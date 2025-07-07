"""Tests for the config_manager module."""
import os
import json
import pytest
from unittest.mock import patch, mock_open

from unified_agent.models import AgentConfig, MCPServerConfig, MemoryConfig
from unified_agent.config_manager import ConfigManager


class TestConfigManager:
    """Tests for the ConfigManager class."""
    
    @pytest.fixture
    def mock_config_path(self, tmp_path):
        """Create a temporary config path for testing."""
        config_file = tmp_path / "config.json"
        return str(config_file)
    
    def test_init_creates_config_dir(self, mock_config_path):
        """Test that init creates the config directory if it doesn't exist."""
        config_dir = os.path.dirname(mock_config_path)
        
        # Ensure directory doesn't exist
        if os.path.exists(config_dir):
            os.rmdir(config_dir)
        
        # Initialize config manager
        ConfigManager(mock_config_path)
        
        # Check that directory was created
        assert os.path.exists(config_dir)
    
    def test_load_config_from_file(self, mock_config_path):
        """Test loading config from an existing file."""
        # Create a config file
        config_data = {
            "name": "Test Agent",
            "system_prompt": "You are a test agent",
            "mcp_servers": [
                {
                    "name": "test-server",
                    "url": "https://example.com/mcp",
                    "server_type": "sse",
                    "enabled": True
                }
            ],
            "memory": {
                "enabled": True,
                "user_id": "test-user"
            },
            "http_enabled": True
        }
        
        with open(mock_config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Initialize config manager
        config_manager = ConfigManager(mock_config_path)
        
        # Check that config was loaded correctly
        assert config_manager.config.name == "Test Agent"
        assert config_manager.config.system_prompt == "You are a test agent"
        assert len(config_manager.config.mcp_servers) == 1
        assert config_manager.config.mcp_servers[0].name == "test-server"
        assert config_manager.config.memory.user_id == "test-user"
        assert config_manager.config.http_enabled is True
    
    def test_create_default_config(self, mock_config_path):
        """Test creating a default config when file doesn't exist."""
        # Ensure file doesn't exist
        if os.path.exists(mock_config_path):
            os.remove(mock_config_path)
        
        # Initialize config manager
        config_manager = ConfigManager(mock_config_path)
        
        # Check that default config was created
        assert config_manager.config.name == "Unified Agent"
        assert "You are a helpful assistant" in config_manager.config.system_prompt
        assert config_manager.config.mcp_servers == []
        assert config_manager.config.memory is not None
        assert config_manager.config.memory.user_id == "default_user"
        assert config_manager.config.http_enabled is True
    
    def test_save_config(self, mock_config_path):
        """Test saving config to file."""
        # Initialize config manager
        config_manager = ConfigManager(mock_config_path)
        
        # Modify config
        config_manager.config.name = "Modified Agent"
        
        # Save config
        result = config_manager.save_config()
        
        # Check that save was successful
        assert result is True
        
        # Check that file was written correctly
        with open(mock_config_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["name"] == "Modified Agent"
    
    def test_add_mcp_server_new(self, mock_config_path):
        """Test adding a new MCP server."""
        # Initialize config manager
        config_manager = ConfigManager(mock_config_path)
        
        # Add server
        server_config = MCPServerConfig(
            name="new-server",
            url="https://example.com/mcp"
        )
        
        result = config_manager.add_mcp_server(server_config)
        
        # Check that add was successful
        assert result is True
        
        # Check that server was added
        assert len(config_manager.config.mcp_servers) == 1
        assert config_manager.config.mcp_servers[0].name == "new-server"
        
        # Check that config was saved
        with open(mock_config_path, 'r') as f:
            saved_data = json.load(f)
        
        assert len(saved_data["mcp_servers"]) == 1
        assert saved_data["mcp_servers"][0]["name"] == "new-server"
    
    def test_add_mcp_server_update(self, mock_config_path):
        """Test updating an existing MCP server."""
        # Initialize config manager
        config_manager = ConfigManager(mock_config_path)
        
        # Add initial server
        server_config1 = MCPServerConfig(
            name="test-server",
            url="https://example.com/mcp"
        )
        
        config_manager.add_mcp_server(server_config1)
        
        # Update server
        server_config2 = MCPServerConfig(
            name="test-server",
            url="https://updated.example.com/mcp"
        )
        
        result = config_manager.add_mcp_server(server_config2)
        
        # Check that update was successful
        assert result is True
        
        # Check that server was updated
        assert len(config_manager.config.mcp_servers) == 1
        assert config_manager.config.mcp_servers[0].url == "https://updated.example.com/mcp"
    
    def test_remove_mcp_server(self, mock_config_path):
        """Test removing an MCP server."""
        # Initialize config manager
        config_manager = ConfigManager(mock_config_path)
        
        # Add server
        server_config = MCPServerConfig(
            name="test-server",
            url="https://example.com/mcp"
        )
        
        config_manager.add_mcp_server(server_config)
        
        # Remove server
        result = config_manager.remove_mcp_server("test-server")
        
        # Check that remove was successful
        assert result is True
        
        # Check that server was removed
        assert len(config_manager.config.mcp_servers) == 0
    
    def test_remove_nonexistent_server(self, mock_config_path):
        """Test removing a server that doesn't exist."""
        # Initialize config manager
        config_manager = ConfigManager(mock_config_path)
        
        # Remove nonexistent server
        result = config_manager.remove_mcp_server("nonexistent")
        
        # Check that remove failed
        assert result is False
    
    def test_update_memory_config(self, mock_config_path):
        """Test updating memory configuration."""
        # Initialize config manager
        config_manager = ConfigManager(mock_config_path)
        
        # Update memory config
        memory_config = MemoryConfig(
            enabled=True,
            user_id="updated-user"
        )
        
        result = config_manager.update_memory_config(memory_config)
        
        # Check that update was successful
        assert result is True
        
        # Check that memory config was updated
        assert config_manager.config.memory.user_id == "updated-user"
