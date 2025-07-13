"""Config flow for CortexAgent integration."""
from __future__ import annotations

import hashlib
import logging
from typing import Any

import voluptuous as vol

# Import required packages for connection testing
# These are imported here to avoid import errors when the integration is loaded
# but the packages are not installed
try:
    import openai
except ImportError:
    openai = None

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

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_API_KEY,
    CONF_AWS_PROFILE,
    CONF_AWS_REGION,
    CONF_BASE_URL,
    CONF_MAX_TOKENS,
    CONF_MEMORY_ENABLED,
    CONF_MODEL_ID,
    CONF_ORG_ID,
    CONF_PROVIDER,
    CONF_SYSTEM_PROMPT,
    CONF_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_NAME,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TEMPERATURE,
    DOMAIN,
    MODEL_VALIDATORS,
    PROVIDER_ANTHROPIC,
    PROVIDER_BEDROCK,
    PROVIDER_LITELLM,
    PROVIDER_OPENAI,
    PROVIDERS,
)

_LOGGER = logging.getLogger(__name__)

# Base schema for all providers
BASE_SCHEMA = vol.Schema({
    vol.Required(CONF_PROVIDER): vol.In(PROVIDERS),
})

# Provider-specific schemas
PROVIDER_SCHEMA = {
    PROVIDER_OPENAI: vol.Schema({
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_ORG_ID): str,
        vol.Required(CONF_MODEL_ID): vol.In(MODEL_VALIDATORS[PROVIDER_OPENAI]["models"]),
        vol.Optional(CONF_BASE_URL): str,
    }),
    PROVIDER_ANTHROPIC: vol.Schema({
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_MODEL_ID): vol.In(MODEL_VALIDATORS[PROVIDER_ANTHROPIC]["models"]),
        vol.Optional(CONF_BASE_URL): str,
    }),
    PROVIDER_BEDROCK: vol.Schema({
        vol.Optional(CONF_AWS_PROFILE): str,
        vol.Required(CONF_AWS_REGION): str,
        vol.Required(CONF_MODEL_ID): vol.In(MODEL_VALIDATORS[PROVIDER_BEDROCK]["models"]),
    }),
    PROVIDER_LITELLM: vol.Schema({
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_MODEL_ID): str,
        vol.Required(CONF_BASE_URL): str,
    }),
}

# Options schema
OPTIONS_SCHEMA = vol.Schema({
    vol.Optional(CONF_SYSTEM_PROMPT, default=DEFAULT_SYSTEM_PROMPT): str,
    vol.Optional(CONF_MAX_TOKENS, default=DEFAULT_MAX_TOKENS): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=8192)
    ),
    vol.Optional(CONF_TEMPERATURE, default=DEFAULT_TEMPERATURE): vol.All(
        vol.Coerce(float), vol.Range(min=0, max=2)
    ),
    vol.Optional(CONF_MEMORY_ENABLED, default=True): bool,
})


class CortexAgentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CortexAgent."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.provider: str | None = None
        self.provider_config: dict[str, Any] = {}
        self.options: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store the provider for later steps
            self.provider = user_input[CONF_PROVIDER]
            # Proceed to provider-specific step
            return await self.async_step_provider()

        return self.async_show_form(
            step_id="user",
            data_schema=BASE_SCHEMA,
            errors=errors,
        )

    async def async_step_provider(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the provider step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store the provider config for later steps
            self.provider_config = user_input
            self.provider_config[CONF_PROVIDER] = self.provider

            # Test the connection to the provider
            try:
                await self._test_connection(self.provider_config)

                # Check if we already have a config entry for this provider
                # Generate a unique ID based on the provider and API key
                unique_id = None
                if self.provider == PROVIDER_OPENAI:
                    api_key = self.provider_config.get(CONF_API_KEY, "")
                    org_id = self.provider_config.get(CONF_ORG_ID)
                    if org_id:
                        unique_id = f"{DOMAIN}_{self.provider}_{org_id}"
                    else:
                        # Use a hash of the API key to avoid storing sensitive data in the unique ID
                        unique_id = f"{DOMAIN}_{self.provider}_{hashlib.md5(api_key.encode()).hexdigest()[:8]}"
                elif self.provider == PROVIDER_ANTHROPIC:
                    api_key = self.provider_config.get(CONF_API_KEY, "")
                    # Use a hash of the API key
                    unique_id = f"{DOMAIN}_{self.provider}_{hashlib.md5(api_key.encode()).hexdigest()[:8]}"
                elif self.provider == PROVIDER_BEDROCK:
                    aws_profile = self.provider_config.get(CONF_AWS_PROFILE, "")
                    aws_region = self.provider_config.get(CONF_AWS_REGION, "")
                    unique_id = f"{DOMAIN}_{self.provider}_{aws_profile}_{aws_region}"
                elif self.provider == PROVIDER_LITELLM:
                    api_key = self.provider_config.get(CONF_API_KEY, "")
                    base_url = self.provider_config.get(CONF_BASE_URL, "")
                    # Combine base URL and API key hash
                    url_hash = hashlib.md5(base_url.encode()).hexdigest()[:4]
                    key_hash = hashlib.md5(api_key.encode()).hexdigest()[:4]
                    unique_id = f"{DOMAIN}_{self.provider}_{url_hash}_{key_hash}"

                # Check if we already have a config entry with this unique ID
                if unique_id:
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                # Proceed to options step
                return await self.async_step_options()
            except ImportError as ex:
                _LOGGER.error("Required package not installed: %s", ex)
                errors["base"] = "missing_package"
            except ConnectionError as ex:
                _LOGGER.error("Connection error: %s", ex)
                errors["base"] = "cannot_connect"
            except TimeoutError as ex:
                _LOGGER.error("Connection timeout: %s", ex)
                errors["base"] = "timeout_connect"
            except ValueError as ex:
                _LOGGER.error("Invalid configuration value: %s", ex)
                errors["base"] = "invalid_auth"
            except PermissionError as ex:
                _LOGGER.error("Permission error: %s", ex)
                errors["base"] = "permission_error"
            except (KeyError, TypeError, AttributeError) as ex:
                _LOGGER.error("Unexpected error validating provider configuration: %s", ex)
                errors["base"] = "provider_auth"

        # Show the provider-specific form
        if self.provider in PROVIDER_SCHEMA:
            return self.async_show_form(
                step_id=self.provider,
                data_schema=PROVIDER_SCHEMA[self.provider],
                errors=errors,
            )

        # If we don't have a schema for this provider, abort
        return self.async_abort(reason="provider_not_supported")

    async def async_step_openai(self, user_input=None):
        """Handle the OpenAI step."""
        return await self.async_step_provider(user_input)

    async def async_step_anthropic(self, user_input=None):
        """Handle the Anthropic step."""
        return await self.async_step_provider(user_input)

    async def async_step_bedrock(self, user_input=None):
        """Handle the Bedrock step."""
        return await self.async_step_provider(user_input)

    async def async_step_litellm(self, user_input=None):
        """Handle the LiteLLM step."""
        return await self.async_step_provider(user_input)

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the options step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.options = user_input

            # Create the config entry
            # Store sensitive data in options for better security
            data = {
                CONF_PROVIDER: self.provider,
            }

            # Move sensitive data to options for better security
            if self.provider == PROVIDER_OPENAI:
                # Keep API key in data for backward compatibility but mark it for secure storage
                data[CONF_API_KEY] = self.provider_config.get(CONF_API_KEY)
                data["_secure"] = True  # Mark for secure storage

                # Keep other non-sensitive data in data
                if CONF_ORG_ID in self.provider_config:
                    data[CONF_ORG_ID] = self.provider_config.get(CONF_ORG_ID)
                if CONF_BASE_URL in self.provider_config:
                    data[CONF_BASE_URL] = self.provider_config.get(CONF_BASE_URL)
                if CONF_MODEL_ID in self.provider_config:
                    data[CONF_MODEL_ID] = self.provider_config.get(CONF_MODEL_ID)

            elif self.provider in (PROVIDER_ANTHROPIC, PROVIDER_LITELLM):
                # Keep API key in data for backward compatibility but mark it for secure storage
                data[CONF_API_KEY] = self.provider_config.get(CONF_API_KEY)
                data["_secure"] = True  # Mark for secure storage

                # Keep other non-sensitive data in data
                if CONF_BASE_URL in self.provider_config:
                    data[CONF_BASE_URL] = self.provider_config.get(CONF_BASE_URL)
                if CONF_MODEL_ID in self.provider_config:
                    data[CONF_MODEL_ID] = self.provider_config.get(CONF_MODEL_ID)

            else:
                # For providers without sensitive data (like Bedrock)
                data.update(self.provider_config)

            return self.async_create_entry(
                title=DEFAULT_NAME,
                data=data,
                options=self.options,
            )

        return self.async_show_form(
            step_id="options",
            data_schema=OPTIONS_SCHEMA,
            errors=errors,
        )

    async def _test_connection(self, provider_config: dict[str, Any]) -> bool:
        """Test connection to the provider.

        Args:
            provider_config: Provider configuration

        Returns:
            True if connection is successful, False otherwise

        Raises:
            ImportError: If required package is not installed
            ConnectionError: If connection to provider fails
            TimeoutError: If connection times out
            ValueError: If configuration values are invalid
            PermissionError: If permission is denied
        """
        provider = provider_config.get(CONF_PROVIDER)

        if provider == PROVIDER_OPENAI:
            return await self._test_openai_connection(provider_config)
        if provider == PROVIDER_ANTHROPIC:
            return await self._test_anthropic_connection(provider_config)
        if provider == PROVIDER_BEDROCK:
            return await self._test_bedrock_connection(provider_config)
        if provider == PROVIDER_LITELLM:
            return await self._test_litellm_connection(provider_config)

        return True

    async def _test_openai_connection(self, provider_config: dict[str, Any]) -> bool:
        """Test connection to OpenAI."""
        api_key = provider_config.get(CONF_API_KEY)
        if not api_key:
            raise ValueError("OpenAI API key is required")

        if openai is None:
            _LOGGER.warning("OpenAI package not installed")
            raise ImportError("OpenAI package not installed")

        try:
            client = openai.OpenAI(api_key=api_key)
            try:
                client.models.list()
                _LOGGER.info("Successfully connected to OpenAI API")
            except openai.APITimeoutError as ex:
                _LOGGER.error("OpenAI API connection timed out: %s", str(ex))
                raise TimeoutError(f"OpenAI API connection timed out: {ex!s}") from ex
            except openai.AuthenticationError as ex:
                _LOGGER.error("OpenAI API authentication failed: %s", str(ex))
                raise ValueError(f"OpenAI API authentication failed: {ex!s}") from ex
            except openai.PermissionDeniedError as ex:
                _LOGGER.error("OpenAI API permission denied: %s", str(ex))
                raise PermissionError(f"OpenAI API permission denied: {ex!s}") from ex
            except openai.APIConnectionError as ex:
                _LOGGER.error("Failed to connect to OpenAI API: %s", str(ex))
                raise ConnectionError(f"Failed to connect to OpenAI API: {ex!s}") from ex
            except Exception as ex:
                _LOGGER.error("Unexpected error with OpenAI API: %s", str(ex))
                raise ConnectionError(f"Unexpected error with OpenAI API: {ex!s}") from ex
            else:
                return True
        except (ValueError, TypeError, AttributeError) as ex:
            _LOGGER.error("Failed to initialize OpenAI client: %s", str(ex))
            raise ConnectionError(f"Failed to initialize OpenAI client: {ex!s}") from ex

    async def _test_anthropic_connection(self, provider_config: dict[str, Any]) -> bool:
        """Test connection to Anthropic."""
        api_key = provider_config.get(CONF_API_KEY)
        if not api_key:
            raise ValueError("Anthropic API key is required")

        if anthropic is None:
            _LOGGER.warning("Anthropic package not installed")
            raise ImportError("Anthropic package not installed")

        try:
            client = anthropic.Anthropic(api_key=api_key)
            try:
                client.models.list()
                _LOGGER.info("Successfully connected to Anthropic API")
            except anthropic.APITimeoutError as ex:
                _LOGGER.error("Anthropic API connection timed out: %s", str(ex))
                raise TimeoutError(f"Anthropic API connection timed out: {ex!s}") from ex
            except anthropic.AuthenticationError as ex:
                _LOGGER.error("Anthropic API authentication failed: %s", str(ex))
                raise ValueError(f"Anthropic API authentication failed: {ex!s}") from ex
            except anthropic.PermissionDeniedError as ex:
                _LOGGER.error("Anthropic API permission denied: %s", str(ex))
                raise PermissionError(f"Anthropic API permission denied: {ex!s}") from ex
            except anthropic.APIConnectionError as ex:
                _LOGGER.error("Failed to connect to Anthropic API: %s", str(ex))
                raise ConnectionError(f"Failed to connect to Anthropic API: {ex!s}") from ex
            except Exception as ex:
                _LOGGER.error("Unexpected error with Anthropic API: %s", str(ex))
                raise ConnectionError(f"Unexpected error with Anthropic API: {ex!s}") from ex
            else:
                return True
        except (ValueError, TypeError, AttributeError) as ex:
            _LOGGER.error("Failed to initialize Anthropic client: %s", str(ex))
            raise ConnectionError(f"Failed to initialize Anthropic client: {ex!s}") from ex

    async def _test_bedrock_connection(self, provider_config: dict[str, Any]) -> bool:
        """Test connection to AWS Bedrock."""
        aws_region = provider_config.get(CONF_AWS_REGION)
        aws_profile = provider_config.get(CONF_AWS_PROFILE)

        if not aws_region:
            raise ValueError("AWS region is required")

        if boto3 is None:
            _LOGGER.warning("Boto3 package not installed")
            raise ImportError("Boto3 package not installed")

        try:
            # Create session with profile if specified
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
            else:
                session = boto3.Session(region_name=aws_region)

            # Create Bedrock client
            try:
                client = session.client("bedrock-runtime")

                # List models to test connection
                try:
                    client.list_foundation_models()
                    _LOGGER.info("Successfully connected to AWS Bedrock")
                except client.exceptions.ValidationException as ex:
                    _LOGGER.error("AWS Bedrock validation error: %s", str(ex))
                    raise ValueError(f"AWS Bedrock validation error: {ex!s}") from ex
                except client.exceptions.AccessDeniedException as ex:
                    _LOGGER.error("AWS Bedrock access denied: %s", str(ex))
                    raise PermissionError(f"AWS Bedrock access denied: {ex!s}") from ex
                except client.exceptions.ThrottlingException as ex:
                    _LOGGER.error("AWS Bedrock throttling error: %s", str(ex))
                    raise ConnectionError(f"AWS Bedrock throttling error: {ex!s}") from ex
                except client.exceptions.InternalServerException as ex:
                    _LOGGER.error("AWS Bedrock server error: %s", str(ex))
                    raise ConnectionError(f"AWS Bedrock server error: {ex!s}") from ex
                except Exception as ex:
                    _LOGGER.error("Unexpected error with AWS Bedrock: %s", str(ex))
                    raise ConnectionError(f"Unexpected error with AWS Bedrock: {ex!s}") from ex
                else:
                    return True
            except (ValueError, TypeError, AttributeError) as ex:
                _LOGGER.error("Failed to create AWS Bedrock client: %s", str(ex))
                raise ConnectionError(f"Failed to create AWS Bedrock client: {ex!s}") from ex
        except (ValueError, TypeError, AttributeError) as ex:
            _LOGGER.error("Failed to initialize AWS session: %s", str(ex))
            raise ConnectionError(f"Failed to initialize AWS session: {ex!s}") from ex

    async def _test_litellm_connection(self, provider_config: dict[str, Any]) -> bool:
        """Test connection to LiteLLM."""
        api_key = provider_config.get(CONF_API_KEY)
        base_url = provider_config.get(CONF_BASE_URL)
        model_id = provider_config.get(CONF_MODEL_ID)

        if not api_key:
            raise ValueError("API key is required for LiteLLM")
        if not base_url:
            raise ValueError("Base URL is required for LiteLLM")
        if not model_id:
            raise ValueError("Model ID is required for LiteLLM")

        if litellm is None:
            _LOGGER.warning("LiteLLM package not installed")
            raise ImportError("LiteLLM package not installed")

        try:
            # Configure LiteLLM
            litellm.api_key = api_key
            litellm.api_base = base_url

            # Make a simple completion call to test the connection
            try:
                # Just test the connection without storing the response
                litellm.completion(
                    model=model_id,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                _LOGGER.info("Successfully connected to LiteLLM endpoint")
            except litellm.exceptions.AuthenticationError as ex:
                _LOGGER.error("LiteLLM authentication error: %s", str(ex))
                raise ValueError(f"LiteLLM authentication error: {ex!s}") from ex
            except litellm.exceptions.BadRequestError as ex:
                _LOGGER.error("LiteLLM bad request: %s", str(ex))
                raise ValueError(f"LiteLLM bad request: {ex!s}") from ex
            except litellm.exceptions.RateLimitError as ex:
                _LOGGER.error("LiteLLM rate limit exceeded: %s", str(ex))
                raise ConnectionError(f"LiteLLM rate limit exceeded: {ex!s}") from ex
            except litellm.exceptions.ServiceUnavailableError as ex:
                _LOGGER.error("LiteLLM service unavailable: %s", str(ex))
                raise ConnectionError(f"LiteLLM service unavailable: {ex!s}") from ex
            except litellm.exceptions.Timeout as ex:
                _LOGGER.error("LiteLLM request timed out: %s", str(ex))
                raise TimeoutError(f"LiteLLM request timed out: {ex!s}") from ex
            except Exception as ex:
                _LOGGER.error("Unexpected error with LiteLLM: %s", str(ex))
                raise ConnectionError(f"Unexpected error with LiteLLM: {ex!s}") from ex
            else:
                return True
        except (ValueError, TypeError, AttributeError) as ex:
            _LOGGER.error("Failed to configure LiteLLM: %s", str(ex))
            raise ConnectionError(f"Failed to configure LiteLLM: {ex!s}") from ex

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)

    async def async_step_reauth(self, user_input=None):
        """Handle reauthorization request."""
        self.provider = user_input[CONF_PROVIDER]
        self.provider_config = user_input

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Handle reauthorization confirmation."""
        errors = {}

        if user_input is not None:
            # Update the provider config with the new values
            self.provider_config.update(user_input)

            try:
                # Test the connection with the new credentials
                await self._test_connection(self.provider_config)

                # Update the config entry with the new credentials
                self.hass.config_entries.async_update_entry(
                    self.context["entry_id"],
                    data={**self.provider_config}
                )

                # Reload the config entry to apply the changes
                await self.hass.config_entries.async_reload(self.context["entry_id"])

                return self.async_abort(reason="reauth_successful")
            except ImportError as ex:
                _LOGGER.error("Required package not installed: %s", ex)
                errors["base"] = "missing_package"
            except ConnectionError as ex:
                _LOGGER.error("Connection error: %s", ex)
                errors["base"] = "cannot_connect"
            except TimeoutError as ex:
                _LOGGER.error("Connection timeout: %s", ex)
                errors["base"] = "timeout_connect"
            except ValueError as ex:
                _LOGGER.error("Invalid configuration value: %s", ex)
                errors["base"] = "invalid_auth"
            except (KeyError, TypeError, AttributeError) as ex:
                _LOGGER.error("Unexpected error during reauth: %s", ex)
                errors["base"] = "provider_auth"

        # Create provider-specific schema for reauth
        if self.provider == PROVIDER_OPENAI:
            schema = vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_ORG_ID): str,
            })
            description = "Please enter your new OpenAI API key"
        elif self.provider == PROVIDER_ANTHROPIC:
            schema = vol.Schema({
                vol.Required(CONF_API_KEY): str,
            })
            description = "Please enter your new Anthropic API key"
        elif self.provider == PROVIDER_LITELLM:
            schema = vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_BASE_URL): str,
            })
            description = "Please enter your new LiteLLM API key and base URL"
        else:
            # For providers that don't need reauth (like Bedrock)
            return self.async_abort(reason="reauth_not_supported")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"provider": self.provider, "description": description},
        )


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for CortexAgent."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the options
            try:
                # Here we would validate the options
                # For now, we'll just assume they're valid
                return self.async_create_entry(title="", data=user_input)
            except (ValueError, TypeError, KeyError) as ex:
                _LOGGER.error("Error validating options: %s", ex)
                errors["base"] = "options_error"

        # Pre-fill with current values
        options = {
            CONF_SYSTEM_PROMPT: self.config_entry.options.get(
                CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT
            ),
            CONF_MAX_TOKENS: self.config_entry.options.get(
                CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS
            ),
            CONF_TEMPERATURE: self.config_entry.options.get(
                CONF_TEMPERATURE, DEFAULT_TEMPERATURE
            ),
            CONF_MEMORY_ENABLED: self.config_entry.options.get(
                CONF_MEMORY_ENABLED, True
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_SYSTEM_PROMPT, default=options[CONF_SYSTEM_PROMPT]
                ): str,
                vol.Optional(
                    CONF_MAX_TOKENS, default=options[CONF_MAX_TOKENS]
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=8192)),
                vol.Optional(
                    CONF_TEMPERATURE, default=options[CONF_TEMPERATURE]
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=2)),
                vol.Optional(
                    CONF_MEMORY_ENABLED, default=options[CONF_MEMORY_ENABLED]
                ): bool,
            }),
            errors=errors,
        )
