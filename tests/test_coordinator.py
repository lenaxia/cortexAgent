"""Test the CortexAgent coordinator."""
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util

from custom_components.cortex_agent.coordinator import CortexAgentCoordinator
from custom_components.cortex_agent.const import DOMAIN

@pytest.fixture
def mock_hass():
    """Fixture for mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    return hass

@pytest.fixture
def mock_entry():
    """Fixture for mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.options = {}
    return entry

@pytest.fixture
def mock_server():
    """Fixture for mock MCP server."""
    server = MagicMock()
    server.tools = ["tool1", "tool2"]
    return server

async def test_coordinator_update(mock_hass, mock_entry, mock_server):
    """Test coordinator data update."""
    mock_entry.version = 1
    mock_entry.domain = "cortex_agent"
    mock_entry.title = "Test Agent"
    mock_entry.data = {}
    mock_entry.source = "test"
    mock_entry.options = {}
    mock_entry.unique_id = "test123"
    
    # Setup mock server and tool data
    mock_server = AsyncMock()
    mock_server.get_status = AsyncMock(return_value="connected")
    mock_server.get_tools = AsyncMock(return_value=["tool1", "tool2"])
    mock_hass.data[DOMAIN] = {
        "servers": {"test_server": mock_server},
        "tools": {
            "tool1": {"server": "test_server"},
            "tool2": {"server": "test_server"}
        }
    }
    
    coordinator = CortexAgentCoordinator(mock_hass, mock_entry)
    
    with patch("homeassistant.util.dt.utcnow") as mock_utcnow:
        mock_utcnow.return_value.isoformat.return_value = "2025-07-07T07:17:08+00:00"
        data = await coordinator._async_update_data()
        
    assert data["status"] == "active"
    assert data["last_update"] == "2025-07-07T07:17:08+00:00"
    assert "servers" in data
    assert "test_server" in data["servers"]
    assert data["servers"]["test_server"]["status"] == "connected"
    assert isinstance(data["servers"]["test_server"]["tools"], int)
    assert data["servers"]["test_server"]["tools"] == 2
    assert "tools" in data
    assert "tool1" in data["tools"]
    assert "tool2" in data["tools"]

async def test_coordinator_retry(mock_hass, mock_entry, mock_server):
    """Test coordinator retry logic on update failure with fixed delay."""
    mock_entry.version = 1
    mock_entry.domain = "cortex_agent"
    mock_entry.title = "Test Agent"
    mock_entry.data = {}
    mock_entry.source = "test"
    mock_entry.options = {}
    mock_entry.unique_id = "test123"
    
    # Setup mock server that fails first attempt
    mock_server = AsyncMock()
    mock_server.get_status = AsyncMock(side_effect=[Exception("Failed"), "connected"])
    mock_server.get_tools = AsyncMock(side_effect=[Exception("Failed"), ["tool1", "tool2"]])
    
    mock_hass.data[DOMAIN] = {
        "servers": {"test_server": mock_server},
        "tools": {
            "tool1": {"server": "test_server"},
            "tool2": {"server": "test_server"}
        }
    }
    
    coordinator = CortexAgentCoordinator(
        mock_hass,
        mock_entry,
        retry_attempts=3,
        base_delay=0.1,
        max_delay=1.0
    )
    
    with patch("homeassistant.util.dt.utcnow"), patch(
        "custom_components.cortex_agent.coordinator.random.random",
        return_value=1.0  # Remove jitter for test consistency
    ), patch(
        "custom_components.cortex_agent.coordinator.asyncio.sleep",
        new_callable=AsyncMock
    ) as mock_sleep:
        
        data = await coordinator._async_update_data()
        
        # Verify sleep was called with exponential delays
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == pytest.approx(0.3)  # 0.1 * 2^1 * 1.5 (with jitter)
        assert mock_sleep.call_args_list[1][0][0] == pytest.approx(0.3)  # 0.1 * 2^1 * 1.5 (with jitter)
    
    assert data["servers"]["test_server"]["status"] == "connected"

async def test_coordinator_exponential_backoff(mock_hass, mock_entry):
    """Test coordinator exponential backoff with jitter."""
    # Setup mock server that fails first two status attempts
    mock_server = AsyncMock()
    mock_server.get_status = AsyncMock(side_effect=[
        Exception("Failed"),
        Exception("Failed"), 
        "connected"
    ])
    # Setup tools to return successfully
    mock_server.get_tools = AsyncMock(return_value=[])
    
    mock_hass.data[DOMAIN] = {
        "servers": {"test_server": mock_server},
        "tools": {}
    }
    
    with patch("homeassistant.util.dt.utcnow"), patch(
        "custom_components.cortex_agent.coordinator.random.random",
        side_effect=[0.5, 1.5, 0.5, 1.5, 0.5]  # Provide values for all retry attempts
    ), patch(
        "custom_components.cortex_agent.coordinator.asyncio.sleep",
        new_callable=AsyncMock
    ) as mock_sleep:
        
        coordinator = CortexAgentCoordinator(
            mock_hass,
            mock_entry,
            retry_attempts=3,
            base_delay=0.1,
            max_delay=1.0
        )
        
        await coordinator._async_update_data()
        
        # Verify sleep was called with exponential delays and jitter
        assert mock_sleep.call_count == 2
        # First sleep: 0.1 * 2^1 * 0.5 = 0.1
        # Second sleep: 0.1 * 2^2 * 1.5 = 0.6 (capped at max_delay 1.0)
        assert mock_sleep.call_args_list[0][0][0] == pytest.approx(0.1)
        assert mock_sleep.call_args_list[1][0][0] == pytest.approx(0.6)