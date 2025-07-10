"""Tests for the generate_response method in ModelProvider."""
import pytest
from unittest.mock import patch, MagicMock

from custom_components.cortex_agent.model_provider import (
    ModelProvider,
    OpenAIModelProvider,
    BedrockModelProvider,
    AnthropicModelProvider,
    LiteLLMModelProvider,
)
from custom_components.cortex_agent.exceptions import (
    ModelProviderError,
    NetworkError,
)


class TestModelProviderGenerate:
    """Test the generate_response method in ModelProvider."""

    @pytest.fixture
    def mock_openai_model(self):
        """Mock OpenAI model."""
        with patch("strands.models.OpenAIModel") as mock_model:
            instance = mock_model.return_value
            instance.generate.return_value = {
                "content": "Test response",
                "tool_calls": None,
            }
            yield instance

    @pytest.fixture
    def mock_bedrock_model(self):
        """Mock Bedrock model."""
        with patch("strands.models.BedrockModel") as mock_model:
            instance = mock_model.return_value
            instance.generate.return_value = {
                "content": "Test response",
                "tool_calls": None,
            }
            yield instance

    @pytest.fixture
    def mock_anthropic_model(self):
        """Mock Anthropic model."""
        with patch("strands.models.AnthropicModel") as mock_model:
            instance = mock_model.return_value
            instance.generate.return_value = {
                "content": "Test response",
                "tool_calls": None,
            }
            yield instance

    @pytest.fixture
    def mock_litellm_model(self):
        """Mock LiteLLM model."""
        with patch("strands.models.LiteLLMModel") as mock_model:
            instance = mock_model.return_value
            instance.generate.return_value = {
                "content": "Test response",
                "tool_calls": None,
            }
            yield instance

    async def test_openai_generate_response(self, mock_openai_model):
        """Test OpenAI generate_response method."""
        provider = OpenAIModelProvider({"provider": "openai", "api_key": "test"})
        provider._model = mock_openai_model

        messages = [{"role": "user", "content": "Hello"}]
        response = await provider.generate_response(messages=messages)

        assert response == {"content": "Test response", "tool_calls": None}
        mock_openai_model.generate.assert_called_once_with(
            messages=messages, tools=None, max_tokens=None, temperature=None
        )

    async def test_bedrock_generate_response(self, mock_bedrock_model):
        """Test Bedrock generate_response method."""
        provider = BedrockModelProvider({"provider": "bedrock", "aws_region": "us-west-2"})
        provider._model = mock_bedrock_model

        messages = [{"role": "user", "content": "Hello"}]
        response = await provider.generate_response(messages=messages)

        assert response == {"content": "Test response", "tool_calls": None}
        mock_bedrock_model.generate.assert_called_once_with(
            messages=messages, tools=None, max_tokens=None, temperature=None
        )

    async def test_anthropic_generate_response(self, mock_anthropic_model):
        """Test Anthropic generate_response method."""
        provider = AnthropicModelProvider({"provider": "anthropic", "api_key": "test"})
        provider._model = mock_anthropic_model

        messages = [{"role": "user", "content": "Hello"}]
        response = await provider.generate_response(messages=messages)

        assert response == {"content": "Test response", "tool_calls": None}
        mock_anthropic_model.generate.assert_called_once_with(
            messages=messages, tools=None, max_tokens=None, temperature=None
        )

    async def test_litellm_generate_response(self, mock_litellm_model):
        """Test LiteLLM generate_response method."""
        provider = LiteLLMModelProvider({"provider": "litellm", "api_key": "test", "model_id": "test", "base_url": "test"})
        provider._model = mock_litellm_model

        messages = [{"role": "user", "content": "Hello"}]
        response = await provider.generate_response(messages=messages)

        assert response == {"content": "Test response", "tool_calls": None}
        mock_litellm_model.generate.assert_called_once_with(
            messages=messages, tools=None, max_tokens=None, temperature=None
        )

    async def test_generate_response_with_tools(self, mock_openai_model):
        """Test generate_response method with tools."""
        provider = OpenAIModelProvider({"provider": "openai", "api_key": "test"})
        provider._model = mock_openai_model

        messages = [{"role": "user", "content": "Hello"}]
        tools = [{"name": "test_tool", "description": "Test tool", "parameters": {}}]
        response = await provider.generate_response(messages=messages, tools=tools)

        assert response == {"content": "Test response", "tool_calls": None}
        mock_openai_model.generate.assert_called_once_with(
            messages=messages, tools=tools, max_tokens=None, temperature=None
        )

    async def test_generate_response_with_parameters(self, mock_openai_model):
        """Test generate_response method with parameters."""
        provider = OpenAIModelProvider({"provider": "openai", "api_key": "test"})
        provider._model = mock_openai_model

        messages = [{"role": "user", "content": "Hello"}]
        response = await provider.generate_response(
            messages=messages, max_tokens=100, temperature=0.5
        )

        assert response == {"content": "Test response", "tool_calls": None}
        mock_openai_model.generate.assert_called_once_with(
            messages=messages, tools=None, max_tokens=100, temperature=0.5
        )

    async def test_generate_response_network_error(self, mock_openai_model):
        """Test generate_response method with network error."""
        provider = OpenAIModelProvider({"provider": "openai", "api_key": "test"})
        provider._model = mock_openai_model
        mock_openai_model.generate.side_effect = Exception("Network error")

        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(NetworkError):
            await provider.generate_response(messages=messages)

    async def test_generate_response_model_error(self, mock_openai_model):
        """Test generate_response method with model error."""
        provider = OpenAIModelProvider({"provider": "openai", "api_key": "test"})
        provider._model = mock_openai_model
        mock_openai_model.generate.side_effect = ValueError("Model error")

        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(ModelProviderError):
            await provider.generate_response(messages=messages)

    async def test_generate_response_lazy_model_creation(self):
        """Test generate_response method with lazy model creation."""
        with patch.object(OpenAIModelProvider, "create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_model.generate.return_value = {
                "content": "Test response",
                "tool_calls": None,
            }
            mock_create_model.return_value = mock_model

            provider = OpenAIModelProvider({"provider": "openai", "api_key": "test"})
            messages = [{"role": "user", "content": "Hello"}]
            response = await provider.generate_response(messages=messages)

            assert response == {"content": "Test response", "tool_calls": None}
            mock_create_model.assert_called_once()
            mock_model.generate.assert_called_once_with(
                messages=messages, tools=None, max_tokens=None, temperature=None
            )