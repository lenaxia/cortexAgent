"""Tests for the CortexAgent models module."""
import pytest
from datetime import datetime
from pydantic import ValidationError

from custom_components.cortex_agent.models import (
    ModelProviderType,
    MCPServerType,
    ConversationRole,
    ToolExecutionStatus,
    ToolMetadata,
    ToolExecutionResult,
    MCPServerConfig,
    MemoryConfig,
    ConversationEntry,
    AgentConfig,
    AgentMetrics,
)


def test_model_provider_type_enum():
    """Test ModelProviderType enum."""
    assert ModelProviderType.OPENAI == "openai"
    assert ModelProviderType.ANTHROPIC == "anthropic"
    assert ModelProviderType.BEDROCK == "bedrock"
    assert ModelProviderType.LITELLM == "litellm"


def test_mcp_server_type_enum():
    """Test MCPServerType enum."""
    assert MCPServerType.LOCAL == "local"
    assert MCPServerType.REMOTE == "remote"


def test_conversation_role_enum():
    """Test ConversationRole enum."""
    assert ConversationRole.USER == "user"
    assert ConversationRole.ASSISTANT == "assistant"
    assert ConversationRole.SYSTEM == "system"
    assert ConversationRole.TOOL == "tool"


def test_tool_execution_status_enum():
    """Test ToolExecutionStatus enum."""
    assert ToolExecutionStatus.SUCCESS == "success"
    assert ToolExecutionStatus.ERROR == "error"
    assert ToolExecutionStatus.TIMEOUT == "timeout"


def test_tool_metadata():
    """Test ToolMetadata dataclass."""
    metadata = ToolMetadata(
        name="test_tool",
        description="A test tool",
        category="testing",
        permissions=["read"],
        examples=["test example"],
        parameters={"param1": "value1"}
    )
    
    assert metadata.name == "test_tool"
    assert metadata.description == "A test tool"
    assert metadata.category == "testing"
    assert metadata.permissions == ["read"]
    assert metadata.examples == ["test example"]
    assert metadata.parameters == {"param1": "value1"}


def test_tool_metadata_defaults():
    """Test ToolMetadata with default values."""
    metadata = ToolMetadata(
        name="test_tool",
        description="A test tool"
    )
    
    assert metadata.name == "test_tool"
    assert metadata.description == "A test tool"
    assert metadata.category == "uncategorized"
    assert metadata.permissions == []
    assert metadata.examples == []
    assert metadata.parameters == {}


def test_tool_execution_result():
    """Test ToolExecutionResult dataclass."""
    result = ToolExecutionResult(
        tool_name="test_tool",
        success=True,
        result={"data": "test"},
        execution_time=0.5
    )
    
    assert result.tool_name == "test_tool"
    assert result.success is True
    assert result.result == {"data": "test"}
    assert result.error is None
    assert result.execution_time == 0.5
    assert result.status == ToolExecutionStatus.SUCCESS


def test_tool_execution_result_error():
    """Test ToolExecutionResult with error."""
    result = ToolExecutionResult(
        tool_name="test_tool",
        success=False,
        error="Test error"
    )
    
    assert result.tool_name == "test_tool"
    assert result.success is False
    assert result.result is None
    assert result.error == "Test error"
    assert result.status == ToolExecutionStatus.ERROR


def test_mcp_server_config():
    """Test MCPServerConfig model."""
    config = MCPServerConfig(
        name="test_server",
        url="https://example.com/mcp",
        server_type=MCPServerType.REMOTE,
        auth_token="test_token",
        enabled=True
    )
    
    assert config.name == "test_server"
    assert config.url == "https://example.com/mcp"
    assert config.server_type == MCPServerType.REMOTE
    assert config.auth_token == "test_token"
    assert config.enabled is True


def test_mcp_server_config_defaults():
    """Test MCPServerConfig with default values."""
    config = MCPServerConfig(
        name="test_server",
        url="https://example.com/mcp"
    )
    
    assert config.name == "test_server"
    assert config.url == "https://example.com/mcp"
    assert config.server_type == MCPServerType.REMOTE
    assert config.auth_token is None
    assert config.enabled is True


def test_mcp_server_config_invalid_url():
    """Test MCPServerConfig with invalid URL."""
    with pytest.raises(ValidationError):
        MCPServerConfig(
            name="test_server",
            url="invalid_url"
        )


def test_mcp_server_config_valid_urls():
    """Test MCPServerConfig with various valid URLs."""
    valid_urls = [
        "https://example.com/mcp",
        "http://localhost:8000",
        "ws://example.com/ws",
        "wss://example.com/wss"
    ]
    
    for url in valid_urls:
        config = MCPServerConfig(name="test", url=url)
        assert config.url == url


def test_memory_config():
    """Test MemoryConfig model."""
    config = MemoryConfig(
        enabled=True,
        user_id="test_user",
        memory_type="mem0"
    )
    
    assert config.enabled is True
    assert config.user_id == "test_user"
    assert config.memory_type == "mem0"


def test_memory_config_defaults():
    """Test MemoryConfig with default values."""
    config = MemoryConfig(user_id="test_user")
    
    assert config.enabled is True
    assert config.user_id == "test_user"
    assert config.memory_type == "mem0"


def test_conversation_entry():
    """Test ConversationEntry model."""
    entry = ConversationEntry(
        role=ConversationRole.USER,
        content="Hello, world!",
        metadata={"source": "test"}
    )
    
    assert entry.role == ConversationRole.USER
    assert entry.content == "Hello, world!"
    assert entry.metadata == {"source": "test"}
    assert isinstance(entry.timestamp, datetime)


