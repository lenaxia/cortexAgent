"""Tests for the CortexAgent system health module."""
from unittest.mock import MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.components import system_health

from custom_components.cortex_agent.system_health import (
    async_register,
    system_health_info,
)
from custom_components.cortex_agent.const import DATA_AGENT, DOMAIN


@pytest.fixture
def mock_hass():
    """Fixture to provide a mock hass instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.fixture
def mock_agent():
    """Fixture to provide a mock agent."""
    agent = MagicMock()
    agent._setup_done = True
    
    # Mock conversation manager
    agent.conversation_manager = MagicMock()
    agent.conversation_manager.conversations = {
        "conv1": {},
        "conv2": {},
    }
    
    # Mock tool registry
    agent.tool_registry = MagicMock()
    agent.tool_registry._tools = {
        "tool1": {},
        "tool2": {},
        "tool3": {},
    }
    
    return agent


async def test_async_register(mock_hass):
    """Test the async_register function."""
    with patch("homeassistant.components.system_health.async_register_info") as mock_register:
        await async_register(mock_hass)
        
        mock_register.assert_called_once_with(mock_hass, DOMAIN, system_health_info)


async def test_system_health_info_no_agents(mock_hass):
    """Test the system_health_info function with no agents."""
    # Setup empty domain data
    mock_hass.data[DOMAIN] = {}
    
    # Get system health info
    info = await system_health_info(mock_hass)
    
    # Verify info
    assert "version" in info
    assert info["active_agents"] == 0
    assert info["total_conversations"] == 0
    assert info["total_tools"] == 0


async def test_system_health_info_with_agents(mock_hass, mock_agent):
    """Test the system_health_info function with agents."""
    # Setup domain data with one agent
    mock_hass.data[DOMAIN] = {
        "entry1": {
            DATA_AGENT: mock_agent,
        }
    }
    
    # Get system health info
    info = await system_health_info(mock_hass)
    
    # Verify info
    assert "version" in info
    assert info["active_agents"] == 1
    assert info["total_conversations"] == 2  # From the mock agent
    assert info["total_tools"] == 3  # From the mock agent


async def test_system_health_info_with_multiple_agents(mock_hass, mock_agent):
    """Test the system_health_info function with multiple agents."""
    # Create a second agent
    agent2 = MagicMock()
    agent2._setup_done = True
    agent2.conversation_manager = MagicMock()
    agent2.conversation_manager.conversations = {
        "conv3": {},
        "conv4": {},
        "conv5": {},
    }
    agent2.tool_registry = MagicMock()
    agent2.tool_registry._tools = {
        "tool4": {},
        "tool5": {},
    }
    
    # Setup domain data with two agents
    mock_hass.data[DOMAIN] = {
        "entry1": {
            DATA_AGENT: mock_agent,
        },
        "entry2": {
            DATA_AGENT: agent2,
        }
    }
    
    # Get system health info
    info = await system_health_info(mock_hass)
    
    # Verify info
    assert "version" in info
    assert info["active_agents"] == 2
    assert info["total_conversations"] == 5  # 2 from mock_agent + 3 from agent2
    assert info["total_tools"] == 5  # 3 from mock_agent + 2 from agent2


async def test_system_health_info_with_inactive_agent(mock_hass, mock_agent):
    """Test the system_health_info function with an inactive agent."""
    # Create an inactive agent
    inactive_agent = MagicMock()
    inactive_agent._setup_done = False
    
    # Setup domain data with one active and one inactive agent
    mock_hass.data[DOMAIN] = {
        "entry1": {
            DATA_AGENT: mock_agent,
        },
        "entry2": {
            DATA_AGENT: inactive_agent,
        }
    }
    
    # Get system health info
    info = await system_health_info(mock_hass)
    
    # Verify info
    assert "version" in info
    assert info["active_agents"] == 1  # Only the active agent is counted
    assert info["total_conversations"] == 2  # Only from the active agent
    assert info["total_tools"] == 3  # Only from the active agent


async def test_system_health_info_with_incomplete_agent(mock_hass):
    """Test the system_health_info function with an agent missing conversation manager and tool registry."""
    # Create an agent without conversation manager and tool registry
    incomplete_agent = MagicMock()
    incomplete_agent._setup_done = True
    # No conversation_manager attribute
    # No tool_registry attribute
    
    # Setup domain data with the incomplete agent
    mock_hass.data[DOMAIN] = {
        "entry1": {
            DATA_AGENT: incomplete_agent,
        }
    }
    
    # Get system health info
    info = await system_health_info(mock_hass)
    
    # Verify info
    assert "version" in info
    assert info["active_agents"] == 1
    assert info["total_conversations"] == 0  # No conversations
    assert info["total_tools"] == 0  # No tools


async def test_system_health_info_with_no_domain_data(mock_hass):
    """Test the system_health_info function with no domain data."""
    # No domain data in hass.data
    
    # Get system health info
    info = await system_health_info(mock_hass)
    
    # Verify info
    assert "version" in info
    assert info["active_agents"] == 0
    assert info["total_conversations"] == 0
    assert info["total_tools"] == 0


async def test_system_health_info_with_no_agent_data(mock_hass):
    """Test the system_health_info function with entries that don't have agent data."""
    # Setup domain data with entries that don't have agent data
    mock_hass.data[DOMAIN] = {
        "entry1": {
            "some_other_data": "value",
        },
        "entry2": {
            "more_data": "value",
        }
    }
    
    # Get system health info
    info = await system_health_info(mock_hass)
    
    # Verify info
    assert "version" in info
    assert info["active_agents"] == 0
    assert info["total_conversations"] == 0
    assert info["total_tools"] == 0