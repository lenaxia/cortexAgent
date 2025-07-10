"""Tests for the CortexAgent model provider."""
from unittest.mock import patch, MagicMock
import pytest

from custom_components.cortex_agent.model_provider import (
    create_model_provider,
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
    ModelProviderError,
    AuthenticationError,
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


@pytest.fixture
def mock_boto3():
    """Mock boto3."""
    with patch("boto3.Session") as mock:
        yield mock


class TestCreateModelProvider:
    """Test the create_model_provider function."""

    def test_create_openai_provider(self):
        """Test creating an OpenAI provider."""
        config = {CONF_PROVIDER: PROVIDER_OPENAI}
        provider = create_model_provider(config)
        assert isinstance(provider, OpenAIModelProvider)

    def test_create_bedrock_provider(self):
        """Test creating a Bedrock provider."""
        config = {CONF_PROVIDER: PROVIDER_BEDROCK}
        provider = create_model_provider(config)
        assert isinstance(provider, BedrockModelProvider)

    def test_create_anthropic_provider(self):
        """Test creating an Anthropic provider."""
        config = {CONF_PROVIDER: PROVIDER_ANTHROPIC}
        provider = create_model_provider(config)
        assert isinstance(provider, AnthropicModelProvider)

    def test_create_litellm_provider(self):
        """Test creating a LiteLLM provider."""
        config = {CONF_PROVIDER: PROVIDER_LITELLM}
        provider = create_model_provider(config)
        assert isinstance(provider, LiteLLMModelProvider)

    def test_create_invalid_provider(self):
        """Test creating an invalid provider."""
        config = {CONF_PROVIDER: "invalid"}
        with pytest.raises(ModelProviderError):
            create_model_provider(config)


class TestOpenAIModelProvider:
    """Test the OpenAI model provider."""

    def test_create_model_success(self, mock_openai_model):
        """Test creating an OpenAI model successfully."""
        config = {
            CONF_PROVIDER: PROVIDER_OPENAI,
            CONF_API_KEY: "test-api-key",
            CONF_MODEL_ID: "gpt-4o",
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 0.7,
        }
        provider = OpenAIModelProvider(config)
        model = provider.create_model()
        
        mock_openai_model.assert_called_once_with(
            api_key="test-api-key",
            model_id="gpt-4o",
            max_tokens=1024,
            temperature=0.7,
        )
        assert model == mock_openai_model.return_value

    def test_create_model_missing_api_key(self, mock_openai_model):
        """Test creating an OpenAI model with missing API key."""
        config = {
            CONF_PROVIDER: PROVIDER_OPENAI,
            CONF_MODEL_ID: "gpt-4o",
        }
        provider = OpenAIModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
        
        # Verify that the ModelProviderError wraps an AuthenticationError
        assert "OpenAI API key is required" in str(excinfo.value)

    def test_create_model_import_error(self):
        """Test creating an OpenAI model with import error."""
        config = {
            CONF_PROVIDER: PROVIDER_OPENAI,
            CONF_API_KEY: "test-api-key",
        }
        provider = OpenAIModelProvider(config)
        
        with patch("strands.models.OpenAIModel",
                  side_effect=ImportError("Module not found")):
            with pytest.raises(ModelProviderError):
                provider.create_model()


class TestBedrockModelProvider:
    """Test the Bedrock model provider."""

    def test_create_model_success(self, mock_bedrock_model, mock_boto3):
        """Test creating a Bedrock model successfully."""
        config = {
            CONF_PROVIDER: PROVIDER_BEDROCK,
            CONF_MODEL_ID: "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 0.7,
        }
        provider = BedrockModelProvider(config)
        model = provider.create_model()
        
        # Check that the mock was called with the expected parameters
        # The boto_session parameter is added by the implementation
        assert mock_bedrock_model.call_args is not None
        call_kwargs = mock_bedrock_model.call_args.kwargs
        assert call_kwargs["model_id"] == "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        assert call_kwargs["max_tokens"] == 1024
        assert call_kwargs["temperature"] == 0.7
        assert "boto_session" in call_kwargs
        
        assert model == mock_bedrock_model.return_value

    def test_create_model_with_aws_profile(self, mock_bedrock_model, mock_boto3):
        """Test creating a Bedrock model with AWS profile."""
        config = {
            CONF_PROVIDER: PROVIDER_BEDROCK,
            CONF_MODEL_ID: "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            "aws_profile": "test-profile",
            "aws_region": "us-west-2",
        }
        provider = BedrockModelProvider(config)
        model = provider.create_model()
        
        mock_boto3.assert_called_once_with(
            profile_name="test-profile", 
            region_name="us-west-2"
        )
        mock_bedrock_model.assert_called_once()
        assert model == mock_bedrock_model.return_value


class TestAnthropicModelProvider:
    """Test the Anthropic model provider."""

    def test_create_model_success(self, mock_anthropic_model):
        """Test creating an Anthropic model successfully."""
        config = {
            CONF_PROVIDER: PROVIDER_ANTHROPIC,
            CONF_API_KEY: "test-api-key",
            CONF_MODEL_ID: "claude-3-7-sonnet-20250219",
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 0.7,
        }
        provider = AnthropicModelProvider(config)
        model = provider.create_model()
        
        mock_anthropic_model.assert_called_once_with(
            api_key="test-api-key",
            model_id="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            temperature=0.7,
        )
        assert model == mock_anthropic_model.return_value

    def test_create_model_missing_api_key(self, mock_anthropic_model):
        """Test creating an Anthropic model with missing API key."""
        config = {
            CONF_PROVIDER: PROVIDER_ANTHROPIC,
            CONF_MODEL_ID: "claude-3-7-sonnet-20250219",
        }
        provider = AnthropicModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
            
        # Verify that the ModelProviderError wraps an AuthenticationError
        assert "Anthropic API key is required" in str(excinfo.value)


class TestLiteLLMModelProvider:
    """Test the LiteLLM model provider."""

    def test_create_model_success(self, mock_litellm_model):
        """Test creating a LiteLLM model successfully."""
        config = {
            CONF_PROVIDER: PROVIDER_LITELLM,
            CONF_API_KEY: "test-api-key",
            CONF_MODEL_ID: "custom-model",
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 0.7,
        }
        provider = LiteLLMModelProvider(config)
        model = provider.create_model()
        
        mock_litellm_model.assert_called_once_with(
            api_key="test-api-key",
            model_id="custom-model",
            max_tokens=1024,
            temperature=0.7,
        )
        assert model == mock_litellm_model.return_value

    def test_create_model_missing_api_key(self, mock_litellm_model):
        """Test creating a LiteLLM model with missing API key."""
        config = {
            CONF_PROVIDER: PROVIDER_LITELLM,
            CONF_MODEL_ID: "custom-model",
        }
        provider = LiteLLMModelProvider(config)
        
        with pytest.raises(ModelProviderError) as excinfo:
            provider.create_model()
            
        # Verify that the ModelProviderError wraps an AuthenticationError
        assert "API key is required for LiteLLM" in str(excinfo.value)

    def test_create_model_missing_model_id(self, mock_litellm_model):
        """Test creating a LiteLLM model with missing model ID."""
        config = {
            CONF_PROVIDER: PROVIDER_LITELLM,
            CONF_API_KEY: "test-api-key",
        }
        provider = LiteLLMModelProvider(config)
        
        with pytest.raises(ModelProviderError):
            provider.create_model()