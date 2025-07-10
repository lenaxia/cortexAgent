"""Tests for the CortexAgent conversation module."""
from unittest.mock import MagicMock, patch, AsyncMock
import json

import pytest
from homeassistant.components import conversation
from homeassistant.core import Context

from custom_components.cortex_agent.conversation import (
    CortexAgentConversation,
    async_process_response,
)
from custom_components.cortex_agent.model_provider import (
    ModelProvider,
    ModelProviderType,
)
from custom_components.cortex_agent.conversation_manager import (
    ConversationManager,
    ConversationRole,
)
from custom_components.cortex_agent.tool_manager import (
    ToolManager,
    ToolExecutionResult,
)
from custom_components.cortex_agent.exceptions import (
    ModelProviderError,
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
    provider.connected = True
    return provider


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


def test_cortex_agent_conversation_init(
    mock_hass,
    mock_model_provider,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the initialization of CortexAgentConversation."""
    # Create a conversation agent
    agent = CortexAgentConversation(
        hass=mock_hass,
        model_provider=mock_model_provider,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
        name="Test Agent",
        language="en",
    )
    
    # Check the agent properties
    assert agent.hass == mock_hass
    assert agent.model_provider == mock_model_provider
    assert agent.conversation_manager == mock_conversation_manager
    assert agent.tool_manager == mock_tool_manager
    assert agent.agent_id == "test_agent"
    assert agent.name == "Test Agent"
    assert agent.language == "en"


@patch("custom_components.cortex_agent.conversation.ModelProvider")
@patch("custom_components.cortex_agent.conversation.ConversationManager")
@patch("custom_components.cortex_agent.conversation.ToolManager")
def test_cortex_agent_conversation_init_with_defaults(
    mock_tool_manager_class,
    mock_conversation_manager_class,
    mock_model_provider_class,
    mock_hass,
):
    """Test the initialization of CortexAgentConversation with default components."""
    # Set up the mock classes
    mock_model_provider = MagicMock(spec=ModelProvider)
    mock_model_provider_class.return_value = mock_model_provider
    
    mock_conversation_manager = MagicMock(spec=ConversationManager)
    mock_conversation_manager_class.return_value = mock_conversation_manager
    
    mock_tool_manager = MagicMock(spec=ToolManager)
    mock_tool_manager_class.return_value = mock_tool_manager
    
    # Create a conversation agent without providing components
    agent = CortexAgentConversation(
        hass=mock_hass,
        agent_id="test_agent",
    )
    
    # Check that the components were created
    mock_model_provider_class.assert_called_once()
    mock_conversation_manager_class.assert_called_once_with(agent_id="test_agent")
    mock_tool_manager_class.assert_called_once_with(mock_hass)
    
    # Check the agent properties
    assert agent.hass == mock_hass
    assert agent.model_provider == mock_model_provider
    assert agent.conversation_manager == mock_conversation_manager
    assert agent.tool_manager == mock_tool_manager
    assert agent.agent_id == "test_agent"
    assert agent.name == "CortexAgent"
    assert agent.language == "en"


async def test_cortex_agent_conversation_async_process(
    mock_hass,
    mock_model_provider,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the async_process method of CortexAgentConversation."""
    # Set up the mock model provider
    mock_model_provider.generate_response = AsyncMock(return_value={
        "response": "This is a test response",
        "tool_calls": [],
    })
    
    # Set up the mock conversation manager
    mock_conversation_manager.add_entry = MagicMock()
    
    # Create a conversation agent
    agent = CortexAgentConversation(
        hass=mock_hass,
        model_provider=mock_model_provider,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Create a conversation input
    conversation_input = conversation.ConversationInput(
        text="Hello, agent!",
        context=Context(),
    )
    
    # Call async_process
    result = await agent.async_process(conversation_input)
    
    # Check that add_entry was called on the conversation manager
    mock_conversation_manager.add_entry.assert_called_with(
        role=ConversationRole.USER,
        content="Hello, agent!",
    )
    
    # Check that generate_response was called on the model provider
    mock_model_provider.generate_response.assert_called_once()
    
    # Check that add_entry was called again on the conversation manager
    assert mock_conversation_manager.add_entry.call_count == 2
    mock_conversation_manager.add_entry.assert_any_call(
        role=ConversationRole.ASSISTANT,
        content="This is a test response",
    )
    
    # Check the result
    assert result.response.speech["plain"]["speech"] == "This is a test response"
    assert result.response.response_type == "action"
    assert result.response.language == "en"
    assert result.response.data["agent_id"] == "test_agent"


async def test_cortex_agent_conversation_async_process_with_tool_calls(
    mock_hass,
    mock_model_provider,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the async_process method with tool calls."""
    # Set up the mock model provider
    mock_model_provider.generate_response = AsyncMock(return_value={
        "response": "I'll check the weather for you.",
        "tool_calls": [
            {
                "name": "get_weather",
                "arguments": {"location": "New York"},
            },
        ],
    })
    
    # Set up the mock tool manager
    mock_tool_result = ToolExecutionResult(
        tool_name="get_weather",
        success=True,
        result={"temperature": 72, "condition": "sunny"},
        error=None,
    )
    mock_tool_manager.execute_tool = AsyncMock(return_value=mock_tool_result)
    
    # Set up the mock model provider for the second call
    mock_model_provider.generate_response.side_effect = [
        {
            "response": "I'll check the weather for you.",
            "tool_calls": [
                {
                    "name": "get_weather",
                    "arguments": {"location": "New York"},
                },
            ],
        },
        {
            "response": "The weather in New York is sunny with a temperature of 72°F.",
            "tool_calls": [],
        },
    ]
    
    # Create a conversation agent
    agent = CortexAgentConversation(
        hass=mock_hass,
        model_provider=mock_model_provider,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Create a conversation input
    conversation_input = conversation.ConversationInput(
        text="What's the weather in New York?",
        context=Context(),
    )
    
    # Call async_process
    result = await agent.async_process(conversation_input)
    
    # Check that execute_tool was called on the tool manager
    mock_tool_manager.execute_tool.assert_called_once_with(
        "get_weather",
        {"location": "New York"},
    )
    
    # Check that generate_response was called twice on the model provider
    assert mock_model_provider.generate_response.call_count == 2
    
    # Check the result
    assert result.response.speech["plain"]["speech"] == "The weather in New York is sunny with a temperature of 72°F."


async def test_cortex_agent_conversation_async_process_model_provider_error(
    mock_hass,
    mock_model_provider,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the async_process method when the model provider raises an error."""
    # Set up the mock model provider to raise an error
    mock_model_provider.generate_response = AsyncMock(side_effect=ModelProviderError("Model provider error"))
    
    # Create a conversation agent
    agent = CortexAgentConversation(
        hass=mock_hass,
        model_provider=mock_model_provider,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Create a conversation input
    conversation_input = conversation.ConversationInput(
        text="Hello, agent!",
        context=Context(),
    )
    
    # Call async_process
    result = await agent.async_process(conversation_input)
    
    # Check the result
    assert "error" in result.response.speech["plain"]["speech"].lower()
    assert "model provider error" in result.response.speech["plain"]["speech"].lower()


async def test_cortex_agent_conversation_async_process_tool_error(
    mock_hass,
    mock_model_provider,
    mock_conversation_manager,
    mock_tool_manager,
):
    """Test the async_process method when a tool execution fails."""
    # Set up the mock model provider
    mock_model_provider.generate_response = AsyncMock(return_value={
        "response": "I'll check the weather for you.",
        "tool_calls": [
            {
                "name": "get_weather",
                "arguments": {"location": "New York"},
            },
        ],
    })
    
    # Set up the mock tool manager to return an error
    mock_tool_result = ToolExecutionResult(
        tool_name="get_weather",
        success=False,
        result=None,
        error="Tool execution error",
    )
    mock_tool_manager.execute_tool = AsyncMock(return_value=mock_tool_result)
    
    # Set up the mock model provider for the second call
    mock_model_provider.generate_response.side_effect = [
        {
            "response": "I'll check the weather for you.",
            "tool_calls": [
                {
                    "name": "get_weather",
                    "arguments": {"location": "New York"},
                },
            ],
        },
        {
            "response": "I'm sorry, I couldn't get the weather information.",
            "tool_calls": [],
        },
    ]
    
    # Create a conversation agent
    agent = CortexAgentConversation(
        hass=mock_hass,
        model_provider=mock_model_provider,
        conversation_manager=mock_conversation_manager,
        tool_manager=mock_tool_manager,
        agent_id="test_agent",
    )
    
    # Create a conversation input
    conversation_input = conversation.ConversationInput(
        text="What's the weather in New York?",
        context=Context(),
    )
    
    # Call async_process
    result = await agent.async_process(conversation_input)
    
    # Check that execute_tool was called on the tool manager
    mock_tool_manager.execute_tool.assert_called_once_with(
        "get_weather",
        {"location": "New York"},
    )
    
    # Check that generate_response was called twice on the model provider
    assert mock_model_provider.generate_response.call_count == 2
    
    # Check the result
    assert result.response.speech["plain"]["speech"] == "I'm sorry, I couldn't get the weather information."


def test_async_process_response():
    """Test the async_process_response function."""
    # Create a response
    response = "This is a test response"
    
    # Call async_process_response
    result = async_process_response(response, "test_agent", "en")
    
    # Check the result
    assert result.speech["plain"]["speech"] == "This is a test response"
    assert result.response_type == "action"
    assert result.language == "en"
    assert result.data["agent_id"] == "test_agent"


def test_async_process_response_with_error():
    """Test the async_process_response function with an error."""
    # Create an error response
    response = "Error: Something went wrong"
    
    # Call async_process_response
    result = async_process_response(response, "test_agent", "en")
    
    # Check the result
    assert result.speech["plain"]["speech"] == "Error: Something went wrong"
    assert result.response_type == "error"
    assert result.language == "en"
    assert result.data["agent_id"] == "test_agent"