"""End-to-end tests for the conversation module."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components import conversation
from homeassistant.core import HomeAssistant, Context
from homeassistant.helpers import intent

from custom_components.cortex_agent.conversation import CortexAgent
from custom_components.cortex_agent.models import Message, MessageRole
from custom_components.cortex_agent.conversation_manager import ConversationManager
from custom_components.cortex_agent.tool_registry import ToolRegistry
from custom_components.cortex_agent.memory_handler import MemoryHandler
from custom_components.cortex_agent.mcp_connector import MCPConnector


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    return hass


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
    """Mock model provider with realistic responses."""
    provider = MagicMock()
    
    # Define different responses based on input
    async def generate_response_mock(messages, tools=None, max_tokens=None, temperature=None):
        user_message = next((m["content"] for m in messages if m["role"] == "user"), "")
        
        if "weather" in user_message.lower():
            if tools:
                return {
                    "tool_calls": [
                        {
                            "name": "get_weather",
                            "arguments": {"location": "New York"}
                        }
                    ]
                }
            else:
                return {"content": "I can check the weather for you, but I need the weather tool."}
        
        elif "memory" in user_message.lower():
            if tools:
                return {
                    "tool_calls": [
                        {
                            "name": "retrieve_memory",
                            "arguments": {"query": "weather", "limit": 3}
                        }
                    ]
                }
            else:
                return {"content": "I can check your memories, but I need memory access."}
        
        elif "hello" in user_message.lower():
            return {"content": "Hello! How can I help you today?"}
        
        else:
            return {"content": "I'm not sure how to respond to that."}
    
    provider.generate_response = AsyncMock(side_effect=generate_response_mock)
    return provider


@pytest.fixture
def conversation_manager():
    """Create a real conversation manager."""
    return ConversationManager(MagicMock(), "test_entry_id")


@pytest.fixture
def tool_registry(mock_hass):
    """Create a real tool registry with mock tools."""
    registry = ToolRegistry(mock_hass)
    
    # Add a weather tool
    async def get_weather(hass, args):
        location = args.get("location", "Unknown")
        return {"temperature": 72, "condition": "Sunny", "location": location}
    
    # Create tool metadata
    from custom_components.cortex_agent.models import ToolMetadata
    
    metadata = ToolMetadata(
        name="get_weather",
        description="Get the current weather",
        parameters={
            "location": {
                "type": "string",
                "description": "The location to get weather for"
            }
        }
    )
    
    registry.register_tool("get_weather", get_weather, metadata)
    
    return registry


@pytest.fixture
def memory_handler():
    """Create a mock memory handler."""
    handler = MagicMock()
    handler.store_memory = AsyncMock(return_value={"memory_id": "test_id"})
    handler.retrieve_memories = AsyncMock(
        return_value={"memories": [{"content": "It was sunny yesterday."}]}
    )
    return handler


@pytest.fixture
def mcp_connector():
    """Create a mock MCP connector."""
    connector = MagicMock()
    connector.async_get_all_tools = AsyncMock(return_value=[])
    connector.async_execute_tool = AsyncMock(return_value={"result": "success"})
    return connector


class TestConversationE2E:
    """End-to-end tests for conversation."""

    async def test_simple_conversation(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        conversation_manager,
        tool_registry,
    ):
        """Test a simple conversation without tools."""
        # Mock the register_built_in_tools function to avoid issues with register_tool
        with patch("custom_components.cortex_agent.tools.register_built_in_tools", return_value=None):
            agent = CortexAgent(
                hass=mock_hass,
                entry=mock_entry,
                model_provider=mock_model_provider,
                conversation_manager=conversation_manager,
                tool_registry=tool_registry,
            )
        
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
        assert result.response.speech["plain"]["speech"] == "Hello! How can I help you today?"
        
        # Check that the conversation was stored
        conversation_id = result.conversation_id
        assert conversation_id is not None
        
        # Check that the conversation history has two messages
        history = conversation_manager.get_conversation(conversation_id)
        assert len(history) == 2
        assert history[0].role == MessageRole.USER
        assert history[0].content == "Hello, how are you?"
        assert history[1].role == MessageRole.ASSISTANT
        assert history[1].content == "Hello! How can I help you today?"

    async def test_conversation_with_tool_use(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        conversation_manager,
        tool_registry,
    ):
        """Test a conversation with tool use."""
        # Mock the register_built_in_tools function to avoid issues with register_tool
        with patch("custom_components.cortex_agent.tools.register_built_in_tools", return_value=None):
            agent = CortexAgent(
                hass=mock_hass,
                entry=mock_entry,
                model_provider=mock_model_provider,
                conversation_manager=conversation_manager,
                tool_registry=tool_registry,
            )
        
        # Create a conversation input
        context = MagicMock()
        user_input = conversation.ConversationInput(
            text="What's the weather like?",
            conversation_id=None,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Mock the second response after tool execution
        mock_model_provider.generate_response.side_effect = None
        mock_model_provider.generate_response.return_value = {
            "content": "The weather in New York is 72°F and sunny."
        }
        
        # Process the input
        result = await agent.async_process(user_input)
        
        # Check the result
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "The weather in New York is 72°F and sunny."
        
        # Check that the model provider was called twice
        assert mock_model_provider.generate_response.call_count == 2
        
        # Check that the conversation history has two messages
        conversation_id = result.conversation_id
        history = conversation_manager.get_conversation(conversation_id)
        assert len(history) == 2
        assert history[0].role == MessageRole.USER
        assert history[0].content == "What's the weather like?"
        assert history[1].role == MessageRole.ASSISTANT
        assert history[1].content == "The weather in New York is 72°F and sunny."

    async def test_conversation_with_memory(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        conversation_manager,
        tool_registry,
        memory_handler,
    ):
        """Test a conversation with memory use."""
        # Mock the register_built_in_tools function to avoid issues with register_tool
        with patch("custom_components.cortex_agent.tools.register_built_in_tools", return_value=None):
            agent = CortexAgent(
                hass=mock_hass,
                entry=mock_entry,
                model_provider=mock_model_provider,
                conversation_manager=conversation_manager,
                tool_registry=tool_registry,
                memory_handler=memory_handler,
            )
        
        # Register memory tools
        await agent._register_memory_tools()
        
        # Create a conversation input
        context = MagicMock()
        user_input = conversation.ConversationInput(
            text="What do you remember about the weather?",
            conversation_id=None,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Mock the second response after memory retrieval
        mock_model_provider.generate_response.side_effect = None
        mock_model_provider.generate_response.return_value = {
            "content": "I remember that it was sunny yesterday."
        }
        
        # Process the input
        result = await agent.async_process(user_input)
        
        # Check the result
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "I remember that it was sunny yesterday."
        
        # Check that the memory handler was called
        memory_handler.retrieve_memories.assert_called_once()
        
        # Check that the conversation history has two messages
        conversation_id = result.conversation_id
        history = conversation_manager.get_conversation(conversation_id)
        assert len(history) == 2
        assert history[0].role == MessageRole.USER
        assert history[0].content == "What do you remember about the weather?"
        assert history[1].role == MessageRole.ASSISTANT
        assert history[1].content == "I remember that it was sunny yesterday."

    async def test_conversation_with_strands_agent(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        conversation_manager,
        tool_registry,
    ):
        """Test a conversation with Strands Agent."""
        # Enable Strands Agent
        mock_entry.options["use_strands_agent"] = True
        
        # Mock the Strands Agent and register_built_in_tools
        with patch("custom_components.cortex_agent.conversation_strategy.STRANDS_AVAILABLE", True), \
             patch("custom_components.cortex_agent.conversation_strategy.Agent") as mock_agent, \
             patch("custom_components.cortex_agent.tools.register_built_in_tools", return_value=None):
            
            # Configure mock agent
            mock_agent_instance = MagicMock()
            mock_agent_instance.return_value = {
                "message": {
                    "content": [
                        {"text": "Hello from Strands Agent!"}
                    ]
                }
            }
            mock_agent.return_value = mock_agent_instance
            
            agent = CortexAgent(
                hass=mock_hass,
                entry=mock_entry,
                model_provider=mock_model_provider,
                conversation_manager=conversation_manager,
                tool_registry=tool_registry,
            )
            
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
            assert "Hello from Strands Agent!" in result.response.speech["plain"]["speech"]
            
            # Check that the Strands Agent was called
            mock_agent_instance.assert_called_once_with("Hello, how are you?")
            
            # Check that the conversation history has two messages
            conversation_id = result.conversation_id
            history = conversation_manager.get_conversation(conversation_id)
            assert len(history) == 2
            assert history[0].role == MessageRole.USER
            assert history[0].content == "Hello, how are you?"
            assert history[1].role == MessageRole.ASSISTANT
            assert "Hello from Strands Agent!" in history[1].content

    async def test_multi_turn_conversation(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        conversation_manager,
        tool_registry,
    ):
        """Test a multi-turn conversation."""
        # Mock the register_built_in_tools function to avoid issues with register_tool
        with patch("custom_components.cortex_agent.tools.register_built_in_tools", return_value=None):
            agent = CortexAgent(
                hass=mock_hass,
                entry=mock_entry,
                model_provider=mock_model_provider,
                conversation_manager=conversation_manager,
                tool_registry=tool_registry,
            )
        
        # Create a conversation input for the first turn
        context = MagicMock()
        user_input1 = conversation.ConversationInput(
            text="Hello, how are you?",
            conversation_id=None,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Process the first input
        result1 = await agent.async_process(user_input1)
        conversation_id = result1.conversation_id
        
        # Create a conversation input for the second turn
        mock_model_provider.generate_response.reset_mock()
        mock_model_provider.generate_response.return_value = {
            "content": "I can help you with the weather. What location are you interested in?"
        }
        
        user_input2 = conversation.ConversationInput(
            text="What's the weather like?",
            conversation_id=conversation_id,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Process the second input
        result2 = await agent.async_process(user_input2)
        
        # Check the results
        assert result1.conversation_id == result2.conversation_id
        assert result2.response.speech["plain"]["speech"] == "I can help you with the weather. What location are you interested in?"
        
        # Check that the conversation history has four messages
        history = conversation_manager.get_conversation(conversation_id)
        assert len(history) == 4
        assert history[0].role == MessageRole.USER
        assert history[0].content == "Hello, how are you?"
        assert history[1].role == MessageRole.ASSISTANT
        assert history[1].content == "Hello! How can I help you today?"
        assert history[2].role == MessageRole.USER
        assert history[2].content == "What's the weather like?"
        assert history[3].role == MessageRole.ASSISTANT
        assert history[3].content == "I can help you with the weather. What location are you interested in?"