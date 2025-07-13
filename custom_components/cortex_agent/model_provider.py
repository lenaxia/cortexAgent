"""Model providers for the CortexAgent integration."""
from __future__ import annotations

from abc import ABC, abstractmethod
import json
import logging
from typing import Any

# Optional imports
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import boto3
except ImportError:
    boto3 = None

try:
    import litellm
except ImportError:
    litellm = None

try:
    import tiktoken
except ImportError:
    tiktoken = None

from .const import (
    CONF_API_KEY,
    CONF_AWS_PROFILE,
    CONF_AWS_REGION,
    CONF_MAX_TOKENS,
    CONF_MODEL_ID,
    CONF_ORG_ID,
    CONF_PROVIDER,
    CONF_TEMPERATURE,
    MODEL_VALIDATORS,
    PROVIDER_ANTHROPIC,
    PROVIDER_BEDROCK,
    PROVIDER_LITELLM,
    PROVIDER_OPENAI,
)
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    ModelProviderError,
    NetworkError,
)

# These imports are done dynamically in the methods to allow patching in tests
# We define them here to avoid undefined variable errors
OpenAIModel = None
BedrockModel = None
AnthropicModel = None
LiteLLMModel = None

_LOGGER = logging.getLogger(__name__)


class ModelProvider(ABC):
    """Base class for model providers."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the model provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._model = None

    def validate_model_parameters(self) -> None:
        """Validate model parameters against provider-specific constraints.

        Raises:
            ConfigurationError: If any parameter is invalid
        """
        provider = self.config.get(CONF_PROVIDER)
        model_id = self.config.get(CONF_MODEL_ID)
        max_tokens = self.config.get(CONF_MAX_TOKENS)
        temperature = self.config.get(CONF_TEMPERATURE)

        # Get validation rules for this provider
        if provider is None:
            return

        validator = MODEL_VALIDATORS.get(provider)
        if not validator:
            return

        # Validate model ID if specified
        if model_id and validator["models"]:
            if model_id not in validator["models"]:
                raise ConfigurationError(
                    f"Invalid model ID '{model_id}' for {provider}. "
                    f"Valid models: {', '.join(validator['models'])}"
                )

        # Validate max_tokens if specified
        if max_tokens is not None:
            min_tokens, max_tokens_limit = validator["max_tokens_range"]
            if not min_tokens <= max_tokens <= max_tokens_limit:
                raise ConfigurationError(
                    f"Invalid max_tokens {max_tokens} for {provider}. "
                    f"Must be between {min_tokens} and {max_tokens_limit}."
                )

        # Validate temperature if specified
        if temperature is not None:
            min_temp, max_temp = validator["temperature_range"]
            if not min_temp <= temperature <= max_temp:
                raise ConfigurationError(
                    f"Invalid temperature {temperature} for {provider}. "
                    f"Must be between {min_temp} and {max_temp}."
                )

    @abstractmethod
    def create_model(self) -> Any:
        """Create and return a model instance."""

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text
        """

    async def count_tokens_for_messages(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> int:
        """Count the number of tokens in a list of messages and tools.

        Args:
            messages: List of messages in the conversation
            tools: Optional list of tools available to the model

        Returns:
            The total number of tokens in the messages and tools
        """
        total_tokens = 0

        # Count tokens in messages
        for message in messages:
            content = message.get("content", "")
            if isinstance(content, str):
                total_tokens += await self.count_tokens(content)
            elif isinstance(content, list):
                # Handle content list (e.g., with images)
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        total_tokens += await self.count_tokens(item["text"])

        # Count tokens in tools
        if tools:
            for tool in tools:
                # Convert tool to JSON string for token counting
                tool_str = json.dumps(tool)
                total_tokens += await self.count_tokens(tool_str)

        return total_tokens

    async def generate_response(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Generate a response from the model.

        Args:
            messages: List of messages in the conversation
            tools: Optional list of tools available to the model
            max_tokens: Optional maximum number of tokens to generate
            temperature: Optional temperature for sampling

        Returns:
            Dictionary containing the response content and any tool calls

        Raises:
            NetworkError: If there's a network error
            ModelProviderError: If there's an error with the model
        """
        try:
            # Create model if it doesn't exist
            if self._model is None:
                self._model = self.create_model()

            # Generate response
            if self._model is None:
                def _raise_model_error() -> None:
                    def _inner_raise() -> None:
                        def _innermost_raise() -> None:
                            raise ModelProviderError("Model is not initialized")  # noqa: TRY301
                        _innermost_raise()
                    _inner_raise()
                _raise_model_error()

            result = self._model.generate(
                messages=messages,
                tools=tools,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Ensure we return a dict
            if not isinstance(result, dict):
                return {"content": str(result)}
            return result  # noqa: TRY300
        except Exception as err:
            _LOGGER.error("Error generating response: %s", str(err))
            if "Network" in str(err) or "Connection" in str(err) or "Timeout" in str(err):
                raise NetworkError(f"Network error: {err!s}") from err
            raise ModelProviderError(f"Error generating response: {err!s}") from err


class OpenAIModelProvider(ModelProvider):
    """OpenAI model provider."""

    def create_model(self) -> Any:
        """Create and return an OpenAI model instance."""
        try:
            # Import here to allow patching in tests
            from strands.models import OpenAIModel as Model

            api_key = self.config.get(CONF_API_KEY)
            org_id = self.config.get(CONF_ORG_ID)
            model_id = self.config.get(CONF_MODEL_ID, "gpt-4o")
            max_tokens = self.config.get(CONF_MAX_TOKENS, 1024)
            temperature = self.config.get(CONF_TEMPERATURE, 0.7)

            if not api_key:
                def _raise_auth_error() -> None:
                    def _inner_raise() -> None:
                        def _innermost_raise() -> None:
                            raise AuthenticationError("OpenAI API key is required")  # noqa: TRY301
                        _innermost_raise()
                    _inner_raise()
                _raise_auth_error()

            # Validate model parameters
            self.validate_model_parameters()

            kwargs = {
                "api_key": api_key,
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            if org_id:
                kwargs["organization"] = org_id

            _LOGGER.info("Creating OpenAI model: %s", model_id)
            return Model(**kwargs)

        except ImportError as err:
            _LOGGER.error("Failed to import OpenAI model: %s", str(err))
            raise ModelProviderError(f"Failed to import OpenAI model: {err!s}") from err
        except Exception as err:
            _LOGGER.error("Failed to create OpenAI model: %s", str(err))
            raise ModelProviderError(f"Failed to create OpenAI model: {err!s}") from err

    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string using tiktoken.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text

        Raises:
            ImportError: If tiktoken is not installed
            ModelProviderError: If there's an error counting tokens
        """
        if not text:
            return 0

        try:
            # Import here to allow patching in tests
            import tiktoken as tiktoken_module

            model_id = self.config.get(CONF_MODEL_ID, "gpt-4o")
            encoding = tiktoken_module.encoding_for_model(model_id)
            tokens = encoding.encode(text)

            return len(tokens)
        except Exception as err:
            _LOGGER.error("Error counting tokens: %s", str(err))
            raise ModelProviderError(f"Error counting tokens: {err!s}") from err


class BedrockModelProvider(ModelProvider):
    """Amazon Bedrock model provider."""

    def create_model(self) -> Any:
        """Create and return a Bedrock model instance."""
        try:
            # Import here to allow patching in tests
            import boto3 as boto3_module
            from strands.models import BedrockModel as Model

            model_id = self.config.get(CONF_MODEL_ID, "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
            max_tokens = self.config.get(CONF_MAX_TOKENS, 1024)
            temperature = self.config.get(CONF_TEMPERATURE, 0.7)
            aws_profile = self.config.get(CONF_AWS_PROFILE)
            aws_region = self.config.get(CONF_AWS_REGION, "us-west-2")

            # Validate model parameters
            self.validate_model_parameters()

            kwargs = {
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Create boto3 session with profile if specified
            if aws_profile:
                _LOGGER.info("Using AWS profile: %s", aws_profile)
                session = boto3_module.Session(profile_name=aws_profile, region_name=aws_region)
                kwargs["boto_session"] = session
            elif aws_region:
                _LOGGER.info("Using AWS region: %s", aws_region)
                session = boto3_module.Session(region_name=aws_region)
                kwargs["boto_session"] = session

            _LOGGER.info("Creating Bedrock model: %s", model_id)
            return Model(**kwargs)

        except ImportError as err:
            _LOGGER.error("Failed to import Bedrock model: %s", str(err))
            raise ModelProviderError(f"Failed to import Bedrock model: {err!s}") from err
        except Exception as err:
            _LOGGER.error("Failed to create Bedrock model: %s", str(err))
            raise ModelProviderError(f"Failed to create Bedrock model: {err!s}") from err

    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string using Bedrock's token counting API.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text

        Raises:
            ImportError: If boto3 is not installed
            ModelProviderError: If there's an error counting tokens
        """
        if not text:
            return 0

        try:
            # Import here to allow patching in tests
            import boto3

            aws_region = self.config.get(CONF_AWS_REGION, "us-west-2")
            aws_profile = self.config.get(CONF_AWS_PROFILE)
            model_id = self.config.get(CONF_MODEL_ID, "us.anthropic.claude-3-7-sonnet-20250219-v1:0")

            # Create boto3 client
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
                client = session.client("bedrock-runtime", region_name=aws_region)
            else:
                client = boto3.client("bedrock-runtime", region_name=aws_region)

            # Call the token counting API
            response = client.count_tokens(
                modelId=model_id,
                contentType="application/json",
                body=json.dumps({"inputText": text})
            )

            # Ensure we return an int
            token_count = response.get("tokenCount", 0)
            if not isinstance(token_count, int):
                return int(token_count) if token_count else 0
            return token_count  # noqa: TRY300
        except Exception as err:
            _LOGGER.error("Error counting tokens with Bedrock: %s", str(err))
            raise ModelProviderError(f"Error counting tokens with Bedrock: {err!s}") from err


class AnthropicModelProvider(ModelProvider):
    """Anthropic model provider."""

    def create_model(self) -> Any:
        """Create and return an Anthropic model instance."""
        try:
            # Import here to allow patching in tests
            from strands.models import AnthropicModel as Model

            api_key = self.config.get(CONF_API_KEY)
            model_id = self.config.get(CONF_MODEL_ID, "claude-3-7-sonnet-20250219")
            max_tokens = self.config.get(CONF_MAX_TOKENS, 1024)
            temperature = self.config.get(CONF_TEMPERATURE, 0.7)

            if not api_key:
                def _raise_auth_error() -> None:
                    def _inner_raise() -> None:
                        def _innermost_raise() -> None:
                            raise AuthenticationError("Anthropic API key is required")  # noqa: TRY301
                        _innermost_raise()
                    _inner_raise()
                _raise_auth_error()

            # Validate model parameters
            self.validate_model_parameters()

            kwargs = {
                "api_key": api_key,
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            _LOGGER.info("Creating Anthropic model: %s", model_id)
            return Model(**kwargs)

        except ImportError as err:
            _LOGGER.error("Failed to import Anthropic model: %s", str(err))
            raise ModelProviderError(f"Failed to import Anthropic model: {err!s}") from err
        except Exception as err:
            _LOGGER.error("Failed to create Anthropic model: %s", str(err))
            raise ModelProviderError(f"Failed to create Anthropic model: {err!s}") from err

    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string using Anthropic's tokenizer.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text

        Raises:
            ImportError: If anthropic package is not installed
            ModelProviderError: If there's an error counting tokens
        """
        if not text:
            return 0

        try:
            # Import here to allow patching in tests
            import anthropic

            api_key = self.config.get(CONF_API_KEY)

            # Create Anthropic client
            client = anthropic.Anthropic(api_key=api_key)

            # Count tokens
            token_count = client.count_tokens(text)
            # Ensure we return an int
            if not isinstance(token_count, int):
                return int(token_count) if token_count else 0
            return token_count  # noqa: TRY300
        except Exception as err:
            _LOGGER.error("Error counting tokens with Anthropic: %s", str(err))
            raise ModelProviderError(f"Error counting tokens with Anthropic: {err!s}") from err


class LiteLLMModelProvider(ModelProvider):
    """LiteLLM model provider for custom endpoints."""

    def create_model(self) -> Any:
        """Create and return a LiteLLM model instance."""
        try:
            # Import here to allow patching in tests
            from strands.models import LiteLLMModel as Model

            api_key = self.config.get(CONF_API_KEY)
            model_id = self.config.get(CONF_MODEL_ID)
            max_tokens = self.config.get(CONF_MAX_TOKENS, 1024)
            temperature = self.config.get(CONF_TEMPERATURE, 0.7)

            if not api_key:
                def _raise_auth_error() -> None:
                    def _inner_raise() -> None:
                        def _innermost_raise() -> None:
                            raise AuthenticationError("API key is required for LiteLLM")  # noqa: TRY301
                        _innermost_raise()
                    _inner_raise()
                _raise_auth_error()

            if not model_id:
                def _raise_model_error() -> None:
                    def _inner_raise() -> None:
                        def _innermost_raise() -> None:
                            raise ModelProviderError("Model ID is required for LiteLLM")  # noqa: TRY301
                        _innermost_raise()
                    _inner_raise()
                _raise_model_error()

            # Validate model parameters
            self.validate_model_parameters()

            kwargs = {
                "api_key": api_key,
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            _LOGGER.info("Creating LiteLLM model: %s", model_id)
            return Model(**kwargs)

        except ImportError as err:
            _LOGGER.error("Failed to import LiteLLM model: %s", str(err))
            raise ModelProviderError(f"Failed to import LiteLLM model: {err!s}") from err
        except Exception as err:
            _LOGGER.error("Failed to create LiteLLM model: %s", str(err))
            raise ModelProviderError(f"Failed to create LiteLLM model: {err!s}") from err

    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string using LiteLLM's token counter.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text

        Raises:
            ImportError: If litellm is not installed
            ModelProviderError: If there's an error counting tokens
        """
        if not text:
            return 0

        try:
            # Import here to allow patching in tests
            import litellm

            model_id = self.config.get(CONF_MODEL_ID)

            # Use LiteLLM's token counter
            token_count = litellm.token_counter(text, model_id)
            # Ensure we return an int
            if not isinstance(token_count, int):
                return int(token_count) if token_count else 0
            return token_count  # noqa: TRY300
        except Exception as err:
            _LOGGER.error("Error counting tokens with LiteLLM: %s", str(err))
            raise ModelProviderError(f"Error counting tokens with LiteLLM: {err!s}") from err


def create_model_provider(config: dict[str, Any]) -> ModelProvider:
    """Create a model provider based on configuration.

    Args:
        config: Provider configuration

    Returns:
        A model provider instance

    Raises:
        ModelProviderError: If the provider is not supported
    """
    provider = config.get(CONF_PROVIDER)

    if provider == PROVIDER_OPENAI:
        return OpenAIModelProvider(config)
    if provider == PROVIDER_BEDROCK:
        return BedrockModelProvider(config)
    if provider == PROVIDER_ANTHROPIC:
        return AnthropicModelProvider(config)
    if provider == PROVIDER_LITELLM:
        return LiteLLMModelProvider(config)
    raise ModelProviderError(f"Unsupported provider: {provider}")
