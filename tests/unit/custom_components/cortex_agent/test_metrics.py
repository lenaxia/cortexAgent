"""Tests for the CortexAgent metrics module."""
from unittest.mock import MagicMock, patch, AsyncMock
import json
from datetime import datetime

import pytest

from custom_components.cortex_agent.metrics import (
    MetricsTracker,
    ConversationMetrics,
    ToolMetrics,
    ModelMetrics,
)
from custom_components.cortex_agent.exceptions import MetricsError


@pytest.fixture
def mock_hass():
    """Fixture to provide a mock hass instance."""
    return MagicMock()


def test_conversation_metrics_init():
    """Test the initialization of ConversationMetrics."""
    # Create conversation metrics
    metrics = ConversationMetrics()
    
    # Check the metrics properties
    assert metrics.total_conversations == 0
    assert metrics.total_messages == 0
    assert metrics.total_tokens == 0
    assert metrics.average_response_time == 0
    assert metrics.conversation_history == []


def test_conversation_metrics_record_conversation():
    """Test the record_conversation method of ConversationMetrics."""
    # Create conversation metrics
    metrics = ConversationMetrics()
    
    # Record a conversation
    metrics.record_conversation(
        agent_id="test_agent",
        user_message="Hello, agent!",
        assistant_message="Hello, user!",
        tokens_used=100,
        response_time=1.5,
    )
    
    # Check the metrics
    assert metrics.total_conversations == 1
    assert metrics.total_messages == 2
    assert metrics.total_tokens == 100
    assert metrics.average_response_time == 1.5
    assert len(metrics.conversation_history) == 1
    
    # Check the conversation history entry
    entry = metrics.conversation_history[0]
    assert entry["agent_id"] == "test_agent"
    assert entry["user_message"] == "Hello, agent!"
    assert entry["assistant_message"] == "Hello, user!"
    assert entry["tokens_used"] == 100
    assert entry["response_time"] == 1.5
    assert "timestamp" in entry


def test_conversation_metrics_record_conversation_multiple():
    """Test the record_conversation method with multiple conversations."""
    # Create conversation metrics
    metrics = ConversationMetrics()
    
    # Record multiple conversations
    metrics.record_conversation(
        agent_id="test_agent",
        user_message="Hello, agent!",
        assistant_message="Hello, user!",
        tokens_used=100,
        response_time=1.5,
    )
    
    metrics.record_conversation(
        agent_id="test_agent",
        user_message="How are you?",
        assistant_message="I'm doing well, thank you!",
        tokens_used=150,
        response_time=2.0,
    )
    
    # Check the metrics
    assert metrics.total_conversations == 2
    assert metrics.total_messages == 4
    assert metrics.total_tokens == 250
    assert metrics.average_response_time == 1.75
    assert len(metrics.conversation_history) == 2


def test_conversation_metrics_get_stats():
    """Test the get_stats method of ConversationMetrics."""
    # Create conversation metrics
    metrics = ConversationMetrics()
    
    # Record some conversations
    metrics.record_conversation(
        agent_id="test_agent",
        user_message="Hello, agent!",
        assistant_message="Hello, user!",
        tokens_used=100,
        response_time=1.5,
    )
    
    metrics.record_conversation(
        agent_id="test_agent",
        user_message="How are you?",
        assistant_message="I'm doing well, thank you!",
        tokens_used=150,
        response_time=2.0,
    )
    
    # Get the stats
    stats = metrics.get_stats()
    
    # Check the stats
    assert stats["total_conversations"] == 2
    assert stats["total_messages"] == 4
    assert stats["total_tokens"] == 250
    assert stats["average_response_time"] == 1.75


def test_conversation_metrics_get_stats_by_agent():
    """Test the get_stats_by_agent method of ConversationMetrics."""
    # Create conversation metrics
    metrics = ConversationMetrics()
    
    # Record conversations for different agents
    metrics.record_conversation(
        agent_id="agent1",
        user_message="Hello, agent!",
        assistant_message="Hello, user!",
        tokens_used=100,
        response_time=1.5,
    )
    
    metrics.record_conversation(
        agent_id="agent2",
        user_message="How are you?",
        assistant_message="I'm doing well, thank you!",
        tokens_used=150,
        response_time=2.0,
    )
    
    metrics.record_conversation(
        agent_id="agent1",
        user_message="What's the weather?",
        assistant_message="It's sunny today.",
        tokens_used=120,
        response_time=1.8,
    )
    
    # Get the stats for agent1
    stats = metrics.get_stats_by_agent("agent1")
    
    # Check the stats
    assert stats["total_conversations"] == 2
    assert stats["total_messages"] == 4
    assert stats["total_tokens"] == 220
    assert stats["average_response_time"] == 1.65


