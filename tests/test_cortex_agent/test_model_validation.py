"""Tests for model-specific parameter validation in the CortexAgent integration."""
from unittest.mock import patch, MagicMock
import pytest

from custom_components.cortex_agent.model_provider import (
    OpenAIModelProvider,
    BedrockModelProvider,
    AnthropicModelProvider,
    LiteLLMModelProvider,
)
from custom_components.cortex_agent.const import (
    CONF_PROVIDER,
    CONF_API_KEY,
    CONF_MODEL_ID,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    PROVIDER_OPENAI,
    PROVIDER_BEDROCK,
    PROVIDER_ANTHROPIC,
    PROVIDER_LITELLM,
)
from custom_components.cortex_agent.exceptions import (
    ConfigurationError,
    ModelProviderError,
)


@pytest.fixture
def mock_openai_model():
    """Mock OpenAI model."""
    with patch("strands.models.OpenAIModel") as mock:
        yield mock


@pytest.fixture
def mock_bedrock_model():
    """Mock Bedrock model."""
    with patch("strands.models.BedrockModel") as mock:
        yield mock


@pytest.fixture
def mock_anthropic_model():
    """Mock Anthropic model."""
    with patch("strands.models.AnthropicModel") as mock:
        yield mock


@pytest.fixture
def mock_litellm_model():
    """Mock LiteLLM model."""
    with patch("strands.models.LiteLLMModel") as mock:
        yield mock


class TestModelValidation:
    """Test model-specific parameter validation."""

    def test_openai_model_validation_invalid_model(self, mock_openai_model):
        """Test OpenAI model validation with invalid model ID."""
        config = {
            CONF_PROVIDER: PROVIDER_OPENAI,
            CONF_API_KEY: "test-api-key",
            CONF_MODEL_ID: "invalid-model",
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 0.7,
        }
        provider = OpenAIModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
        
        assert "Invalid model ID" in str(excinfo.value)

    def test_openai_model_validation_invalid_max_tokens(self, mock_openai_model):
        """Test OpenAI model validation with invalid max tokens."""
        config = {
            CONF_PROVIDER: PROVIDER_OPENAI,
            CONF_API_KEY: "test-api-key",
            CONF_MODEL_ID: "gpt-4o",
            CONF_MAX_TOKENS: 5000,  # Exceeds the maximum of 4096
            CONF_TEMPERATURE: 0.7,
        }
        provider = OpenAIModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
        
        assert "Invalid max_tokens" in str(excinfo.value)

    def test_openai_model_validation_invalid_temperature(self, mock_openai_model):
        """Test OpenAI model validation with invalid temperature."""
        config = {
            CONF_PROVIDER: PROVIDER_OPENAI,
            CONF_API_KEY: "test-api-key",
            CONF_MODEL_ID: "gpt-4o",
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 1.5,  # Exceeds the maximum of 1.0
        }
        provider = OpenAIModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
        
        assert "Invalid temperature" in str(excinfo.value)

    def test_bedrock_model_validation_invalid_model(self, mock_bedrock_model):
        """Test Bedrock model validation with invalid model ID."""
        config = {
            CONF_PROVIDER: PROVIDER_BEDROCK,
            CONF_MODEL_ID: "invalid-model",
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 0.7,
        }
        provider = BedrockModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
        
        assert "Invalid model ID" in str(excinfo.value)

    def test_bedrock_model_validation_invalid_max_tokens(self, mock_bedrock_model):
        """Test Bedrock model validation with invalid max tokens."""
        config = {
            CONF_PROVIDER: PROVIDER_BEDROCK,
            CONF_MODEL_ID: "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            CONF_MAX_TOKENS: 5000,  # Exceeds the maximum of 4096
            CONF_TEMPERATURE: 0.7,
        }
        provider = BedrockModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
        
        assert "Invalid max_tokens" in str(excinfo.value)

    def test_anthropic_model_validation_invalid_model(self, mock_anthropic_model):
        """Test Anthropic model validation with invalid model ID."""
        config = {
            CONF_PROVIDER: PROVIDER_ANTHROPIC,
            CONF_API_KEY: "test-api-key",
            CONF_MODEL_ID: "invalid-model",
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 0.7,
        }
        provider = AnthropicModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
        
        assert "Invalid model ID" in str(excinfo.value)

    def test_litellm_model_validation_max_tokens_range(self, mock_litellm_model):
        """Test LiteLLM model validation with max tokens at range boundaries."""
        # Test at minimum boundary
        config = {
            CONF_PROVIDER: PROVIDER_LITELLM,
            CONF_API_KEY: "test-api-key",
            CONF_MODEL_ID: "custom-model",
            CONF_MAX_TOKENS: 1,  # Minimum value
            CONF_TEMPERATURE: 0.7,
        }
        provider = LiteLLMModelProvider(config)
        provider.create_model()  # Should not raise an exception
        
        # Test at maximum boundary
        config[CONF_MAX_TOKENS] = 8192  # Maximum value
        provider = LiteLLMModelProvider(config)
        provider.create_model()  # Should not raise an exception
        
        # Test beyond maximum boundary
        config[CONF_MAX_TOKENS] = 8193  # Beyond maximum value
        provider = LiteLLMModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
        
        assert "Invalid max_tokens" in str(excinfo.value)

    def test_litellm_model_validation_temperature_range(self, mock_litellm_model):
        """Test LiteLLM model validation with temperature at range boundaries."""
        # Test at minimum boundary
        config = {
            CONF_PROVIDER: PROVIDER_LITELLM,
            CONF_API_KEY: "test-api-key",
            CONF_MODEL_ID: "custom-model",
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 0.0,  # Minimum value
        }
        provider = LiteLLMModelProvider(config)
        provider.create_model()  # Should not raise an exception
        
        # Test at maximum boundary
        config[CONF_TEMPERATURE] = 2.0  # Maximum value
        provider = LiteLLMModelProvider(config)
        provider.create_model()  # Should not raise an exception
        
        # Test beyond maximum boundary
        config[CONF_TEMPERATURE] = 2.1  # Beyond maximum value
        provider = LiteLLMModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
        
        assert "Invalid temperature" in str(excinfo.value)