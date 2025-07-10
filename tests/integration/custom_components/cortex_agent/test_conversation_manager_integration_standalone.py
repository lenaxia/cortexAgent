"""Standalone integration tests for the ConversationManager implementation."""
import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

# Import the actual implementation
from custom_components.cortex_agent.conversation_manager import ConversationManager
from custom_components.cortex_agent.models import ConversationRole, ConversationEntry


# Mock classes for testing
class MockStore:
    """Mock storage for testing."""
    def __init__(self):
        self.data = None
        
    async def async_load(self):
        """Load data."""
        return self.data
        
    async def async_save(self, data):
        """Save data."""
        self.data = data


class MockMemoryHandler:
    """Mock memory handler for testing."""
    def __init__(self):
        self.memories = []
        self.stored_memories = []
        
    async def retrieve_memories(self, conversation_id, recent_messages=None):
        """Retrieve memories."""
        return self.memories
        
    async def store_memory(self, content, conversation_id, metadata=None):
        """Store memory."""
        self.stored_memories.append({
            "content": content,
            "conversation_id": conversation_id,
            "metadata": metadata or {}
        })


class MockModelProvider:
    """Mock model provider for testing."""
    def get_token_count(self, text):
        """Get token count."""
        # Simple approximation: 1 token per 4 characters
        return len(text) // 4 + 1


# Integration tests
async def test_conversation_flow_happy_path():
    """Test a complete conversation flow with pruning and persistence."""
    # Initialize mocks
    store = MockStore()
    memory_handler = MockMemoryHandler()
    
    # Initialize the conversation manager with storage
    manager = ConversationManager(
        conversation_id="test_conv",
        max_messages=5,
        max_age_hours=24,
        max_tokens=100,
        storage=store
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
    assert "history" in store.data
    assert len(store.data["history"]) == 4
    assert store.data["history"][0]["role"] == "system"
    assert store.data["history"][0]["content"] == "You are a helpful assistant."
    
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
    
    print("✅ test_conversation_flow_happy_path passed")


async def test_conversation_load_and_resume():
    """Test loading a saved conversation and resuming it."""
    # Initialize mocks
    store = MockStore()
    
    # Mock existing data
    store.data = {
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
    
    # Initialize and load
    manager = ConversationManager(
        conversation_id="test_conv",
        max_messages=5,
        max_tokens=100,
        storage=store
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
    assert len(store.data["history"]) == 4
    
    print("✅ test_conversation_load_and_resume passed")


async def test_token_based_pruning():
    """Test pruning based on token count."""
    # Set a very low token limit
    manager = ConversationManager(
        conversation_id="test_conv",
        max_tokens=50
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
    assert "message 9" in manager.history[-2].content or "response 9" in manager.history[-1].content
    
    print("✅ test_token_based_pruning passed")


async def test_unhappy_path_storage_failure():
    """Test handling storage failures gracefully."""
    # Make storage fail
    store = MockStore()
    store.async_save = AsyncMock(side_effect=Exception("Storage failure"))
    
    manager = ConversationManager(
        conversation_id="test_conv",
        storage=store
    )
    
    # Add some messages
    manager.add_entry(ConversationRole.USER, "Hello")
    manager.add_entry(ConversationRole.ASSISTANT, "Hi there!")
    
    # Save should handle the exception
    try:
        await manager.save()
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert str(e) == "Storage failure"
    
    # Manager should still be usable
    manager.add_entry(ConversationRole.USER, "Are you still there?")
    assert len(manager.history) == 3
    
    print("✅ test_unhappy_path_storage_failure passed")


async def test_unhappy_path_invalid_load_data():
    """Test handling invalid data during load."""
    # Mock invalid data
    store = MockStore()
    store.data = {"invalid": "data"}
    
    manager = ConversationManager(
        conversation_id="test_conv",
        storage=store
    )
    
    # Load should handle the invalid data gracefully
    await manager.load()
    
    # History should be empty but loaded flag set
    assert manager._loaded is True
    assert len(manager.history) == 0
    
    # Manager should still be usable
    manager.add_entry(ConversationRole.USER, "Hello")
    assert len(manager.history) == 1
    
    print("✅ test_unhappy_path_invalid_load_data passed")


async def test_unhappy_path_corrupted_timestamps():
    """Test handling corrupted timestamps in loaded data."""
    # Mock data with invalid timestamp
    store = MockStore()
    store.data = {
        "history": [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": "invalid-timestamp",
                "metadata": {}
            }
        ]
    }
    
    manager = ConversationManager(
        conversation_id="test_conv",
        storage=store
    )
    
    # Load should handle the invalid timestamp
    try:
        await manager.load()
        assert False, "Expected exception for invalid timestamp"
    except ValueError:
        # This is expected
        pass
    
    print("✅ test_unhappy_path_corrupted_timestamps passed")


async def test_integration_with_memory_handler():
    """Test integration with memory handler."""
    memory_handler = MockMemoryHandler()
    
    manager = ConversationManager(
        conversation_id="test_conv",
        max_messages=5
    )
    
    # Add some messages
    manager.add_entry(ConversationRole.SYSTEM, "You are a helpful assistant.")
    manager.add_entry(ConversationRole.USER, "My name is John.")
    manager.add_entry(ConversationRole.ASSISTANT, "Nice to meet you, John!")
    
    # Mock memory retrieval
    memory_handler.memories = [
        {"content": "User's name is John", "last_accessed": datetime.now().isoformat()}
    ]
    
    # Get conversation with memories
    conversation_with_memories = await manager.get_conversation_with_memories(memory_handler)
    
    # Should include both history and memories
    assert len(conversation_with_memories) > len(manager.history)
    
    # Memory should be stored after user message
    await manager.add_entry_and_store_memory(
        ConversationRole.USER, 
        "I live in New York.", 
        memory_handler
    )
    
    # Memory handler should have been called
    assert len(memory_handler.stored_memories) == 1
    assert "New York" in memory_handler.stored_memories[0]["content"]
    
    print("✅ test_integration_with_memory_handler passed")


async def test_concurrent_access():
    """Test concurrent access to the conversation manager."""
    manager = ConversationManager(
        conversation_id="test_conv",
        max_messages=10
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
    # But max_messages is 10, so one message should be pruned
    assert len(manager.history) == 10
    
    # System message should be preserved
    assert manager.history[0].role == ConversationRole.SYSTEM
    
    print("✅ test_concurrent_access passed")


async def run_all_tests():
    """Run all tests."""
    print("Running standalone integration tests for ConversationManager...")
    
    await test_conversation_flow_happy_path()
    await test_conversation_load_and_resume()
    await test_token_based_pruning()
    await test_unhappy_path_storage_failure()
    await test_unhappy_path_invalid_load_data()
    await test_unhappy_path_corrupted_timestamps()
    await test_integration_with_memory_handler()
    await test_concurrent_access()
    
    print("All integration tests passed! ✅")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(run_all_tests())