"""Tests for the CortexAgent memory_tools module."""
from unittest.mock import MagicMock, patch

import pytest

from custom_components.cortex_agent.tools.memory_tools import (
    store_memory,
    retrieve_memory,
    list_memories,
    delete_memory,
    tool_registry,
)


def test_tool_registry():
    """Test that the tool registry is initialized."""
    assert tool_registry is not None


@patch("custom_components.cortex_agent.tools.memory_tools.MemoryHandler")
def test_store_memory(mock_memory_handler):
    """Test the store_memory function."""
    # Set up the mock memory handler
    mock_handler_instance = MagicMock()
    mock_memory_handler.return_value = mock_handler_instance
    mock_handler_instance.store.return_value = "memory_id_123"
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call store_memory
    result = store_memory(
        mock_hass,
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
    )
    
    # Check that MemoryHandler was instantiated with the right arguments
    mock_memory_handler.assert_called_once_with(mock_hass)
    
    # Check that store was called with the right arguments
    mock_handler_instance.store.assert_called_once_with(
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
    )
    
    # Check the result
    assert result["success"] is True
    assert result["memory_id"] == "memory_id_123"
    assert result["agent_id"] == "test_agent"


@patch("custom_components.cortex_agent.tools.memory_tools.MemoryHandler")
def test_store_memory_error(mock_memory_handler):
    """Test the store_memory function with an error."""
    # Set up the mock memory handler
    mock_handler_instance = MagicMock()
    mock_memory_handler.return_value = mock_handler_instance
    mock_handler_instance.store.side_effect = Exception("Memory storage error")
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call store_memory
    result = store_memory(
        mock_hass,
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
    )
    
    # Check that MemoryHandler was instantiated with the right arguments
    mock_memory_handler.assert_called_once_with(mock_hass)
    
    # Check that store was called with the right arguments
    mock_handler_instance.store.assert_called_once_with(
        agent_id="test_agent",
        content="This is a test memory",
        metadata={"category": "test"},
    )
    
    # Check the result
    assert result["success"] is False
    assert "Memory storage error" in result["error"]


@patch("custom_components.cortex_agent.tools.memory_tools.MemoryHandler")
def test_retrieve_memory(mock_memory_handler):
    """Test the retrieve_memory function."""
    # Set up the mock memory handler
    mock_handler_instance = MagicMock()
    mock_memory_handler.return_value = mock_handler_instance
    mock_handler_instance.retrieve.return_value = {
        "memory_id": "memory_id_123",
        "agent_id": "test_agent",
        "content": "This is a test memory",
        "metadata": {"category": "test"},
        "timestamp": "2023-01-01T00:00:00+00:00",
    }
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call retrieve_memory
    result = retrieve_memory(
        mock_hass,
        memory_id="memory_id_123",
        agent_id="test_agent",
    )
    
    # Check that MemoryHandler was instantiated with the right arguments
    mock_memory_handler.assert_called_once_with(mock_hass)
    
    # Check that retrieve was called with the right arguments
    mock_handler_instance.retrieve.assert_called_once_with(
        memory_id="memory_id_123",
        agent_id="test_agent",
    )
    
    # Check the result
    assert result["success"] is True
    assert result["memory"]["memory_id"] == "memory_id_123"
    assert result["memory"]["agent_id"] == "test_agent"
    assert result["memory"]["content"] == "This is a test memory"
    assert result["memory"]["metadata"] == {"category": "test"}
    assert result["memory"]["timestamp"] == "2023-01-01T00:00:00+00:00"


@patch("custom_components.cortex_agent.tools.memory_tools.MemoryHandler")
def test_retrieve_memory_not_found(mock_memory_handler):
    """Test the retrieve_memory function with a memory that doesn't exist."""
    # Set up the mock memory handler
    mock_handler_instance = MagicMock()
    mock_memory_handler.return_value = mock_handler_instance
    mock_handler_instance.retrieve.return_value = None
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call retrieve_memory
    result = retrieve_memory(
        mock_hass,
        memory_id="non_existent_memory",
        agent_id="test_agent",
    )
    
    # Check that MemoryHandler was instantiated with the right arguments
    mock_memory_handler.assert_called_once_with(mock_hass)
    
    # Check that retrieve was called with the right arguments
    mock_handler_instance.retrieve.assert_called_once_with(
        memory_id="non_existent_memory",
        agent_id="test_agent",
    )
    
    # Check the result
    assert result["success"] is False
    assert "not found" in result["error"]


