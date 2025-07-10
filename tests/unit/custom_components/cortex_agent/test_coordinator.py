"""Tests for the CortexAgent coordinator module."""
from unittest.mock import MagicMock, patch, AsyncMock
import json
from datetime import timedelta

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.cortex_agent.coordinator import (
    CortexAgentCoordinator,
    CortexAgentData,
)
from custom_components.cortex_agent.model_provider import (
    ModelProvider,
    ModelProviderType,
)
from custom_components.cortex_agent.mcp_connector import (
    MCPConnector,
    MCPServer,
    MCPServerType,
)
from custom_components.cortex_agent.memory_handler import (
    MemoryHandler,
)
from custom_components.cortex_agent.conversation_manager import (
    ConversationManager,
)
from custom_components.cortex_agent.tool_manager import (
    ToolManager,
)
from custom_components.cortex_agent.exceptions import (
    ModelProviderError,
    MCPConnectionError,
    MemoryError,
    ConversationError,
    ToolManagerError,
)


@pytest.fixture
def mock_hass():
    """Fixture to provide a mock hass instance."""
    return MagicMock()


@pytest.fixture
def mock_model_provider():
    """Fixture to provide a mock model provider."""
    provider = MagicMock(spec=ModelProvider)
    provider.provider_type = ModelProviderType.OPENAI
    provider.name = "OpenAI"
    provider.api_key = "test_api_key"
    provider.model = "gpt-4"
    provider.connected = False
    return provider


@pytest.fixture
def mock_mcp_connector():
    """Fixture to provide a mock MCP connector."""
    connector = MagicMock(spec=MCPConnector)
    connector.servers = {}
    return connector


@pytest.fixture
def mock_memory_handler():
    """Fixture to provide a mock memory handler."""
    handler = MagicMock(spec=MemoryHandler)
    handler.memories = {}
    return handler


@pytest.fixture
def mock_conversation_manager():
    """Fixture to provide a mock conversation manager."""
    manager = MagicMock(spec=ConversationManager)
    manager.history = []
    return manager


@pytest.fixture
def mock_tool_manager():
    """Fixture to provide a mock tool manager."""
    manager = MagicMock(spec=ToolManager)
    return manager