def test_conversation_metrics_get_history():
    """Test the get_history method of ConversationMetrics."""
    # Create conversation metrics
    metrics = ConversationMetrics()
    
    # Record some conversations
    metrics.record_conversation(
        agent_id="test_agent",
        user_message="Hello, agent!",
        assistant_message="Hello, user!",
        tokens_used=100,
        response_time=1.5,
    )
    
    metrics.record_conversation(
        agent_id="test_agent",
        user_message="How are you?",
        assistant_message="I'm doing well, thank you!",
        tokens_used=150,
        response_time=2.0,
    )
    
    # Get the history
    history = metrics.get_history()
    
    # Check the history
    assert len(history) == 2
    assert history[0]["agent_id"] == "test_agent"
    assert history[0]["user_message"] == "Hello, agent!"
    assert history[0]["assistant_message"] == "Hello, user!"
    assert history[0]["tokens_used"] == 100
    assert history[0]["response_time"] == 1.5
    assert "timestamp" in history[0]
    
    assert history[1]["agent_id"] == "test_agent"
    assert history[1]["user_message"] == "How are you?"
    assert history[1]["assistant_message"] == "I'm doing well, thank you!"
    assert history[1]["tokens_used"] == 150
    assert history[1]["response_time"] == 2.0
    assert "timestamp" in history[1]


def test_conversation_metrics_get_history_by_agent():
    """Test the get_history_by_agent method of ConversationMetrics."""
    # Create conversation metrics
    metrics = ConversationMetrics()
    
    # Record conversations for different agents
    metrics.record_conversation(
        agent_id="agent1",
        user_message="Hello, agent!",
        assistant_message="Hello, user!",
        tokens_used=100,
        response_time=1.5,
    )
    
    metrics.record_conversation(
        agent_id="agent2",
        user_message="How are you?",
        assistant_message="I'm doing well, thank you!",
        tokens_used=150,
        response_time=2.0,
    )
    
    metrics.record_conversation(
        agent_id="agent1",
        user_message="What's the weather?",
        assistant_message="It's sunny today.",
        tokens_used=120,
        response_time=1.8,
    )
    
    # Get the history for agent1
    history = metrics.get_history_by_agent("agent1")
    
    # Check the history
    assert len(history) == 2
    assert history[0]["agent_id"] == "agent1"
    assert history[0]["user_message"] == "Hello, agent!"
    assert history[1]["agent_id"] == "agent1"
    assert history[1]["user_message"] == "What's the weather?"


def test_conversation_metrics_clear():
    """Test the clear method of ConversationMetrics."""
    # Create conversation metrics
    metrics = ConversationMetrics()
    
    # Record some conversations
    metrics.record_conversation(
        agent_id="test_agent",
        user_message="Hello, agent!",
        assistant_message="Hello, user!",
        tokens_used=100,
        response_time=1.5,
    )
    
    # Clear the metrics
    metrics.clear()
    
    # Check that the metrics were cleared
    assert metrics.total_conversations == 0
    assert metrics.total_messages == 0
    assert metrics.total_tokens == 0
    assert metrics.average_response_time == 0
    assert metrics.conversation_history == []


def test_tool_metrics_init():
    """Test the initialization of ToolMetrics."""
    # Create tool metrics
    metrics = ToolMetrics()
    
    # Check the metrics properties
    assert metrics.total_tool_calls == 0
    assert metrics.successful_tool_calls == 0
    assert metrics.failed_tool_calls == 0
    assert metrics.tool_call_history == []


