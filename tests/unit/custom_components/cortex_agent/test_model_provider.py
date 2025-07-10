"""Tests for the CortexAgent model_provider module."""
from unittest.mock import MagicMock, patch

import pytest

from custom_components.cortex_agent.exceptions import (
    AuthenticationError,
    ModelProviderError,
)
from custom_components.cortex_agent.model_provider import (
    AnthropicModelProvider,
    BedrockModelProvider,
    LiteLLMModelProvider,
    ModelProvider,
    OpenAIModelProvider,
    create_model_provider,
)


def test_model_provider_base_class():
    """Test the ModelProvider base class."""
    config = {"key": "value"}
    provider = ModelProvider(config)
    assert provider.config == config
    
    # Test abstract method
    with pytest.raises(NotImplementedError):
        provider.create_model()


def test_create_model_provider():
    """Test the create_model_provider function."""
    # Test OpenAI provider
    config = {"provider": "openai"}
    provider = create_model_provider(config)
    assert isinstance(provider, OpenAIModelProvider)
    
    # Test Bedrock provider
    config = {"provider": "bedrock"}
    provider = create_model_provider(config)
    assert isinstance(provider, BedrockModelProvider)
    
    # Test Anthropic provider
    config = {"provider": "anthropic"}
    provider = create_model_provider(config)
    assert isinstance(provider, AnthropicModelProvider)
    
    # Test LiteLLM provider
    config = {"provider": "litellm"}
    provider = create_model_provider(config)
    assert isinstance(provider, LiteLLMModelProvider)
    
    # Test invalid provider
    config = {"provider": "invalid"}
    with pytest.raises(ModelProviderError):
        create_model_provider(config)


@patch("custom_components.cortex_agent.model_provider.OpenAIModel")
def test_openai_model_provider(mock_openai_model):
    """Test the OpenAIModelProvider class."""
    # Test with minimal config
    config = {
        "api_key": "test_api_key",
    }
    provider = OpenAIModelProvider(config)
    model = provider.create_model()
    
    # Check that OpenAIModel was called with the right parameters
    mock_openai_model.assert_called_once()
    call_kwargs = mock_openai_model.call_args.kwargs
    assert call_kwargs["api_key"] == "test_api_key"
    assert call_kwargs["model_id"] == "gpt-4o"  # Default value
    assert call_kwargs["max_tokens"] == 1024  # Default value
    assert call_kwargs["temperature"] == 0.7  # Default value
    
    # Test with full config
    config = {
        "api_key": "test_api_key",
        "org_id": "test_org_id",
        "model_id": "gpt-4",
        "max_tokens": 2048,
        "temperature": 0.5,
    }
    mock_openai_model.reset_mock()
    provider = OpenAIModelProvider(config)
    model = provider.create_model()
    
    # Check that OpenAIModel was called with the right parameters
    mock_openai_model.assert_called_once()
    call_kwargs = mock_openai_model.call_args.kwargs
    assert call_kwargs["api_key"] == "test_api_key"
    assert call_kwargs["organization"] == "test_org_id"
    assert call_kwargs["model_id"] == "gpt-4"
    assert call_kwargs["max_tokens"] == 2048
    assert call_kwargs["temperature"] == 0.5
    
    # Test without API key
    config = {}
    provider = OpenAIModelProvider(config)
    with pytest.raises(AuthenticationError):
        provider.create_model()


@patch("custom_components.cortex_agent.model_provider.boto3")
@patch("custom_components.cortex_agent.model_provider.BedrockModel")
def test_bedrock_model_provider(mock_bedrock_model, mock_boto3):
    """Test the BedrockModelProvider class."""
    # Test with minimal config
    config = {}
    provider = BedrockModelProvider(config)
    model = provider.create_model()
    
    # Check that BedrockModel was called with the right parameters
    mock_bedrock_model.assert_called_once()
    call_kwargs = mock_bedrock_model.call_args.kwargs
    assert call_kwargs["model_id"] == "us.anthropic.claude-3-7-sonnet-20250219-v1:0"  # Default value
    assert call_kwargs["max_tokens"] == 1024  # Default value
    assert call_kwargs["temperature"] == 0.7  # Default value
    
    # Test with AWS profile
    config = {
        "aws_profile": "test_profile",
        "aws_region": "us-east-1",
        "model_id": "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
        "max_tokens": 2048,
        "temperature": 0.5,
    }
    mock_bedrock_model.reset_mock()
    mock_boto3.Session.reset_mock()
    provider = BedrockModelProvider(config)
    model = provider.create_model()
    
    # Check that boto3.Session was called with the right parameters
    mock_boto3.Session.assert_called_once_with(
        profile_name="test_profile", region_name="us-east-1"
    )
    
    # Check that BedrockModel was called with the right parameters
    mock_bedrock_model.assert_called_once()
    call_kwargs = mock_bedrock_model.call_args.kwargs
    assert call_kwargs["model_id"] == "us.anthropic.claude-3-5-sonnet-20240620-v1:0"
    assert call_kwargs["max_tokens"] == 2048
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["boto_session"] == mock_boto3.Session.return_value


