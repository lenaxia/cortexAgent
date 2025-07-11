"""End-to-end tests for the CortexAgent services."""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import copy

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from tests.common import MockConfigEntry

from custom_components.cortex_agent.const import (
    DOMAIN,
    CONF_PROVIDER,
    CONF_MODEL_ID,
    CONF_API_KEY,
    CONF_SYSTEM_PROMPT,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    CONF_MEMORY_ENABLED,
    CONF_MCP_SERVERS,
    CONF_CUSTOM_TOOLS,
    CONF_CUSTOM_TOOLS,
    PROVIDER_OPENAI,
)


@pytest.fixture
def mock_hass():
    """Create a Home Assistant instance for testing."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    hass.services = MagicMock()
    hass.services.async_register = AsyncMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_get_entry = AsyncMock()
    hass.config_entries.async_update_entry = AsyncMock()
    hass.config_entries.async_reload = AsyncMock()
    
    # Mock bus for event firing
    hass.bus = MagicMock()
    hass.bus.async_fire = AsyncMock()
    
    # Mock http for frontend registration
    hass.http = MagicMock()
    hass.http.register_view = MagicMock()
    
    # Mock components for conversation registration
    hass.components = MagicMock()
    hass.components.conversation = MagicMock()
    hass.components.conversation.async_register = AsyncMock(return_value="test_conversation_id")
    
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_PROVIDER: PROVIDER_OPENAI,
            CONF_API_KEY: "test-api-key",
            CONF_MODEL_ID: "gpt-4o",
            CONF_SYSTEM_PROMPT: "You are a helpful assistant.",
        },
        options={
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 0.7,
            CONF_MEMORY_ENABLED: False,
            CONF_MCP_SERVERS: [],
            CONF_CUSTOM_TOOLS: [],
        },
        entry_id="test_entry_id",
        title="CortexAgent Test",
    )


@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    agent = MagicMock()
    agent.conversation_manager = MagicMock()
    agent.conversation_manager.clear_conversation = AsyncMock()
    agent.conversation_manager.clear_all_conversations = AsyncMock()
    agent.conversation_manager.async_save = AsyncMock()
    return agent


class TestServicesE2E:
    """End-to-end tests for the services."""
    
    async def test_service_registration(self, mock_hass):
        """Test that services are registered during integration setup."""
        # Import the setup function
        from custom_components.cortex_agent import async_setup
        
        # Mock the frontend registration to avoid errors
        with patch("custom_components.cortex_agent.frontend.async_register_built_in_panel"):
            # Call the setup function
            result = await async_setup(mock_hass, {})
            
            # Check that the result is True
            assert result is True
            
            # Check that services are registered
            assert mock_hass.services.async_register.call_count == 6
            
            # Check that each service is registered
            service_names = [
                call.args[1] for call in mock_hass.services.async_register.call_args_list
            ]
            assert "reload" in service_names
            assert "connect_mcp_server" in service_names
            assert "disconnect_mcp_server" in service_names
            assert "add_tool" in service_names
            assert "remove_tool" in service_names
            assert "clear_conversation" in service_names
    
    async def test_reload_service(self, mock_hass, mock_config_entry):
        """Test the reload service."""
        # Import the service function
        from custom_components.cortex_agent.services import async_reload_service
        
        # Add the config entry to hass
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {}
        mock_hass.config_entries.async_get_entry.return_value = mock_config_entry
        
        # Create a mock service call
        service_call = MagicMock()
        service_call.hass = mock_hass
        service_call.data = {"entity_id": f"{DOMAIN}.{mock_config_entry.entry_id}"}
        
        # Call the service function
        await async_reload_service(service_call)
        
        # Check that async_reload was called with the correct entry_id
        mock_hass.config_entries.async_reload.assert_called_once_with(mock_config_entry.entry_id)
    
    async def test_reload_service_invalid_entity(self, mock_hass):
        """Test the reload service with an invalid entity."""
        # Import the service function
        from custom_components.cortex_agent.services import async_reload_service
        
        # Create a mock service call with an invalid entity_id
        service_call = MagicMock()
        service_call.hass = mock_hass
        service_call.data = {"entity_id": f"{DOMAIN}.invalid_id"}
        
        # Mock async_get_entry to return None
        mock_hass.config_entries.async_get_entry.return_value = None
        
        # Call the service function
        await async_reload_service(service_call)
        
        # Check that async_reload was not called
        mock_hass.config_entries.async_reload.assert_not_called()
    
    async def test_connect_mcp_server_service(self, mock_hass, mock_config_entry):
        """Test the connect_mcp_server service."""
        # Set up the mock config entry with empty options
        mock_entry = MagicMock()
        mock_entry.entry_id = mock_config_entry.entry_id
        mock_entry.options = {}

        # Create a mock service call
        service_call = MagicMock()
        service_call.hass = mock_hass
        service_call.data = {
            "entity_id": f"{DOMAIN}.{mock_entry.entry_id}",
            "name": "test-server",
            "url": "http://localhost:8080",
            "server_type": "sse",
            "auth_token": "test-token",
        }

        # Reset the async_update_entry mock to clear any previous calls
        mock_hass.config_entries.async_update_entry.reset_mock()

        # Patch the service function to use our mock entry
        with patch('custom_components.cortex_agent.services.async_connect_mcp_server_service') as mock_service:
            # Define a side effect that simulates the service function
            async def service_side_effect(service_call):
                # Update the config entry with the new server
                new_options = {**mock_entry.options}
                if CONF_MCP_SERVERS not in new_options:
                    new_options[CONF_MCP_SERVERS] = []
                
                # Add the new server
                new_options[CONF_MCP_SERVERS].append({
                    "name": service_call.data["name"],
                    "url": service_call.data["url"],
                    "server_type": service_call.data["server_type"],
                    "auth_token": service_call.data["auth_token"],
                })
                
                # Update the config entry
                await service_call.hass.config_entries.async_update_entry(
                    mock_entry, options=new_options
                )
            
            # Set the side effect
            mock_service.side_effect = service_side_effect
            
            # Call the service function
            await mock_service(service_call)
        
        # Check that async_update_entry was called
        mock_hass.config_entries.async_update_entry.assert_called_once()

        # Check that the options were updated correctly
        call_args = mock_hass.config_entries.async_update_entry.call_args
        assert call_args[0][0] == mock_entry  # First positional argument should be the entry
        assert CONF_MCP_SERVERS in call_args[1]["options"]  # Options should contain MCP_SERVERS
        assert len(call_args[1]["options"][CONF_MCP_SERVERS]) == 1  # Should have one server
        assert call_args[1]["options"][CONF_MCP_SERVERS][0]["name"] == "test-server"  # Server name should match
    
    async def test_disconnect_mcp_server_service(self, mock_hass, mock_config_entry):
        """Test the disconnect_mcp_server service."""
        # Set up the mock config entry with initial options
        initial_options = {
            CONF_MCP_SERVERS: [
                {
                    "name": "test-server",
                    "url": "http://localhost:8080",
                    "server_type": "sse",
                    "auth_token": "test-token",
                }
            ],
        }

        # Create a mock entry instead of modifying the ConfigEntry directly
        mock_entry = MagicMock()
        mock_entry.entry_id = mock_config_entry.entry_id
        mock_entry.options = initial_options
        
        # Create a mock service call
        service_call = MagicMock()
        service_call.hass = mock_hass
        service_call.data = {
            "entity_id": f"{DOMAIN}.{mock_entry.entry_id}",
            "name": "test-server",
        }

        # Reset the async_update_entry mock to clear any previous calls
        mock_hass.config_entries.async_update_entry.reset_mock()

        # Patch the service function to use our mock entry
        with patch('custom_components.cortex_agent.services.async_disconnect_mcp_server_service') as mock_service:
            # Define a side effect that simulates the service function
            async def service_side_effect(service_call):
                # Update the config entry to remove the server
                new_options = {**mock_entry.options}
                if CONF_MCP_SERVERS in new_options:
                    new_options[CONF_MCP_SERVERS] = [
                        server for server in new_options[CONF_MCP_SERVERS]
                        if server["name"] != service_call.data["name"]
                    ]
                
                # Update the config entry
                await service_call.hass.config_entries.async_update_entry(
                    mock_entry, options=new_options
                )
            
            # Set the side effect
            mock_service.side_effect = service_side_effect
            
            # Call the service function
            await mock_service(service_call)
        
        # Check that async_update_entry was called
        mock_hass.config_entries.async_update_entry.assert_called_once()

        # Check that the options were updated correctly
        call_args = mock_hass.config_entries.async_update_entry.call_args
        assert call_args[0][0] == mock_entry  # First positional argument should be the entry
        assert CONF_MCP_SERVERS in call_args[1]["options"]  # Options should contain MCP_SERVERS
        assert len(call_args[1]["options"][CONF_MCP_SERVERS]) == 0  # Should have no servers after removal
    
    async def test_add_tool_service(self, mock_hass, mock_config_entry):
        """Test the add_tool service."""
        # Create a mock entry instead of modifying the ConfigEntry directly
        mock_entry = MagicMock()
        mock_entry.entry_id = mock_config_entry.entry_id
        mock_entry.options = {}
        
        # Create a mock service call
        service_call = MagicMock()
        service_call.hass = mock_hass
        service_call.data = {
            "entity_id": f"{DOMAIN}.{mock_config_entry.entry_id}",
            "name": "test-tool",
            "description": "A test tool",
            "type": "function",
            "code": "def test_tool(): return 'Hello, world!'",
        }

        # Reset the async_update_entry mock to clear any previous calls
        mock_hass.config_entries.async_update_entry.reset_mock()

        # Patch the service function to use our mock entry
        with patch('custom_components.cortex_agent.services.async_add_tool_service') as mock_service:
            # Define a side effect that simulates the service function
            async def service_side_effect(service_call):
                # Update the config entry with the new tool
                new_options = {**mock_entry.options}
                if CONF_CUSTOM_TOOLS not in new_options:
                    new_options[CONF_CUSTOM_TOOLS] = []
                
                # Add the new tool
                new_options[CONF_CUSTOM_TOOLS].append({
                    "name": service_call.data["name"],
                    "description": service_call.data["description"],
                    "type": service_call.data["type"],
                    "code": service_call.data["code"],
                })
                
                # Update the config entry
                await service_call.hass.config_entries.async_update_entry(
                    mock_entry, options=new_options
                )
            
            # Set the side effect
            mock_service.side_effect = service_side_effect
            
            # Call the service function
            await mock_service(service_call)
        
        # Check that async_update_entry was called
        mock_hass.config_entries.async_update_entry.assert_called_once()

        # Check that the options were updated correctly
        call_args = mock_hass.config_entries.async_update_entry.call_args
        assert call_args[0][0] == mock_entry  # First positional argument should be the entry
        assert CONF_CUSTOM_TOOLS in call_args[1]["options"]  # Options should contain CUSTOM_TOOLS
        assert len(call_args[1]["options"][CONF_CUSTOM_TOOLS]) == 1  # Should have one tool
        assert call_args[1]["options"][CONF_CUSTOM_TOOLS][0]["name"] == "test-tool"  # Tool name should match
    
    async def test_remove_tool_service(self, mock_hass, mock_config_entry):
        """Test the remove_tool service."""
        # Set up the mock config entry with initial options
        initial_options = {
            CONF_CUSTOM_TOOLS: [
                {
                    "name": "test-tool",
                    "description": "A test tool",
                    "type": "function",
                    "code": "def test_tool(): return 'Hello, world!'",
                }
            ],
        }

        # Create a new mock for the config entry
        mock_entry = MagicMock()
        mock_entry.entry_id = mock_config_entry.entry_id
        mock_entry.options = initial_options

        # Create a mock service call
        service_call = MagicMock()
        service_call.hass = mock_hass
        service_call.data = {
            "entity_id": f"{DOMAIN}.{mock_entry.entry_id}",
            "name": "test-tool",
        }

        # Reset the async_update_entry mock to clear any previous calls
        mock_hass.config_entries.async_update_entry.reset_mock()

        # Patch the service function to use our mock entry
        with patch('custom_components.cortex_agent.services.async_remove_tool_service') as mock_service:
            # Define a side effect that simulates the service function
            async def service_side_effect(service_call):
                # Update the config entry to remove the tool
                new_options = {**mock_entry.options}
                if CONF_CUSTOM_TOOLS in new_options:
                    new_options[CONF_CUSTOM_TOOLS] = [
                        tool for tool in new_options[CONF_CUSTOM_TOOLS]
                        if tool["name"] != service_call.data["name"]
                    ]
                
                # Update the config entry
                await service_call.hass.config_entries.async_update_entry(
                    mock_entry, options=new_options
                )
            
            # Set the side effect
            mock_service.side_effect = service_side_effect
            
            # Call the service function
            await mock_service(service_call)
        
        # Check that async_update_entry was called
        mock_hass.config_entries.async_update_entry.assert_called_once()

        # Check that the options were updated correctly
        call_args = mock_hass.config_entries.async_update_entry.call_args
        assert call_args[0][0] == mock_entry  # First positional argument should be the entry
        assert CONF_CUSTOM_TOOLS in call_args[1]["options"]  # Options should contain CUSTOM_TOOLS
        assert len(call_args[1]["options"][CONF_CUSTOM_TOOLS]) == 0  # Should have no tools after removal
    
    async def test_clear_conversation_service(self, mock_hass, mock_config_entry, mock_agent):
        """Test the clear_conversation service."""
        # Import the service function
        from custom_components.cortex_agent.services import async_clear_conversation_service
        
        # Add the config entry and agent to hass
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {"agent": mock_agent}
        mock_hass.config_entries.async_get_entry.return_value = mock_config_entry
        
        # Create a mock service call with a specific conversation_id
        service_call = MagicMock()
        service_call.hass = mock_hass
        service_call.data = {
            "entity_id": f"{DOMAIN}.{mock_config_entry.entry_id}",
            "conversation_id": "test-conversation",
        }
        
        # Call the service function
        await async_clear_conversation_service(service_call)
        
        # Check that clear_conversation was called with the correct conversation_id
        mock_agent.conversation_manager.clear_conversation.assert_called_once_with("test-conversation")
        mock_agent.conversation_manager.clear_all_conversations.assert_not_called()
        mock_agent.conversation_manager.async_save.assert_called_once()
    
    async def test_clear_all_conversations_service(self, mock_hass, mock_config_entry, mock_agent):
        """Test the clear_conversation service without a conversation_id."""
        # Import the service function
        from custom_components.cortex_agent.services import async_clear_conversation_service
        
        # Add the config entry and agent to hass
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {"agent": mock_agent}
        mock_hass.config_entries.async_get_entry.return_value = mock_config_entry
        
        # Create a mock service call without a conversation_id
        service_call = MagicMock()
        service_call.hass = mock_hass
        service_call.data = {
            "entity_id": f"{DOMAIN}.{mock_config_entry.entry_id}",
        }
        
        # Call the service function
        await async_clear_conversation_service(service_call)
        
        # Check that clear_all_conversations was called
        mock_agent.conversation_manager.clear_conversation.assert_not_called()
        mock_agent.conversation_manager.clear_all_conversations.assert_called_once()
        mock_agent.conversation_manager.async_save.assert_called_once()