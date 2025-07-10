"""Test the Cortex Agent services."""
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import ConfigEntry

from custom_components.cortex_agent import services
from custom_components.cortex_agent.const import (
    DOMAIN,
    CONF_MCP_SERVERS,
    CONF_CUSTOM_TOOLS
)

@pytest.fixture
def mock_hass():
    """Fixture for mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    return hass

@pytest.fixture
def mock_entry():
    """Fixture for mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.options = {}
    return entry

async def test_reload_service(mock_hass, mock_entry):
    """Test reload service."""
    mock_entry.entry_id = "test_entry"
    mock_hass.config_entries.async_get_entry = AsyncMock(return_value=mock_entry)
    mock_hass.config_entries.async_reload = AsyncMock()
    mock_hass.data[DOMAIN] = {mock_entry.entry_id: {"agent": MagicMock()}}
    
    service = MagicMock()
    service.hass = mock_hass
    service.data = {"entity_id": f"{DOMAIN}.{mock_entry.entry_id}"}

    await services.async_reload_service(service)
    mock_hass.config_entries.async_get_entry.assert_awaited_once_with(mock_entry.entry_id)
    mock_hass.config_entries.async_reload.assert_awaited_once_with(mock_entry.entry_id)

async def test_connect_mcp_server_service_new(mock_hass, mock_entry):
    """Test connect_mcp_server service with new server."""
    mock_entry.options = {}  # Initialize options dict
    mock_hass.config_entries.async_get_entry.return_value = mock_entry
    mock_update = AsyncMock()
    mock_hass.config_entries.async_update_entry = mock_update
    
    service = MagicMock()
    service.hass = mock_hass
    service.data = {
        "entity_id": f"{DOMAIN}.test_entity",
        "name": "test_server",
        "url": "http://test",
        "server_type": "local"
    }
    
    await services.async_connect_mcp_server_service(service)
    
    # Verify the update was called with expected options
    args, kwargs = mock_update.call_args
    assert kwargs["options"][CONF_MCP_SERVERS] == [{
        "name": "test_server",
        "url": "http://test",
        "server_type": "local",
        "auth_token": None
    }]

async def test_connect_mcp_server_service_update(mock_hass, mock_entry):
    """Test connect_mcp_server service updating existing server."""
    mock_entry.options = {
        CONF_MCP_SERVERS: [{
            "name": "test_server",
            "url": "http://old",
            "server_type": "remote"
        }]
    }
    mock_hass.config_entries.async_get_entry.return_value = mock_entry
    service = MagicMock()
    service.hass = mock_hass
    service.data = {
        "entity_id": f"{DOMAIN}.test_entity",
        "name": "test_server",
        "url": "http://new",
        "server_type": "local",
        "auth_token": "test_token"
    }
    
    await services.async_connect_mcp_server_service(service)
    assert mock_entry.options[CONF_MCP_SERVERS] == [{
        "name": "test_server",
        "url": "http://new",
        "server_type": "local",
        "auth_token": "test_token"
    }]

async def test_disconnect_mcp_server_service(mock_hass, mock_entry):
    """Test disconnect_mcp_server service."""
    mock_entry.options = {
        CONF_MCP_SERVERS: [{
            "name": "test_server",
            "url": "http://test",
            "server_type": "local"
        }]
    }
    mock_hass.config_entries.async_get_entry.return_value = mock_entry
    mock_update = AsyncMock()
    mock_hass.config_entries.async_update_entry = mock_update
    
    service = MagicMock()
    service.hass = mock_hass
    service.data = {
        "entity_id": f"{DOMAIN}.test_entity",
        "name": "test_server"
    }
    
    await services.async_disconnect_mcp_server_service(service)
    
    # Verify the update was called with empty servers list
    args, kwargs = mock_update.call_args
    assert kwargs["options"][CONF_MCP_SERVERS] == []

async def test_add_tool_service_new(mock_hass, mock_entry):
    """Test add_tool service with new tool."""
    mock_hass.config_entries.async_get_entry.return_value = mock_entry
    mock_entry.options = {CONF_CUSTOM_TOOLS: []}
    service = MagicMock()
    service.hass = mock_hass
    service.data = {
        "entity_id": f"{DOMAIN}.test_entity",
        "name": "test_tool",
        "description": "Test tool",
        "type": "function",
        "code": "def test(): pass"
    }

    await services.async_add_tool_service(service)
    assert mock_entry.options[CONF_CUSTOM_TOOLS] == [{
        "name": "test_tool",
        "description": "Test tool",
        "type": "function",
        "code": "def test(): pass",
        "path": None
    }]