@patch("custom_components.cortex_agent.model_provider.AnthropicModel")
def test_anthropic_model_provider(mock_anthropic_model):
    """Test the AnthropicModelProvider class."""
    # Test with minimal config
    config = {
        "api_key": "test_api_key",
    }
    provider = AnthropicModelProvider(config)
    model = provider.create_model()
    
    # Check that AnthropicModel was called with the right parameters
    mock_anthropic_model.assert_called_once()
    call_kwargs = mock_anthropic_model.call_args.kwargs
    assert call_kwargs["api_key"] == "test_api_key"
    assert call_kwargs["model_id"] == "claude-3-7-sonnet-20250219"  # Default value
    assert call_kwargs["max_tokens"] == 1024  # Default value
    assert call_kwargs["temperature"] == 0.7  # Default value
    
    # Test with full config
    config = {
        "api_key": "test_api_key",
        "model_id": "claude-3-haiku-20240307",
        "max_tokens": 2048,
        "temperature": 0.5,
    }
    mock_anthropic_model.reset_mock()
    provider = AnthropicModelProvider(config)
    model = provider.create_model()
    
    # Check that AnthropicModel was called with the right parameters
    mock_anthropic_model.assert_called_once()
    call_kwargs = mock_anthropic_model.call_args.kwargs
    assert call_kwargs["api_key"] == "test_api_key"
    assert call_kwargs["model_id"] == "claude-3-haiku-20240307"
    assert call_kwargs["max_tokens"] == 2048
    assert call_kwargs["temperature"] == 0.5
    
    # Test without API key
    config = {}
    provider = AnthropicModelProvider(config)
    with pytest.raises(AuthenticationError):
        provider.create_model()


@patch("custom_components.cortex_agent.model_provider.LiteLLMModel")
def test_litellm_model_provider(mock_litellm_model):
    """Test the LiteLLMModelProvider class."""
    # Test with minimal config
    config = {
        "api_key": "test_api_key",
        "model_id": "test_model",
    }
    provider = LiteLLMModelProvider(config)
    model = provider.create_model()
    
    # Check that LiteLLMModel was called with the right parameters
    mock_litellm_model.assert_called_once()
    call_kwargs = mock_litellm_model.call_args.kwargs
    assert call_kwargs["api_key"] == "test_api_key"
    assert call_kwargs["model_id"] == "test_model"
    assert call_kwargs["max_tokens"] == 1024  # Default value
    assert call_kwargs["temperature"] == 0.7  # Default value
    
    # Test with full config
    config = {
        "api_key": "test_api_key",
        "model_id": "test_model",
        "max_tokens": 2048,
        "temperature": 0.5,
    }
    mock_litellm_model.reset_mock()
    provider = LiteLLMModelProvider(config)
    model = provider.create_model()
    
    # Check that LiteLLMModel was called with the right parameters
    mock_litellm_model.assert_called_once()
    call_kwargs = mock_litellm_model.call_args.kwargs
    assert call_kwargs["api_key"] == "test_api_key"
    assert call_kwargs["model_id"] == "test_model"
    assert call_kwargs["max_tokens"] == 2048
    assert call_kwargs["temperature"] == 0.5
    
    # Test without API key
    config = {
        "model_id": "test_model",
    }
    provider = LiteLLMModelProvider(config)
    with pytest.raises(AuthenticationError):
        provider.create_model()
        
    # Test without model ID
    config = {
        "api_key": "test_api_key",
    }
    provider = LiteLLMModelProvider(config)
    with pytest.raises(ModelProviderError):
        provider.create_model()