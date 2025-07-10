"""Tests for the CortexAgent integration initialization."""
from unittest.mock import patch, MagicMock, AsyncMock, call

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import Platform
from homeassistant.components import conversation

from custom_components.cortex_agent import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
    async_reload_entry,
    async_setup_services,
)
from custom_components.cortex_agent.const import (
    ATTR_AUTH_TOKEN,
    ATTR_CODE,
    ATTR_CONVERSATION_ID,
    ATTR_DESCRIPTION,
    ATTR_NAME,
    ATTR_PARAMETERS,
    ATTR_PATH,
    ATTR_SERVER_TYPE,
    ATTR_TOOL_NAME,
    ATTR_TYPE,
    ATTR_URL,
    DATA_AGENT,
    DATA_COORDINATOR,
    DOMAIN,
)


@pytest.fixture
def mock_hass():
    """Fixture to provide a mock hass instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.fixture
def mock_config_entry():
    """Fixture to provide a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.options = {}
    return entry


@pytest.fixture
def mock_coordinator():
    """Fixture to provide a mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_agent():
    """Fixture to provide a mock agent."""
    agent = MagicMock()
    agent.entry = MagicMock()
    agent.async_setup = AsyncMock()
    agent.mcp_connector = MagicMock()
    agent.mcp_connector.async_connect = AsyncMock()
    agent.mcp_connector.async_disconnect = AsyncMock()
    agent.conversation_manager = MagicMock()
    agent.conversation_manager.clear_conversation = MagicMock()
    agent.conversation_manager.clear_all_conversations = MagicMock()
    agent.conversation_manager.async_save = AsyncMock()
    agent.event_listener = MagicMock()
    agent.event_listener.async_unload = MagicMock()
    return agent


async def test_async_setup(mock_hass):
    """Test the async_setup function."""
    with patch(
        "custom_components.cortex_agent.async_register_websocket_commands", AsyncMock()
    ) as mock_register_ws, patch(
        "custom_components.cortex_agent.async_setup_services", AsyncMock()
    ) as mock_setup_services:
        result = await async_setup(mock_hass, {})
        
        assert result is True
        assert DOMAIN in mock_hass.data
        mock_register_ws.assert_called_once_with(mock_hass)
        mock_setup_services.assert_called_once_with(mock_hass)


async def test_async_setup_entry(mock_hass, mock_config_entry):
    """Test the async_setup_entry function."""
    with patch(
        "custom_components.cortex_agent.CortexAgentCoordinator", return_value=MagicMock()
    ) as mock_coordinator_class, patch(
        "custom_components.cortex_agent.CortexAgent", return_value=MagicMock()
    ) as mock_agent_class, patch(
        "custom_components.cortex_agent.conversation.async_set_agent"
    ) as mock_set_agent, patch(
        "custom_components.cortex_agent.async_setup_services", AsyncMock()
    ) as mock_setup_services, patch(
        "custom_components.cortex_agent.system_health.async_register", AsyncMock()
    ) as mock_register_health:
        
        # Setup mocks
        coordinator = mock_coordinator_class.return_value
        coordinator.async_config_entry_first_refresh = AsyncMock()
        agent = mock_agent_class.return_value
        
        # Call function
        result = await async_setup_entry(mock_hass, mock_config_entry)
        
        # Verify results
        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
        assert mock_hass.data[DOMAIN][mock_config_entry.entry_id][DATA_AGENT] == agent
        assert mock_hass.data[DOMAIN][mock_config_entry.entry_id][DATA_COORDINATOR] == coordinator
        
        # Verify method calls
        mock_coordinator_class.assert_called_once_with(mock_hass, mock_config_entry)
        coordinator.async_config_entry_first_refresh.assert_called_once()
        mock_agent_class.assert_called_once_with(mock_hass, mock_config_entry)
        assert coordinator.agent == agent
        mock_set_agent.assert_called_once_with(mock_hass, mock_config_entry, agent)
        mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
            mock_config_entry, [Platform.SENSOR]
        )
        mock_setup_services.assert_called_once_with(mock_hass)
        mock_register_health.assert_called_once_with(mock_hass)


async def test_async_setup_entry_system_health_already_registered(mock_hass, mock_config_entry):
    """Test the async_setup_entry function when system health is already registered."""
    with patch(
        "custom_components.cortex_agent.CortexAgentCoordinator", return_value=MagicMock()
    ) as mock_coordinator_class, patch(
        "custom_components.cortex_agent.CortexAgent", return_value=MagicMock()
    ) as mock_agent_class, patch(
        "custom_components.cortex_agent.conversation.async_set_agent"
    ) as mock_set_agent, patch(
        "custom_components.cortex_agent.async_setup_services", AsyncMock()
    ) as mock_setup_services, patch(
        "custom_components.cortex_agent.system_health.async_register", AsyncMock()
    ) as mock_register_health:
        
        # Setup mocks
        coordinator = mock_coordinator_class.return_value
        coordinator.async_config_entry_first_refresh = AsyncMock()
        agent = mock_agent_class.return_value
        
        # Set system health as already registered
        mock_hass.data[f"{DOMAIN}_system_health_registered"] = True
        
        # Call function
        result = await async_setup_entry(mock_hass, mock_config_entry)
        
        # Verify results
        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
        
        # Verify system health not registered again
        mock_register_health.assert_not_called()


async def test_async_unload_entry(mock_hass, mock_config_entry, mock_agent):
    """Test the async_unload_entry function."""
    # Setup test data
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_AGENT: mock_agent,
            DATA_COORDINATOR: MagicMock(),
        }
    }
    
    with patch(
        "custom_components.cortex_agent.conversation.async_unset_agent"
    ) as mock_unset_agent:
        # Mock successful platform unload
        mock_hass.config_entries.async_unload_platforms.return_value = True
        
        # Call function
        result = await async_unload_entry(mock_hass, mock_config_entry)
        
        # Verify results
        assert result is True
        assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]
        
        # Verify method calls
        mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_config_entry, [Platform.SENSOR]
        )
        mock_unset_agent.assert_called_once_with(mock_hass, mock_config_entry)
        mock_agent.event_listener.async_unload.assert_called_once()


async def test_async_unload_entry_failed_platform_unload(mock_hass, mock_config_entry, mock_agent):
    """Test the async_unload_entry function when platform unload fails."""
    # Setup test data
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_AGENT: mock_agent,
            DATA_COORDINATOR: MagicMock(),
        }
    }
    
    with patch(
        "custom_components.cortex_agent.conversation.async_unset_agent"
    ) as mock_unset_agent:
        # Mock failed platform unload
        mock_hass.config_entries.async_unload_platforms.return_value = False
        
        # Call function
        result = await async_unload_entry(mock_hass, mock_config_entry)
        
        # Verify results
        assert result is False
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
        
        # Verify method calls
        mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_config_entry, [Platform.SENSOR]
        )
        mock_unset_agent.assert_called_once_with(mock_hass, mock_config_entry)
        mock_agent.event_listener.async_unload.assert_called_once()


async def test_async_reload_entry(mock_hass, mock_config_entry):
    """Test the async_reload_entry function."""
    with patch(
        "custom_components.cortex_agent.async_unload_entry", AsyncMock(return_value=True)
    ) as mock_unload, patch(
        "custom_components.cortex_agent.async_setup_entry", AsyncMock(return_value=True)
    ) as mock_setup:
        # Call function
        await async_reload_entry(mock_hass, mock_config_entry)
        
        # Verify method calls
        mock_unload.assert_called_once_with(mock_hass, mock_config_entry)
        mock_setup.assert_called_once_with(mock_hass, mock_config_entry)


async def test_async_setup_services(mock_hass):
    """Test the async_setup_services function."""
    # Call function
    await async_setup_services(mock_hass)
    
    # Verify service registration
    assert mock_hass.services.async_register.call_count == 6
    
    # Check each service registration
    service_calls = mock_hass.services.async_register.call_args_list
    
    # Check reload service
    assert service_calls[0][0][0] == DOMAIN
    assert service_calls[0][0][1] == "reload"
    
    # Check connect_mcp_server service
    assert service_calls[1][0][0] == DOMAIN
    assert service_calls[1][0][1] == "connect_mcp_server"
    
    # Check disconnect_mcp_server service
    assert service_calls[2][0][0] == DOMAIN
    assert service_calls[2][0][1] == "disconnect_mcp_server"
    
    # Check add_tool service
    assert service_calls[3][0][0] == DOMAIN
    assert service_calls[3][0][1] == "add_tool"
    
    # Check remove_tool service
    assert service_calls[4][0][0] == DOMAIN
    assert service_calls[4][0][1] == "remove_tool"
    
    # Check clear_conversation service
    assert service_calls[5][0][0] == DOMAIN
    assert service_calls[5][0][1] == "clear_conversation"


async def test_reload_service(mock_hass, mock_agent):
    """Test the reload service."""
    # Setup test data
    mock_hass.data[DOMAIN] = {
        "test_entity_id": mock_agent,
    }
    
    # Create service call
    service_call = ServiceCall(
        domain=DOMAIN,
        service="reload",
        service_data={},
        context=None,
        target={"entity_id": ["test_entity_id"]},
    )
    
    # Get the reload service handler
    await async_setup_services(mock_hass)
    reload_service = mock_hass.services.async_register.call_args_list[0][0][2]
    
    # Call the service
    await reload_service(service_call)
    
    # Verify agent setup was called
    mock_agent.async_setup.assert_called_once()


async def test_connect_mcp_server_service(mock_hass, mock_agent, mock_config_entry):
    """Test the connect_mcp_server service."""
    # Setup test data
    mock_agent.entry = mock_config_entry
    mock_hass.data[DOMAIN] = {
        "test_entity_id": {
            DATA_AGENT: mock_agent,
            DATA_COORDINATOR: MagicMock(),
        },
    }
    
    # Create service call
    service_call = ServiceCall(
        domain=DOMAIN,
        service="connect_mcp_server",
        service_data={
            ATTR_NAME: "test_server",
            ATTR_URL: "https://example.com/mcp",
            ATTR_SERVER_TYPE: "sse",
            ATTR_AUTH_TOKEN: "test_token",
        },
        context=None,
        target={"entity_id": ["test_entity_id"]},
    )
    
    # Get the connect_mcp_server service handler
    await async_setup_services(mock_hass)
    connect_service = mock_hass.services.async_register.call_args_list[1][0][2]
    
    # Call the service
    await connect_service(service_call)
    
    # Verify config entry was updated
    mock_hass.config_entries.async_update_entry.assert_called_once()
    
    # Verify server was connected
    mock_agent.mcp_connector.async_connect.assert_called_once()
    
    # Verify agent setup was called
    mock_agent.async_setup.assert_called_once()


async def test_disconnect_mcp_server_service(mock_hass, mock_agent, mock_config_entry):
    """Test the disconnect_mcp_server service."""
    # Setup test data
    mock_agent.entry = mock_config_entry
    mock_config_entry.options = {
        "mcp_servers": [
            {
                ATTR_NAME: "test_server",
                ATTR_URL: "https://example.com/mcp",
                ATTR_SERVER_TYPE: "sse",
            }
        ]
    }
    mock_hass.data[DOMAIN] = {
        "test_entity_id": {
            DATA_AGENT: mock_agent,
            DATA_COORDINATOR: MagicMock(),
        },
    }
    
    # Create service call
    service_call = ServiceCall(
        domain=DOMAIN,
        service="disconnect_mcp_server",
        service_data={
            ATTR_NAME: "test_server",
        },
        context=None,
        target={"entity_id": ["test_entity_id"]},
    )
    
    # Get the disconnect_mcp_server service handler
    await async_setup_services(mock_hass)
    disconnect_service = mock_hass.services.async_register.call_args_list[2][0][2]
    
    # Call the service
    await disconnect_service(service_call)
    
    # Verify config entry was updated
    mock_hass.config_entries.async_update_entry.assert_called_once()
    
    # Verify server was disconnected
    mock_agent.mcp_connector.async_disconnect.assert_called_once_with("test_server")
    
    # Verify agent setup was called
    mock_agent.async_setup.assert_called_once()


async def test_add_tool_service_function(mock_hass, mock_agent, mock_config_entry):
    """Test the add_tool service with a function tool."""
    # Setup test data
    mock_agent.entry = mock_config_entry
    mock_hass.data[DOMAIN] = {
        "test_entity_id": {
            DATA_AGENT: mock_agent,
            DATA_COORDINATOR: MagicMock(),
        },
    }
    
    # Create service call
    service_call = ServiceCall(
        domain=DOMAIN,
        service="add_tool",
        service_data={
            ATTR_NAME: "test_tool",
            ATTR_DESCRIPTION: "A test tool",
            ATTR_TYPE: "function",
            ATTR_CODE: "def test_tool(): return 'Hello'",
            ATTR_PARAMETERS: {"param1": "value1"},
        },
        context=None,
        target={"entity_id": ["test_entity_id"]},
    )
    
    # Get the add_tool service handler
    await async_setup_services(mock_hass)
    add_tool_service = mock_hass.services.async_register.call_args_list[3][0][2]
    
    # Call the service
    await add_tool_service(service_call)
    
    # Verify config entry was updated
    mock_hass.config_entries.async_update_entry.assert_called_once()
    
    # Verify agent setup was called
    mock_agent.async_setup.assert_called_once()


async def test_add_tool_service_module(mock_hass, mock_agent, mock_config_entry):
    """Test the add_tool service with a module tool."""
    # Setup test data
    mock_agent.entry = mock_config_entry
    mock_hass.data[DOMAIN] = {
        "test_entity_id": {
            DATA_AGENT: mock_agent,
            DATA_COORDINATOR: MagicMock(),
        },
    }
    
    # Create service call
    service_call = ServiceCall(
        domain=DOMAIN,
        service="add_tool",
        service_data={
            ATTR_NAME: "test_tool",
            ATTR_DESCRIPTION: "A test tool",
            ATTR_TYPE: "module",
            ATTR_PATH: "/path/to/module.py",
            ATTR_PARAMETERS: {"param1": "value1"},
        },
        context=None,
        target={"entity_id": ["test_entity_id"]},
    )
    
    # Get the add_tool service handler
    await async_setup_services(mock_hass)
    add_tool_service = mock_hass.services.async_register.call_args_list[3][0][2]
    
    # Call the service
    await add_tool_service(service_call)
    
    # Verify config entry was updated
    mock_hass.config_entries.async_update_entry.assert_called_once()
    
    # Verify agent setup was called
    mock_agent.async_setup.assert_called_once()


async def test_remove_tool_service(mock_hass, mock_agent, mock_config_entry):
    """Test the remove_tool service."""
    # Setup test data
    mock_agent.entry = mock_config_entry
    mock_config_entry.options = {
        "custom_tools": [
            {
                ATTR_NAME: "test_tool",
                ATTR_DESCRIPTION: "A test tool",
                ATTR_TYPE: "function",
                ATTR_CODE: "def test_tool(): return 'Hello'",
                ATTR_PARAMETERS: {"param1": "value1"},
            }
        ]
    }
    mock_hass.data[DOMAIN] = {
        "test_entity_id": {
            DATA_AGENT: mock_agent,
            DATA_COORDINATOR: MagicMock(),
        },
    }
    
    # Create service call
    service_call = ServiceCall(
        domain=DOMAIN,
        service="remove_tool",
        service_data={
            ATTR_TOOL_NAME: "test_tool",
        },
        context=None,
        target={"entity_id": ["test_entity_id"]},
    )
    
    # Get the remove_tool service handler
    await async_setup_services(mock_hass)
    remove_tool_service = mock_hass.services.async_register.call_args_list[4][0][2]
    
    # Call the service
    await remove_tool_service(service_call)
    
    # Verify config entry was updated
    mock_hass.config_entries.async_update_entry.assert_called_once()
    
    # Verify agent setup was called
    mock_agent.async_setup.assert_called_once()


async def test_clear_conversation_service_specific(mock_hass, mock_agent):
    """Test the clear_conversation service for a specific conversation."""
    # Setup test data
    mock_hass.data[DOMAIN] = {
        "test_entity_id": {
            DATA_AGENT: mock_agent,
            DATA_COORDINATOR: MagicMock(),
        },
    }
    
    # Create service call
    service_call = ServiceCall(
        domain=DOMAIN,
        service="clear_conversation",
        service_data={
            ATTR_CONVERSATION_ID: "test_conversation",
        },
        context=None,
        target={"entity_id": ["test_entity_id"]},
    )
    
    # Get the clear_conversation service handler
    await async_setup_services(mock_hass)
    clear_conversation_service = mock_hass.services.async_register.call_args_list[5][0][2]
    
    # Call the service
    await clear_conversation_service(service_call)
    
    # Verify conversation was cleared
    mock_agent.conversation_manager.clear_conversation.assert_called_once_with("test_conversation")
    mock_agent.conversation_manager.clear_all_conversations.assert_not_called()
    mock_agent.conversation_manager.async_save.assert_called_once()


async def test_clear_conversation_service_all(mock_hass, mock_agent):
    """Test the clear_conversation service for all conversations."""
    # Setup test data
    mock_hass.data[DOMAIN] = {
        "test_entity_id": {
            DATA_AGENT: mock_agent,
            DATA_COORDINATOR: MagicMock(),
        },
    }
    
    # Create service call
    service_call = ServiceCall(
        domain=DOMAIN,
        service="clear_conversation",
        service_data={},
        context=None,
        target={"entity_id": ["test_entity_id"]},
    )
    
    # Get the clear_conversation service handler
    await async_setup_services(mock_hass)
    clear_conversation_service = mock_hass.services.async_register.call_args_list[5][0][2]
    
    # Call the service
    await clear_conversation_service(service_call)
    
    # Verify all conversations were cleared
    mock_agent.conversation_manager.clear_conversation.assert_not_called()
    mock_agent.conversation_manager.clear_all_conversations.assert_called_once()
    mock_agent.conversation_manager.async_save.assert_called_once()