async def test_remove_tool_service(mock_hass, mock_entry):
    """Test remove_tool service."""
    mock_entry.options = {
        CONF_CUSTOM_TOOLS: [{
            "name": "test_tool",
            "description": "Test tool",
            "type": "function"
        }]
    }
    mock_hass.config_entries.async_get_entry.return_value = mock_entry
    mock_hass.config_entries.async_update_entry = AsyncMock()
    service = MagicMock()
    service.hass = mock_hass
    service.data = {
        "entity_id": f"{DOMAIN}.test_entity",
        "name": "test_tool"
    }

    await services.async_remove_tool_service(service)
    mock_hass.config_entries.async_update_entry.assert_called_once_with(
        mock_entry,
        options={CONF_CUSTOM_TOOLS: []}
    )

async def test_clear_conversation_service_specific(mock_hass, mock_entry):
    """Test clear_conversation service for specific conversation."""
    mock_agent = MagicMock()
    mock_conversation_manager = MagicMock()
    mock_conversation_manager.clear_conversation = AsyncMock()
    mock_conversation_manager.async_save = AsyncMock()
    mock_agent.conversation_manager = mock_conversation_manager
    
    entry_id = "test_entry"
    mock_hass.data[DOMAIN] = {entry_id: {"agent": mock_agent}}
    mock_hass.config_entries.async_get_entry = AsyncMock(return_value=mock_entry)
    service = MagicMock()
    service.hass = mock_hass
    service.data = {
        "entity_id": f"{DOMAIN}.{entry_id}",
        "conversation_id": "test_conv"
    }

    await services.async_clear_conversation_service(service)
    mock_hass.config_entries.async_get_entry.assert_awaited_once_with(entry_id)
    mock_conversation_manager.clear_conversation.assert_awaited_once_with("test_conv")
    mock_conversation_manager.async_save.assert_awaited_once()
    mock_hass.config_entries.async_get_entry.assert_awaited_once_with(entry_id)
    mock_agent.conversation_manager.clear_conversation.assert_awaited_once_with("test_conv")
    mock_agent.conversation_manager.async_save.assert_called_once()

async def test_clear_conversation_service_all(mock_hass, mock_entry):
    """Test clear_conversation service for all conversations."""
    mock_agent = MagicMock()
    mock_conversation_manager = MagicMock()
    mock_conversation_manager.clear_all_conversations = AsyncMock()
    mock_conversation_manager.async_save = AsyncMock()
    mock_agent.conversation_manager = mock_conversation_manager
    
    entry_id = "test_entry"
    mock_hass.data[DOMAIN] = {entry_id: {"agent": mock_agent}}
    mock_hass.config_entries.async_get_entry = AsyncMock(return_value=mock_entry)
    service = MagicMock()
    service.hass = mock_hass
    service.data = {
        "entity_id": f"{DOMAIN}.{entry_id}"
    }

    await services.async_clear_conversation_service(service)
    mock_hass.config_entries.async_get_entry.assert_awaited_once_with(entry_id)
    mock_conversation_manager.clear_all_conversations.assert_awaited_once()
    mock_conversation_manager.async_save.assert_awaited_once()
    mock_agent.conversation_manager.clear_all_conversations.assert_called_once()
    mock_agent.conversation_manager.async_save.assert_called_once()

async def test_services_not_found_handling(mock_hass, mock_entry):
    """Test service error handling when config entry or agent not found."""
    # Test config entry not found
    mock_hass.config_entries.async_get_entry = AsyncMock(return_value=None)
    service = MagicMock()
    service.hass = mock_hass
    service.data = {"entity_id": f"{DOMAIN}.test_entity"}

    with patch.object(services._LOGGER, "error") as mock_logger:
        await services.async_reload_service(service)
        mock_logger.assert_called_once_with("Config entry not found")
    
    # Test agent not found
    mock_entry.entry_id = "test_entry"
    mock_hass.config_entries.async_get_entry = AsyncMock(return_value=mock_entry)
    mock_hass.config_entries.async_reload = AsyncMock()
    mock_hass.data[DOMAIN] = {}
    
    with patch.object(services._LOGGER, "error") as mock_logger:
        await services.async_reload_service(service)
        mock_logger.assert_called_once_with("Agent not found")
    
    # Test agent not found
    mock_hass.data[DOMAIN] = {"test_entry": {}}
    service = MagicMock()
    service.hass = mock_hass
    service.data = {"entity_id": f"{DOMAIN}.test_entity"}
    
    with patch.object(services._LOGGER, "error") as mock_logger:
        await services.async_clear_conversation_service(service)
        mock_logger.assert_called_once_with("Agent not found")