def test_tool_metrics_record_tool_call_success():
    """Test the record_tool_call method of ToolMetrics with a successful call."""
    # Create tool metrics
    metrics = ToolMetrics()
    
    # Record a successful tool call
    metrics.record_tool_call(
        agent_id="test_agent",
        tool_name="test_tool",
        arguments={"param": "value"},
        success=True,
        result={"key": "value"},
        error=None,
        execution_time=0.5,
    )
    
    # Check the metrics
    assert metrics.total_tool_calls == 1
    assert metrics.successful_tool_calls == 1
    assert metrics.failed_tool_calls == 0
    assert len(metrics.tool_call_history) == 1
    
    # Check the tool call history entry
    entry = metrics.tool_call_history[0]
    assert entry["agent_id"] == "test_agent"
    assert entry["tool_name"] == "test_tool"
    assert entry["arguments"] == {"param": "value"}
    assert entry["success"] is True
    assert entry["result"] == {"key": "value"}
    assert entry["error"] is None
    assert entry["execution_time"] == 0.5
    assert "timestamp" in entry


def test_tool_metrics_record_tool_call_failure():
    """Test the record_tool_call method of ToolMetrics with a failed call."""
    # Create tool metrics
    metrics = ToolMetrics()
    
    # Record a failed tool call
    metrics.record_tool_call(
        agent_id="test_agent",
        tool_name="test_tool",
        arguments={"param": "value"},
        success=False,
        result=None,
        error="Tool execution error",
        execution_time=0.5,
    )
    
    # Check the metrics
    assert metrics.total_tool_calls == 1
    assert metrics.successful_tool_calls == 0
    assert metrics.failed_tool_calls == 1
    assert len(metrics.tool_call_history) == 1
    
    # Check the tool call history entry
    entry = metrics.tool_call_history[0]
    assert entry["agent_id"] == "test_agent"
    assert entry["tool_name"] == "test_tool"
    assert entry["arguments"] == {"param": "value"}
    assert entry["success"] is False
    assert entry["result"] is None
    assert entry["error"] == "Tool execution error"
    assert entry["execution_time"] == 0.5
    assert "timestamp" in entry


def test_tool_metrics_get_stats():
    """Test the get_stats method of ToolMetrics."""
    # Create tool metrics
    metrics = ToolMetrics()
    
    # Record some tool calls
    metrics.record_tool_call(
        agent_id="test_agent",
        tool_name="test_tool",
        arguments={"param": "value"},
        success=True,
        result={"key": "value"},
        error=None,
        execution_time=0.5,
    )
    
    metrics.record_tool_call(
        agent_id="test_agent",
        tool_name="test_tool",
        arguments={"param": "value2"},
        success=False,
        result=None,
        error="Tool execution error",
        execution_time=0.7,
    )
    
    # Get the stats
    stats = metrics.get_stats()
    
    # Check the stats
    assert stats["total_tool_calls"] == 2
    assert stats["successful_tool_calls"] == 1
    assert stats["failed_tool_calls"] == 1
    assert stats["success_rate"] == 0.5
    assert stats["average_execution_time"] == 0.6


def test_tool_metrics_get_stats_by_tool():
    """Test the get_stats_by_tool method of ToolMetrics."""
    # Create tool metrics
    metrics = ToolMetrics()
    
    # Record tool calls for different tools
    metrics.record_tool_call(
        agent_id="test_agent",
        tool_name="tool1",
        arguments={"param": "value"},
        success=True,
        result={"key": "value"},
        error=None,
        execution_time=0.5,
    )
    
    metrics.record_tool_call(
        agent_id="test_agent",
        tool_name="tool2",
        arguments={"param": "value"},
        success=True,
        result={"key": "value"},
        error=None,
        execution_time=0.7,
    )
    
    metrics.record_tool_call(
        agent_id="test_agent",
        tool_name="tool1",
        arguments={"param": "value2"},
        success=False,
        result=None,
        error="Tool execution error",
        execution_time=0.6,
    )
    
    # Get the stats for tool1
    stats = metrics.get_stats_by_tool("tool1")
    
    # Check the stats
    assert stats["total_tool_calls"] == 2
    assert stats["successful_tool_calls"] == 1
    assert stats["failed_tool_calls"] == 1
    assert stats["success_rate"] == 0.5
    assert stats["average_execution_time"] == 0.55


