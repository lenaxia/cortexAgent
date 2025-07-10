"""Tests for the CortexAgent diagnostics module."""
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry

from custom_components.cortex_agent.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.cortex_agent.coordinator import (
    CortexAgentCoordinator,
    CortexAgentData,
)
from custom_components.cortex_agent.const import DOMAIN


@pytest.fixture
def mock_hass():
    """Fixture to provide a mock hass instance."""
    hass = MagicMock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Fixture to provide a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.domain = DOMAIN
    entry.data = {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "model_provider": "openai",
        "api_key": "sk-test_api_key",
        "model": "gpt-4",
    }
    return entry


@pytest.fixture
def mock_coordinator():
    """Fixture to provide a mock coordinator."""
    coordinator = MagicMock(spec=CortexAgentCoordinator)
    coordinator.agent_id = "test_agent"
    coordinator.name = "Test Agent"
    
    # Set up the coordinator data
    coordinator.data = CortexAgentData(
        model_provider_connected=True,
        model_provider_name="OpenAI",
        model_provider_model="gpt-4",
        mcp_servers=[
            {
                "server_id": "server_123",
                "name": "Test Server",
                "server_type": "remote",
                "connected": True,
            },
        ],
        memory_count=10,
        conversation_history_length=5,
        available_tools=["tool1", "tool2"],
    )
    
    return coordinator


async def test_async_get_config_entry_diagnostics(mock_hass, mock_config_entry, mock_coordinator):
    """Test the async_get_config_entry_diagnostics function."""
    # Set up the mock hass.data
    mock_hass.data = {
        DOMAIN: {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator,
            }
        }
    }
    
    # Call async_get_config_entry_diagnostics
    diagnostics = await async_get_config_entry_diagnostics(mock_hass, mock_config_entry)
    
    # Check the diagnostics
    assert diagnostics["config"] == {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "model_provider": "openai",
        "model": "gpt-4",
    }
    
    assert diagnostics["data"] == {
        "model_provider_connected": True,
        "model_provider_name": "OpenAI",
        "model_provider_model": "gpt-4",
        "mcp_servers": [
            {
                "server_id": "server_123",
                "name": "Test Server",
                "server_type": "remote",
                "connected": True,
            },
        ],
        "memory_count": 10,
        "conversation_history_length": 5,
        "available_tools": ["tool1", "tool2"],
    }


async def test_async_get_config_entry_diagnostics_no_coordinator(mock_hass, mock_config_entry):
    """Test the async_get_config_entry_diagnostics function with no coordinator."""
    # Set up the mock hass.data without a coordinator
    mock_hass.data = {
        DOMAIN: {
            mock_config_entry.entry_id: {}
        }
    }
    
    # Call async_get_config_entry_diagnostics
    diagnostics = await async_get_config_entry_diagnostics(mock_hass, mock_config_entry)
    
    # Check the diagnostics
    assert diagnostics["config"] == {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "model_provider": "openai",
        "model": "gpt-4",
    }
    
    assert diagnostics["data"] is None


async def test_async_get_config_entry_diagnostics_no_data(mock_hass, mock_config_entry, mock_coordinator):
    """Test the async_get_config_entry_diagnostics function with no coordinator data."""
    # Set up the mock coordinator with no data
    mock_coordinator.data = None
    
    # Set up the mock hass.data
    mock_hass.data = {
        DOMAIN: {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator,
            }
        }
    }
    
    # Call async_get_config_entry_diagnostics
    diagnostics = await async_get_config_entry_diagnostics(mock_hass, mock_config_entry)
    
    # Check the diagnostics
    assert diagnostics["config"] == {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "model_provider": "openai",
        "model": "gpt-4",
    }
    
    assert diagnostics["data"] is None


async def test_async_get_config_entry_diagnostics_redacts_api_key(mock_hass, mock_config_entry, mock_coordinator):
    """Test that the async_get_config_entry_diagnostics function redacts the API key."""
    # Set up the mock hass.data
    mock_hass.data = {
        DOMAIN: {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator,
            }
        }
    }
    
    # Call async_get_config_entry_diagnostics
    diagnostics = await async_get_config_entry_diagnostics(mock_hass, mock_config_entry)
    
    # Check that the API key is not in the diagnostics
    assert "api_key" not in diagnostics["config"]