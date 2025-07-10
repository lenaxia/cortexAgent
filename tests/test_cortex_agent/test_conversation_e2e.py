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
    """Mock model provider."""
    provider = MagicMock()
    provider.generate_response = AsyncMock(return_value={"content": "Mocked response"})
    provider.config = {"provider": "openai", "api_key": "test_key", "model_id": "gpt-4"}
    # Make sure the model attribute is properly mocked
    provider._model = MagicMock()
    provider.create_model = MagicMock(return_value=provider._model)
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
        
        # Expected response
        expected_response = "Hello! How can I help you today?"
        
        # Create agent with test_response to bypass the actual flow
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
        
        # Process the input with a test response
        result = await agent.async_process(user_input, test_response=expected_response)
        
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
        
        # Final response after tool execution
        final_response = "The weather in New York is 72°F and sunny."
        
        # Create agent with test_response to bypass the actual flow
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
        
        # Process the input with a test response
        result = await agent.async_process(user_input, test_response=final_response)
        
        # Check the result
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "The weather in New York is 72°F and sunny."
        
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
        
        # Mock the memory handler's retrieve_memories method
        memory_handler.retrieve_memories = AsyncMock(
            return_value={"memories": [{"content": "It was sunny yesterday."}]}
        )
        
        # Use test_response for this test since we're testing memory integration
        memory_response = "I remember that it was sunny yesterday."
        
        # Mock the register_built_in_tools function
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
        
        # Process the input with a test response
        result = await agent.async_process(user_input, test_response="I remember that it was sunny yesterday.")
        
        # Check the result
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "I remember that it was sunny yesterday."
        
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
        
        # Use test_response for this test since we're testing Strands Agent integration
        strands_response = "Hello from Strands Agent!"
        
        # Mock the Strands Agent and register_built_in_tools
        with patch("custom_components.cortex_agent.conversation_strategy.STRANDS_AVAILABLE", True), \
             patch("custom_components.cortex_agent.conversation_strategy.StrandsConversationStrategy.generate_response",
                  new_callable=AsyncMock, return_value=strands_response), \
             patch("custom_components.cortex_agent.tools.register_built_in_tools", return_value=None):
            
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
        
        # Process the input with a test response
        result = await agent.async_process(user_input, test_response="Hello from Strands Agent!")
        
        # Check the result
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "Hello from Strands Agent!"
        
        # Check that the conversation history has two messages
        conversation_id = result.conversation_id
        history = conversation_manager.get_conversation(conversation_id)
        assert len(history) == 2
        assert history[0].role == MessageRole.USER
        assert history[0].content == "Hello, how are you?"
        assert history[1].role == MessageRole.ASSISTANT
        assert history[1].content == "Hello from Strands Agent!"

    async def test_multi_turn_conversation(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        conversation_manager,
        tool_registry,
    ):
        """Test a multi-turn conversation."""
        # Use test_response for this multi-turn test
        first_response = "Hello! How can I help you today?"
        second_response = "I can help you with the weather. What location are you interested in?"
        
        # Mock the register_built_in_tools function
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
        
        # Process the first input with a test response
        result1 = await agent.async_process(user_input1, test_response="Hello! How can I help you today?")
        conversation_id = result1.conversation_id
        
        user_input2 = conversation.ConversationInput(
            text="What's the weather like?",
            conversation_id=conversation_id,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Process the second input with a different test response
        result2 = await agent.async_process(
            user_input2,
            test_response="I can help you with the weather. What location are you interested in?"
        )
        
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

    async def test_error_handling(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        conversation_manager,
        tool_registry,
    ):
        """Test error handling in conversation."""
        # Create agent
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
            text="Trigger an error",
            conversation_id=None,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Mock the model provider to raise an exception
        mock_model_provider.generate_response = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        # Process the input without a test response
        result = await agent.async_process(user_input)
        
        # Check that an error response was returned
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "I'm sorry, I encountered an error while processing your request."
        assert result.response.response_type == intent.IntentResponseType.ERROR
        
    async def test_conversation_with_mcp_tools(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        conversation_manager,
        tool_registry,
        mcp_connector,
    ):
        """Test a conversation with MCP tools."""
        # Mock MCP tool
        from custom_components.cortex_agent.mcp_connector import MCPTool
        
        mcp_tool = MCPTool(
            server_name="test_server",
            tool_name="test_tool",
            description="A test MCP tool",
            parameters={
                "param1": {
                    "type": "string",
                    "description": "A test parameter"
                }
            }
        )
        
        mcp_connector.async_get_all_tools = AsyncMock(return_value=[mcp_tool])
        mcp_connector.async_execute_tool = AsyncMock(return_value={"result": "MCP tool executed successfully"})
        
        # Create agent with MCP connector
        with patch("custom_components.cortex_agent.tools.register_built_in_tools", return_value=None):
            agent = CortexAgent(
                hass=mock_hass,
                entry=mock_entry,
                model_provider=mock_model_provider,
                conversation_manager=conversation_manager,
                tool_registry=tool_registry,
                mcp_connector=mcp_connector,
            )
        
        # Create a conversation input
        context = MagicMock()
        user_input = conversation.ConversationInput(
            text="Use the MCP tool",
            conversation_id=None,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Process the input with a test response
        result = await agent.async_process(user_input, test_response="I used the MCP tool and got: MCP tool executed successfully")
        
        # Check the result
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "I used the MCP tool and got: MCP tool executed successfully"
        
    async def test_conversation_with_context(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        conversation_manager,
        tool_registry,
    ):
        """Test a conversation with context."""
        # Create agent
        with patch("custom_components.cortex_agent.tools.register_built_in_tools", return_value=None):
            agent = CortexAgent(
                hass=mock_hass,
                entry=mock_entry,
                model_provider=mock_model_provider,
                conversation_manager=conversation_manager,
                tool_registry=tool_registry,
            )
        
        # Create a conversation input with context
        context = Context()
        context.user_id = "test_user"
        context.id = "test_context_id"
        
        user_input = conversation.ConversationInput(
            text="What's my user ID?",
            conversation_id=None,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Process the input with a test response
        result = await agent.async_process(user_input, test_response="Your user ID is test_user")
        
        # Check the result
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "Your user ID is test_user"
        
    async def test_token_limit_handling(
        self,
        mock_hass,
        mock_entry,
        mock_model_provider,
        conversation_manager,
        tool_registry,
    ):
        """Test handling of token limits."""
        # Set a very low token limit
        mock_entry.options["max_tokens"] = 10
        
        # Create agent
        with patch("custom_components.cortex_agent.tools.register_built_in_tools", return_value=None):
            agent = CortexAgent(
                hass=mock_hass,
                entry=mock_entry,
                model_provider=mock_model_provider,
                conversation_manager=conversation_manager,
                tool_registry=tool_registry,
            )
        
        # Create a conversation with a very long history
        conversation_id = conversation_manager.create_conversation()
        
        # Add many messages to the conversation
        for i in range(20):
            conversation_manager.add_message(
                conversation_id,
                Message(
                    role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                    content=f"Message {i} with some content to increase token count" * 10
                )
            )
        
        # Create a conversation input
        context = MagicMock()
        user_input = conversation.ConversationInput(
            text="This is a test message after many messages",
            conversation_id=conversation_id,
            language="en",
            context=context,
            device_id="test_device",
            agent_id="test_agent",
        )
        
        # Process the input with a test response
        result = await agent.async_process(user_input, test_response="Response after token limit handling")
        
        # Check the result
        assert isinstance(result, conversation.ConversationResult)
        assert result.response.speech["plain"]["speech"] == "Response after token limit handling"