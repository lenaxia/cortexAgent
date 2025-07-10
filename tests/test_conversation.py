"""Test the CortexAgent conversation support."""
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components import conversation

from custom_components.cortex_agent.conversation import CortexAgent
from custom_components.cortex_agent.const import DOMAIN

@pytest.fixture
def agent(hass: HomeAssistant, config_entry: ConfigEntry) -> CortexAgent:
    """Create a CortexAgent instance."""
    return CortexAgent(hass, config_entry)

async def test_async_process(agent: CortexAgent):
    """Test async_process method."""
    input_text = "Hello, how are you?"
    conversation_input = conversation.ConversationInput(
        text=input_text,
        context=None,
        conversation_id="test123",
        language="en"
    )
    
    result = await agent.async_process(conversation_input)
    
    assert result.response.startswith("I received:")
    assert result.conversation_id == "test123"

async def test_generate_response(agent: CortexAgent):
    """Test _generate_response method."""
    input_text = "Test input"
    response = await agent._generate_response(input_text)
    
    assert response == f"I received: {input_text}"