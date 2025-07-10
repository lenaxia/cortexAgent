"""Tests for the CortexAgent memory_handler module."""
from unittest.mock import MagicMock, patch, mock_open
import json
from datetime import datetime
import os

import pytest

from custom_components.cortex_agent.memory_handler import (
    MemoryHandler,
    Memory,
)
from custom_components.cortex_agent.exceptions import MemoryError


def test_memory_init():
    """Test the initialization of a Memory."""
    # Create a memory
    memory = Memory(
        memory_id="memory_123",
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    # Check the memory properties
    assert memory.memory_id == "memory_123"
    assert memory.agent_id == "test_agent"
    assert memory.content == "This is a test memory"
    assert memory.metadata == {"category": "test"}
    assert memory.timestamp == datetime(2023, 1, 1, 12, 0, 0)


def test_memory_to_dict():
    """Test the to_dict method of Memory."""
    # Create a memory
    memory = Memory(
        memory_id="memory_123",
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    # Convert to dict
    memory_dict = memory.to_dict()
    
    # Check the dict
    assert memory_dict["memory_id"] == "memory_123"
    assert memory_dict["agent_id"] == "test_agent"
    assert memory_dict["content"] == "This is a test memory"
    assert memory_dict["metadata"] == {"category": "test"}
    assert memory_dict["timestamp"] == "2023-01-01T12:00:00"


def test_memory_from_dict():
    """Test the from_dict method of Memory."""
    # Create a dict
    memory_dict = {
        "memory_id": "memory_123",
        "agent_id": "test_agent",
        "content": "This is a test memory",
        "metadata": {"category": "test"},
        "timestamp": "2023-01-01T12:00:00",
    }
    
    # Convert to Memory
    memory = Memory.from_dict(memory_dict)
    
    # Check the memory
    assert memory.memory_id == "memory_123"
    assert memory.agent_id == "test_agent"
    assert memory.content == "This is a test memory"
    assert memory.metadata == {"category": "test"}
    assert memory.timestamp == datetime(2023, 1, 1, 12, 0, 0)


def test_memory_from_dict_invalid_timestamp():
    """Test the from_dict method with an invalid timestamp."""
    # Create a dict with an invalid timestamp
    memory_dict = {
        "memory_id": "memory_123",
        "agent_id": "test_agent",
        "content": "This is a test memory",
        "metadata": {"category": "test"},
        "timestamp": "invalid_timestamp",
    }
    
    # Try to convert to Memory
    with pytest.raises(ValueError):
        Memory.from_dict(memory_dict)


def test_memory_handler_init():
    """Test the initialization of a MemoryHandler."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Check the handler properties
    assert handler.hass == mock_hass
    assert handler.memories == {}


@patch("custom_components.cortex_agent.memory_handler.uuid")
def test_memory_handler_store(mock_uuid):
    """Test the store method of MemoryHandler."""
    # Set up the mock uuid
    mock_uuid.uuid4.return_value = "memory_123"
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Store a memory
    memory_id = handler.store(
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
    )
    
    # Check the memory_id
    assert memory_id == "memory_123"
    
    # Check that the memory was stored
    assert "test_agent" in handler.memories
    assert "memory_123" in handler.memories["test_agent"]
    
    memory = handler.memories["test_agent"]["memory_123"]
    assert memory.memory_id == "memory_123"
    assert memory.agent_id == "test_agent"
    assert memory.content == "This is a test memory"
    assert memory.metadata == {"category": "test"}
    assert isinstance(memory.timestamp, datetime)


@patch("custom_components.cortex_agent.memory_handler.uuid")
def test_memory_handler_store_with_timestamp(mock_uuid):
    """Test the store method with a custom timestamp."""
    # Set up the mock uuid
    mock_uuid.uuid4.return_value = "memory_123"
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Store a memory with a custom timestamp
    timestamp = datetime(2023, 1, 1, 12, 0, 0)
    memory_id = handler.store(
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
        timestamp=timestamp,
    )
    
    # Check the memory_id
    assert memory_id == "memory_123"
    
    # Check that the memory was stored
    assert "test_agent" in handler.memories
    assert "memory_123" in handler.memories["test_agent"]
    
    memory = handler.memories["test_agent"]["memory_123"]
    assert memory.memory_id == "memory_123"
    assert memory.agent_id == "test_agent"
    assert memory.content == "This is a test memory"
    assert memory.metadata == {"category": "test"}
    assert memory.timestamp == timestamp


def test_memory_handler_retrieve():
    """Test the retrieve method of MemoryHandler."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Store a memory
    memory = Memory(
        memory_id="memory_123",
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    # Add the memory to the handler
    handler.memories["test_agent"] = {"memory_123": memory}
    
    # Retrieve the memory
    retrieved_memory = handler.retrieve(
        memory_id="memory_123",
        agent_id="test_agent",
    )
    
    # Check the retrieved memory
    assert retrieved_memory == memory


def test_memory_handler_retrieve_not_found():
    """Test the retrieve method with a memory that doesn't exist."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Try to retrieve a non-existent memory
    retrieved_memory = handler.retrieve(
        memory_id="non_existent_memory",
        agent_id="test_agent",
    )
    
    # Check that None was returned
    assert retrieved_memory is None


def test_memory_handler_list_memories():
    """Test the list_memories method of MemoryHandler."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Store some memories
    memory1 = Memory(
        memory_id="memory_123",
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    memory2 = Memory(
        memory_id="memory_456",
        agent_id="test_agent",
        content="This is another test memory",
        metadata={"category": "test"},
        timestamp=datetime(2023, 1, 2, 12, 0, 0),
    )
    
    # Add the memories to the handler
    handler.memories["test_agent"] = {
        "memory_123": memory1,
        "memory_456": memory2,
    }
    
    # List the memories
    memories = handler.list_memories(agent_id="test_agent")
    
    # Check the memories
    assert len(memories) == 2
    assert memories[0] == memory1.to_dict()
    assert memories[1] == memory2.to_dict()


def test_memory_handler_list_memories_with_filters():
    """Test the list_memories method with filters."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Store some memories
    memory1 = Memory(
        memory_id="memory_123",
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test1"},
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    memory2 = Memory(
        memory_id="memory_456",
        agent_id="test_agent",
        content="This is another test memory",
        metadata={"category": "test2"},
        timestamp=datetime(2023, 1, 2, 12, 0, 0),
    )
    
    # Add the memories to the handler
    handler.memories["test_agent"] = {
        "memory_123": memory1,
        "memory_456": memory2,
    }
    
    # List the memories with a filter
    memories = handler.list_memories(
        agent_id="test_agent",
        filters={"category": "test1"},
    )
    
    # Check the memories
    assert len(memories) == 1
    assert memories[0] == memory1.to_dict()


def test_memory_handler_list_memories_with_limit():
    """Test the list_memories method with a limit."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Store some memories
    memory1 = Memory(
        memory_id="memory_123",
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    memory2 = Memory(
        memory_id="memory_456",
        agent_id="test_agent",
        content="This is another test memory",
        metadata={"category": "test"},
        timestamp=datetime(2023, 1, 2, 12, 0, 0),
    )
    
    memory3 = Memory(
        memory_id="memory_789",
        agent_id="test_agent",
        content="This is a third test memory",
        metadata={"category": "test"},
        timestamp=datetime(2023, 1, 3, 12, 0, 0),
    )
    
    # Add the memories to the handler
    handler.memories["test_agent"] = {
        "memory_123": memory1,
        "memory_456": memory2,
        "memory_789": memory3,
    }
    
    # List the memories with a limit
    memories = handler.list_memories(
        agent_id="test_agent",
        limit=2,
    )
    
    # Check the memories
    assert len(memories) == 2
    # The memories should be sorted by timestamp, with the most recent first
    assert memories[0] == memory3.to_dict()
    assert memories[1] == memory2.to_dict()


def test_memory_handler_delete():
    """Test the delete method of MemoryHandler."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Store a memory
    memory = Memory(
        memory_id="memory_123",
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    # Add the memory to the handler
    handler.memories["test_agent"] = {"memory_123": memory}
    
    # Delete the memory
    result = handler.delete(
        memory_id="memory_123",
        agent_id="test_agent",
    )
    
    # Check the result
    assert result is True
    
    # Check that the memory was deleted
    assert "memory_123" not in handler.memories["test_agent"]


def test_memory_handler_delete_not_found():
    """Test the delete method with a memory that doesn't exist."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Try to delete a non-existent memory
    result = handler.delete(
        memory_id="non_existent_memory",
        agent_id="test_agent",
    )
    
    # Check the result
    assert result is False


@patch("custom_components.cortex_agent.memory_handler.json")
@patch("custom_components.cortex_agent.memory_handler.os.path.exists")
@patch("custom_components.cortex_agent.memory_handler.os.makedirs")
def test_memory_handler_save_to_file(mock_makedirs, mock_exists, mock_json):
    """Test the save_to_file method of MemoryHandler."""
    # Set up the mock os.path.exists
    mock_exists.return_value = False
    
    # Mock hass
    mock_hass = MagicMock()
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Store a memory
    memory = Memory(
        memory_id="memory_123",
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    
    # Add the memory to the handler
    handler.memories["test_agent"] = {"memory_123": memory}
    
    # Mock open
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        # Save to file
        handler.save_to_file()
    
    # Check that os.path.exists was called with the right arguments
    mock_exists.assert_called_once_with("/path/to/config/cortex_agent")
    
    # Check that os.makedirs was called with the right arguments
    mock_makedirs.assert_called_once_with("/path/to/config/cortex_agent")
    
    # Check that open was called with the right arguments
    mock_file.assert_called_once_with("/path/to/config/cortex_agent/memories.json", "w")
    
    # Check that json.dump was called with the right arguments
    mock_json.dump.assert_called_once()
    args, kwargs = mock_json.dump.call_args
    assert args[1] == mock_file()
    
    # Check the serialized memories
    serialized_memories = args[0]
    assert "test_agent" in serialized_memories
    assert "memory_123" in serialized_memories["test_agent"]
    assert serialized_memories["test_agent"]["memory_123"] == memory.to_dict()


@patch("custom_components.cortex_agent.memory_handler.json")
@patch("custom_components.cortex_agent.memory_handler.os.path.exists")
def test_memory_handler_save_to_file_error(mock_exists, mock_json):
    """Test the save_to_file method with an error."""
    # Set up the mock os.path.exists
    mock_exists.return_value = True
    
    # Mock hass
    mock_hass = MagicMock()
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Mock open to raise an exception
    mock_file = MagicMock()
    mock_file.side_effect = IOError("File error")
    
    # Try to save to file
    with patch("builtins.open", mock_file):
        with pytest.raises(MemoryError):
            handler.save_to_file()


@patch("custom_components.cortex_agent.memory_handler.json")
@patch("custom_components.cortex_agent.memory_handler.os.path.exists")
def test_memory_handler_load_from_file(mock_exists, mock_json):
    """Test the load_from_file method of MemoryHandler."""
    # Set up the mock os.path.exists
    mock_exists.return_value = True
    
    # Create a serialized memories dict
    serialized_memories = {
        "test_agent": {
            "memory_123": {
                "memory_id": "memory_123",
                "agent_id": "test_agent",
                "content": "This is a test memory",
                "metadata": {"category": "test"},
                "timestamp": "2023-01-01T12:00:00",
            }
        }
    }
    
    # Mock json.load to return the serialized memories
    mock_json.load.return_value = serialized_memories
    
    # Mock hass
    mock_hass = MagicMock()
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Mock open
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        # Load from file
        handler.load_from_file()
    
    # Check that os.path.exists was called with the right arguments
    mock_exists.assert_called_once_with("/path/to/config/cortex_agent/memories.json")
    
    # Check that open was called with the right arguments
    mock_file.assert_called_once_with("/path/to/config/cortex_agent/memories.json", "r")
    
    # Check that json.load was called with the right arguments
    mock_json.load.assert_called_once_with(mock_file())
    
    # Check the loaded memories
    assert "test_agent" in handler.memories
    assert "memory_123" in handler.memories["test_agent"]
    
    memory = handler.memories["test_agent"]["memory_123"]
    assert memory.memory_id == "memory_123"
    assert memory.agent_id == "test_agent"
    assert memory.content == "This is a test memory"
    assert memory.metadata == {"category": "test"}
    assert memory.timestamp == datetime(2023, 1, 1, 12, 0, 0)


@patch("custom_components.cortex_agent.memory_handler.os.path.exists")
def test_memory_handler_load_from_file_not_exists(mock_exists):
    """Test the load_from_file method when the file doesn't exist."""
    # Set up the mock os.path.exists
    mock_exists.return_value = False
    
    # Mock hass
    mock_hass = MagicMock()
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Load from file
    handler.load_from_file()
    
    # Check that os.path.exists was called with the right arguments
    mock_exists.assert_called_once_with("/path/to/config/cortex_agent/memories.json")
    
    # Check that the memories dict is empty
    assert handler.memories == {}


@patch("custom_components.cortex_agent.memory_handler.os.path.exists")
def test_memory_handler_load_from_file_error(mock_exists):
    """Test the load_from_file method with an error."""
    # Set up the mock os.path.exists
    mock_exists.return_value = True
    
    # Mock hass
    mock_hass = MagicMock()
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Mock open to raise an exception
    mock_file = MagicMock()
    mock_file.side_effect = IOError("File error")
    
    # Try to load from file
    with patch("builtins.open", mock_file):
        with pytest.raises(MemoryError):
            handler.load_from_file()


@patch("custom_components.cortex_agent.memory_handler.json")
@patch("custom_components.cortex_agent.memory_handler.os.path.exists")
def test_memory_handler_load_from_file_invalid_json(mock_exists, mock_json):
    """Test the load_from_file method with invalid JSON."""
    # Set up the mock os.path.exists
    mock_exists.return_value = True
    
    # Mock json.load to raise an exception
    mock_json.load.side_effect = json.JSONDecodeError("JSON error", "", 0)
    
    # Mock hass
    mock_hass = MagicMock()
    mock_hass.config.path.return_value = "/path/to/config"
    
    # Create a memory handler
    handler = MemoryHandler(mock_hass)
    
    # Mock open
    mock_file = mock_open()
    
    # Try to load from file
    with patch("builtins.open", mock_file):
        with pytest.raises(MemoryError):
            handler.load_from_file()