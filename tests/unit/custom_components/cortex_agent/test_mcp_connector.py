"""Tests for the MCP connector component."""
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.cortex_agent.mcp_connector import (
    MCPConnector,
    MCPServerConfig,
    MCPTool,
)
from custom_components.cortex_agent.const import (
    ATTR_AUTH_TOKEN,
    ATTR_NAME,
    ATTR_SERVER_TYPE,
    ATTR_URL,
    CONF_MCP_SERVERS,
    SERVER_TYPE_SSE,
    SERVER_TYPE_STREAMABLE_HTTP,
)
from custom_components.cortex_agent.exceptions import NetworkError


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
    return hass


@pytest.fixture
def mock_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.options = {
        CONF_MCP_SERVERS: [
            {
                ATTR_NAME: "test_server",
                ATTR_URL: "https://example.com/mcp",
                ATTR_SERVER_TYPE: SERVER_TYPE_SSE,
                ATTR_AUTH_TOKEN: "test_token",
                "enabled": True,
            }
        ]
    }
    return entry


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client."""
    client = MagicMock()
    client.list_tools_sync = MagicMock(return_value=[
        MagicMock(
            tool_name="test_tool_1",
            description="Test tool 1",
            parameters={"param1": "value1"}
        ),
        MagicMock(
            tool_name="test_tool_2",
            description="Test tool 2",
            parameters={"param2": "value2"}
        )
    ])
    client.execute_tool_sync = MagicMock(return_value={"result": "success", "data": {"value": 42}})
    return client


@pytest.fixture
def mcp_connector(mock_hass, mock_entry):
    """Create an MCP connector instance."""
    return MCPConnector(mock_hass, mock_entry)


@pytest.mark.asyncio
async def test_mcp_connector_setup(mcp_connector, mock_hass, mock_entry):
    """Test setting up the MCP connector."""
    with patch.object(mcp_connector, "async_connect", AsyncMock(return_value=True)) as mock_connect:
        await mcp_connector.async_setup()
        
        # Should call async_connect for each enabled server
        assert mock_connect.call_count == 1
        mock_connect.assert_called_with(mock_entry.options[CONF_MCP_SERVERS][0])


@pytest.mark.asyncio
async def test_mcp_connector_connect(mcp_connector, mock_hass, mock_mcp_client):
    """Test connecting to an MCP server."""
    # Mock the import statement itself
    mock_module = MagicMock()
    mock_module.MCPClient = MagicMock(return_value=mock_mcp_client)
    mock_module.sse_client = MagicMock(return_value=MagicMock())
    
    with patch.dict('sys.modules', {
        'mcp.client.sse': mock_module,
        'mcp.client.streamable_http': mock_module,
        'strands.tools.mcp.mcp_client': mock_module
    }):
        # Connect to a server
        config = {
            ATTR_NAME: "test_server",
            ATTR_URL: "https://example.com/mcp",
            ATTR_SERVER_TYPE: SERVER_TYPE_SSE,
            ATTR_AUTH_TOKEN: "test_token",
            "enabled": True,
        }
        
        result = await mcp_connector.async_connect(config)
        
        assert result is True
        assert "test_server" in mcp_connector.clients


@pytest.mark.asyncio
async def test_mcp_connector_connect_streamable_http(mcp_connector, mock_hass, mock_mcp_client):
    """Test connecting to a streamable HTTP MCP server."""
    # Mock the import statement itself
    mock_module = MagicMock()
    mock_module.MCPClient = MagicMock(return_value=mock_mcp_client)
    mock_module.streamablehttp_client = MagicMock(return_value=MagicMock())
    
    with patch.dict('sys.modules', {
        'mcp.client.sse': mock_module,
        'mcp.client.streamable_http': mock_module,
        'strands.tools.mcp.mcp_client': mock_module
    }):
        # Connect to a server
        config = {
            ATTR_NAME: "test_server",
            ATTR_URL: "https://example.com/mcp",
            ATTR_SERVER_TYPE: SERVER_TYPE_STREAMABLE_HTTP,
            ATTR_AUTH_TOKEN: "test_token",
            "enabled": True,
        }
        
        result = await mcp_connector.async_connect(config)
        
        assert result is True
        assert "test_server" in mcp_connector.clients


@pytest.mark.asyncio
async def test_mcp_connector_connect_unsupported_type(mcp_connector, mock_hass):
    """Test connecting to an unsupported server type."""
    # Connect to a server with an unsupported type
    config = {
        ATTR_NAME: "test_server",
        ATTR_URL: "https://example.com/mcp",
        ATTR_SERVER_TYPE: "unsupported",
        "enabled": True,
    }
    
    result = await mcp_connector.async_connect(config)
    
    assert result is False
    assert "test_server" not in mcp_connector.clients


@pytest.mark.asyncio
async def test_mcp_connector_connect_import_error(mcp_connector, mock_hass):
    """Test connecting when import fails."""
    # Mock the import to fail
    with patch.dict('sys.modules', {
        'mcp.client.sse': None,
        'mcp.client.streamable_http': None,
        'strands.tools.mcp.mcp_client': None
    }):
        # Connect to a server
        config = {
            ATTR_NAME: "test_server",
            ATTR_URL: "https://example.com/mcp",
            ATTR_SERVER_TYPE: SERVER_TYPE_SSE,
            "enabled": True,
        }
        
        # This should fail with a NetworkError
        result = await mcp_connector.async_connect(config)
        
        # Since we're mocking at a different level, the error is caught in the method
        # and it returns False instead of raising an exception
        assert result is False
        assert "test_server" not in mcp_connector.clients


@pytest.mark.asyncio
async def test_mcp_connector_disconnect(mcp_connector, mock_hass, mock_mcp_client):
    """Test disconnecting from an MCP server."""
    # Add a client to disconnect
    mcp_connector.clients["test_server"] = mock_mcp_client
    mcp_connector.tools_cache["test_server"] = [MagicMock()]
    
    # Disconnect
    result = await mcp_connector.async_disconnect("test_server")
    
    assert result is True
    assert "test_server" not in mcp_connector.clients
    assert "test_server" not in mcp_connector.tools_cache


@pytest.mark.asyncio
async def test_mcp_connector_disconnect_not_connected(mcp_connector, mock_hass):
    """Test disconnecting from a server that is not connected."""
    # Disconnect from a server that is not connected
    result = await mcp_connector.async_disconnect("nonexistent_server")
    
    assert result is False


@pytest.mark.asyncio
async def test_mcp_connector_disconnect_error(mcp_connector, mock_hass):
    """Test disconnecting when an error occurs."""
    # Add a client that will raise an error when disconnecting
    client = MagicMock()
    client.disconnect = MagicMock(side_effect=Exception("Test error"))
    mcp_connector.clients["test_server"] = client
    
    # Disconnect
    result = await mcp_connector.async_disconnect("test_server")
    
    # Should still return True as we handle the error
    assert result is True
    assert "test_server" not in mcp_connector.clients


@pytest.mark.asyncio
async def test_mcp_connector_update_tools_cache(mcp_connector, mock_hass, mock_mcp_client):
    """Test updating the tools cache."""
    # Add a client
    mcp_connector.clients["test_server"] = mock_mcp_client
    
    # Update tools cache
    mcp_connector._update_tools_cache("test_server")
    
    assert "test_server" in mcp_connector.tools_cache
    assert len(mcp_connector.tools_cache["test_server"]) == 2
    assert mcp_connector.tools_cache["test_server"][0].tool_name == "test_tool_1"
    assert mcp_connector.tools_cache["test_server"][1].tool_name == "test_tool_2"


@pytest.mark.asyncio
async def test_mcp_connector_update_tools_cache_no_list_tools(mcp_connector, mock_hass):
    """Test updating the tools cache when list_tools_sync is not available."""
    # Add a client without list_tools_sync
    client = MagicMock()
    delattr(client, "list_tools_sync")
    mcp_connector.clients["test_server"] = client
    
    # Update tools cache
    mcp_connector._update_tools_cache("test_server")
    
    assert "test_server" in mcp_connector.tools_cache
    assert len(mcp_connector.tools_cache["test_server"]) == 0


@pytest.mark.asyncio
async def test_mcp_connector_update_tools_cache_error(mcp_connector, mock_hass):
    """Test updating the tools cache when an error occurs."""
    # Add a client that will raise an error
    client = MagicMock()
    client.list_tools_sync = MagicMock(side_effect=Exception("Test error"))
    mcp_connector.clients["test_server"] = client
    
    # Update tools cache
    mcp_connector._update_tools_cache("test_server")
    
    assert "test_server" in mcp_connector.tools_cache
    assert len(mcp_connector.tools_cache["test_server"]) == 0


@pytest.mark.asyncio
async def test_mcp_connector_get_all_tools(mcp_connector, mock_hass, mock_mcp_client):
    """Test getting all tools from all servers."""
    # Add clients
    mcp_connector.clients["server1"] = mock_mcp_client
    mcp_connector.clients["server2"] = mock_mcp_client
    
    # Mock _update_tools_cache to set up the cache
    with patch.object(mcp_connector, "_update_tools_cache") as mock_update:
        def update_side_effect(server_name):
            mcp_connector.tools_cache[server_name] = [
                MCPTool(
                    server_name=server_name,
                    tool_name=f"tool1_{server_name}",
                    description=f"Tool 1 from {server_name}",
                    parameters={"param1": "value1"}
                ),
                MCPTool(
                    server_name=server_name,
                    tool_name=f"tool2_{server_name}",
                    description=f"Tool 2 from {server_name}",
                    parameters={"param2": "value2"}
                )
            ]
        
        mock_update.side_effect = update_side_effect
        
        # Get all tools
        tools = await mcp_connector.async_get_all_tools()
        
        assert len(tools) == 4  # 2 tools per server
        assert mock_update.call_count == 2
        
        # Check that tools from both servers are included
        tool_names = [tool.tool_name for tool in tools]
        assert "tool1_server1" in tool_names
        assert "tool2_server1" in tool_names
        assert "tool1_server2" in tool_names
        assert "tool2_server2" in tool_names


@pytest.mark.asyncio
async def test_mcp_connector_get_server_tools(mcp_connector, mock_hass, mock_mcp_client):
    """Test getting tools for a specific server."""
    # Add a client
    mcp_connector.clients["test_server"] = mock_mcp_client
    
    # Mock _update_tools_cache to set up the cache
    with patch.object(mcp_connector, "_update_tools_cache") as mock_update:
        def update_side_effect(server_name):
            mcp_connector.tools_cache[server_name] = [
                MCPTool(
                    server_name=server_name,
                    tool_name=f"tool1_{server_name}",
                    description=f"Tool 1 from {server_name}",
                    parameters={"param1": "value1"}
                ),
                MCPTool(
                    server_name=server_name,
                    tool_name=f"tool2_{server_name}",
                    description=f"Tool 2 from {server_name}",
                    parameters={"param2": "value2"}
                )
            ]
        
        mock_update.side_effect = update_side_effect
        
        # Get tools for the server
        tools = await mcp_connector.async_get_server_tools("test_server")
        
        assert len(tools) == 2
        assert mock_update.call_count == 1
        assert tools[0].server_name == "test_server"
        assert tools[0].tool_name == "tool1_test_server"
        assert tools[1].tool_name == "tool2_test_server"


@pytest.mark.asyncio
async def test_mcp_connector_get_server_tools_not_connected(mcp_connector, mock_hass):
    """Test getting tools for a server that is not connected."""
    # Get tools for a server that is not connected
    tools = await mcp_connector.async_get_server_tools("nonexistent_server")
    
    assert len(tools) == 0


@pytest.mark.asyncio
async def test_mcp_connector_get_connected_servers(mcp_connector, mock_hass):
    """Test getting connected servers."""
    # Add clients
    mcp_connector.clients["server1"] = MagicMock()
    mcp_connector.clients["server2"] = MagicMock()
    
    # Get connected servers
    servers = mcp_connector.get_connected_servers()
    
    assert len(servers) == 2
    assert "server1" in servers
    assert "server2" in servers


@pytest.mark.asyncio
async def test_mcp_connector_get_client(mcp_connector, mock_hass, mock_mcp_client):
    """Test getting a client for a specific server."""
    # Add a client
    mcp_connector.clients["test_server"] = mock_mcp_client
    
    # Get the client
    client = mcp_connector.get_client("test_server")
    
    assert client == mock_mcp_client


@pytest.mark.asyncio
async def test_mcp_connector_get_client_not_connected(mcp_connector, mock_hass):
    """Test getting a client for a server that is not connected."""
    # Get a client for a server that is not connected
    client = mcp_connector.get_client("nonexistent_server")
    
    assert client is None


@pytest.mark.asyncio
async def test_mcp_connector_execute_tool(mcp_connector, mock_hass, mock_mcp_client):
    """Test executing a tool on an MCP server."""
    # Add a client
    mcp_connector.clients["test_server"] = mock_mcp_client
    
    # Execute a tool
    result = await mcp_connector.async_execute_tool(
        "test_server", 
        "test_tool", 
        {"param1": "value1"}
    )
    
    # Check that the tool was executed with the correct arguments
    mock_mcp_client.execute_tool_sync.assert_called_once_with(
        "test_tool", 
        {"param1": "value1"}
    )
    
    # Check the result
    assert result == {"result": "success", "data": {"value": 42}}


@pytest.mark.asyncio
async def test_mcp_connector_execute_tool_server_not_connected(mcp_connector, mock_hass):
    """Test executing a tool on a server that is not connected."""
    # Try to execute a tool on a server that is not connected
    with pytest.raises(NetworkError) as excinfo:
        await mcp_connector.async_execute_tool(
            "nonexistent_server", 
            "test_tool", 
            {"param1": "value1"}
        )
    
    assert "Server nonexistent_server not connected" in str(excinfo.value)


@pytest.mark.asyncio
async def test_mcp_connector_execute_tool_client_error(mcp_connector, mock_hass):
    """Test executing a tool when the client raises an error."""
    # Add a client that will raise an error
    client = MagicMock()
    client.execute_tool_sync = MagicMock(side_effect=Exception("Test error"))
    mcp_connector.clients["test_server"] = client
    
    # Try to execute a tool
    with pytest.raises(NetworkError) as excinfo:
        await mcp_connector.async_execute_tool(
            "test_server", 
            "test_tool", 
            {"param1": "value1"}
        )
    
    assert "Failed to execute tool: Test error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_mcp_connector_execution_callbacks(mcp_connector, mock_hass):
    """Test registering and unregistering execution callbacks."""
    # Register a callback
    callback = MagicMock()
    mcp_connector.register_execution_callback("test_server", callback)
    
    assert "test_server" in mcp_connector._execution_callbacks
    assert mcp_connector._execution_callbacks["test_server"] == callback
    
    # Unregister the callback
    mcp_connector.unregister_execution_callback("test_server")
    
    assert "test_server" not in mcp_connector._execution_callbacks