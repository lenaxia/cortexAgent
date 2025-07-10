"""Tests for the conversation module."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components import conversation
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent

from custom_components.cortex_agent.conversation import CortexAgent
from custom_components.cortex_agent.models import Message, MessageRole
from custom_components.cortex_agent.conversation_strategy import (
    DefaultConversationStrategy,
    StrandsConversationStrategy,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MagicMock()


@pytest.fixture
def mock_entry():
    """Mock config entry."""
    entry = MagicMock()
    entry.options = {
        "system_prompt": "You are a helpful assistant.",
        "max_tokens": 100,
        "temperature": 0.7,
        "use_strands_agent": False,
    }
    return entry


@pytest.fixture
def mock_model_provider():
    """Mock model provider."""
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={"content": "This is a test response"}
    )
    return provider


@pytest.fixture
def mock_conversation_manager():
    """Mock conversation manager."""
    manager = MagicMock()
    manager.create_conversation = MagicMock(return_value="test_conversation")
    manager.add_message = MagicMock()
    manager.get_conversation = MagicMock(
        return_value=[
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            Message(role=MessageRole.USER, content="Hello, how are you?"),
        ]
    )
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry."""
    registry = MagicMock()
    registry.get_all_tools = MagicMock(return_value=[])
    return registry


@pytest.fixture
def mock_memory_handler():
    """Mock memory handler."""
    handler = MagicMock()
    handler.async_save = AsyncMock()
    return handler


@pytest.fixture
def mock_mcp_connector():
    """Mock MCP connector."""
    connector = MagicMock()
    connector.async_get_all_tools = AsyncMock(return_value=[])
    return connector


class TestCortexAgent:
    """Tests for CortexAgent."""

    async def test_init_default_strategy(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        mock_conversation_manager,
        mock_tool_registry,
    ):
        """Test initialization with default strategy."""
        agent = CortexAgent(
            hass=mock_hass,
            entry=mock_entry,
            model_provider=mock_model_provider,
            conversation_manager=mock_conversation_manager,
            tool_registry=mock_tool_registry,
        )

        assert isinstance(agent.strategy, DefaultConversationStrategy)

    async def test_init_strands_strategy(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        mock_conversation_manager,
        mock_tool_registry,
    ):
        """Test initialization with Strands strategy."""
        mock_entry.options["use_strands_agent"] = True
        
        agent = CortexAgent(
            hass=mock_hass,
            entry=mock_entry,
            model_provider=mock_model_provider,
            conversation_manager=mock_conversation_manager,
            tool_registry=mock_tool_registry,
        )

        assert isinstance(agent.strategy, StrandsConversationStrategy)

    async def test_async_process(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        mock_conversation_manager,
        mock_tool_registry,
    ):
        """Test async_process method."""
        agent = CortexAgent(
            hass=mock_hass,
            entry=mock_entry,
            model_provider=mock_model_provider,
            conversation_manager=mock_conversation_manager,
            tool_registry=mock_tool_registry,
        )
        
        # Mock the strategy's generate_response method
        agent.strategy.generate_response = AsyncMock(return_value="This is a test response")
        
        # Create a conversation input
        context = MagicMock()
        user_input = conversation.ConversationInput(
            text="Hello, how are you?",
            conversation_id=None,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Process the input
        result = await agent.async_process(user_input)
        
        # Check that the conversation manager was called correctly
        mock_conversation_manager.create_conversation.assert_called_once()
        mock_conversation_manager.add_message.assert_called()
        mock_conversation_manager.get_conversation.assert_called()
        mock_conversation_manager.async_save.assert_called_once()
        
        # Check that the strategy was called correctly
        agent.strategy.generate_response.assert_called_once()
        
        # Check the result
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "This is a test response"
        assert result.conversation_id == "test_conversation"

    async def test_async_process_error(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        mock_conversation_manager,
        mock_tool_registry,
    ):
        """Test async_process method with error."""
        agent = CortexAgent(
            hass=mock_hass,
            entry=mock_entry,
            model_provider=mock_model_provider,
            conversation_manager=mock_conversation_manager,
            tool_registry=mock_tool_registry,
        )
        
        # Mock the strategy's generate_response method to raise an exception
        agent.strategy.generate_response = AsyncMock(side_effect=Exception("Test error"))
        
        # Create a conversation input
        context = MagicMock()
        user_input = conversation.ConversationInput(
            text="Hello, how are you?",
            conversation_id=None,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Process the input
        result = await agent.async_process(user_input)
        
        # Check the result
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "I'm sorry, I encountered an error while processing your request."
        assert result.response.error_code == intent.IntentResponseErrorCode.FAILED_TO_HANDLE

    async def test_async_unload(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        mock_conversation_manager,
        mock_tool_registry,
        mock_memory_handler,
    ):
        """Test async_unload method."""
        agent = CortexAgent(
            hass=mock_hass,
            entry=mock_entry,
            model_provider=mock_model_provider,
            conversation_manager=mock_conversation_manager,
            tool_registry=mock_tool_registry,
            memory_handler=mock_memory_handler,
        )
        
        # Mock the strategy's reload method
        agent.strategy.reload = AsyncMock()
        
        # Unload the agent
        await agent.async_unload()
        
        # Check that the conversation manager and memory handler were called correctly
        mock_conversation_manager.async_save.assert_called_once()
        mock_memory_handler.async_save.assert_called_once()
        
        # Check that the strategy was reloaded
        agent.strategy.reload.assert_called_once()