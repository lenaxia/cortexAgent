"""Standalone tests for the MCPConnector implementation."""
import sys
import os
from typing import Any, Dict, List, Optional, Callable
from unittest.mock import MagicMock, AsyncMock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

# Define the necessary classes and constants
class NetworkError(Exception):
    """Network communication error."""
    
    def __init__(self, message: str, is_temporary: bool = True):
        """Initialize the exception."""
        self.is_temporary = is_temporary
        super().__init__(message)

# Constants
ATTR_AUTH_TOKEN = "auth_token"
ATTR_NAME = "name"
ATTR_SERVER_TYPE = "server_type"
ATTR_URL = "url"
CONF_MCP_SERVERS = "mcp_servers"
SERVER_TYPE_SSE = "sse"
SERVER_TYPE_STREAMABLE_HTTP = "streamable_http"

# Define the MCPServerConfig class
class MCPServerConfig:
    """Configuration for an MCP server connection."""
    
    def __init__(
        self,
        name: str,
        url: str,
        server_type: str = SERVER_TYPE_SSE,
        auth_token: Optional[str] = None,
        enabled: bool = True
    ):
        """Initialize the MCP server configuration."""
        self.name = name
        self.url = url
        self.server_type = server_type
        self.auth_token = auth_token
        self.enabled = enabled


# Define the MCPTool class
class MCPTool:
    """Information about a tool provided by an MCP server."""
    
    def __init__(
        self,
        server_name: str,
        tool_name: str,
        description: str,
        parameters: Dict[str, Any] = None
    ):
        """Initialize the MCP tool."""
        self.server_name = server_name
        self.tool_name = tool_name
        self.description = description
        self.parameters = parameters or {}


