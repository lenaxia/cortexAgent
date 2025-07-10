"""Test the CortexAgent initialization."""
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.cortex_agent import async_setup, async_setup_entry, async_unload_entry
from custom_components.cortex_agent.const import DOMAIN
from custom_components.cortex_agent.conversation import CortexAgent

@pytest.fixture
def mock_hass():
    """Fixture for mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.services = MagicMock()
    hass.async_create_task = MagicMock()
    return hass

async def test_async_setup(mock_hass):
    """Test async_setup."""
    # Setup mock service registration
    registered_services = []
    
    def mock_async_register(*args, **kwargs):
        service = args[0] if args else kwargs.get('service')
        registered_services.append(service)
        async def noop(*_args, **_kwargs): pass
        return noop
    
    mock_hass.services.async_register = mock_async_register
    
    with patch(
        "custom_components.cortex_agent.services.async_reload_service"
    ) as mock_reload, patch(
        "custom_components.cortex_agent.services.async_connect_mcp_server_service"
    ) as mock_connect, patch(
        "custom_components.cortex_agent.services.async_disconnect_mcp_server_service"
    ) as mock_disconnect, patch(
        "custom_components.cortex_agent.services.async_add_tool_service"
    ) as mock_add_tool, patch(
        "custom_components.cortex_agent.services.async_remove_tool_service"
    ) as mock_remove_tool, patch(
        "custom_components.cortex_agent.services.async_clear_conversation_service"
    ) as mock_clear_conv:
    
        result = await async_setup(mock_hass, {})
        await asyncio.sleep(0)  # Allow any pending tasks to complete
    
    assert result is True
    assert DOMAIN in mock_hass.data
    assert len(registered_services) == 6, f"Expected 6 services, got {registered_services}"


async def test_async_setup_entry(mock_hass, mock_config_entry):
    """Test async_setup_entry."""
    result = await async_setup_entry(mock_hass, mock_config_entry)

    assert result is True
    assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
    assert "agent" in mock_hass.data[DOMAIN][mock_config_entry.entry_id]
    assert isinstance(mock_hass.data[DOMAIN][mock_config_entry.entry_id]["agent"], CortexAgent)

async def test_async_unload_entry(mock_hass, mock_config_entry):
    """Test async_unload_entry."""
    mock_agent = AsyncMock()
    mock_hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = {"agent": mock_agent}
    
    # Setup mock components structure
    mock_hass.components = MagicMock()
    mock_hass.components.conversation = MagicMock()
    mock_hass.components.conversation.async_unset_agent = AsyncMock()

    result = await async_unload_entry(mock_hass, mock_config_entry)

    assert result is True
    assert mock_config_entry.entry_id not in mock_hass.data.get(DOMAIN, {})
    mock_hass.components.conversation.async_unset_agent.assert_called_once_with(mock_hass, mock_config_entry)
    mock_agent.async_unload.assert_called_once()