def test_tool_metrics_get_stats_by_agent():
    """Test the get_stats_by_agent method of ToolMetrics."""
    # Create tool metrics
    metrics = ToolMetrics()
    
    # Record tool calls for different agents
    metrics.record_tool_call(
        agent_id="agent1",
        tool_name="test_tool",
        arguments={"param": "value"},
        success=True,
        result={"key": "value"},
        error=None,
        execution_time=0.5,
    )
    
    metrics.record_tool_call(
        agent_id="agent2",
        tool_name="test_tool",
        arguments={"param": "value"},
        success=True,
        result={"key": "value"},
        error=None,
        execution_time=0.7,
    )
    
    metrics.record_tool_call(
        agent_id="agent1",
        tool_name="test_tool",
        arguments={"param": "value2"},
        success=False,
        result=None,
        error="Tool execution error",
        execution_time=0.6,
    )
    
    # Get the stats for agent1
    stats = metrics.get_stats_by_agent("agent1")
    
    # Check the stats
    assert stats["total_tool_calls"] == 2
    assert stats["successful_tool_calls"] == 1
    assert stats["failed_tool_calls"] == 1
    assert stats["success_rate"] == 0.5
    assert stats["average_execution_time"] == 0.55


def test_tool_metrics_get_history():
    """Test the get_history method of ToolMetrics."""
    # Create tool metrics
    metrics = ToolMetrics()
    
    # Record some tool calls
    metrics.record_tool_call(
        agent_id="test_agent",
        tool_name="test_tool",
        arguments={"param": "value"},
        success=True,
        result={"key": "value"},
        error=None,
        execution_time=0.5,
    )
    
    metrics.record_tool_call(
        agent_id="test_agent",
        tool_name="test_tool",
        arguments={"param": "value2"},
        success=False,
        result=None,
        error="Tool execution error",
        execution_time=0.7,
    )
    
    # Get the history
    history = metrics.get_history()
    
    # Check the history
    assert len(history) == 2
    assert history[0]["agent_id"] == "test_agent"
    assert history[0]["tool_name"] == "test_tool"
    assert history[0]["arguments"] == {"param": "value"}
    assert history[0]["success"] is True
    assert history[0]["result"] == {"key": "value"}
    assert history[0]["error"] is None
    assert history[0]["execution_time"] == 0.5
    assert "timestamp" in history[0]
    
    assert history[1]["agent_id"] == "test_agent"
    assert history[1]["tool_name"] == "test_tool"
    assert history[1]["arguments"] == {"param": "value2"}
    assert history[1]["success"] is False
    assert history[1]["result"] is None
    assert history[1]["error"] == "Tool execution error"
    assert history[1]["execution_time"] == 0.7
    assert "timestamp" in history[1]


def test_tool_metrics_clear():
    """Test the clear method of ToolMetrics."""
    # Create tool metrics
    metrics = ToolMetrics()
    
    # Record a tool call
    metrics.record_tool_call(
        agent_id="test_agent",
        tool_name="test_tool",
        arguments={"param": "value"},
        success=True,
        result={"key": "value"},
        error=None,
        execution_time=0.5,
    )
    
    # Clear the metrics
    metrics.clear()
    
    # Check that the metrics were cleared
    assert metrics.total_tool_calls == 0
    assert metrics.successful_tool_calls == 0
    assert metrics.failed_tool_calls == 0
    assert metrics.tool_call_history == []


def test_model_metrics_init():
    """Test the initialization of ModelMetrics."""
    # Create model metrics
    metrics = ModelMetrics()
    
    # Check the metrics properties
    assert metrics.total_tokens == 0
    assert metrics.prompt_tokens == 0
    assert metrics.completion_tokens == 0
    assert metrics.total_cost == 0
    assert metrics.model_usage == {}


def test_model_metrics_record_usage():
    """Test the record_usage method of ModelMetrics."""
    # Create model metrics
    metrics = ModelMetrics()
    
    # Record usage
    metrics.record_usage(
        agent_id="test_agent",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        cost=0.02,
    )
    
    # Check the metrics
    assert metrics.total_tokens == 150
    assert metrics.prompt_tokens == 100
    assert metrics.completion_tokens == 50
    assert metrics.total_cost == 0.02
    assert "gpt-4" in metrics.model_usage
    assert metrics.model_usage["gpt-4"]["total_tokens"] == 150
    assert metrics.model_usage["gpt-4"]["prompt_tokens"] == 100
    assert metrics.model_usage["gpt-4"]["completion_tokens"] == 50
    assert metrics.model_usage["gpt-4"]["total_cost"] == 0.02


