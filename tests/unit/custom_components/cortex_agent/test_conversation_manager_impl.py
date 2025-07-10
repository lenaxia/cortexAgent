"""Tests for the ConversationManager implementation."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta

from custom_components.cortex_agent.models import ConversationRole, ConversationEntry
from custom_components.cortex_agent.conversation_manager import ConversationManager


@pytest.fixture
def mock_storage():
    """Mock storage for testing."""
    storage = MagicMock()
    storage.async_load = AsyncMock(return_value=None)
    storage.async_save = AsyncMock()
    return storage


def test_conversation_manager_init():
    """Test ConversationManager initialization."""
    manager = ConversationManager(
        conversation_id="test_conv",
        max_messages=10,
        max_age_hours=24,
        max_tokens=8000
    )
    
    assert manager.conversation_id == "test_conv"
    assert manager.max_messages == 10
    assert manager.max_age_hours == 24
    assert manager.max_tokens == 8000
    assert manager.history == []
    assert manager._loaded is False
    assert manager._history_hash == 0
    assert manager._preserved_indices == set()


def test_conversation_manager_add_entry():
    """Test adding entries to conversation."""
    manager = ConversationManager("test_conv")
    
    # Add user message
    manager.add_entry(ConversationRole.USER, "Hello")
    
    assert len(manager.history) == 1
    assert manager.history[0].role == ConversationRole.USER
    assert manager.history[0].content == "Hello"
    assert isinstance(manager.history[0].timestamp, datetime)
    
    # Add assistant message
    manager.add_entry(ConversationRole.ASSISTANT, "Hi there!")
    
    assert len(manager.history) == 2
    assert manager.history[1].role == ConversationRole.ASSISTANT
    assert manager.history[1].content == "Hi there!"
    
    # Add system message (should be preserved during pruning)
    manager.add_entry(ConversationRole.SYSTEM, "System prompt")
    
    assert len(manager.history) == 3
    assert manager.history[2].role == ConversationRole.SYSTEM
    assert manager.history[2].content == "System prompt"
    assert 2 in manager._preserved_indices  # System message should be marked for preservation


def test_conversation_manager_add_entry_with_metadata():
    """Test adding entries with metadata."""
    manager = ConversationManager("test_conv")
    
    metadata = {"source": "test", "confidence": 0.9}
    manager.add_entry(ConversationRole.USER, "Hello", metadata)
    
    assert len(manager.history) == 1
    assert manager.history[0].metadata == metadata


def test_conversation_manager_get_history():
    """Test getting conversation history."""
    manager = ConversationManager("test_conv")
    
    # Add some messages
    manager.add_entry(ConversationRole.USER, "Hello")
    manager.add_entry(ConversationRole.ASSISTANT, "Hi!")
    manager.add_entry(ConversationRole.USER, "How are you?")
    
    # Get all history
    history = manager.get_history()
    assert len(history) == 3
    
    # Get limited history
    history = manager.get_history(limit=2)
    assert len(history) == 2
    assert history[0].content == "Hi!"  # Should get the most recent 2
    assert history[1].content == "How are you?"


def test_conversation_manager_get_formatted_history():
    """Test getting formatted history for model consumption."""
    manager = ConversationManager("test_conv")
    
    # Add some messages
    manager.add_entry(ConversationRole.USER, "Hello")
    manager.add_entry(ConversationRole.ASSISTANT, "Hi there!")
    
    # Get formatted history
    formatted = manager.get_formatted_history()
    
    assert len(formatted) == 2
    assert formatted[0] == {"role": "user", "content": "Hello"}
    assert formatted[1] == {"role": "assistant", "content": "Hi there!"}
    
    # Test caching - get formatted history again
    initial_history_hash = manager._history_hash
    formatted_again = manager.get_formatted_history(initial_history_hash)
    
    # Add another message to invalidate cache
    manager.add_entry(ConversationRole.USER, "How are you?")
    
    # Hash should have changed
    assert manager._history_hash != initial_history_hash
    
    # Get updated formatted history
    updated_formatted = manager.get_formatted_history()
    assert len(updated_formatted) == 3


def test_conversation_manager_clear_history():
    """Test clearing conversation history."""
    manager = ConversationManager("test_conv")
    
    # Add some messages
    manager.add_entry(ConversationRole.USER, "Hello")
    manager.add_entry(ConversationRole.ASSISTANT, "Hi!")
    
    assert len(manager.history) == 2
    
    # Clear history
    manager.clear_history()
    
    assert len(manager.history) == 0


def test_conversation_manager_prune_history():
    """Test the combined pruning strategy."""
    manager = ConversationManager("test_conv", max_messages=3)
    
    # Add more messages than the limit
    for i in range(5):
        manager.add_entry(ConversationRole.USER, f"Message {i}")
    
    # Should only keep the most recent 3
    assert len(manager.history) == 3
    assert manager.history[0].content == "Message 2"
    assert manager.history[1].content == "Message 3"
    assert manager.history[2].content == "Message 4"


def test_conversation_manager_prune_by_age():
    """Test pruning messages by age."""
    manager = ConversationManager("test_conv", max_age_hours=1)
    
    # Add old message
    old_entry = ConversationEntry(
        role=ConversationRole.USER,
        content="Old message",
        timestamp=datetime.now() - timedelta(hours=2)
    )
    manager.history.append(old_entry)
    
    # Add recent message
    manager.add_entry(ConversationRole.USER, "Recent message")
    
    # Should have pruned the old message automatically
    assert len(manager.history) == 1
    assert manager.history[0].content == "Recent message"


def test_conversation_manager_preserve_system_messages():
    """Test that system messages are preserved during pruning."""
    manager = ConversationManager("test_conv", max_messages=3)
    
    # Add system message (should be preserved)
    manager.add_entry(ConversationRole.SYSTEM, "System prompt")
    
    # Add more messages than the limit
    for i in range(5):
        manager.add_entry(ConversationRole.USER, f"Message {i}")
    
    # Should keep the system message and the most recent messages
    assert len(manager.history) == 3
    assert manager.history[0].role == ConversationRole.SYSTEM
    assert manager.history[0].content == "System prompt"
    # The other two should be the most recent user messages
    assert manager.history[1].content == "Message 3"
    assert manager.history[2].content == "Message 4"


def test_conversation_manager_mark_for_preservation():
    """Test marking messages for preservation."""
    manager = ConversationManager("test_conv", max_messages=3)
    
    # Add some messages
    manager.add_entry(ConversationRole.USER, "Message 0")
    manager.add_entry(ConversationRole.ASSISTANT, "Response 0")
    manager.add_entry(ConversationRole.USER, "Message 1")
    
    # Mark the first message for preservation
    manager.mark_for_preservation(0)
    
    # Add more messages to trigger pruning
    manager.add_entry(ConversationRole.ASSISTANT, "Response 1")
    manager.add_entry(ConversationRole.USER, "Message 2")
    
    # Should keep the preserved message and the most recent ones
    assert len(manager.history) == 3
    assert manager.history[0].content == "Message 0"  # Preserved
    assert manager.history[1].content == "Response 1"
    assert manager.history[2].content == "Message 2"


def test_conversation_manager_token_based_pruning():
    """Test pruning based on token count."""
    # Set a very low token limit (approximately 20 tokens)
    manager = ConversationManager("test_conv", max_tokens=20)
    
    # Add messages that exceed the token limit
    manager.add_entry(ConversationRole.USER, "This is a short message")  # ~5 tokens
    manager.add_entry(ConversationRole.ASSISTANT, "This is a longer response that should exceed the remaining token budget")  # ~15 tokens
    manager.add_entry(ConversationRole.USER, "Another message that should trigger pruning")  # ~8 tokens
    
    # Should have pruned to keep under the token limit
    assert len(manager.history) <= 2
    
    # The most recent message should be kept
    assert manager.history[-1].content == "Another message that should trigger pruning"


def test_conversation_manager_estimate_token_count():
    """Test estimating token count."""
    manager = ConversationManager("test_conv")
    
    # Add some messages
    manager.add_entry(ConversationRole.USER, "Hello")  # ~1 token
    manager.add_entry(ConversationRole.ASSISTANT, "Hi there!")  # ~2 tokens
    
    # Estimate should be roughly correct (using 4 chars ≈ 1 token)
    token_count = manager.estimate_token_count()
    assert 2 <= token_count <= 4  # Allow some flexibility in the estimate


async def test_conversation_manager_save_and_load(mock_storage):
    """Test saving and loading conversation."""
    manager = ConversationManager("test_conv", storage=mock_storage)
    
    # Add some messages
    manager.add_entry(ConversationRole.USER, "Hello")
    manager.add_entry(ConversationRole.ASSISTANT, "Hi!")
    
    # Save
    await manager.save()
    
    # Check that storage.async_save was called with correct data
    mock_storage.async_save.assert_called_once()
    saved_data = mock_storage.async_save.call_args[0][0]
    
    assert "history" in saved_data
    assert len(saved_data["history"]) == 2
    assert saved_data["history"][0]["role"] == "user"
    assert saved_data["history"][0]["content"] == "Hello"


async def test_conversation_manager_load_existing_data(mock_storage):
    """Test loading existing conversation data."""
    # Mock existing data
    existing_data = {
        "history": [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": datetime.now().isoformat(),
                "metadata": {}
            },
            {
                "role": "assistant", 
                "content": "Hi!",
                "timestamp": datetime.now().isoformat(),
                "metadata": {}
            }
        ]
    }
    mock_storage.async_load.return_value = existing_data
    
    manager = ConversationManager("test_conv", storage=mock_storage)
    
    # Load
    await manager.load()
    
    # Check that history was loaded
    assert manager._loaded is True
    assert len(manager.history) == 2
    assert manager.history[0].role == ConversationRole.USER
    assert manager.history[0].content == "Hello"
    assert manager.history[1].role == ConversationRole.ASSISTANT
    assert manager.history[1].content == "Hi!"


async def test_conversation_manager_load_no_existing_data(mock_storage):
    """Test loading when no existing data."""
    mock_storage.async_load.return_value = None
    
    manager = ConversationManager("test_conv", storage=mock_storage)
    
    # Load
    await manager.load()
    
    # Check that history is empty but loaded flag is set
    assert manager._loaded is True
    assert len(manager.history) == 0


def test_conversation_manager_auto_prune_on_add():
    """Test that adding entries automatically prunes when needed."""
    manager = ConversationManager("test_conv", max_messages=2)
    
    # Add messages that exceed the limit
    manager.add_entry(ConversationRole.USER, "Message 1")
    manager.add_entry(ConversationRole.ASSISTANT, "Response 1")
    manager.add_entry(ConversationRole.USER, "Message 2")  # Should trigger pruning
    
    # Should only keep the most recent 2
    assert len(manager.history) == 2
    assert manager.history[0].content == "Response 1"
    assert manager.history[1].content == "Message 2"
    
    # Add a system message (should be preserved)
    manager.add_entry(ConversationRole.SYSTEM, "System prompt")
    
    # Should keep the system message and the most recent message
    assert len(manager.history) == 2
    assert manager.history[0].role == ConversationRole.SYSTEM
    assert manager.history[0].content == "System prompt"
    assert manager.history[1].content == "Message 2"


def test_conversation_manager_get_summary():
    """Test getting conversation summary."""
    manager = ConversationManager("test_conv")
    
    # Add some messages
    manager.add_entry(ConversationRole.USER, "Hello")
    manager.add_entry(ConversationRole.ASSISTANT, "Hi there!")
    manager.add_entry(ConversationRole.USER, "How are you?")
    
    summary = manager.get_summary()
    
    assert summary["conversation_id"] == "test_conv"
    assert summary["message_count"] == 3
    assert summary["first_message"]["content"] == "Hello"
    assert summary["last_message"]["content"] == "How are you?"
    assert "created_at" in summary
    assert "updated_at" in summary