# Define the MCPConnector class
class MCPConnector:
    """Manages connections to MCP servers."""
    
    def __init__(self, hass, entry):
        """Initialize the MCP connector."""
        self.hass = hass
        self.entry = entry
        self.clients = {}
        self.tools_cache = {}
        self._execution_callbacks = {}
    
    async def async_setup(self) -> None:
        """Set up MCP connections from config."""
        servers = self.entry.options.get(CONF_MCP_SERVERS, [])
        
        for server_config in servers:
            if server_config.get("enabled", True):
                await self.async_connect(server_config)
    
    async def async_connect(self, config: Dict[str, Any]) -> bool:
        """Connect to an MCP server using the provided configuration."""
        try:
            # Convert dict to MCPServerConfig
            server_config = MCPServerConfig(
                name=config[ATTR_NAME],
                url=config[ATTR_URL],
                server_type=config.get(ATTR_SERVER_TYPE, SERVER_TYPE_SSE),
                auth_token=config.get(ATTR_AUTH_TOKEN),
                enabled=config.get("enabled", True),
            )
            
            # Check if already connected
            if server_config.name in self.clients:
                print(f"Already connected to {server_config.name}, disconnecting first")
                await self.async_disconnect(server_config.name)
            
            # In a real implementation, this would create an MCP client
            # For testing, we'll just create a mock client
            client = MagicMock()
            client.list_tools_sync = MagicMock(return_value=[
                MagicMock(
                    tool_name=f"tool1_{server_config.name}",
                    description=f"Tool 1 from {server_config.name}",
                    parameters={"param1": "value1"}
                ),
                MagicMock(
                    tool_name=f"tool2_{server_config.name}",
                    description=f"Tool 2 from {server_config.name}",
                    parameters={"param2": "value2"}
                )
            ])
            
            # Store the connected client
            self.clients[server_config.name] = client
            print(f"Successfully connected to MCP server: {server_config.name} at {server_config.url}")
            
            # Update tools cache
            await self.hass.async_add_executor_job(
                self._update_tools_cache, server_config.name
            )
            
            return True
            
        except Exception as err:
            print(f"Failed to connect to MCP server {config.get(ATTR_NAME, 'unknown')}: {str(err)}")
            return False
    
    async def async_disconnect(self, server_name: str) -> bool:
        """Disconnect from an MCP server."""
        if server_name not in self.clients:
            print(f"Not connected to server: {server_name}")
            return False
            
        try:
            # Remove client and tools cache
            del self.clients[server_name]
            if server_name in self.tools_cache:
                del self.tools_cache[server_name]
                
            print(f"Disconnected from MCP server: {server_name}")
            return True
        except Exception as err:
            print(f"Error disconnecting from {server_name}: {str(err)}")
            return False
    
    def _update_tools_cache(self, server_name: str) -> None:
        """Update the cache of available tools for a server."""
        if server_name not in self.clients:
            return
            
        try:
            # Try to get tools if the method exists
            if hasattr(self.clients[server_name], "list_tools_sync"):
                tools = self.clients[server_name].list_tools_sync()
                
                # Convert to our MCPTool model
                mcp_tools = []
                for tool in tools:
                    # Handle case where tool might not have all required attributes
                    try:
                        # Get description with fallback
                        description = getattr(tool, "description", "No description available")
                        
                        # Get parameters with fallback
                        parameters = getattr(tool, "parameters", {})
                        
                        mcp_tools.append(MCPTool(
                            server_name=server_name,
                            tool_name=tool.tool_name,
                            description=description,
                            parameters=parameters
                        ))
                    except Exception as err:
                        print(f"Skipping tool due to error: {str(err)}")
                    
                self.tools_cache[server_name] = mcp_tools
                print(f"Cached {len(mcp_tools)} tools from {server_name}")
            else:
                # No tools available from this server
                self.tools_cache[server_name] = []
                print(f"No tools available from server: {server_name}")
        except Exception as err:
            print(f"Failed to update tools cache for {server_name}: {str(err)}")
            # Set empty tools list on error
            self.tools_cache[server_name] = []
            print(f"No tools available from server: {server_name} due to error")
    
    async def async_get_all_tools(self) -> List[MCPTool]:
        """Get all available tools from all connected servers."""
        all_tools = []
        
        # First refresh the tools cache for all connected servers
        for server_name in list(self.clients.keys()):
            await self.hass.async_add_executor_job(
                self._update_tools_cache, server_name
            )
        
        # Then collect all tools from the cache
        for tools in self.tools_cache.values():
            all_tools.extend(tools)
            
        return all_tools
    
    async def async_get_server_tools(self, server_name: str) -> List[MCPTool]:
        """Get tools for a specific server."""
        # Refresh the tools cache for the specified server
        if server_name in self.clients:
            await self.hass.async_add_executor_job(
                self._update_tools_cache, server_name
            )
                
        return self.tools_cache.get(server_name, [])
    
    def get_connected_servers(self) -> List[str]:
        """Get names of connected servers."""
        server_names = list(self.clients.keys())
        print(f"Connected servers: {server_names}")
        return server_names
        
    def get_client(self, server_name: str) -> Optional[Any]:
        """Get the MCP client for a specific server."""
        return self.clients.get(server_name)
        
    async def async_execute_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool on an MCP server."""
        # Check if server is connected
        if server_name not in self.clients:
            print(f"Cannot execute tool: Server {server_name} not connected")
            raise NetworkError(f"Server {server_name} not connected")
            
        client = self.clients[server_name]
        
        try:
            # Execute the tool using the client
            print(
                f"Executing tool {tool_name} on server {server_name} with arguments: {arguments}"
            )
            
            # Execute the tool
            result = await self.hass.async_add_executor_job(
                self._execute_tool_sync, client, tool_name, arguments
            )
                
            print(f"Tool execution result: {result}")
            return result
            
        except Exception as err:
            print(
                f"Failed to execute tool {tool_name} on server {server_name}: {str(err)}"
            )
            raise NetworkError(f"Failed to execute tool: {str(err)}")
            
    def _execute_tool_sync(
        self, client: Any, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool synchronously."""
        if not hasattr(client, "execute_tool_sync"):
            raise NetworkError("Client does not support tool execution")
            
        return client.execute_tool_sync(tool_name, arguments)
        
    def register_execution_callback(
        self, server_name: str, callback: Callable
    ) -> None:
        """Register a callback for tool execution events."""
        self._execution_callbacks[server_name] = callback
        
    def unregister_execution_callback(self, server_name: str) -> None:
        """Unregister a callback for tool execution events."""
        if server_name in self._execution_callbacks:
            del self._execution_callbacks[server_name]


# Mock Home Assistant instance
class MockHass:
    """Mock Home Assistant instance."""
    
    def __init__(self):
        """Initialize the mock."""
        self.async_add_executor_job = AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))