def test_model_metrics_record_usage_multiple():
    """Test the record_usage method with multiple usages."""
    # Create model metrics
    metrics = ModelMetrics()
    
    # Record multiple usages
    metrics.record_usage(
        agent_id="test_agent",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        cost=0.02,
    )
    
    metrics.record_usage(
        agent_id="test_agent",
        model="gpt-4",
        prompt_tokens=200,
        completion_tokens=100,
        cost=0.04,
    )
    
    metrics.record_usage(
        agent_id="test_agent",
        model="claude-3",
        prompt_tokens=150,
        completion_tokens=75,
        cost=0.03,
    )
    
    # Check the metrics
    assert metrics.total_tokens == 675
    assert metrics.prompt_tokens == 450
    assert metrics.completion_tokens == 225
    assert metrics.total_cost == 0.09
    
    assert "gpt-4" in metrics.model_usage
    assert metrics.model_usage["gpt-4"]["total_tokens"] == 450
    assert metrics.model_usage["gpt-4"]["prompt_tokens"] == 300
    assert metrics.model_usage["gpt-4"]["completion_tokens"] == 150
    assert metrics.model_usage["gpt-4"]["total_cost"] == 0.06
    
    assert "claude-3" in metrics.model_usage
    assert metrics.model_usage["claude-3"]["total_tokens"] == 225
    assert metrics.model_usage["claude-3"]["prompt_tokens"] == 150
    assert metrics.model_usage["claude-3"]["completion_tokens"] == 75
    assert metrics.model_usage["claude-3"]["total_cost"] == 0.03


def test_model_metrics_get_stats():
    """Test the get_stats method of ModelMetrics."""
    # Create model metrics
    metrics = ModelMetrics()
    
    # Record some usage
    metrics.record_usage(
        agent_id="test_agent",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        cost=0.02,
    )
    
    metrics.record_usage(
        agent_id="test_agent",
        model="claude-3",
        prompt_tokens=150,
        completion_tokens=75,
        cost=0.03,
    )
    
    # Get the stats
    stats = metrics.get_stats()
    
    # Check the stats
    assert stats["total_tokens"] == 375
    assert stats["prompt_tokens"] == 250
    assert stats["completion_tokens"] == 125
    assert stats["total_cost"] == 0.05
    assert len(stats["model_usage"]) == 2
    assert "gpt-4" in stats["model_usage"]
    assert "claude-3" in stats["model_usage"]


def test_model_metrics_get_stats_by_model():
    """Test the get_stats_by_model method of ModelMetrics."""
    # Create model metrics
    metrics = ModelMetrics()
    
    # Record usage for different models
    metrics.record_usage(
        agent_id="test_agent",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        cost=0.02,
    )
    
    metrics.record_usage(
        agent_id="test_agent",
        model="claude-3",
        prompt_tokens=150,
        completion_tokens=75,
        cost=0.03,
    )
    
    metrics.record_usage(
        agent_id="test_agent",
        model="gpt-4",
        prompt_tokens=200,
        completion_tokens=100,
        cost=0.04,
    )
    
    # Get the stats for gpt-4
    stats = metrics.get_stats_by_model("gpt-4")
    
    # Check the stats
    assert stats["total_tokens"] == 450
    assert stats["prompt_tokens"] == 300
    assert stats["completion_tokens"] == 150
    assert stats["total_cost"] == 0.06


def test_model_metrics_get_stats_by_agent():
    """Test the get_stats_by_agent method of ModelMetrics."""
    # Create model metrics
    metrics = ModelMetrics()
    
    # Record usage for different agents
    metrics.record_usage(
        agent_id="agent1",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        cost=0.02,
    )
    
    metrics.record_usage(
        agent_id="agent2",
        model="gpt-4",
        prompt_tokens=150,
        completion_tokens=75,
        cost=0.03,
    )
    
    metrics.record_usage(
        agent_id="agent1",
        model="claude-3",
        prompt_tokens=200,
        completion_tokens=100,
        cost=0.04,
    )
    
    # Get the stats for agent1
    stats = metrics.get_stats_by_agent("agent1")
    
    # Check the stats
    assert stats["total_tokens"] == 450
    assert stats["prompt_tokens"] == 300
    assert stats["completion_tokens"] == 150
    assert stats["total_cost"] == 0.06
    assert len(stats["model_usage"]) == 2
    assert "gpt-4" in stats["model_usage"]
    assert "claude-3" in stats["model_usage"]


