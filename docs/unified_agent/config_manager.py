"""Configuration management for the unified agent."""
import json
import os
import logging
import shutil
from typing import Dict, Optional
from pathlib import Path

from unified_agent.models import AgentConfig, MCPServerConfig, MemoryConfig, IConfigManager

logger = logging.getLogger(__name__)


class ConfigManagerFactory:
    """Factory for creating configuration managers."""
    
    @staticmethod
    def create(config_path: str = "~/.unified_agent/config.json") -> 'ConfigManager':
        """Create a new configuration manager."""
        return ConfigManager(config_path)


class ConfigManager:
    """Manages configuration persistence."""
    
    def __init__(self, config_path: str = "~/.unified_agent/config.json"):
        self.config_path = os.path.expanduser(config_path)
        self._ensure_config_dir()
        self._config = self._load_config()
    
    @property
    def config(self) -> AgentConfig:
        """Get the current configuration."""
        return self._config
    
    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
    
    def _load_config(self) -> AgentConfig:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_dict = json.load(f)
                return AgentConfig.parse_obj(config_dict)
            except Exception as e:
                logger.error(f"Failed to load config: {str(e)}")
                return self._create_default_config()
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> AgentConfig:
        """Create a default configuration."""
        # Try to load from default_config.json
        default_config_path = os.path.join(os.path.dirname(__file__), "default_config.json")
        if os.path.exists(default_config_path):
            try:
                with open(default_config_path, 'r') as f:
                    config_dict = json.load(f)
                logger.info(f"Loaded default config from {default_config_path}")
                
                # Save the default config to the user's config path
                with open(self.config_path, 'w') as f:
                    json.dump(config_dict, f, indent=2)
                logger.info(f"Saved default config to {self.config_path}")
                
                return AgentConfig.parse_obj(config_dict)
            except Exception as e:
                logger.error(f"Failed to load default config: {str(e)}")
        
        # Fallback to hardcoded default
        logger.info("Using hardcoded default config")
        return AgentConfig(
            name="Unified Agent",
            system_prompt="You are a helpful assistant with access to various tools and memory capabilities.",
            mcp_servers=[],
            memory=MemoryConfig(
                enabled=True,
                user_id="default_user"
            ),
            http_enabled=True
        )
    
    def save_config(self) -> bool:
        """Save the current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._config.dict(), f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
            return False
    
    def add_mcp_server(self, server_config: MCPServerConfig) -> bool:
        """Add or update an MCP server configuration."""
        # Check if server with this name already exists
        for i, server in enumerate(self._config.mcp_servers):
            if server.name == server_config.name:
                # Update existing server
                self._config.mcp_servers[i] = server_config
                return self.save_config()
        
        # Add new server
        self._config.mcp_servers.append(server_config)
        return self.save_config()
    
    def remove_mcp_server(self, server_name: str) -> bool:
        """Remove an MCP server configuration."""
        initial_count = len(self._config.mcp_servers)
        self._config.mcp_servers = [s for s in self._config.mcp_servers if s.name != server_name]
        
        if len(self._config.mcp_servers) < initial_count:
            return self.save_config()
        return False
    
    def update_memory_config(self, memory_config: MemoryConfig) -> bool:
        """Update memory configuration."""
        self._config.memory = memory_config
        return self.save_config()
