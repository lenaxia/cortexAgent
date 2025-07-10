"""Integration tests for the ConversationManager implementation."""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
import json
import os

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from custom_components.cortex_agent.models import ConversationRole, ConversationEntry
from custom_components.cortex_agent.conversation_manager import ConversationManager
from custom_components.cortex_agent.model_provider import ModelProvider
from custom_components.cortex_agent.memory_handler import MemoryHandler


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock()
    hass.config.path = MagicMock(return_value="/config")
    return hass


@pytest.fixture
def mock_store(mock_hass):
    """Mock storage for testing."""
    store = Store(mock_hass, 1, "cortex_agent/conversations/test_conv")
    store.async_load = AsyncMock(return_value=None)
    store.async_save = AsyncMock()
    return store


@pytest.fixture
def mock_model_provider():
    """Mock model provider for testing."""
    provider = MagicMock(spec=ModelProvider)
    provider.get_token_count = MagicMock(return_value=10)  # Mock token count calculation
    return provider


@pytest.fixture
def mock_memory_handler():
    """Mock memory handler for testing."""
    handler = MagicMock(spec=MemoryHandler)
    handler.store_memory = AsyncMock()
    handler.retrieve_memories = AsyncMock(return_value=[])
    return handler


class TestConversationManagerIntegration:
    """Integration tests for ConversationManager."""

    async def test_conversation_flow_happy_path(self, mock_store, mock_model_provider, mock_memory_handler):
        """Test a complete conversation flow with pruning and persistence."""
        # Initialize the conversation manager with storage
        manager = ConversationManager(
            conversation_id="test_conv",
            max_messages=5,
            max_age_hours=24,
            max_tokens=100,
            storage=mock_store
        )
        
        # Add system message (should be preserved)
        manager.add_entry(ConversationRole.SYSTEM, "You are a helpful assistant.")
        
        # Add user and assistant messages
        manager.add_entry(ConversationRole.USER, "Hello")
        manager.add_entry(ConversationRole.ASSISTANT, "Hi there! How can I help you today?")
        manager.add_entry(ConversationRole.USER, "What's the weather like?")
        
        # Save the conversation
        await manager.save()
        
        # Verify storage was called with correct data
        mock_store.async_save.assert_called_once()
        saved_data = mock_store.async_save.call_args[0][0]
        assert "history" in saved_data
        assert len(saved_data["history"]) == 4
        assert saved_data["history"][0]["role"] == "system"
        assert saved_data["history"][0]["content"] == "You are a helpful assistant."
        
        # Add more messages to trigger pruning
        manager.add_entry(ConversationRole.ASSISTANT, "I don't have access to weather information.")
        manager.add_entry(ConversationRole.USER, "Tell me a joke then.")
        manager.add_entry(ConversationRole.ASSISTANT, "Why did the chicken cross the road?")
        
        # Should have pruned to max_messages (5), but kept the system message
        assert len(manager.history) == 5
        assert manager.history[0].role == ConversationRole.SYSTEM
        assert manager.history[0].content == "You are a helpful assistant."
        
        # Get formatted history for model consumption
        formatted = manager.get_formatted_history()
        assert len(formatted) == 5
        assert formatted[0]["role"] == "system"
        
        # Test caching - get formatted history again
        formatted_again = manager.get_formatted_history()
        assert formatted is formatted_again  # Should be the same object due to caching
        
        # Add another message to invalidate cache
        manager.add_entry(ConversationRole.USER, "To get to the other side?")
        
        # Get updated formatted history
        updated_formatted = manager.get_formatted_history()
        assert updated_formatted is not formatted  # Should be a different object
        assert len(updated_formatted) == 5  # Still limited to 5 messages
        
        # Save again
        await manager.save()
        assert mock_store.async_save.call_count == 2

    async def test_conversation_load_and_resume(self, mock_store, mock_model_provider):
        """Test loading a saved conversation and resuming it."""
        # Mock existing data
        existing_data = {
            "history": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {}
                },
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {}
                },
                {
                    "role": "assistant", 
                    "content": "Hi there! How can I help you today?",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {}
                }
            ]
        }
        mock_store.async_load.return_value = existing_data
        
        # Initialize and load
        manager = ConversationManager(
            conversation_id="test_conv",
            max_messages=5,
            max_tokens=100,
            storage=mock_store
        )
        
        await manager.load()
        
        # Check that history was loaded
        assert manager._loaded is True
        assert len(manager.history) == 3
        assert manager.history[0].role == ConversationRole.SYSTEM
        assert manager.history[0].content == "You are a helpful assistant."
        assert manager.history[1].role == ConversationRole.USER
        assert manager.history[1].content == "Hello"
        
        # Resume conversation
        manager.add_entry(ConversationRole.USER, "What's the weather like?")
        
        # Check that the system message is still preserved
        assert len(manager.history) == 4
        assert manager.history[0].role == ConversationRole.SYSTEM
        
        # Save the updated conversation
        await manager.save()
        
        # Verify storage was called with correct data
        saved_data = mock_store.async_save.call_args[0][0]
        assert len(saved_data["history"]) == 4

    async def test_token_based_pruning(self, mock_store, mock_model_provider):
        """Test pruning based on token count."""
        # Set a very low token limit
        manager = ConversationManager(
            conversation_id="test_conv",
            max_tokens=50,
            storage=mock_store
        )
        
        # Add system message (should be preserved)
        manager.add_entry(ConversationRole.SYSTEM, "You are a helpful assistant.")
        
        # Add messages that exceed the token limit
        for i in range(10):
            manager.add_entry(ConversationRole.USER, f"This is message {i} with some extra text to increase token count")
            manager.add_entry(ConversationRole.ASSISTANT, f"This is response {i} with even more text to ensure we exceed the token limit")
        
        # Should have pruned to keep under the token limit, but kept the system message
        assert len(manager.history) < 20  # Should be significantly less than the 21 total messages
        assert manager.history[0].role == ConversationRole.SYSTEM
        assert manager.history[0].content == "You are a helpful assistant."
        
        # The most recent messages should be kept
        assert "message 9" in manager.history[-2].content
        assert "response 9" in manager.history[-1].content

    async def test_unhappy_path_storage_failure(self, mock_store):
        """Test handling storage failures gracefully."""
        # Make storage fail
        mock_store.async_save.side_effect = Exception("Storage failure")
        
        manager = ConversationManager(
            conversation_id="test_conv",
            storage=mock_store
        )
        
        # Add some messages
        manager.add_entry(ConversationRole.USER, "Hello")
        manager.add_entry(ConversationRole.ASSISTANT, "Hi there!")
        
        # Save should handle the exception
        with pytest.raises(Exception, match="Storage failure"):
            await manager.save()
        
        # Manager should still be usable
        manager.add_entry(ConversationRole.USER, "Are you still there?")
        assert len(manager.history) == 3

    async def test_unhappy_path_invalid_load_data(self, mock_store):
        """Test handling invalid data during load."""
        # Mock invalid data
        mock_store.async_load.return_value = {"invalid": "data"}
        
        manager = ConversationManager(
            conversation_id="test_conv",
            storage=mock_store
        )
        
        # Load should handle the invalid data gracefully
        await manager.load()
        
        # History should be empty but loaded flag set
        assert manager._loaded is True
        assert len(manager.history) == 0
        
        # Manager should still be usable
        manager.add_entry(ConversationRole.USER, "Hello")
        assert len(manager.history) == 1

    async def test_unhappy_path_corrupted_timestamps(self, mock_store):
        """Test handling corrupted timestamps in loaded data."""
        # Mock data with invalid timestamp
        existing_data = {
            "history": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "invalid-timestamp",
                    "metadata": {}
                }
            ]
        }
        mock_store.async_load.return_value = existing_data
        
        manager = ConversationManager(
            conversation_id="test_conv",
            storage=mock_store
        )
        
        # Load should handle the invalid timestamp
        await manager.load()
        
        # History should contain the message with a default timestamp
        assert len(manager.history) == 1
        assert manager.history[0].content == "Hello"
        assert isinstance(manager.history[0].timestamp, datetime)

    async def test_integration_with_memory_handler(self, mock_store, mock_memory_handler):
        """Test integration with memory handler."""
        manager = ConversationManager(
            conversation_id="test_conv",
            max_messages=5,
            storage=mock_store
        )
        
        # Add some messages
        manager.add_entry(ConversationRole.SYSTEM, "You are a helpful assistant.")
        manager.add_entry(ConversationRole.USER, "My name is John.")
        manager.add_entry(ConversationRole.ASSISTANT, "Nice to meet you, John!")
        
        # Mock memory retrieval
        mock_memory_handler.retrieve_memories.return_value = [
            {"content": "User's name is John", "last_accessed": datetime.now().isoformat()}
        ]
        
        # Get conversation with memories
        conversation_with_memories = await manager.get_conversation_with_memories(mock_memory_handler)
        
        # Should include both history and memories
        assert len(conversation_with_memories) > len(manager.history)
        
        # Memory should be stored after user message
        await manager.add_entry_and_store_memory(
            ConversationRole.USER, 
            "I live in New York.", 
            mock_memory_handler
        )
        
        # Memory handler should have been called
        mock_memory_handler.store_memory.assert_called_once()
        assert "New York" in mock_memory_handler.store_memory.call_args[0][0]

    async def test_concurrent_access(self, mock_store):
        """Test concurrent access to the conversation manager."""
        manager = ConversationManager(
            conversation_id="test_conv",
            max_messages=10,
            storage=mock_store
        )
        
        # Add initial message
        manager.add_entry(ConversationRole.SYSTEM, "You are a helpful assistant.")
        
        # Simulate concurrent access
        async def add_messages(prefix, count):
            for i in range(count):
                manager.add_entry(ConversationRole.USER, f"{prefix} message {i}")
                await asyncio.sleep(0.01)  # Small delay to simulate processing
                manager.add_entry(ConversationRole.ASSISTANT, f"Response to {prefix} {i}")
        
        # Run concurrent tasks
        await asyncio.gather(
            add_messages("Task1", 5),
            add_messages("Task2", 5)
        )
        
        # Should have 11 messages total (1 system + 5*2 from each task)
        assert len(manager.history) == 11
        
        # Should have pruned to 10 messages
        assert len(manager.history) == 10
        
        # System message should be preserved
        assert manager.history[0].role == ConversationRole.SYSTEM