def test_model_metrics_clear():
    """Test the clear method of ModelMetrics."""
    # Create model metrics
    metrics = ModelMetrics()
    
    # Record some usage
    metrics.record_usage(
        agent_id="test_agent",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        cost=0.02,
    )
    
    # Clear the metrics
    metrics.clear()
    
    # Check that the metrics were cleared
    assert metrics.total_tokens == 0
    assert metrics.prompt_tokens == 0
    assert metrics.completion_tokens == 0
    assert metrics.total_cost == 0
    assert metrics.model_usage == {}


def test_metrics_tracker_init(mock_hass):
    """Test the initialization of MetricsTracker."""
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Check the tracker properties
    assert tracker.hass == mock_hass
    assert isinstance(tracker.conversation_metrics, ConversationMetrics)
    assert isinstance(tracker.tool_metrics, ToolMetrics)
    assert isinstance(tracker.model_metrics, ModelMetrics)


def test_metrics_tracker_record_conversation(mock_hass):
    """Test the record_conversation method of MetricsTracker."""
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Set up a spy on the conversation_metrics.record_conversation method
    tracker.conversation_metrics.record_conversation = MagicMock()
    
    # Record a conversation
    tracker.record_conversation(
        agent_id="test_agent",
        user_message="Hello, agent!",
        assistant_message="Hello, user!",
        tokens_used=100,
        response_time=1.5,
    )
    
    # Check that record_conversation was called with the right arguments
    tracker.conversation_metrics.record_conversation.assert_called_once_with(
        agent_id="test_agent",
        user_message="Hello, agent!",
        assistant_message="Hello, user!",
        tokens_used=100,
        response_time=1.5,
    )


def test_metrics_tracker_record_tool_call(mock_hass):
    """Test the record_tool_call method of MetricsTracker."""
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Set up a spy on the tool_metrics.record_tool_call method
    tracker.tool_metrics.record_tool_call = MagicMock()
    
    # Record a tool call
    tracker.record_tool_call(
        agent_id="test_agent",
        tool_name="test_tool",
        arguments={"param": "value"},
        success=True,
        result={"key": "value"},
        error=None,
        execution_time=0.5,
    )
    
    # Check that record_tool_call was called with the right arguments
    tracker.tool_metrics.record_tool_call.assert_called_once_with(
        agent_id="test_agent",
        tool_name="test_tool",
        arguments={"param": "value"},
        success=True,
        result={"key": "value"},
        error=None,
        execution_time=0.5,
    )


def test_metrics_tracker_record_model_usage(mock_hass):
    """Test the record_model_usage method of MetricsTracker."""
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Set up a spy on the model_metrics.record_usage method
    tracker.model_metrics.record_usage = MagicMock()
    
    # Record model usage
    tracker.record_model_usage(
        agent_id="test_agent",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        cost=0.02,
    )
    
    # Check that record_usage was called with the right arguments
    tracker.model_metrics.record_usage.assert_called_once_with(
        agent_id="test_agent",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        cost=0.02,
    )


def test_metrics_tracker_get_conversation_stats(mock_hass):
    """Test the get_conversation_stats method of MetricsTracker."""
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Set up a spy on the conversation_metrics.get_stats method
    tracker.conversation_metrics.get_stats = MagicMock(return_value={"total_conversations": 10})
    
    # Get the conversation stats
    stats = tracker.get_conversation_stats()
    
    # Check that get_stats was called
    tracker.conversation_metrics.get_stats.assert_called_once()
    
    # Check the stats
    assert stats == {"total_conversations": 10}


def test_metrics_tracker_get_tool_stats(mock_hass):
    """Test the get_tool_stats method of MetricsTracker."""
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Set up a spy on the tool_metrics.get_stats method
    tracker.tool_metrics.get_stats = MagicMock(return_value={"total_tool_calls": 10})
    
    # Get the tool stats
    stats = tracker.get_tool_stats()
    
    # Check that get_stats was called
    tracker.tool_metrics.get_stats.assert_called_once()
    
    # Check the stats
    assert stats == {"total_tool_calls": 10}


def test_metrics_tracker_get_model_stats(mock_hass):
    """Test the get_model_stats method of MetricsTracker."""
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Set up a spy on the model_metrics.get_stats method
    tracker.model_metrics.get_stats = MagicMock(return_value={"total_tokens": 1000})
    
    # Get the model stats
    stats = tracker.get_model_stats()
    
    # Check that get_stats was called
    tracker.model_metrics.get_stats.assert_called_once()
    
    # Check the stats
    assert stats == {"total_tokens": 1000}


