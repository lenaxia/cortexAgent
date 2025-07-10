"""Test the CortexAgent config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.cortex_agent.const import (
    DOMAIN,
    CONF_PROVIDER,
    CONF_MODEL_ID,
    CONF_API_KEY,
    CONF_SYSTEM_PROMPT,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    CONF_MEMORY_ENABLED,
    CONF_BASE_URL,
    CONF_ORG_ID,
    CONF_AWS_PROFILE,
    CONF_AWS_REGION,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    PROVIDER_OPENAI,
    PROVIDER_ANTHROPIC,
    PROVIDER_BEDROCK,
    PROVIDER_LITELLM,
)
from custom_components.cortex_agent.config_flow import ConfigFlow


@pytest.fixture
def mock_setup_entry():
    """Mock setting up a config entry."""
    with patch(
        "custom_components.cortex_agent.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


async def test_config_flow_openai(hass: HomeAssistant, mock_setup_entry):
    """Test the config flow for OpenAI."""
    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    
    # Test provider selection
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROVIDER: PROVIDER_OPENAI}
    )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "provider"
    
    # Test provider configuration
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "test_api_key",
            CONF_MODEL_ID: "gpt-4o",
            CONF_ORG_ID: "test_org_id",
            CONF_BASE_URL: "https://api.example.com",
        },
    )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "options"
    
    # Test options configuration
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SYSTEM_PROMPT: "Test system prompt",
            CONF_MAX_TOKENS: 2000,
            CONF_TEMPERATURE: 0.8,
            CONF_MEMORY_ENABLED: True,
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Cortex Agent"
    assert result["data"] == {
        CONF_PROVIDER: PROVIDER_OPENAI,
        CONF_API_KEY: "test_api_key",
        CONF_MODEL_ID: "gpt-4o",
        CONF_ORG_ID: "test_org_id",
        CONF_BASE_URL: "https://api.example.com",
    }
    assert result["options"] == {
        CONF_SYSTEM_PROMPT: "Test system prompt",
        CONF_MAX_TOKENS: 2000,
        CONF_TEMPERATURE: 0.8,
        CONF_MEMORY_ENABLED: True,
    }


async def test_config_flow_anthropic(hass: HomeAssistant, mock_setup_entry):
    """Test the config flow for Anthropic."""
    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Test provider selection
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROVIDER: PROVIDER_ANTHROPIC}
    )
    
    # Test provider configuration
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "test_api_key",
            CONF_MODEL_ID: "claude-3-7-sonnet-20250219",
            CONF_BASE_URL: "https://api.example.com",
        },
    )
    
    # Test options configuration
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SYSTEM_PROMPT: "Test system prompt",
            CONF_MAX_TOKENS: 2000,
            CONF_TEMPERATURE: 0.8,
            CONF_MEMORY_ENABLED: True,
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_PROVIDER: PROVIDER_ANTHROPIC,
        CONF_API_KEY: "test_api_key",
        CONF_MODEL_ID: "claude-3-7-sonnet-20250219",
        CONF_BASE_URL: "https://api.example.com",
    }


async def test_config_flow_bedrock(hass: HomeAssistant, mock_setup_entry):
    """Test the config flow for Bedrock."""
    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Test provider selection
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROVIDER: PROVIDER_BEDROCK}
    )
    
    # Test provider configuration
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_AWS_PROFILE: "default",
            CONF_AWS_REGION: "us-west-2",
            CONF_MODEL_ID: "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        },
    )
    
    # Test options configuration
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SYSTEM_PROMPT: "Test system prompt",
            CONF_MAX_TOKENS: 2000,
            CONF_TEMPERATURE: 0.8,
            CONF_MEMORY_ENABLED: True,
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_PROVIDER: PROVIDER_BEDROCK,
        CONF_AWS_PROFILE: "default",
        CONF_AWS_REGION: "us-west-2",
        CONF_MODEL_ID: "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    }


async def test_config_flow_litellm(hass: HomeAssistant, mock_setup_entry):
    """Test the config flow for LiteLLM."""
    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Test provider selection
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROVIDER: PROVIDER_LITELLM}
    )
    
    # Test provider configuration
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "test_api_key",
            CONF_MODEL_ID: "custom-model",
            CONF_BASE_URL: "https://api.example.com",
        },
    )
    
    # Test options configuration
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SYSTEM_PROMPT: "Test system prompt",
            CONF_MAX_TOKENS: 2000,
            CONF_TEMPERATURE: 0.8,
            CONF_MEMORY_ENABLED: True,
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_PROVIDER: PROVIDER_LITELLM,
        CONF_API_KEY: "test_api_key",
        CONF_MODEL_ID: "custom-model",
        CONF_BASE_URL: "https://api.example.com",
    }


async def test_options_flow(hass: HomeAssistant, mock_setup_entry):
    """Test the options flow."""
    # Create a config entry
    config_entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Cortex Agent",
        data={
            CONF_PROVIDER: PROVIDER_OPENAI,
            CONF_API_KEY: "test_api_key",
            CONF_MODEL_ID: "gpt-4o",
        },
        options={
            CONF_SYSTEM_PROMPT: DEFAULT_SYSTEM_PROMPT,
            CONF_MAX_TOKENS: DEFAULT_MAX_TOKENS,
            CONF_TEMPERATURE: DEFAULT_TEMPERATURE,
            CONF_MEMORY_ENABLED: True,
        },
        source=config_entries.SOURCE_USER,
        entry_id="test_entry_id",
        unique_id=f"{DOMAIN}_{PROVIDER_OPENAI}",
    )
    
    # Start the options flow
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    
    # Test options configuration
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SYSTEM_PROMPT: "Updated system prompt",
            CONF_MAX_TOKENS: 3000,
            CONF_TEMPERATURE: 0.5,
            CONF_MEMORY_ENABLED: False,
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_SYSTEM_PROMPT: "Updated system prompt",
        CONF_MAX_TOKENS: 3000,
        CONF_TEMPERATURE: 0.5,
        CONF_MEMORY_ENABLED: False,
    }