@patch("custom_components.cortex_agent.tools.memory_tools.MemoryHandler")
def test_list_memories(mock_memory_handler):
    """Test the list_memories function."""
    # Set up the mock memory handler
    mock_handler_instance = MagicMock()
    mock_memory_handler.return_value = mock_handler_instance
    mock_handler_instance.list_memories.return_value = [
        {
            "memory_id": "memory_id_123",
            "agent_id": "test_agent",
            "content": "This is a test memory",
            "metadata": {"category": "test"},
            "timestamp": "2023-01-01T00:00:00+00:00",
        },
        {
            "memory_id": "memory_id_456",
            "agent_id": "test_agent",
            "content": "This is another test memory",
            "metadata": {"category": "test"},
            "timestamp": "2023-01-02T00:00:00+00:00",
        },
    ]
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call list_memories
    result = list_memories(
        mock_hass,
        agent_id="test_agent",
        filters={"category": "test"},
        limit=10,
    )
    
    # Check that MemoryHandler was instantiated with the right arguments
    mock_memory_handler.assert_called_once_with(mock_hass)
    
    # Check that list_memories was called with the right arguments
    mock_handler_instance.list_memories.assert_called_once_with(
        agent_id="test_agent",
        filters={"category": "test"},
        limit=10,
    )
    
    # Check the result
    assert result["success"] is True
    assert len(result["memories"]) == 2
    assert result["memories"][0]["memory_id"] == "memory_id_123"
    assert result["memories"][0]["content"] == "This is a test memory"
    assert result["memories"][1]["memory_id"] == "memory_id_456"
    assert result["memories"][1]["content"] == "This is another test memory"


@patch("custom_components.cortex_agent.tools.memory_tools.MemoryHandler")
def test_list_memories_empty(mock_memory_handler):
    """Test the list_memories function with no memories."""
    # Set up the mock memory handler
    mock_handler_instance = MagicMock()
    mock_memory_handler.return_value = mock_handler_instance
    mock_handler_instance.list_memories.return_value = []
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call list_memories
    result = list_memories(
        mock_hass,
        agent_id="test_agent",
        filters={"category": "non_existent"},
        limit=10,
    )
    
    # Check that MemoryHandler was instantiated with the right arguments
    mock_memory_handler.assert_called_once_with(mock_hass)
    
    # Check that list_memories was called with the right arguments
    mock_handler_instance.list_memories.assert_called_once_with(
        agent_id="test_agent",
        filters={"category": "non_existent"},
        limit=10,
    )
    
    # Check the result
    assert result["success"] is True
    assert len(result["memories"]) == 0


@patch("custom_components.cortex_agent.tools.memory_tools.MemoryHandler")
def test_delete_memory(mock_memory_handler):
    """Test the delete_memory function."""
    # Set up the mock memory handler
    mock_handler_instance = MagicMock()
    mock_memory_handler.return_value = mock_handler_instance
    mock_handler_instance.delete.return_value = True
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call delete_memory
    result = delete_memory(
        mock_hass,
        memory_id="memory_id_123",
        agent_id="test_agent",
    )
    
    # Check that MemoryHandler was instantiated with the right arguments
    mock_memory_handler.assert_called_once_with(mock_hass)
    
    # Check that delete was called with the right arguments
    mock_handler_instance.delete.assert_called_once_with(
        memory_id="memory_id_123",
        agent_id="test_agent",
    )
    
    # Check the result
    assert result["success"] is True
    assert result["memory_id"] == "memory_id_123"
    assert result["agent_id"] == "test_agent"


@patch("custom_components.cortex_agent.tools.memory_tools.MemoryHandler")
def test_delete_memory_not_found(mock_memory_handler):
    """Test the delete_memory function with a memory that doesn't exist."""
    # Set up the mock memory handler
    mock_handler_instance = MagicMock()
    mock_memory_handler.return_value = mock_handler_instance
    mock_handler_instance.delete.return_value = False
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call delete_memory
    result = delete_memory(
        mock_hass,
        memory_id="non_existent_memory",
        agent_id="test_agent",
    )
    
    # Check that MemoryHandler was instantiated with the right arguments
    mock_memory_handler.assert_called_once_with(mock_hass)
    
    # Check that delete was called with the right arguments
    mock_handler_instance.delete.assert_called_once_with(
        memory_id="non_existent_memory",
        agent_id="test_agent",
    )
    
    # Check the result
    assert result["success"] is False
    assert "not found" in result["error"]