def test_metrics_tracker_get_all_stats(mock_hass):
    """Test the get_all_stats method of MetricsTracker."""
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Set up spies on the get_stats methods
    tracker.conversation_metrics.get_stats = MagicMock(return_value={"total_conversations": 10})
    tracker.tool_metrics.get_stats = MagicMock(return_value={"total_tool_calls": 20})
    tracker.model_metrics.get_stats = MagicMock(return_value={"total_tokens": 1000})
    
    # Get all stats
    stats = tracker.get_all_stats()
    
    # Check that get_stats was called for each metrics type
    tracker.conversation_metrics.get_stats.assert_called_once()
    tracker.tool_metrics.get_stats.assert_called_once()
    tracker.model_metrics.get_stats.assert_called_once()
    
    # Check the stats
    assert stats["conversation"] == {"total_conversations": 10}
    assert stats["tool"] == {"total_tool_calls": 20}
    assert stats["model"] == {"total_tokens": 1000}


def test_metrics_tracker_clear(mock_hass):
    """Test the clear method of MetricsTracker."""
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Set up spies on the clear methods
    tracker.conversation_metrics.clear = MagicMock()
    tracker.tool_metrics.clear = MagicMock()
    tracker.model_metrics.clear = MagicMock()
    
    # Clear the metrics
    tracker.clear()
    
    # Check that clear was called for each metrics type
    tracker.conversation_metrics.clear.assert_called_once()
    tracker.tool_metrics.clear.assert_called_once()
    tracker.model_metrics.clear.assert_called_once()


@patch("custom_components.cortex_agent.metrics.json")
@patch("custom_components.cortex_agent.metrics.os.path.exists")
@patch("custom_components.cortex_agent.metrics.os.makedirs")
def test_metrics_tracker_save_to_file(mock_makedirs, mock_exists, mock_json, mock_hass):
    """Test the save_to_file method of MetricsTracker."""
    # Set up the mock os.path.exists
    mock_exists.return_value = False
    
    # Set up the mock hass.config.path
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Set up spies on the get_stats methods
    tracker.conversation_metrics.get_stats = MagicMock(return_value={"total_conversations": 10})
    tracker.tool_metrics.get_stats = MagicMock(return_value={"total_tool_calls": 20})
    tracker.model_metrics.get_stats = MagicMock(return_value={"total_tokens": 1000})
    
    # Mock open
    mock_file = MagicMock()
    with patch("builtins.open", mock_file):
        # Save to file
        tracker.save_to_file()
    
    # Check that os.path.exists was called with the right arguments
    mock_exists.assert_called_once_with("/path/to/config/cortex_agent")
    
    # Check that os.makedirs was called with the right arguments
    mock_makedirs.assert_called_once_with("/path/to/config/cortex_agent")
    
    # Check that open was called with the right arguments
    mock_file.assert_called_once_with("/path/to/config/cortex_agent/metrics.json", "w")
    
    # Check that json.dump was called with the right arguments
    mock_json.dump.assert_called_once()
    args, kwargs = mock_json.dump.call_args
    assert args[1] == mock_file().__enter__()
    
    # Check the serialized metrics
    serialized_metrics = args[0]
    assert serialized_metrics["conversation"] == {"total_conversations": 10}
    assert serialized_metrics["tool"] == {"total_tool_calls": 20}
    assert serialized_metrics["model"] == {"total_tokens": 1000}


@patch("custom_components.cortex_agent.metrics.json")
@patch("custom_components.cortex_agent.metrics.os.path.exists")
def test_metrics_tracker_save_to_file_error(mock_exists, mock_json, mock_hass):
    """Test the save_to_file method with an error."""
    # Set up the mock os.path.exists
    mock_exists.return_value = True
    
    # Set up the mock hass.config.path
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Mock open to raise an exception
    mock_file = MagicMock()
    mock_file.side_effect = IOError("File error")
    
    # Try to save to file
    with patch("builtins.open", mock_file):
        with pytest.raises(MetricsError):
            tracker.save_to_file()


