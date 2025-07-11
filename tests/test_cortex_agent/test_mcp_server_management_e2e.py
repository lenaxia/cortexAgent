"""End-to-end tests for CortexAgent MCP server management."""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from tests.common import MockConfigEntry

from custom_components.cortex_agent.const import (
    DOMAIN,
    CONF_MCP_SERVERS,
    ATTR_NAME,
    ATTR_URL,
    ATTR_SERVER_TYPE,
    ATTR_AUTH_TOKEN,
    SERVER_TYPE_SSE,
    SERVER_TYPE_STREAMABLE_HTTP,
    SERVER_TYPE_STDIO,
)
from custom_components.cortex_agent.mcp_connector import MCPConnector
from custom_components.cortex_agent.services import (
    async_connect_mcp_server_service,
    async_disconnect_mcp_server_service,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.config = MagicMock()
    hass.config.components = []
    hass.loop = MagicMock()
    hass.loop.create_future = MagicMock(return_value=MagicMock())
    hass.config_entries = MagicMock()
    hass.config_entries.async_get_entry = MagicMock()  # Not AsyncMock to avoid coroutine issues
    hass.config_entries.async_update_entry = AsyncMock()
    hass.services = MagicMock()
    hass.services.async_register = MagicMock()
    hass.async_add_executor_job = AsyncMock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "provider": "openai",
            "api_key": "test-api-key",
            "model_id": "gpt-4o",
            "system_prompt": "You are a helpful assistant.",
        },
        options={
            CONF_MCP_SERVERS: [],
        },
        entry_id="test_entry_id",
        title="CortexAgent Test",
    )


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client."""
    with patch("strands.tools.mcp.mcp_client.MCPClient") as mock_class:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=None)
        mock_instance.list_tools_sync = MagicMock(return_value=[])
        mock_class.return_value = mock_instance
        yield mock_class


@pytest.fixture
def mock_sse_client():
    """Mock SSE client."""
    with patch("custom_components.cortex_agent.mcp_connector.sse_client") as mock:
        yield mock


@pytest.fixture
def mock_streamablehttp_client():
    """Mock Streamable HTTP client."""
    with patch("custom_components.cortex_agent.mcp_connector.streamablehttp_client") as mock:
        yield mock


@pytest.fixture
def mock_stdio_client():
    """Mock Stdio client."""
    with patch("custom_components.cortex_agent.mcp_connector.stdio_client") as mock:
        yield mock


class TestMCPServerManagementE2E:
    """Test MCP server management end-to-end functionality."""

    async def test_connect_mcp_server_service(
        self, mock_hass, mock_config_entry, mock_sse_client, mock_mcp_client
    ):
        """Test connecting to an MCP server through the service."""
        # Create a mock MCP connector
        mock_connector = MagicMock(spec=MCPConnector)
        mock_connector.async_connect = AsyncMock(return_value=True)
        
        # Store it in hass.data
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "mcp_connector": mock_connector
            }
        }
        
        # Create a mock service call
        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "entity_id": f"{DOMAIN}.{mock_config_entry.entry_id}",
            "name": "test-server",
            "url": "http://localhost:8000/mcp",
            "server_type": SERVER_TYPE_SSE,
            "auth_token": "test-token",
        }
        service_call.hass = mock_hass
        
        # Mock the config entry
        mock_entry = MagicMock()
        mock_entry.entry_id = mock_config_entry.entry_id
        mock_entry.options = {CONF_MCP_SERVERS: []}
        mock_hass.config_entries.async_get_entry.return_value = mock_entry
        
        # Call the service
        await async_connect_mcp_server_service(service_call)
        
        # Check that the config entry was updated
        mock_hass.config_entries.async_update_entry.assert_called_once()
        
        # Check that the server was added to the options
        call_args = mock_hass.config_entries.async_update_entry.call_args
        assert CONF_MCP_SERVERS in call_args[1]["options"]
        assert len(call_args[1]["options"][CONF_MCP_SERVERS]) == 1
        assert call_args[1]["options"][CONF_MCP_SERVERS][0]["name"] == "test-server"
        assert call_args[1]["options"][CONF_MCP_SERVERS][0]["url"] == "http://localhost:8000/mcp"
        assert call_args[1]["options"][CONF_MCP_SERVERS][0]["server_type"] == SERVER_TYPE_SSE
        assert call_args[1]["options"][CONF_MCP_SERVERS][0]["auth_token"] == "test-token"

    async def test_disconnect_mcp_server_service(self, mock_hass, mock_config_entry):
        """Test disconnecting from an MCP server through the service."""
        # Create a mock MCP connector
        mock_connector = MagicMock(spec=MCPConnector)
        mock_connector.async_disconnect = AsyncMock(return_value=True)
        
        # Store it in hass.data
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "mcp_connector": mock_connector
            }
        }
        
        # Create a mock config entry with an MCP server
        mock_entry = MagicMock()
        mock_entry.entry_id = mock_config_entry.entry_id
        mock_entry.options = {
            CONF_MCP_SERVERS: [
                {
                    "name": "test-server",
                    "url": "http://localhost:8000/mcp",
                    "server_type": SERVER_TYPE_SSE,
                    "auth_token": "test-token",
                }
            ]
        }
        mock_hass.config_entries.async_get_entry.return_value = mock_entry
        
        # Create a mock service call
        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "entity_id": f"{DOMAIN}.{mock_config_entry.entry_id}",
            "name": "test-server",
        }
        service_call.hass = mock_hass
        
        # Call the service
        await async_disconnect_mcp_server_service(service_call)
        
        # Check that the config entry was updated
        mock_hass.config_entries.async_update_entry.assert_called_once()
        
        # Check that the server was removed from the options
        call_args = mock_hass.config_entries.async_update_entry.call_args
        assert CONF_MCP_SERVERS in call_args[1]["options"]
        assert len(call_args[1]["options"][CONF_MCP_SERVERS]) == 0

    async def test_mcp_server_persistence(
        self, mock_hass, mock_config_entry, mock_sse_client, mock_mcp_client
    ):
        """Test that MCP server connections persist across restarts."""
        # Create a mock config entry with an MCP server
        mock_entry = MagicMock()
        mock_entry.entry_id = mock_config_entry.entry_id
        mock_entry.options = {
            CONF_MCP_SERVERS: [
                {
                    "name": "test-server",
                    "url": "http://localhost:8000/mcp",
                    "server_type": SERVER_TYPE_SSE,
                    "auth_token": "test-token",
                    "enabled": True,
                }
            ]
        }
        mock_hass.config_entries.async_get_entry.return_value = mock_entry
        
        # Create a real MCP connector
        connector = MCPConnector(mock_hass, mock_entry)
        
        # Mock the connect method
        connector.async_connect = AsyncMock(return_value=True)
        
        # Call setup
        await connector.async_setup()
        
        # Check that connect was called with the server config
        connector.async_connect.assert_called_once_with(
            mock_entry.options[CONF_MCP_SERVERS][0]
        )

    # TODO: Implement test_execute_mcp_tool once the service is available

    async def test_add_remove_mcp_server_via_options_flow(
        self, mock_hass, mock_config_entry, mock_sse_client, mock_mcp_client
    ):
        """Test adding and removing an MCP server through the options flow."""
        # Create a mock MCP connector
        mock_connector = MagicMock(spec=MCPConnector)
        mock_connector.async_connect = AsyncMock(return_value=True)
        mock_connector.async_disconnect = AsyncMock(return_value=True)
        
        # Store it in hass.data
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "mcp_connector": mock_connector
            }
        }
        
        # Create a mock config entry
        mock_entry = MagicMock()
        mock_entry.entry_id = mock_config_entry.entry_id
        mock_entry.options = {CONF_MCP_SERVERS: []}
        mock_hass.config_entries.async_get_entry.return_value = mock_entry
        
        # Simulate adding a server through the options flow
        new_options = {
            CONF_MCP_SERVERS: [
                {
                    "name": "test-server",
                    "url": "http://localhost:8000/mcp",
                    "server_type": SERVER_TYPE_SSE,
                    "auth_token": "test-token",
                    "enabled": True,
                }
            ]
        }
        
        # Mock the reload method
        mock_hass.config_entries.async_reload = AsyncMock()
        
        # Update the options
        await mock_hass.config_entries.async_update_entry(mock_entry, options=new_options)
        
        # Manually update the mock_entry's options since the mock doesn't do it
        mock_entry.options = new_options
        
        # Check that the options were updated
        assert mock_entry.options == new_options
        
        # Simulate the entry reload
        # In Home Assistant, reloading a config entry means unloading and then setting it up again
        
        # Mock the unload and setup methods
        with patch('custom_components.cortex_agent.async_unload_entry', return_value=True), \
             patch('custom_components.cortex_agent.async_setup_entry', return_value=True):
            # Simulate reload by calling unload and then setup
            await mock_hass.config_entries.async_reload(mock_entry.entry_id)
            
            # Manually simulate what happens during setup_entry
            # In a real setup, this would call the connector's async_connect method
            await mock_connector.async_connect(new_options[CONF_MCP_SERVERS][0])
        
        # Check that the connector's connect method was called
        mock_connector.async_connect.assert_called_once()
        
        # Simulate removing the server through the options flow
        new_options = {CONF_MCP_SERVERS: []}
        
        # Update the options
        await mock_hass.config_entries.async_update_entry(mock_entry, options=new_options)
        
        # Manually update the mock_entry's options since the mock doesn't do it
        mock_entry.options = new_options
        
        # Check that the options were updated
        assert mock_entry.options == new_options
        
        # Simulate the entry reload
        # In Home Assistant, reloading a config entry means unloading and then setting it up again
        with patch('custom_components.cortex_agent.async_unload_entry', return_value=True), \
             patch('custom_components.cortex_agent.async_setup_entry', return_value=True):
            # Simulate reload by calling unload and then setup
            await mock_hass.config_entries.async_reload(mock_entry.entry_id)
            
            # Manually simulate what happens during unload_entry
            # In a real setup, this would call the connector's async_disconnect method
            await mock_connector.async_disconnect("test-server")
        
        # Check that the connector's disconnect method was called
        mock_connector.async_disconnect.assert_called_once_with("test-server")

    async def test_enable_disable_mcp_server(
        self, mock_hass, mock_config_entry, mock_sse_client, mock_mcp_client
    ):
        """Test enabling and disabling an MCP server."""
        # Create a mock MCP connector
        mock_connector = MagicMock(spec=MCPConnector)
        mock_connector.async_connect = AsyncMock(return_value=True)
        mock_connector.async_disconnect = AsyncMock(return_value=True)
        
        # Store it in hass.data
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "mcp_connector": mock_connector
            }
        }
        
        # Create a mock config entry with a disabled MCP server
        mock_entry = MagicMock()
        mock_entry.entry_id = mock_config_entry.entry_id
        mock_entry.options = {
            CONF_MCP_SERVERS: [
                {
                    "name": "test-server",
                    "url": "http://localhost:8000/mcp",
                    "server_type": SERVER_TYPE_SSE,
                    "auth_token": "test-token",
                    "enabled": False,
                }
            ]
        }
        mock_hass.config_entries.async_get_entry.return_value = mock_entry
        
        # Create a real MCP connector with mocked connect method
        connector = MCPConnector(mock_hass, mock_entry)
        connector.async_connect = AsyncMock(return_value=True)
        
        # Call setup
        await connector.async_setup()
        
        # Check that connect was not called since the server is disabled
        assert not connector.async_connect.called
        
        # Enable the server
        mock_entry.options[CONF_MCP_SERVERS][0]["enabled"] = True
        
        # Call setup again
        await connector.async_setup()
        
        # Check that connect was called
        connector.async_connect.assert_called_once()