"""Tests for the WebSocket API."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from homeassistant.components.websocket_api.const import TYPE_RESULT
from homeassistant.core import HomeAssistant

from custom_components.cortex_agent.websocket_api import (
    async_register_websocket_commands,
    ws_get_conversations,
    ws_get_conversation_history,
    ws_clear_conversation,
    ws_get_tools,
    ws_get_mcp_servers,
    ws_get_agent_status,
    ws_subscribe_events,
)
from custom_components.cortex_agent.const import DOMAIN


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_connection():
    """Mock WebSocket connection."""
    connection = MagicMock()
    connection.send_result = AsyncMock()
    connection.send_error = AsyncMock()
    connection.subscriptions = {}
    return connection


@pytest.fixture
def mock_agent():
    """Mock agent."""
    agent = MagicMock()
    agent.conversation_manager = MagicMock()
    agent.tool_registry = MagicMock()
    agent.memory_handler = MagicMock()
    agent.mcp_connector = MagicMock()
    agent.model_provider = MagicMock()
    return agent


async def test_register_websocket_commands(mock_hass):
    """Test registering WebSocket commands."""
    with patch("homeassistant.components.websocket_api.async_register_command") as mock_register:
        async_register_websocket_commands(mock_hass)
        assert mock_register.call_count == 7


async def test_ws_get_conversations(mock_hass, mock_connection, mock_agent):
    """Test getting conversations."""
    entry_id = "test_entry_id"
    mock_hass.data[DOMAIN] = {entry_id: {"agent": mock_agent}}
    
    # Mock conversation manager
    mock_agent.conversation_manager.get_conversation_ids.return_value = ["conv1", "conv2"]
    mock_agent.conversation_manager.get_conversation.return_value = [
        MagicMock(content="Hello"),
        MagicMock(content="Hi there"),
    ]
    mock_agent.conversation_manager.get_conversation_metadata.return_value = {
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:01:00",
    }
    
    # Call the WebSocket command
    await ws_get_conversations(
        mock_hass,
        mock_connection,
        {"id": 1, "type": "cortex_agent/get_conversations", "entry_id": entry_id},
    )
    
    # Check that the result was sent
    mock_connection.send_result.assert_called_once()
    result = mock_connection.send_result.call_args[0][1]
    assert "conversations" in result
    assert len(result["conversations"]) == 2


async def test_ws_get_conversations_agent_not_found(mock_hass, mock_connection):
    """Test getting conversations when agent is not found."""
    # Call the WebSocket command with an invalid entry_id
    await ws_get_conversations(
        mock_hass,
        mock_connection,
        {"id": 1, "type": "cortex_agent/get_conversations", "entry_id": "invalid_id"},
    )
    
    # Check that an error was sent
    mock_connection.send_error.assert_called_once()


async def test_ws_get_conversation_history(mock_hass, mock_connection, mock_agent):
    """Test getting conversation history."""
    entry_id = "test_entry_id"
    conversation_id = "test_conversation_id"
    mock_hass.data[DOMAIN] = {entry_id: {"agent": mock_agent}}
    
    # Mock conversation manager
    mock_agent.conversation_manager.get_conversation.return_value = [
        MagicMock(role="user", content="Hello", timestamp="2023-01-01T00:00:00"),
        MagicMock(role="assistant", content="Hi there", timestamp="2023-01-01T00:00:01"),
    ]
    mock_agent.conversation_manager.get_conversation_metadata.return_value = {
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:01:00",
    }
    
    # Call the WebSocket command
    await ws_get_conversation_history(
        mock_hass,
        mock_connection,
        {
            "id": 1,
            "type": "cortex_agent/get_conversation_history",
            "entry_id": entry_id,
            "conversation_id": conversation_id,
        },
    )
    
    # Check that the result was sent
    mock_connection.send_result.assert_called_once()
    result = mock_connection.send_result.call_args[0][1]
    assert "messages" in result
    assert len(result["messages"]) == 2
    assert result["conversation_id"] == conversation_id


async def test_ws_clear_conversation(mock_hass, mock_connection, mock_agent):
    """Test clearing a conversation."""
    entry_id = "test_entry_id"
    conversation_id = "test_conversation_id"
    mock_hass.data[DOMAIN] = {entry_id: {"agent": mock_agent}}
    
    # Mock conversation manager
    mock_agent.conversation_manager.clear_conversation = AsyncMock()
    mock_agent.conversation_manager.async_save = AsyncMock()
    
    # Call the WebSocket command
    await ws_clear_conversation(
        mock_hass,
        mock_connection,
        {
            "id": 1,
            "type": "cortex_agent/clear_conversation",
            "entry_id": entry_id,
            "conversation_id": conversation_id,
        },
    )
    
    # Check that the conversation was cleared
    mock_agent.conversation_manager.clear_conversation.assert_called_once_with(conversation_id)
    mock_agent.conversation_manager.async_save.assert_called_once()
    
    # Check that the result was sent
    mock_connection.send_result.assert_called_once()
    result = mock_connection.send_result.call_args[0][1]
    assert result["success"] is True


async def test_ws_clear_all_conversations(mock_hass, mock_connection, mock_agent):
    """Test clearing all conversations."""
    entry_id = "test_entry_id"
    mock_hass.data[DOMAIN] = {entry_id: {"agent": mock_agent}}
    
    # Mock conversation manager
    mock_agent.conversation_manager.clear_all_conversations = AsyncMock()
    mock_agent.conversation_manager.async_save = AsyncMock()
    
    # Call the WebSocket command
    await ws_clear_conversation(
        mock_hass,
        mock_connection,
        {
            "id": 1,
            "type": "cortex_agent/clear_conversation",
            "entry_id": entry_id,
        },
    )
    
    # Check that all conversations were cleared
    mock_agent.conversation_manager.clear_all_conversations.assert_called_once()
    mock_agent.conversation_manager.async_save.assert_called_once()
    
    # Check that the result was sent
    mock_connection.send_result.assert_called_once()
    result = mock_connection.send_result.call_args[0][1]
    assert result["success"] is True


async def test_ws_get_tools(mock_hass, mock_connection, mock_agent):
    """Test getting tools."""
    entry_id = "test_entry_id"
    mock_hass.data[DOMAIN] = {entry_id: {"agent": mock_agent}}
    
    # Mock tool registry
    mock_agent.tool_registry.get_all_tools.return_value = [
        {
            "name": "tool1",
            "description": "Tool 1",
            "parameters": {"param1": {"type": "string", "description": "Parameter 1"}},
            "category": "category1",
        },
        {
            "name": "tool2",
            "description": "Tool 2",
            "parameters": {"param2": {"type": "number", "description": "Parameter 2"}},
            "category": "category2",
        },
    ]
    
    # Call the WebSocket command
    await ws_get_tools(
        mock_hass,
        mock_connection,
        {"id": 1, "type": "cortex_agent/get_tools", "entry_id": entry_id},
    )
    
    # Check that the result was sent
    mock_connection.send_result.assert_called_once()
    result = mock_connection.send_result.call_args[0][1]
    assert "tools" in result
    assert len(result["tools"]) == 2


async def test_ws_get_tools_by_category(mock_hass, mock_connection, mock_agent):
    """Test getting tools by category."""
    entry_id = "test_entry_id"
    category = "category1"
    mock_hass.data[DOMAIN] = {entry_id: {"agent": mock_agent}}
    
    # Mock tool registry
    mock_agent.tool_registry.get_tools_by_category.return_value = [
        {
            "name": "tool1",
            "description": "Tool 1",
            "parameters": {"param1": {"type": "string", "description": "Parameter 1"}},
            "category": "category1",
        },
    ]
    
    # Call the WebSocket command
    await ws_get_tools(
        mock_hass,
        mock_connection,
        {
            "id": 1,
            "type": "cortex_agent/get_tools",
            "entry_id": entry_id,
            "category": category,
        },
    )
    
    # Check that the result was sent
    mock_connection.send_result.assert_called_once()
    result = mock_connection.send_result.call_args[0][1]
    assert "tools" in result
    assert len(result["tools"]) == 1
    assert result["tools"][0]["category"] == category


async def test_ws_get_mcp_servers(mock_hass, mock_connection, mock_agent):
    """Test getting MCP servers."""
    entry_id = "test_entry_id"
    mock_hass.data[DOMAIN] = {entry_id: {"agent": mock_agent, "mcp_connector": mock_agent.mcp_connector}}
    
    # Mock MCP connector
    mock_agent.mcp_connector.get_connected_servers.return_value = ["server1", "server2"]
    mock_agent.mcp_connector.async_get_server_tools = AsyncMock()
    mock_agent.mcp_connector.async_get_server_tools.side_effect = [
        [
            MagicMock(
                tool_name="tool1",
                description="Tool 1",
                parameters={"param1": {"type": "string", "description": "Parameter 1"}},
            ),
        ],
        [
            MagicMock(
                tool_name="tool2",
                description="Tool 2",
                parameters={"param2": {"type": "number", "description": "Parameter 2"}},
            ),
        ],
    ]
    
    # Call the WebSocket command
    await ws_get_mcp_servers(
        mock_hass,
        mock_connection,
        {"id": 1, "type": "cortex_agent/get_mcp_servers", "entry_id": entry_id},
    )
    
    # Check that the result was sent
    mock_connection.send_result.assert_called_once()
    result = mock_connection.send_result.call_args[0][1]
    assert "servers" in result
    assert len(result["servers"]) == 2


async def test_ws_get_agent_status(mock_hass, mock_connection, mock_agent):
    """Test getting agent status."""
    entry_id = "test_entry_id"
    mock_hass.data[DOMAIN] = {entry_id: {"agent": mock_agent}}
    
    # Mock agent components
    mock_agent.entry.data = {"model_id": "test_model"}
    mock_agent.conversation_manager.get_conversation_ids.return_value = ["conv1", "conv2"]
    mock_agent.tool_registry.get_all_tools.return_value = ["tool1", "tool2", "tool3"]
    mock_agent.memory_handler.get_all_memories = AsyncMock(return_value=["mem1", "mem2"])
    mock_agent.mcp_connector.get_connected_servers.return_value = ["server1"]
    
    # Call the WebSocket command
    await ws_get_agent_status(
        mock_hass,
        mock_connection,
        {"id": 1, "type": "cortex_agent/get_agent_status", "entry_id": entry_id},
    )
    
    # Check that the result was sent
    mock_connection.send_result.assert_called_once()
    result = mock_connection.send_result.call_args[0][1]
    assert "status" in result
    assert result["status"]["model_id"] == "test_model"
    assert result["status"]["conversation_count"] == 2
    assert result["status"]["tool_count"] == 3
    assert result["status"]["memory_count"] == 2
    assert result["status"]["mcp_server_count"] == 1


async def test_ws_subscribe_events(mock_hass, mock_connection):
    """Test subscribing to events."""
    entry_id = "test_entry_id"
    mock_hass.data[DOMAIN] = {entry_id: {}}
    
    # Mock async_dispatcher_connect
    with patch("homeassistant.helpers.dispatcher.async_dispatcher_connect", return_value=lambda: None) as mock_connect:
        # Call the WebSocket command
        ws_subscribe_events(
            mock_hass,
            mock_connection,
            {"id": 1, "type": "cortex_agent/subscribe_events", "entry_id": entry_id},
        )
        
        # Check that the subscription was registered
        assert 1 in mock_connection.subscriptions
        assert callable(mock_connection.subscriptions[1])
        assert mock_connect.call_count == 3
        
        # Check that the result was sent
        mock_connection.send_result.assert_called_once_with(1)