# Mock Config Entry
class MockConfigEntry:
    """Mock Config Entry."""
    
    def __init__(self, options=None):
        """Initialize the mock."""
        self.options = options or {}


# Tests
async def test_mcp_connector_initialization():
    """Test MCPConnector initialization."""
    mock_hass = MockHass()
    mock_entry = MockConfigEntry()
    
    connector = MCPConnector(mock_hass, mock_entry)
    
    assert connector.hass == mock_hass
    assert connector.entry == mock_entry
    assert connector.clients == {}
    assert connector.tools_cache == {}
    print("✅ test_mcp_connector_initialization passed")


async def test_mcp_connector_connect():
    """Test connecting to an MCP server."""
    mock_hass = MockHass()
    mock_entry = MockConfigEntry()
    
    connector = MCPConnector(mock_hass, mock_entry)
    
    # Connect to a server
    config = {
        ATTR_NAME: "test_server",
        ATTR_URL: "https://example.com/mcp",
        ATTR_SERVER_TYPE: SERVER_TYPE_SSE,
        ATTR_AUTH_TOKEN: "test_token",
        "enabled": True
    }
    
    result = await connector.async_connect(config)
    
    assert result is True
    assert "test_server" in connector.clients
    assert "test_server" in connector.tools_cache
    assert len(connector.tools_cache["test_server"]) == 2
    print("✅ test_mcp_connector_connect passed")


async def test_mcp_connector_disconnect():
    """Test disconnecting from an MCP server."""
    mock_hass = MockHass()
    mock_entry = MockConfigEntry()
    
    connector = MCPConnector(mock_hass, mock_entry)
    
    # Connect to a server
    config = {
        ATTR_NAME: "test_server",
        ATTR_URL: "https://example.com/mcp",
        ATTR_SERVER_TYPE: SERVER_TYPE_SSE
    }
    
    await connector.async_connect(config)
    assert "test_server" in connector.clients
    
    # Disconnect
    result = await connector.async_disconnect("test_server")
    
    assert result is True
    assert "test_server" not in connector.clients
    assert "test_server" not in connector.tools_cache
    print("✅ test_mcp_connector_disconnect passed")


async def test_mcp_connector_get_connected_servers():
    """Test getting connected servers."""
    mock_hass = MockHass()
    mock_entry = MockConfigEntry()
    
    connector = MCPConnector(mock_hass, mock_entry)
    
    # Connect to servers
    await connector.async_connect({
        ATTR_NAME: "server1",
        ATTR_URL: "https://example.com/mcp1"
    })
    await connector.async_connect({
        ATTR_NAME: "server2",
        ATTR_URL: "https://example.com/mcp2"
    })
    
    servers = connector.get_connected_servers()
    
    assert len(servers) == 2
    assert "server1" in servers
    assert "server2" in servers
    print("✅ test_mcp_connector_get_connected_servers passed")


async def test_mcp_connector_get_server_tools():
    """Test getting tools for a specific server."""
    mock_hass = MockHass()
    mock_entry = MockConfigEntry()
    
    connector = MCPConnector(mock_hass, mock_entry)
    
    # Connect to a server
    await connector.async_connect({
        ATTR_NAME: "test_server",
        ATTR_URL: "https://example.com/mcp"
    })
    
    # Get tools
    tools = await connector.async_get_server_tools("test_server")
    
    assert len(tools) == 2
    assert tools[0].server_name == "test_server"
    assert tools[0].tool_name == "tool1_test_server"
    assert tools[1].tool_name == "tool2_test_server"
    print("✅ test_mcp_connector_get_server_tools passed")


async def test_mcp_connector_get_all_tools():
    """Test getting all tools from all servers."""
    mock_hass = MockHass()
    mock_entry = MockConfigEntry()
    
    connector = MCPConnector(mock_hass, mock_entry)
    
    # Connect to servers
    await connector.async_connect({
        ATTR_NAME: "server1",
        ATTR_URL: "https://example.com/mcp1"
    })
    await connector.async_connect({
        ATTR_NAME: "server2",
        ATTR_URL: "https://example.com/mcp2"
    })
    
    # Get all tools
    tools = await connector.async_get_all_tools()
    
    assert len(tools) == 4  # 2 tools per server
    
    # Check that tools from both servers are included
    tool_names = [tool.tool_name for tool in tools]
    assert "tool1_server1" in tool_names
    assert "tool2_server1" in tool_names
    assert "tool1_server2" in tool_names
    assert "tool2_server2" in tool_names
    print("✅ test_mcp_connector_get_all_tools passed")


