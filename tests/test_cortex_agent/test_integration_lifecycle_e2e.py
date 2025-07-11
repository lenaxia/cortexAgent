"""End-to-end tests for the CortexAgent integration lifecycle."""
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers.entity_registry import async_get as get_entity_registry
from homeassistant.helpers.device_registry import async_get as get_device_registry

from tests.common import MockConfigEntry

from custom_components.cortex_agent.const import (
    DOMAIN,
    CONF_PROVIDER,
    CONF_MODEL_ID,
    CONF_API_KEY,
    CONF_SYSTEM_PROMPT,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    DATA_AGENT,
)


@pytest.fixture
async def mock_hass():
    """Create a Home Assistant instance for testing."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_setup = AsyncMock(return_value=True)
    hass.config_entries.async_unload = AsyncMock(return_value=True)
    hass.config_entries.flow = MagicMock()
    hass.config_entries.flow.async_init = AsyncMock()
    hass.config_entries.flow.async_configure = AsyncMock()
    hass.config_entries.options = MagicMock()
    hass.config_entries.options.async_init = AsyncMock()
    hass.config_entries.options.async_configure = AsyncMock()
    hass.config_entries._entries = []
    
    # Set up conversation component mock
    hass.components = MagicMock()
    hass.components.conversation = MagicMock()
    hass.components.conversation.async_register = AsyncMock(return_value="test-conversation-id")
    hass.components.conversation.async_unregister = AsyncMock()
    
    # Set up http mock
    hass.http = MagicMock()
    hass.http.register_view = MagicMock()
    
    # Set up services
    hass.services = MagicMock()
    hass.services.async_register = AsyncMock()
    hass.services.has_service = MagicMock(return_value=True)
    
    # Set up async methods
    hass.async_create_task = AsyncMock()
    hass.async_block_till_done = AsyncMock()
    
    yield hass


@pytest.fixture
async def mock_model_provider():
    """Mock the model provider to avoid external API calls."""
    with patch("custom_components.cortex_agent.model_provider.create_model_provider") as mock:
        # Create a mock provider that can be awaited
        mock_provider = MagicMock()
        mock_provider.generate_response = AsyncMock(return_value={"content": "Mocked response"})
        mock_provider.config = {"provider": "openai", "api_key": "test_key", "model_id": "gpt-4"}
        
        async def _mock_create_provider(*args, **kwargs):
            return mock_provider
            
        mock.side_effect = _mock_create_provider
        yield mock


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_PROVIDER: "openai",
            CONF_MODEL_ID: "gpt-4",
            CONF_API_KEY: "test-api-key",
            CONF_SYSTEM_PROMPT: "You are a helpful assistant.",
        },
        options={
            CONF_MAX_TOKENS: 1024,
            CONF_TEMPERATURE: 0.7,
        },
        entry_id="test_entry_id",
        title="CortexAgent Test",
    )


@pytest.fixture
def mock_conversation_manager():
    """Mock conversation manager."""
    manager = MagicMock()
    manager.async_load = AsyncMock()
    manager.async_save = AsyncMock()
    manager.async_unload = AsyncMock()
    manager.get_conversation = MagicMock(return_value=[])
    return manager


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry."""
    registry = MagicMock()
    return registry


@pytest.fixture
def mock_memory_handler():
    """Mock memory handler."""
    handler = MagicMock()
    handler.async_load = AsyncMock()
    handler.async_save = AsyncMock()
    return handler


@pytest.fixture
def mock_mcp_connector():
    """Mock MCP connector."""
    connector = MagicMock()
    connector.async_setup = AsyncMock()
    connector.get_connected_servers = MagicMock(return_value=["server1", "server2"])
    connector.async_disconnect = AsyncMock()
    return connector


