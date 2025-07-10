"""Config flow for CortexAgent integration."""
from __future__ import annotations

import logging
import voluptuous as vol
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_PROVIDER,
    CONF_MODEL_ID,
    CONF_API_KEY,
    CONF_SYSTEM_PROMPT,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    CONF_MEMORY_ENABLED,
    CONF_MCP_SERVERS,
    CONF_BASE_URL,
    CONF_ORG_ID,
    CONF_AWS_PROFILE,
    CONF_AWS_REGION,
    DEFAULT_NAME,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    PROVIDERS,
    PROVIDER_OPENAI,
    PROVIDER_ANTHROPIC,
    PROVIDER_BEDROCK,
    PROVIDER_LITELLM,
    MODEL_VALIDATORS,
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

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.provider: Optional[str] = None
        self.provider_config: Dict[str, Any] = {}
        self.options: Dict[str, Any] = {}

    async def async_step_user(
        self, user_input: Dict[str, Any] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            self.provider = user_input[CONF_PROVIDER]
            return await self.async_step_provider()

        return self.async_show_form(
            step_id="user",
            data_schema=BASE_SCHEMA,
            errors=errors,
        )

    async def async_step_provider(
        self, user_input: Dict[str, Any] = None
    ) -> FlowResult:
        """Handle the provider step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            self.provider_config = {**user_input, CONF_PROVIDER: self.provider}
            
            # Validate the provider configuration
            try:
                # Test connection to the provider
                await self._test_connection(self.provider_config)
                
                # Create a unique ID for this entry
                await self.async_set_unique_id(f"{DOMAIN}_{self.provider}")
                self._abort_if_unique_id_configured()
                
                # Return to the options step
                return await self.async_step_options()
            except Exception as ex:
                _LOGGER.error("Error validating provider configuration: %s", ex)
                errors["base"] = "provider_auth"

        return self.async_show_form(
            step_id="provider",
            data_schema=PROVIDER_SCHEMA[self.provider],
            errors=errors,
        )

    async def async_step_options(
        self, user_input: Dict[str, Any] = None
    ) -> FlowResult:
        """Handle the options step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            self.options = user_input
            
            # Create the config entry
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    CONF_PROVIDER: self.provider,
                    **self.provider_config,
                },
                options=self.options,
            )

        return self.async_show_form(
            step_id="options",
            data_schema=OPTIONS_SCHEMA,
            errors=errors,
        )

    async def _test_connection(self, provider_config: Dict[str, Any]) -> bool:
        """Test connection to the provider.
        
        Args:
            provider_config: Provider configuration
            
        Returns:
            True if connection is successful, False otherwise
            
        Raises:
            Exception: If connection fails
        """
        provider = provider_config.get(CONF_PROVIDER)
        
        if provider == PROVIDER_OPENAI:
            # Test OpenAI connection
            api_key = provider_config.get(CONF_API_KEY)
            if not api_key:
                raise Exception("OpenAI API key is required")
                
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                # Make a simple models.list call to test the connection
                models = client.models.list()
                _LOGGER.info("Successfully connected to OpenAI API")
                return True
            except ImportError:
                _LOGGER.warning("OpenAI package not installed, skipping connection test")
                return True
            except Exception as ex:
                _LOGGER.error("Failed to connect to OpenAI API: %s", str(ex))
                raise Exception(f"Failed to connect to OpenAI API: {str(ex)}")
                
        elif provider == PROVIDER_ANTHROPIC:
            # Test Anthropic connection
            api_key = provider_config.get(CONF_API_KEY)
            if not api_key:
                raise Exception("Anthropic API key is required")
                
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                # Make a simple models.list call to test the connection
                models = client.models.list()
                _LOGGER.info("Successfully connected to Anthropic API")
                return True
            except ImportError:
                _LOGGER.warning("Anthropic package not installed, skipping connection test")
                return True
            except Exception as ex:
                _LOGGER.error("Failed to connect to Anthropic API: %s", str(ex))
                raise Exception(f"Failed to connect to Anthropic API: {str(ex)}")
                
        elif provider == PROVIDER_BEDROCK:
            # Test Bedrock connection
            aws_region = provider_config.get(CONF_AWS_REGION)
            aws_profile = provider_config.get(CONF_AWS_PROFILE)
            
            if not aws_region:
                raise Exception("AWS region is required")
                
            try:
                import boto3
                
                # Create session with profile if specified
                if aws_profile:
                    session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
                else:
                    session = boto3.Session(region_name=aws_region)
                    
                # Create Bedrock client
                client = session.client("bedrock-runtime")
                
                # List models to test connection
                response = client.list_foundation_models()
                _LOGGER.info("Successfully connected to AWS Bedrock")
                return True
            except ImportError:
                _LOGGER.warning("boto3 package not installed, skipping connection test")
                return True
            except Exception as ex:
                _LOGGER.error("Failed to connect to AWS Bedrock: %s", str(ex))
                raise Exception(f"Failed to connect to AWS Bedrock: {str(ex)}")
                
        elif provider == PROVIDER_LITELLM:
            # Test LiteLLM connection
            api_key = provider_config.get(CONF_API_KEY)
            base_url = provider_config.get(CONF_BASE_URL)
            model_id = provider_config.get(CONF_MODEL_ID)
            
            if not api_key:
                raise Exception("API key is required for LiteLLM")
            if not base_url:
                raise Exception("Base URL is required for LiteLLM")
            if not model_id:
                raise Exception("Model ID is required for LiteLLM")
                
            try:
                import litellm
                
                # Configure LiteLLM
                litellm.api_key = api_key
                litellm.api_base = base_url
                
                # Make a simple completion call to test the connection
                response = litellm.completion(
                    model=model_id,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                _LOGGER.info("Successfully connected to LiteLLM endpoint")
                return True
            except ImportError:
                _LOGGER.warning("litellm package not installed, skipping connection test")
                return True
            except Exception as ex:
                _LOGGER.error("Failed to connect to LiteLLM endpoint: %s", str(ex))
                raise Exception(f"Failed to connect to LiteLLM endpoint: {str(ex)}")
        
        return True

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for CortexAgent."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Validate the options
            try:
                # Here we would validate the options
                # For now, we'll just assume they're valid
                return self.async_create_entry(title="", data=user_input)
            except Exception as ex:
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