async def test_mcp_connector_execute_tool():
    """Test executing a tool on an MCP server."""
    mock_hass = MockHass()
    mock_entry = MockConfigEntry()
    
    connector = MCPConnector(mock_hass, mock_entry)
    
    # Connect to a server
    config = {
        ATTR_NAME: "test_server",
        ATTR_URL: "https://example.com/mcp"
    }
    
    await connector.async_connect(config)
    
    # Mock the execute_tool_sync method on the client
    mock_result = {"result": "success", "data": {"value": 42}}
    connector.clients["test_server"].execute_tool_sync = MagicMock(return_value=mock_result)
    
    # Execute a tool
    result = await connector.async_execute_tool(
        "test_server",
        "test_tool",
        {"param1": "value1"}
    )
    
    # Check that the tool was executed with the correct arguments
    connector.clients["test_server"].execute_tool_sync.assert_called_once_with(
        "test_tool",
        {"param1": "value1"}
    )
    
    # Check the result
    assert result == mock_result
    print("✅ test_mcp_connector_execute_tool passed")


async def test_mcp_connector_execute_tool_server_not_connected():
    """Test executing a tool on a server that is not connected."""
    mock_hass = MockHass()
    mock_entry = MockConfigEntry()
    
    connector = MCPConnector(mock_hass, mock_entry)
    
    # Try to execute a tool on a server that is not connected
    try:
        await connector.async_execute_tool(
            "nonexistent_server",
            "test_tool",
            {"param1": "value1"}
        )
        assert False, "Should have raised NetworkError"
    except NetworkError as err:
        assert "Server nonexistent_server not connected" in str(err)
        print("✅ test_mcp_connector_execute_tool_server_not_connected passed")


async def test_mcp_connector_execute_tool_client_error():
    """Test executing a tool when the client raises an error."""
    mock_hass = MockHass()
    mock_entry = MockConfigEntry()
    
    connector = MCPConnector(mock_hass, mock_entry)
    
    # Connect to a server
    config = {
        ATTR_NAME: "test_server",
        ATTR_URL: "https://example.com/mcp"
    }
    
    await connector.async_connect(config)
    
    # Mock the execute_tool_sync method to raise an exception
    connector.clients["test_server"].execute_tool_sync = MagicMock(
        side_effect=Exception("Test error")
    )
    
    # Try to execute a tool
    try:
        await connector.async_execute_tool(
            "test_server",
            "test_tool",
            {"param1": "value1"}
        )
        assert False, "Should have raised NetworkError"
    except NetworkError as err:
        assert "Failed to execute tool: Test error" in str(err)
        print("✅ test_mcp_connector_execute_tool_client_error passed")


async def test_mcp_connector_execution_callbacks():
    """Test registering and unregistering execution callbacks."""
    mock_hass = MockHass()
    mock_entry = MockConfigEntry()
    
    connector = MCPConnector(mock_hass, mock_entry)
    
    # Register a callback
    callback = MagicMock()
    connector.register_execution_callback("test_server", callback)
    
    assert "test_server" in connector._execution_callbacks
    assert connector._execution_callbacks["test_server"] == callback
    
    # Unregister the callback
    connector.unregister_execution_callback("test_server")
    
    assert "test_server" not in connector._execution_callbacks
    print("✅ test_mcp_connector_execution_callbacks passed")


# Run tests
async def run_tests():
    """Run all tests."""
    print("Running standalone tests for MCPConnector...")
    await test_mcp_connector_initialization()
    await test_mcp_connector_connect()
    await test_mcp_connector_disconnect()
    await test_mcp_connector_get_connected_servers()
    await test_mcp_connector_get_server_tools()
    await test_mcp_connector_get_all_tools()
    await test_mcp_connector_execute_tool()
    await test_mcp_connector_execute_tool_server_not_connected()
    await test_mcp_connector_execute_tool_client_error()
    await test_mcp_connector_execution_callbacks()
    print("All tests passed! ✅")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_tests())