@patch("custom_components.cortex_agent.metrics.json")
@patch("custom_components.cortex_agent.metrics.os.path.exists")
def test_metrics_tracker_load_from_file(mock_exists, mock_json, mock_hass):
    """Test the load_from_file method of MetricsTracker."""
    # Set up the mock os.path.exists
    mock_exists.return_value = True
    
    # Set up the mock hass.config.path
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a serialized metrics dict
    serialized_metrics = {
        "conversation": {
            "total_conversations": 10,
            "total_messages": 20,
            "total_tokens": 1000,
            "average_response_time": 1.5,
            "conversation_history": [],
        },
        "tool": {
            "total_tool_calls": 20,
            "successful_tool_calls": 15,
            "failed_tool_calls": 5,
            "tool_call_history": [],
        },
        "model": {
            "total_tokens": 1000,
            "prompt_tokens": 700,
            "completion_tokens": 300,
            "total_cost": 0.05,
            "model_usage": {},
        },
    }
    
    # Mock json.load to return the serialized metrics
    mock_json.load.return_value = serialized_metrics
    
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Mock open
    mock_file = MagicMock()
    with patch("builtins.open", mock_file):
        # Load from file
        tracker.load_from_file()
    
    # Check that os.path.exists was called with the right arguments
    mock_exists.assert_called_once_with("/path/to/config/cortex_agent/metrics.json")
    
    # Check that open was called with the right arguments
    mock_file.assert_called_once_with("/path/to/config/cortex_agent/metrics.json", "r")
    
    # Check that json.load was called with the right arguments
    mock_json.load.assert_called_once_with(mock_file().__enter__())
    
    # Check the loaded metrics
    assert tracker.conversation_metrics.total_conversations == 10
    assert tracker.conversation_metrics.total_messages == 20
    assert tracker.conversation_metrics.total_tokens == 1000
    assert tracker.conversation_metrics.average_response_time == 1.5
    
    assert tracker.tool_metrics.total_tool_calls == 20
    assert tracker.tool_metrics.successful_tool_calls == 15
    assert tracker.tool_metrics.failed_tool_calls == 5
    
    assert tracker.model_metrics.total_tokens == 1000
    assert tracker.model_metrics.prompt_tokens == 700
    assert tracker.model_metrics.completion_tokens == 300
    assert tracker.model_metrics.total_cost == 0.05


@patch("custom_components.cortex_agent.metrics.os.path.exists")
def test_metrics_tracker_load_from_file_not_exists(mock_exists, mock_hass):
    """Test the load_from_file method when the file doesn't exist."""
    # Set up the mock os.path.exists
    mock_exists.return_value = False
    
    # Set up the mock hass.config.path
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Load from file
    tracker.load_from_file()
    
    # Check that os.path.exists was called with the right arguments
    mock_exists.assert_called_once_with("/path/to/config/cortex_agent/metrics.json")
    
    # Check that the metrics were not modified
    assert tracker.conversation_metrics.total_conversations == 0
    assert tracker.tool_metrics.total_tool_calls == 0
    assert tracker.model_metrics.total_tokens == 0


@patch("custom_components.cortex_agent.metrics.os.path.exists")
def test_metrics_tracker_load_from_file_error(mock_exists, mock_hass):
    """Test the load_from_file method with an error."""
    # Set up the mock os.path.exists
    mock_exists.return_value = True
    
    # Set up the mock hass.config.path
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Mock open to raise an exception
    mock_file = MagicMock()
    mock_file.side_effect = IOError("File error")
    
    # Try to load from file
    with patch("builtins.open", mock_file):
        with pytest.raises(MetricsError):
            tracker.load_from_file()


@patch("custom_components.cortex_agent.metrics.json")
@patch("custom_components.cortex_agent.metrics.os.path.exists")
def test_metrics_tracker_load_from_file_invalid_json(mock_exists, mock_json, mock_hass):
    """Test the load_from_file method with invalid JSON."""
    # Set up the mock os.path.exists
    mock_exists.return_value = True
    
    # Set up the mock hass.config.path
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Mock json.load to raise an exception
    mock_json.load.side_effect = json.JSONDecodeError("JSON error", "", 0)
    
    # Create a metrics tracker
    tracker = MetricsTracker(mock_hass)
    
    # Mock open
    mock_file = MagicMock()
    
    # Try to load from file
    with patch("builtins.open", mock_file):
        with pytest.raises(MetricsError):
            tracker.load_from_file()