"""Tests for the CortexAgent exceptions module."""
import pytest

from custom_components.cortex_agent.exceptions import (
    APIRateLimitError,
    AuthenticationError,
    CortexAgentError,
    MemoryError,
    ModelProviderError,
    NetworkError,
    ToolExecutionError,
    ConfigurationError,
)


def test_cortex_agent_error():
    """Test the CortexAgentError class."""
    error = CortexAgentError("Test error")
    assert str(error) == "Test error"


def test_model_provider_error():
    """Test the ModelProviderError class."""
    error = ModelProviderError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, CortexAgentError)


def test_api_rate_limit_error():
    """Test the APIRateLimitError class."""
    # Test without retry_after
    error = APIRateLimitError("openai")
    assert "openai rate limit exceeded" in str(error).lower()
    assert "unknown" in str(error).lower()
    assert error.provider == "openai"
    assert error.retry_after is None
    assert isinstance(error, ModelProviderError)
    
    # Test with retry_after
    error = APIRateLimitError("openai", 60)
    assert "openai rate limit exceeded" in str(error).lower()
    assert "60 seconds" in str(error)
    assert error.provider == "openai"
    assert error.retry_after == 60
    assert isinstance(error, ModelProviderError)


def test_authentication_error():
    """Test the AuthenticationError class."""
    error = AuthenticationError("Invalid API key")
    assert str(error) == "Invalid API key"
    assert isinstance(error, ModelProviderError)


def test_network_error():
    """Test the NetworkError class."""
    # Test with temporary=True (default)
    error = NetworkError("Connection timeout")
    assert str(error) == "Connection timeout"
    assert error.is_temporary is True
    assert isinstance(error, CortexAgentError)
    
    # Test with temporary=False
    error = NetworkError("DNS resolution failed", False)
    assert str(error) == "DNS resolution failed"
    assert error.is_temporary is False
    assert isinstance(error, CortexAgentError)


def test_tool_execution_error():
    """Test the ToolExecutionError class."""
    error = ToolExecutionError("http_request", "Invalid URL")
    assert "error executing tool 'http_request'" in str(error).lower()
    assert "invalid url" in str(error).lower()
    assert error.tool_name == "http_request"
    assert isinstance(error, CortexAgentError)


def test_memory_error():
    """Test the MemoryError class."""
    error = MemoryError("Failed to store memory")
    assert str(error) == "Failed to store memory"
    assert isinstance(error, CortexAgentError)


def test_configuration_error():
    """Test the ConfigurationError class."""
    error = ConfigurationError("Invalid configuration")
    assert str(error) == "Invalid configuration"
    assert isinstance(error, CortexAgentError)