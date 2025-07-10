"""Tests for the CortexAgent conversation manager."""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from custom_components.cortex_agent.conversation_manager import (
    ConversationManager,
    Conversation,
    Message,
    MessageRole,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    return hass


@pytest.fixture
def mock_store():
    """Mock Store."""
    with patch("homeassistant.helpers.storage.Store") as mock_class:
        store_instance = MagicMock()
        store_instance.async_load = AsyncMock(return_value=None)
        store_instance.async_save = AsyncMock()
        mock_class.return_value = store_instance
        yield mock_class


@pytest.fixture
def conversation_manager(mock_hass, mock_store):
    """Create a conversation manager."""
    return ConversationManager(
        hass=mock_hass,
        entry_id="test-entry-id",
        max_conversations=3,
        max_messages=5,
        max_age_hours=24,
    )


class TestConversationManager:
    """Test the conversation manager."""

    def test_init(self, mock_hass, mock_store):
        """Test initialization."""
        manager = ConversationManager(
            hass=mock_hass,
            entry_id="test-entry-id",
            max_conversations=3,
            max_messages=5,
            max_age_hours=24,
        )
        
        assert manager.hass == mock_hass
        assert manager.entry_id == "test-entry-id"
        assert manager.max_conversations == 3
        assert manager.max_messages == 5
        assert manager.max_age_hours == 24
        assert manager.conversations == {}
        assert manager._loaded is False
        
        mock_store.assert_called_once()

    async def test_async_load_empty(self, conversation_manager):
        """Test loading when storage is empty."""
        # Load
        await conversation_manager.async_load()
        
        # Check result
        assert conversation_manager._loaded is True
        assert conversation_manager.conversations == {}

    async def test_async_load_with_data(self, conversation_manager):
        """Test loading with data in storage."""
        # Set up mock data
        conversation_manager.storage.async_load.return_value = {
            "conversations": {
                "conv1": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello",
                            "timestamp": "2023-01-01T12:00:00",
                        },
                        {
                            "role": "assistant",
                            "content": "Hi there",
                            "timestamp": "2023-01-01T12:00:01",
                        },
                    ],
                    "created_at": "2023-01-01T12:00:00",
                    "updated_at": "2023-01-01T12:00:01",
                }
            }
        }
        
        # Load
        await conversation_manager.async_load()
        
        # Check result
        assert conversation_manager._loaded is True
        assert "conv1" in conversation_manager.conversations
        assert len(conversation_manager.conversations["conv1"].messages) == 2
        assert conversation_manager.conversations["conv1"].messages[0].role == MessageRole.USER
        assert conversation_manager.conversations["conv1"].messages[0].content == "Hello"

    async def test_async_save(self, conversation_manager):
        """Test saving conversations."""
        # Add a conversation
        conversation_manager.conversations = {
            "conv1": Conversation(
                messages=[
                    Message(role=MessageRole.USER, content="Hello"),
                    Message(role=MessageRole.ASSISTANT, content="Hi there"),
                ],
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                updated_at=datetime(2023, 1, 1, 12, 0, 1),
            )
        }
        
        # Save
        await conversation_manager.async_save()
        
        # Check that store was called
        conversation_manager.storage.async_save.assert_called_once()
        
        # Check saved data
        saved_data = conversation_manager.storage.async_save.call_args[0][0]
        assert "conversations" in saved_data
        assert "conv1" in saved_data["conversations"]
        assert len(saved_data["conversations"]["conv1"]["messages"]) == 2

    def test_create_conversation(self, conversation_manager):
        """Test creating a new conversation."""
        # Create conversation
        conversation_id = conversation_manager.create_conversation()
        
        # Check result
        assert conversation_id in conversation_manager.conversations
        assert conversation_manager.conversations[conversation_id].messages == []
        assert isinstance(conversation_manager.conversations[conversation_id].created_at, datetime)
        assert isinstance(conversation_manager.conversations[conversation_id].updated_at, datetime)

    def test_add_message(self, conversation_manager):
        """Test adding a message to a conversation."""
        # Create conversation
        conversation_id = conversation_manager.create_conversation()
        
        # Add message
        conversation_manager.add_message(
            conversation_id,
            Message(role=MessageRole.USER, content="Hello")
        )
        
        # Check result
        assert len(conversation_manager.conversations[conversation_id].messages) == 1
        assert conversation_manager.conversations[conversation_id].messages[0].role == MessageRole.USER
        assert conversation_manager.conversations[conversation_id].messages[0].content == "Hello"

    def test_add_message_nonexistent_conversation(self, conversation_manager):
        """Test adding a message to a nonexistent conversation."""
        # Add message
        conversation_manager.add_message(
            "nonexistent",
            Message(role=MessageRole.USER, content="Hello")
        )
        
        # Check that conversation was created
        assert "nonexistent" in conversation_manager.conversations
        assert len(conversation_manager.conversations["nonexistent"].messages) == 1

    def test_add_message_pruning(self, conversation_manager):
        """Test message pruning when adding messages."""
        # Create conversation
        conversation_id = conversation_manager.create_conversation()
        
        # Add more messages than max_messages
        for i in range(10):
            conversation_manager.add_message(
                conversation_id,
                Message(role=MessageRole.USER, content=f"Message {i}")
            )
        
        # Check result
        assert len(conversation_manager.conversations[conversation_id].messages) == 5
        assert conversation_manager.conversations[conversation_id].messages[0].content == "Message 5"
        assert conversation_manager.conversations[conversation_id].messages[4].content == "Message 9"

    def test_get_conversation(self, conversation_manager):
        """Test getting a conversation."""
        # Create conversation
        conversation_id = conversation_manager.create_conversation()
        
        # Add message
        conversation_manager.add_message(
            conversation_id,
            Message(role=MessageRole.USER, content="Hello")
        )
        
        # Get conversation
        messages = conversation_manager.get_conversation(conversation_id)
        
        # Check result
        assert len(messages) == 1
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"

    def test_get_nonexistent_conversation(self, conversation_manager):
        """Test getting a nonexistent conversation."""
        # Get conversation
        messages = conversation_manager.get_conversation("nonexistent")
        
        # Check result
        assert messages == []

    def test_get_formatted_history(self, conversation_manager):
        """Test getting formatted conversation history."""
        # Create conversation
        conversation_id = conversation_manager.create_conversation()
        
        # Add messages
        conversation_manager.add_message(
            conversation_id,
            Message(role=MessageRole.USER, content="Hello")
        )
        conversation_manager.add_message(
            conversation_id,
            Message(role=MessageRole.ASSISTANT, content="Hi there")
        )
        
        # Get formatted history
        history = conversation_manager.get_formatted_history(conversation_id)
        
        # Check result
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there"

    def test_clear_conversation(self, conversation_manager):
        """Test clearing a conversation."""
        # Create conversation
        conversation_id = conversation_manager.create_conversation()
        
        # Add message
        conversation_manager.add_message(
            conversation_id,
            Message(role=MessageRole.USER, content="Hello")
        )
        
        # Clear conversation
        result = conversation_manager.clear_conversation(conversation_id)
        
        # Check result
        assert result is True
        assert conversation_id not in conversation_manager.conversations

    def test_clear_nonexistent_conversation(self, conversation_manager):
        """Test clearing a nonexistent conversation."""
        # Clear conversation
        result = conversation_manager.clear_conversation("nonexistent")
        
        # Check result
        assert result is False

    def test_clear_all_conversations(self, conversation_manager):
        """Test clearing all conversations."""
        # Create conversations
        conversation_manager.create_conversation()
        conversation_manager.create_conversation()
        
        # Clear all conversations
        conversation_manager.clear_all_conversations()
        
        # Check result
        assert conversation_manager.conversations == {}

    def test_prune_old_conversations(self, conversation_manager):
        """Test pruning old conversations."""
        # Create old conversation
        old_id = "old-conversation"
        conversation_manager.conversations[old_id] = Conversation(
            messages=[],
            created_at=datetime.now() - timedelta(hours=48),
            updated_at=datetime.now() - timedelta(hours=48),
        )
        
        # Create new conversation
        new_id = "new-conversation"
        conversation_manager.conversations[new_id] = Conversation(
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Prune conversations
        conversation_manager._prune_conversations()
        
        # Check result
        assert old_id not in conversation_manager.conversations
        assert new_id in conversation_manager.conversations

    def test_prune_excess_conversations(self, conversation_manager):
        """Test pruning excess conversations."""
        # Create conversations
        for i in range(5):
            conversation_id = f"conv{i}"
            conversation_manager.conversations[conversation_id] = Conversation(
                messages=[],
                created_at=datetime.now() - timedelta(hours=i),
                updated_at=datetime.now() - timedelta(hours=i),
            )
        
        # Prune conversations
        conversation_manager._prune_conversations()
        
        # Check result
        assert len(conversation_manager.conversations) == 3
        assert "conv0" in conversation_manager.conversations
        assert "conv1" in conversation_manager.conversations
        assert "conv2" in conversation_manager.conversations
        assert "conv3" not in conversation_manager.conversations
        assert "conv4" not in conversation_manager.conversations

    def test_get_conversation_summary(self, conversation_manager):
        """Test getting conversation summary."""
        # Create conversations
        conversation_manager.conversations = {
            "conv1": Conversation(
                messages=[
                    Message(role=MessageRole.USER, content="Hello"),
                    Message(role=MessageRole.ASSISTANT, content="Hi there"),
                ],
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                updated_at=datetime(2023, 1, 1, 12, 0, 1),
            ),
            "conv2": Conversation(
                messages=[
                    Message(role=MessageRole.USER, content="How are you?"),
                ],
                created_at=datetime(2023, 1, 2, 12, 0, 0),
                updated_at=datetime(2023, 1, 2, 12, 0, 0),
            ),
        }
        
        # Get summary
        summary = conversation_manager.get_conversation_summary()
        
        # Check result
        assert len(summary) == 2
        assert summary[0]["id"] in ["conv1", "conv2"]
        assert summary[1]["id"] in ["conv1", "conv2"]
        assert summary[0]["id"] != summary[1]["id"]
        
        # Check first conversation
        conv1 = next(s for s in summary if s["id"] == "conv1")
        assert conv1["message_count"] == 2
        assert conv1["first_message"]["content"] == "Hello"
        assert conv1["last_message"]["content"] == "Hi there"
        
        # Check second conversation
        conv2 = next(s for s in summary if s["id"] == "conv2")
        assert conv2["message_count"] == 1
        assert conv2["first_message"]["content"] == "How are you?"
        assert conv2["last_message"]["content"] == "How are you?"