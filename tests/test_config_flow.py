"""Test the CortexAgent config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.cortex_agent.config_flow import CortexAgentConfigFlow
from custom_components.cortex_agent.const import DOMAIN, CONF_PROVIDER, PROVIDERS

@pytest.fixture
def config_flow(hass: HomeAssistant) -> CortexAgentConfigFlow:
    """Create a config flow."""
    flow = CortexAgentConfigFlow()
    flow.hass = hass
    return flow

async def test_user_step(hass: HomeAssistant, config_flow: CortexAgentConfigFlow):
    """Test the user step."""
    result = await config_flow.async_step_user()
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    
    # Test with user input
    result = await config_flow.async_step_user({
        CONF_PROVIDER: PROVIDERS[0]
    })
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Cortex Agent"
    assert result["data"][CONF_PROVIDER] == PROVIDERS[0]

async def test_options_flow(hass: HomeAssistant):
    """Test options flow initialization."""
    # Create a mock config entry
    entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Cortex Agent",
        data={CONF_PROVIDER: PROVIDERS[0]},
        source="user",
        options={},
        unique_id="test123"
    )
    
    flow = CortexAgentConfigFlow.async_get_options_flow(entry)
    result = await flow.async_step_init()
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"