def test_cortex_agent_data_init():
    """Test the initialization of CortexAgentData."""
    # Create CortexAgentData
    data = CortexAgentData(
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
    
    # Check the data properties
    assert data.model_provider_connected is True
    assert data.model_provider_name == "OpenAI"
    assert data.model_provider_model == "gpt-4"
    assert len(data.mcp_servers) == 1
    assert data.mcp_servers[0]["server_id"] == "server_123"
    assert data.mcp_servers[0]["name"] == "Test Server"
    assert data.mcp_servers[0]["server_type"] == "remote"
    assert data.mcp_servers[0]["connected"] is True
    assert data.memory_count == 10
    assert data.conversation_history_length == 5
    assert data.available_tools == ["tool1", "tool2"]


def test_cortex_agent_coordinator_init(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the initialization of CortexAgentCoordinator."""
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
        update_interval=timedelta(seconds=30),
    )
    
    # Check the coordinator properties
    assert coordinator.hass == mock_hass
    assert coordinator.model_provider == mock_model_provider
    assert coordinator.mcp_connector == mock_mcp_connector
    assert coordinator.memory_handler == mock_memory_handler
    assert coordinator.conversation_manager == mock_conversation_manager
    assert coordinator.tool_manager == mock_tool_manager
    assert coordinator.agent_id == "test_agent"
    assert coordinator.update_interval == timedelta(seconds=30)
    assert isinstance(coordinator, DataUpdateCoordinator)


@patch("custom_components.cortex_agent.coordinator.ModelProvider")
@patch("custom_components.cortex_agent.coordinator.MCPConnector")
@patch("custom_components.cortex_agent.coordinator.MemoryHandler")
@patch("custom_components.cortex_agent.coordinator.ConversationManager")
@patch("custom_components.cortex_agent.coordinator.ToolManager")
def test_cortex_agent_coordinator_init_with_defaults(
    mock_tool_manager_class,
    mock_conversation_manager_class,
    mock_memory_handler_class,
    mock_mcp_connector_class,
    mock_model_provider_class,
    mock_hass,
):
    """Test the initialization of CortexAgentCoordinator with default components."""
    # Set up the mock classes
    mock_model_provider = MagicMock(spec=ModelProvider)
    mock_model_provider_class.return_value = mock_model_provider
    
    mock_mcp_connector = MagicMock(spec=MCPConnector)
    mock_mcp_connector_class.return_value = mock_mcp_connector
    
    mock_memory_handler = MagicMock(spec=MemoryHandler)
    mock_memory_handler_class.return_value = mock_memory_handler
    
    mock_conversation_manager = MagicMock(spec=ConversationManager)
    mock_conversation_manager_class.return_value = mock_conversation_manager
    
    mock_tool_manager = MagicMock(spec=ToolManager)
    mock_tool_manager_class.return_value = mock_tool_manager
    
    # Create a coordinator without providing components
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        agent_id="test_agent",
    )
    
    # Check that the components were created
    mock_model_provider_class.assert_called_once()
    mock_mcp_connector_class.assert_called_once_with(mock_hass)
    mock_memory_handler_class.assert_called_once_with(mock_hass)
    mock_conversation_manager_class.assert_called_once_with(agent_id="test_agent")
    mock_tool_manager_class.assert_called_once_with(mock_hass)
    
    # Check the coordinator properties
    assert coordinator.hass == mock_hass
    assert coordinator.model_provider == mock_model_provider
    assert coordinator.mcp_connector == mock_mcp_connector
    assert coordinator.memory_handler == mock_memory_handler
    assert coordinator.conversation_manager == mock_conversation_manager
    assert coordinator.tool_manager == mock_tool_manager
    assert coordinator.agent_id == "test_agent"
    assert coordinator.update_interval == timedelta(seconds=60)


async def test_cortex_agent_coordinator_async_update_data(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the _async_update_data method of CortexAgentCoordinator."""
    # Set up the mock model provider
    mock_model_provider.connected = True
    mock_model_provider.name = "OpenAI"
    mock_model_provider.model = "gpt-4"
    
    # Set up the mock MCP connector
    mock_server = MagicMock(spec=MCPServer)
    mock_server.server_id = "server_123"
    mock_server.name = "Test Server"
    mock_server.server_type = MCPServerType.REMOTE
    mock_server.connected = True
    mock_server.to_dict.return_value = {
        "server_id": "server_123",
        "name": "Test Server",
        "server_type": "remote",
        "connected": True,
    }
    mock_mcp_connector.servers = {"server_123": mock_server}
    mock_mcp_connector.list_servers.return_value = [mock_server.to_dict()]
    
    # Set up the mock memory handler
    mock_memory_handler.list_memories.return_value = [
        {"memory_id": "memory_123", "content": "Test memory"},
        {"memory_id": "memory_456", "content": "Another test memory"},
    ]
    
    # Set up the mock conversation manager
    mock_conversation_manager.history = [MagicMock(), MagicMock(), MagicMock()]
    
    # Set up the mock tool manager
    mock_tool_manager.list_tools.return_value = [
        {"name": "tool1", "description": "Tool 1"},
        {"name": "tool2", "description": "Tool 2"},
    ]
    
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Call _async_update_data
    data = await coordinator._async_update_data()
    
    # Check the data
    assert data.model_provider_connected is True
    assert data.model_provider_name == "OpenAI"
    assert data.model_provider_model == "gpt-4"
    assert len(data.mcp_servers) == 1
    assert data.mcp_servers[0]["server_id"] == "server_123"
    assert data.mcp_servers[0]["name"] == "Test Server"
    assert data.mcp_servers[0]["server_type"] == "remote"
    assert data.mcp_servers[0]["connected"] is True
    assert data.memory_count == 2
    assert data.conversation_history_length == 3
    assert len(data.available_tools) == 2
    assert "tool1" in data.available_tools
    assert "tool2" in data.available_tools


async def test_cortex_agent_coordinator_async_update_data_model_provider_error(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the _async_update_data method when the model provider raises an error."""
    # Set up the mock model provider to raise an error
    mock_model_provider.connected = False
    mock_model_provider.name = "OpenAI"
    mock_model_provider.model = "gpt-4"
    
    # Set up the mock MCP connector
    mock_mcp_connector.list_servers.return_value = []
    
    # Set up the mock memory handler
    mock_memory_handler.list_memories.return_value = []
    
    # Set up the mock conversation manager
    mock_conversation_manager.history = []
    
    # Set up the mock tool manager
    mock_tool_manager.list_tools.return_value = []
    
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Call _async_update_data
    data = await coordinator._async_update_data()
    
    # Check the data
    assert data.model_provider_connected is False
    assert data.model_provider_name == "OpenAI"
    assert data.model_provider_model == "gpt-4"
    assert data.mcp_servers == []
    assert data.memory_count == 0
    assert data.conversation_history_length == 0
    assert data.available_tools == []


async def test_cortex_agent_coordinator_async_update_data_mcp_connector_error(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the _async_update_data method when the MCP connector raises an error."""
    # Set up the mock model provider
    mock_model_provider.connected = True
    mock_model_provider.name = "OpenAI"
    mock_model_provider.model = "gpt-4"
    
    # Set up the mock MCP connector to raise an error
    mock_mcp_connector.list_servers.side_effect = MCPConnectionError("Connection error")
    
    # Set up the mock memory handler
    mock_memory_handler.list_memories.return_value = []
    
    # Set up the mock conversation manager
    mock_conversation_manager.history = []
    
    # Set up the mock tool manager
    mock_tool_manager.list_tools.return_value = []
    
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Call _async_update_data
    data = await coordinator._async_update_data()
    
    # Check the data
    assert data.model_provider_connected is True
    assert data.model_provider_name == "OpenAI"
    assert data.model_provider_model == "gpt-4"
    assert data.mcp_servers == []
    assert data.memory_count == 0
    assert data.conversation_history_length == 0
    assert data.available_tools == []


async def test_cortex_agent_coordinator_async_update_data_memory_handler_error(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the _async_update_data method when the memory handler raises an error."""
    # Set up the mock model provider
    mock_model_provider.connected = True
    mock_model_provider.name = "OpenAI"
    mock_model_provider.model = "gpt-4"
    
    # Set up the mock MCP connector
    mock_mcp_connector.list_servers.return_value = []
    
    # Set up the mock memory handler to raise an error
    mock_memory_handler.list_memories.side_effect = MemoryError("Memory error")
    
    # Set up the mock conversation manager
    mock_conversation_manager.history = []
    
    # Set up the mock tool manager
    mock_tool_manager.list_tools.return_value = []
    
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Call _async_update_data
    data = await coordinator._async_update_data()
    
    # Check the data
    assert data.model_provider_connected is True
    assert data.model_provider_name == "OpenAI"
    assert data.model_provider_model == "gpt-4"
    assert data.mcp_servers == []
    assert data.memory_count == 0
    assert data.conversation_history_length == 0
    assert data.available_tools == []


async def test_cortex_agent_coordinator_async_update_data_tool_manager_error(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the _async_update_data method when the tool manager raises an error."""
    # Set up the mock model provider
    mock_model_provider.connected = True
    mock_model_provider.name = "OpenAI"
    mock_model_provider.model = "gpt-4"
    
    # Set up the mock MCP connector
    mock_mcp_connector.list_servers.return_value = []
    
    # Set up the mock memory handler
    mock_memory_handler.list_memories.return_value = []
    
    # Set up the mock conversation manager
    mock_conversation_manager.history = []
    
    # Set up the mock tool manager to raise an error
    mock_tool_manager.list_tools.side_effect = ToolManagerError("Tool manager error")
    
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Call _async_update_data
    data = await coordinator._async_update_data()
    
    # Check the data
    assert data.model_provider_connected is True
    assert data.model_provider_name == "OpenAI"
    assert data.model_provider_model == "gpt-4"
    assert data.mcp_servers == []
    assert data.memory_count == 0
    assert data.conversation_history_length == 0
    assert data.available_tools == []


async def test_cortex_agent_coordinator_connect_model_provider(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the connect_model_provider method of CortexAgentCoordinator."""
    # Set up the mock model provider
    mock_model_provider.connect = AsyncMock()
    
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Call connect_model_provider
    await coordinator.connect_model_provider()
    
    # Check that connect was called on the model provider
    mock_model_provider.connect.assert_called_once()


async def test_cortex_agent_coordinator_connect_model_provider_error(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the connect_model_provider method when the model provider raises an error."""
    # Set up the mock model provider to raise an error
    mock_model_provider.connect = AsyncMock(side_effect=ModelProviderError("Connection error"))
    
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Call connect_model_provider
    with pytest.raises(ModelProviderError):
        await coordinator.connect_model_provider()
    
    # Check that connect was called on the model provider
    mock_model_provider.connect.assert_called_once()


async def test_cortex_agent_coordinator_disconnect_model_provider(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the disconnect_model_provider method of CortexAgentCoordinator."""
    # Set up the mock model provider
    mock_model_provider.disconnect = AsyncMock()
    
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Call disconnect_model_provider
    await coordinator.disconnect_model_provider()
    
    # Check that disconnect was called on the model provider
    mock_model_provider.disconnect.assert_called_once()


async def test_cortex_agent_coordinator_connect_mcp_server(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the connect_mcp_server method of CortexAgentCoordinator."""
    # Set up the mock MCP connector
    mock_mcp_connector.connect_server = AsyncMock()
    
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Call connect_mcp_server
    await coordinator.connect_mcp_server("server_123")
    
    # Check that connect_server was called on the MCP connector
    mock_mcp_connector.connect_server.assert_called_once_with("server_123")


async def test_cortex_agent_coordinator_disconnect_mcp_server(
    mock_hass,
    mock_model_provider,
    mock_mcp_connector,
    mock_memory_handler,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the disconnect_mcp_server method of CortexAgentCoordinator."""
    # Set up the mock MCP connector
    mock_mcp_connector.disconnect_server = AsyncMock()
    
    # Create a coordinator
    coordinator = CortexAgentCoordinator(
        hass=mock_hass,
        model_provider=mock_model_provider,
        mcp_connector=mock_mcp_connector,
        memory_handler=mock_memory_handler,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Call disconnect_mcp_server
    await coordinator.disconnect_mcp_server("server_123")
    
    # Check that disconnect_server was called on the MCP connector
    mock_mcp_connector.disconnect_server.assert_called_once_with("server_123")