def test_conversation_entry_defaults():
    """Test ConversationEntry with default values."""
    entry = ConversationEntry(
        role=ConversationRole.USER,
        content="Hello, world!"
    )
    
    assert entry.role == ConversationRole.USER
    assert entry.content == "Hello, world!"
    assert entry.metadata == {}
    assert isinstance(entry.timestamp, datetime)


def test_agent_config():
    """Test AgentConfig model."""
    config = AgentConfig(
        name="Test Agent",
        system_prompt="You are a test agent",
        provider=ModelProviderType.OPENAI,
        model_id="gpt-4",
        api_key="test_key",
        max_tokens=2000,
        temperature=0.8,
        memory_enabled=True
    )
    
    assert config.name == "Test Agent"
    assert config.system_prompt == "You are a test agent"
    assert config.provider == ModelProviderType.OPENAI
    assert config.model_id == "gpt-4"
    assert config.api_key == "test_key"
    assert config.max_tokens == 2000
    assert config.temperature == 0.8
    assert config.memory_enabled is True
    assert config.mcp_servers == []
    assert config.custom_tools == []


def test_agent_config_defaults():
    """Test AgentConfig with default values."""
    config = AgentConfig(
        system_prompt="You are a test agent",
        provider=ModelProviderType.OPENAI,
        model_id="gpt-4"
    )
    
    assert config.name == "CortexAgent"
    assert config.system_prompt == "You are a test agent"
    assert config.provider == ModelProviderType.OPENAI
    assert config.model_id == "gpt-4"
    assert config.api_key is None
    assert config.max_tokens == 1500
    assert config.temperature == 0.7
    assert config.memory_enabled is False
    assert config.mcp_servers == []
    assert config.custom_tools == []


def test_agent_metrics():
    """Test AgentMetrics model."""
    metrics = AgentMetrics()
    
    # Test initial state
    assert metrics.requests == 0
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 0
    assert metrics.tool_usage == {}
    assert metrics.response_times == []
    assert metrics.token_usage == {"prompt": 0, "completion": 0, "total": 0}
    assert metrics.errors == {"api": 0, "rate_limit": 0, "network": 0, "timeout": 0, "other": 0}
    assert isinstance(metrics.last_reset, datetime)


def test_agent_metrics_record_request():
    """Test AgentMetrics record_request method."""
    metrics = AgentMetrics()
    
    # Record successful request
    metrics.record_request(successful=True, response_time=1.5)
    
    assert metrics.requests == 1
    assert metrics.successful_requests == 1
    assert metrics.failed_requests == 0
    assert metrics.response_times == [1.5]
    
    # Record failed request
    metrics.record_request(successful=False, error_type="api")
    
    assert metrics.requests == 2
    assert metrics.successful_requests == 1
    assert metrics.failed_requests == 1
    assert metrics.errors["api"] == 1


def test_agent_metrics_record_tool_usage():
    """Test AgentMetrics record_tool_usage method."""
    metrics = AgentMetrics()
    
    # Record tool usage
    metrics.record_tool_usage("test_tool")
    metrics.record_tool_usage("test_tool")
    metrics.record_tool_usage("other_tool")
    
    assert metrics.tool_usage["test_tool"] == 2
    assert metrics.tool_usage["other_tool"] == 1


def test_agent_metrics_record_token_usage():
    """Test AgentMetrics record_token_usage method."""
    metrics = AgentMetrics()
    
    # Record token usage
    metrics.record_token_usage(100, 50)
    metrics.record_token_usage(200, 75)
    
    assert metrics.token_usage["prompt"] == 300
    assert metrics.token_usage["completion"] == 125
    assert metrics.token_usage["total"] == 425


def test_agent_metrics_success_rate():
    """Test AgentMetrics success_rate property."""
    metrics = AgentMetrics()
    
    # No requests
    assert metrics.success_rate == 0.0
    
    # Record some requests
    metrics.record_request(successful=True)
    metrics.record_request(successful=True)
    metrics.record_request(successful=False)
    
    assert metrics.success_rate == 2/3


def test_agent_metrics_avg_response_time():
    """Test AgentMetrics avg_response_time property."""
    metrics = AgentMetrics()
    
    # No response times
    assert metrics.avg_response_time == 0.0
    
    # Record some response times
    metrics.record_request(successful=True, response_time=1.0)
    metrics.record_request(successful=True, response_time=2.0)
    metrics.record_request(successful=True, response_time=3.0)
    
    assert metrics.avg_response_time == 2.0


def test_agent_metrics_reset():
    """Test AgentMetrics reset method."""
    metrics = AgentMetrics()
    
    # Add some data
    metrics.record_request(successful=True, response_time=1.0)
    metrics.record_tool_usage("test_tool")
    metrics.record_token_usage(100, 50)
    
    # Reset
    old_reset_time = metrics.last_reset
    metrics.reset()
    
    # Check that everything is reset
    assert metrics.requests == 0
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 0
    assert metrics.tool_usage == {}
    assert metrics.response_times == []
    assert metrics.token_usage == {"prompt": 0, "completion": 0, "total": 0}
    assert metrics.errors == {"api": 0, "rate_limit": 0, "network": 0, "timeout": 0, "other": 0}
    assert metrics.last_reset > old_reset_time


def test_agent_metrics_response_times_limit():
    """Test that AgentMetrics limits response times to 100 entries."""
    metrics = AgentMetrics()
    
    # Add 150 response times
    for i in range(150):
        metrics.record_request(successful=True, response_time=float(i))
    
    # Should only keep the last 100
    assert len(metrics.response_times) == 100
    assert metrics.response_times[0] == 50.0  # First of the last 100
    assert metrics.response_times[-1] == 149.0  # Last entry