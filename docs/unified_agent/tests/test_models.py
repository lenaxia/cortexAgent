"""Tests for the models module."""
import pytest
from pydantic import ValidationError
from typing import Dict, List, Any

# Import the models we'll be testing
# These will be implemented after we write the tests
from unified_agent.models import (
    MCPServerType, MCPServerConfig, MCPTool, 
    MemoryConfig, AgentConfig, CommandResult
)


class TestMCPServerConfig:
    """Tests for the MCPServerConfig model."""
    
    def test_valid_config(self):
        """Test creating a valid server config."""
        config = MCPServerConfig(
            name="test-server",
            url="https://example.com/mcp",
            server_type=MCPServerType.SSE,
            auth_token="test-token",
            enabled=True
        )
        
        assert config.name == "test-server"
        assert config.url == "https://example.com/mcp"
        assert config.server_type == MCPServerType.SSE
        assert config.auth_token == "test-token"
        assert config.enabled is True
    
    def test_default_values(self):
        """Test default values are set correctly."""
        config = MCPServerConfig(
            name="test-server",
            url="https://example.com/mcp"
        )
        
        assert config.server_type == MCPServerType.SSE
        assert config.auth_token is None
        assert config.enabled is True
    
    def test_invalid_url(self):
        """Test validation for invalid URL."""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                name="test-server",
                url="invalid-url"
            )


class TestMCPTool:
    """Tests for the MCPTool model."""
    
    def test_valid_tool(self):
        """Test creating a valid tool."""
        tool = MCPTool(
            server_name="test-server",
            tool_name="test-tool",
            description="A test tool",
            parameters={"param1": "string", "param2": "integer"}
        )
        
        assert tool.server_name == "test-server"
        assert tool.tool_name == "test-tool"
        assert tool.description == "A test tool"
        assert tool.parameters == {"param1": "string", "param2": "integer"}
    
    def test_default_parameters(self):
        """Test default parameters are set correctly."""
        tool = MCPTool(
            server_name="test-server",
            tool_name="test-tool",
            description="A test tool"
        )
        
        assert tool.parameters == {}


class TestMemoryConfig:
    """Tests for the MemoryConfig model."""
    
    def test_valid_config(self):
        """Test creating a valid memory config."""
        config = MemoryConfig(
            enabled=True,
            user_id="test-user",
            memory_type="mem0",
            aws_region="us-west-2",
            opensearch_host="test-host"
        )
        
        assert config.enabled is True
        assert config.user_id == "test-user"
        assert config.memory_type == "mem0"
        assert config.aws_region == "us-west-2"
        assert config.opensearch_host == "test-host"
    
    def test_default_values(self):
        """Test default values are set correctly."""
        config = MemoryConfig(
            user_id="test-user"
        )
        
        assert config.enabled is True
        assert config.memory_type == "mem0"
        assert config.aws_region is None
        assert config.opensearch_host is None


class TestAgentConfig:
    """Tests for the AgentConfig model."""
    
    def test_valid_config(self):
        """Test creating a valid agent config."""
        config = AgentConfig(
            name="Test Agent",
            system_prompt="You are a test agent",
            mcp_servers=[
                MCPServerConfig(
                    name="test-server",
                    url="https://example.com/mcp"
                )
            ],
            memory=MemoryConfig(user_id="test-user"),
            http_enabled=True
        )
        
        assert config.name == "Test Agent"
        assert config.system_prompt == "You are a test agent"
        assert len(config.mcp_servers) == 1
        assert config.mcp_servers[0].name == "test-server"
        assert config.memory.user_id == "test-user"
        assert config.http_enabled is True
    
    def test_default_values(self):
        """Test default values are set correctly."""
        config = AgentConfig(
            system_prompt="You are a test agent"
        )
        
        assert config.name == "Unified Agent"
        assert config.mcp_servers == []
        assert config.memory is None
        assert config.http_enabled is False


class TestCommandResult:
    """Tests for the CommandResult model."""
    
    def test_valid_result(self):
        """Test creating a valid command result."""
        result = CommandResult(
            success=True,
            message="Command executed successfully",
            data={"key": "value"}
        )
        
        assert result.success is True
        assert result.message == "Command executed successfully"
        assert result.data == {"key": "value"}
    
    def test_default_data(self):
        """Test default data is set correctly."""
        result = CommandResult(
            success=False,
            message="Command failed"
        )
        
        assert result.data is None