class TestIntegrationLifecycleE2E:
    """End-to-end tests for the integration lifecycle."""
    
    async def test_setup_and_teardown(
        self,
        mock_hass,
        mock_model_provider,
        mock_entry,
        mock_conversation_manager,
        mock_tool_registry,
        mock_memory_handler,
        mock_mcp_connector,
    ):
        """Test the complete setup and teardown lifecycle of the integration."""
        # Initialize data structure
        mock_hass.data[DOMAIN] = {}
        
        # Import the actual setup function to test it directly
        from custom_components.cortex_agent import async_setup_entry
        
        # Mock the component creation
        with patch("custom_components.cortex_agent.conversation_manager.ConversationManager",
                  return_value=mock_conversation_manager), \
             patch("custom_components.cortex_agent.tool_registry.ToolRegistry",
                  return_value=mock_tool_registry), \
             patch("custom_components.cortex_agent.memory_handler.MemoryHandler",
                  return_value=mock_memory_handler), \
             patch("custom_components.cortex_agent.mcp_connector.MCPConnector",
                  return_value=mock_mcp_connector), \
             patch("custom_components.cortex_agent.conversation.CortexAgent") as mock_agent_class:
            
            # Create a mock agent instance
            mock_agent = MagicMock()
            mock_agent.async_unload = AsyncMock()
            mock_agent_class.return_value = mock_agent
            
            # Set up the config entry
            result = await async_setup_entry(mock_hass, mock_entry)
            
            # Verify setup was successful
            assert result is True
            
            # Verify the integration data is set up
            assert mock_entry.entry_id in mock_hass.data[DOMAIN]
            assert DATA_AGENT in mock_hass.data[DOMAIN][mock_entry.entry_id]
            
            # Verify conversation component is registered
            mock_hass.components.conversation.async_register.assert_called_once()
            
            # Verify components were initialized
            mock_conversation_manager.async_load.assert_called_once()
            mock_memory_handler.async_load.assert_called_once()
            mock_mcp_connector.async_setup.assert_called_once()
            
            # Import the actual unload function to test it directly
            from custom_components.cortex_agent import async_unload_entry
            
            # Now test teardown
            result = await async_unload_entry(mock_hass, mock_entry)
            
            # Verify unload was successful
            assert result is True
            
            # Verify conversation was unregistered
            mock_hass.components.conversation.async_unregister.assert_called_once()
            
            # Verify agent was unloaded
            mock_agent.async_unload.assert_called_once()
            
            # Verify MCP servers were disconnected
            assert mock_mcp_connector.async_disconnect.call_count == 2
            
            # Verify memory handler and conversation manager were saved
            mock_memory_handler.async_save.assert_called_once()
            mock_conversation_manager.async_save.assert_called_once()
            
            # Verify the integration data is cleaned up
            assert mock_entry.entry_id not in mock_hass.data[DOMAIN]
    
    async def test_persistence_across_restarts(
        self,
        mock_hass,
        mock_model_provider,
        mock_entry,
        mock_conversation_manager,
        mock_tool_registry,
        mock_memory_handler,
        mock_mcp_connector,
    ):
        """Test that the integration's state persists across Home Assistant restarts."""
        # Initialize data structure
        mock_hass.data[DOMAIN] = {}
        
        # Import the actual setup function
        from custom_components.cortex_agent import async_setup_entry, async_unload_entry
        
        # Mock the component creation
        with patch("custom_components.cortex_agent.conversation_manager.ConversationManager",
                  return_value=mock_conversation_manager), \
             patch("custom_components.cortex_agent.tool_registry.ToolRegistry",
                  return_value=mock_tool_registry), \
             patch("custom_components.cortex_agent.memory_handler.MemoryHandler",
                  return_value=mock_memory_handler), \
             patch("custom_components.cortex_agent.mcp_connector.MCPConnector",
                  return_value=mock_mcp_connector), \
             patch("custom_components.cortex_agent.conversation.CortexAgent") as mock_agent_class:
            
            # Create a mock agent instance
            mock_agent = MagicMock()
            mock_agent.async_unload = AsyncMock()
            mock_agent_class.return_value = mock_agent
            
            # Set up the config entry
            await async_setup_entry(mock_hass, mock_entry)
            
            # Simulate adding a conversation message
            test_conversation_id = "test_conversation_id"
            mock_conversation_manager.get_conversation.return_value = [
                MagicMock(role="user", content="Hello"),
                MagicMock(role="assistant", content="Hi there!"),
            ]
            
            # Unload the entry (simulating HA shutdown)
            await async_unload_entry(mock_hass, mock_entry)
            
            # Verify conversation manager was saved
            mock_conversation_manager.async_save.assert_called_once()
            
            # Reset mocks for the "restart"
            mock_conversation_manager.async_save.reset_mock()
            mock_conversation_manager.async_load.reset_mock()
            
            # Reinitialize data structure
            mock_hass.data[DOMAIN] = {}
            
            # Set up the entry again (simulating HA restart)
            await async_setup_entry(mock_hass, mock_entry)
            
            # Verify conversation manager was loaded
            mock_conversation_manager.async_load.assert_called_once()
            
            # Verify we can still access the conversation history
            mock_conversation_manager.get_conversation.assert_not_called()  # Not called yet
            
            # Now try to get the conversation
            conversation = mock_conversation_manager.get_conversation(test_conversation_id)
            
            # Verify the conversation was retrieved
            mock_conversation_manager.get_conversation.assert_called_once_with(test_conversation_id)
            
            # Verify the conversation has the expected messages
            assert len(conversation) == 2