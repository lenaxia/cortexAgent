"""Tests for the CortexAgent conversation_manager module."""
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

import pytest

from custom_components.cortex_agent.conversation_manager import (
    ConversationManager,
    ConversationEntry,
    ConversationRole,
)
from custom_components.cortex_agent.exceptions import ConversationError


def test_conversation_entry_init():
    """Test the initialization of a ConversationEntry."""
    # Create a conversation entry
    entry = ConversationEntry(
        role=ConversationRole.USER,
        content="Hello, agent!",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    # Check the entry properties
    assert entry.role == ConversationRole.USER
    assert entry.content == "Hello, agent!"
    assert entry.timestamp == datetime(2023, 1, 1, 12, 0, 0)


def test_conversation_entry_to_dict():
    """Test the to_dict method of ConversationEntry."""
    # Create a conversation entry
    entry = ConversationEntry(
        role=ConversationRole.USER,
        content="Hello, agent!",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    # Convert to dict
    entry_dict = entry.to_dict()
    
    # Check the dict
    assert entry_dict["role"] == "user"
    assert entry_dict["content"] == "Hello, agent!"
    assert entry_dict["timestamp"] == "2023-01-01T12:00:00"


def test_conversation_entry_from_dict():
    """Test the from_dict method of ConversationEntry."""
    # Create a dict
    entry_dict = {
        "role": "assistant",
        "content": "Hello, user!",
        "timestamp": "2023-01-01T12:00:00",
    }
    
    # Convert to ConversationEntry
    entry = ConversationEntry.from_dict(entry_dict)
    
    # Check the entry
    assert entry.role == ConversationRole.ASSISTANT
    assert entry.content == "Hello, user!"
    assert entry.timestamp == datetime(2023, 1, 1, 12, 0, 0)


def test_conversation_entry_from_dict_invalid_role():
    """Test the from_dict method with an invalid role."""
    # Create a dict with an invalid role
    entry_dict = {
        "role": "invalid_role",
        "content": "Hello, user!",
        "timestamp": "2023-01-01T12:00:00",
    }
    
    # Try to convert to ConversationEntry
    with pytest.raises(ValueError):
        ConversationEntry.from_dict(entry_dict)


def test_conversation_entry_from_dict_invalid_timestamp():
    """Test the from_dict method with an invalid timestamp."""
    # Create a dict with an invalid timestamp
    entry_dict = {
        "role": "user",
        "content": "Hello, agent!",
        "timestamp": "invalid_timestamp",
    }
    
    # Try to convert to ConversationEntry
    with pytest.raises(ValueError):
        ConversationEntry.from_dict(entry_dict)


def test_conversation_manager_init():
    """Test the initialization of a ConversationManager."""
    # Create a conversation manager
    manager = ConversationManager(agent_id="test_agent")
    
    # Check the manager properties
    assert manager.agent_id == "test_agent"
    assert manager.history == []
    assert manager.max_history_length == 100


def test_conversation_manager_init_with_max_history():
    """Test the initialization of a ConversationManager with a custom max_history_length."""
    # Create a conversation manager with a custom max_history_length
    manager = ConversationManager(agent_id="test_agent", max_history_length=50)
    
    # Check the manager properties
    assert manager.agent_id == "test_agent"
    assert manager.history == []
    assert manager.max_history_length == 50


def test_conversation_manager_add_entry():
    """Test the add_entry method of ConversationManager."""
    # Create a conversation manager
    manager = ConversationManager(agent_id="test_agent")
    
    # Add an entry
    entry = manager.add_entry(
        role=ConversationRole.USER,
        content="Hello, agent!",
    )
    
    # Check the entry
    assert entry.role == ConversationRole.USER
    assert entry.content == "Hello, agent!"
    assert isinstance(entry.timestamp, datetime)
    
    # Check that the entry was added to the history
    assert len(manager.history) == 1
    assert manager.history[0] == entry


def test_conversation_manager_add_entry_with_timestamp():
    """Test the add_entry method with a custom timestamp."""
    # Create a conversation manager
    manager = ConversationManager(agent_id="test_agent")
    
    # Add an entry with a custom timestamp
    timestamp = datetime(2023, 1, 1, 12, 0, 0)
    entry = manager.add_entry(
        role=ConversationRole.USER,
        content="Hello, agent!",
        timestamp=timestamp,
    )
    
    # Check the entry
    assert entry.role == ConversationRole.USER
    assert entry.content == "Hello, agent!"
    assert entry.timestamp == timestamp
    
    # Check that the entry was added to the history
    assert len(manager.history) == 1
    assert manager.history[0] == entry


def test_conversation_manager_add_entry_max_history():
    """Test that the history is truncated when it exceeds max_history_length."""
    # Create a conversation manager with a small max_history_length
    manager = ConversationManager(agent_id="test_agent", max_history_length=3)
    
    # Add 4 entries
    for i in range(4):
        manager.add_entry(
            role=ConversationRole.USER,
            content=f"Message {i}",
        )
    
    # Check that the history was truncated
    assert len(manager.history) == 3
    assert manager.history[0].content == "Message 1"
    assert manager.history[1].content == "Message 2"
    assert manager.history[2].content == "Message 3"


def test_conversation_manager_get_history():
    """Test the get_history method of ConversationManager."""
    # Create a conversation manager
    manager = ConversationManager(agent_id="test_agent")
    
    # Add some entries
    manager.add_entry(
        role=ConversationRole.USER,
        content="Hello, agent!",
    )
    manager.add_entry(
        role=ConversationRole.ASSISTANT,
        content="Hello, user!",
    )
    manager.add_entry(
        role=ConversationRole.USER,
        content="How are you?",
    )
    
    # Get the history
    history = manager.get_history()
    
    # Check the history
    assert len(history) == 3
    assert history[0].role == ConversationRole.USER
    assert history[0].content == "Hello, agent!"
    assert history[1].role == ConversationRole.ASSISTANT
    assert history[1].content == "Hello, user!"
    assert history[2].role == ConversationRole.USER
    assert history[2].content == "How are you?"


def test_conversation_manager_get_history_limit():
    """Test the get_history method with a limit."""
    # Create a conversation manager
    manager = ConversationManager(agent_id="test_agent")
    
    # Add some entries
    manager.add_entry(
        role=ConversationRole.USER,
        content="Hello, agent!",
    )
    manager.add_entry(
        role=ConversationRole.ASSISTANT,
        content="Hello, user!",
    )
    manager.add_entry(
        role=ConversationRole.USER,
        content="How are you?",
    )
    
    # Get the history with a limit
    history = manager.get_history(limit=2)
    
    # Check the history
    assert len(history) == 2
    assert history[0].role == ConversationRole.ASSISTANT
    assert history[0].content == "Hello, user!"
    assert history[1].role == ConversationRole.USER
    assert history[1].content == "How are you?"


def test_conversation_manager_clear_history():
    """Test the clear_history method of ConversationManager."""
    # Create a conversation manager
    manager = ConversationManager(agent_id="test_agent")
    
    # Add some entries
    manager.add_entry(
        role=ConversationRole.USER,
        content="Hello, agent!",
    )
    manager.add_entry(
        role=ConversationRole.ASSISTANT,
        content="Hello, user!",
    )
    
    # Clear the history
    manager.clear_history()
    
    # Check that the history is empty
    assert manager.history == []


def test_conversation_manager_to_dict():
    """Test the to_dict method of ConversationManager."""
    # Create a conversation manager
    manager = ConversationManager(agent_id="test_agent")
    
    # Add some entries
    manager.add_entry(
        role=ConversationRole.USER,
        content="Hello, agent!",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    manager.add_entry(
        role=ConversationRole.ASSISTANT,
        content="Hello, user!",
        timestamp=datetime(2023, 1, 1, 12, 1, 0),
    )
    
    # Convert to dict
    manager_dict = manager.to_dict()
    
    # Check the dict
    assert manager_dict["agent_id"] == "test_agent"
    assert len(manager_dict["history"]) == 2
    assert manager_dict["history"][0]["role"] == "user"
    assert manager_dict["history"][0]["content"] == "Hello, agent!"
    assert manager_dict["history"][0]["timestamp"] == "2023-01-01T12:00:00"
    assert manager_dict["history"][1]["role"] == "assistant"
    assert manager_dict["history"][1]["content"] == "Hello, user!"
    assert manager_dict["history"][1]["timestamp"] == "2023-01-01T12:01:00"


def test_conversation_manager_from_dict():
    """Test the from_dict method of ConversationManager."""
    # Create a dict
    manager_dict = {
        "agent_id": "test_agent",
        "history": [
            {
                "role": "user",
                "content": "Hello, agent!",
                "timestamp": "2023-01-01T12:00:00",
            },
            {
                "role": "assistant",
                "content": "Hello, user!",
                "timestamp": "2023-01-01T12:01:00",
            },
        ],
    }
    
    # Convert to ConversationManager
    manager = ConversationManager.from_dict(manager_dict)
    
    # Check the manager
    assert manager.agent_id == "test_agent"
    assert len(manager.history) == 2
    assert manager.history[0].role == ConversationRole.USER
    assert manager.history[0].content == "Hello, agent!"
    assert manager.history[0].timestamp == datetime(2023, 1, 1, 12, 0, 0)
    assert manager.history[1].role == ConversationRole.ASSISTANT
    assert manager.history[1].content == "Hello, user!"
    assert manager.history[1].timestamp == datetime(2023, 1, 1, 12, 1, 0)


def test_conversation_manager_from_dict_invalid_history():
    """Test the from_dict method with an invalid history."""
    # Create a dict with an invalid history
    manager_dict = {
        "agent_id": "test_agent",
        "history": [
            {
                "role": "invalid_role",
                "content": "Hello, agent!",
                "timestamp": "2023-01-01T12:00:00",
            },
        ],
    }
    
    # Try to convert to ConversationManager
    with pytest.raises(ValueError):
        ConversationManager.from_dict(manager_dict)


@patch("custom_components.cortex_agent.conversation_manager.json")
def test_conversation_manager_save_to_file(mock_json):
    """Test the save_to_file method of ConversationManager."""
    # Create a conversation manager
    manager = ConversationManager(agent_id="test_agent")
    
    # Add some entries
    manager.add_entry(
        role=ConversationRole.USER,
        content="Hello, agent!",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    # Mock open
    mock_open = MagicMock()
    with patch("builtins.open", mock_open):
        # Save to file
        manager.save_to_file("/path/to/file.json")
    
    # Check that open was called with the right arguments
    mock_open.assert_called_once_with("/path/to/file.json", "w")
    
    # Check that json.dump was called with the right arguments
    mock_json.dump.assert_called_once()
    args, kwargs = mock_json.dump.call_args
    assert args[0] == manager.to_dict()
    assert args[1] == mock_open().__enter__()


@patch("custom_components.cortex_agent.conversation_manager.json")
def test_conversation_manager_save_to_file_error(mock_json):
    """Test the save_to_file method with an error."""
    # Create a conversation manager
    manager = ConversationManager(agent_id="test_agent")
    
    # Mock open to raise an exception
    mock_open = MagicMock()
    mock_open.side_effect = IOError("File error")
    
    # Try to save to file
    with patch("builtins.open", mock_open):
        with pytest.raises(ConversationError):
            manager.save_to_file("/path/to/file.json")


@patch("custom_components.cortex_agent.conversation_manager.json")
def test_conversation_manager_load_from_file(mock_json):
    """Test the load_from_file method of ConversationManager."""
    # Create a dict
    manager_dict = {
        "agent_id": "test_agent",
        "history": [
            {
                "role": "user",
                "content": "Hello, agent!",
                "timestamp": "2023-01-01T12:00:00",
            },
        ],
    }
    
    # Mock json.load to return the dict
    mock_json.load.return_value = manager_dict
    
    # Mock open
    mock_open = MagicMock()
    with patch("builtins.open", mock_open):
        # Load from file
        manager = ConversationManager.load_from_file("/path/to/file.json")
    
    # Check that open was called with the right arguments
    mock_open.assert_called_once_with("/path/to/file.json", "r")
    
    # Check that json.load was called with the right arguments
    mock_json.load.assert_called_once_with(mock_open().__enter__())
    
    # Check the manager
    assert manager.agent_id == "test_agent"
    assert len(manager.history) == 1
    assert manager.history[0].role == ConversationRole.USER
    assert manager.history[0].content == "Hello, agent!"
    assert manager.history[0].timestamp == datetime(2023, 1, 1, 12, 0, 0)


@patch("custom_components.cortex_agent.conversation_manager.json")
def test_conversation_manager_load_from_file_error(mock_json):
    """Test the load_from_file method with an error."""
    # Mock open to raise an exception
    mock_open = MagicMock()
    mock_open.side_effect = IOError("File error")
    
    # Try to load from file
    with patch("builtins.open", mock_open):
        with pytest.raises(ConversationError):
            ConversationManager.load_from_file("/path/to/file.json")


@patch("custom_components.cortex_agent.conversation_manager.json")
def test_conversation_manager_load_from_file_invalid_json(mock_json):
    """Test the load_from_file method with invalid JSON."""
    # Mock json.load to raise an exception
    mock_json.load.side_effect = json.JSONDecodeError("JSON error", "", 0)
    
    # Mock open
    mock_open = MagicMock()
    with patch("builtins.open", mock_open):
        # Try to load from file
        with pytest.raises(ConversationError):
            ConversationManager.load_from_file("/path/to/file.json")