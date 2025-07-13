"""Conversation management for CortexAgent."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Any

from homeassistant.helpers.storage import Store

from .models import Message, MessageRole

_LOGGER = logging.getLogger(__name__)

@dataclass
class Conversation:
    """A conversation with messages."""
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)



class ConversationManager:
    """Manages conversation history with pruning strategies."""

    def __init__(
        self,
        hass: Any,
        entry_id: str,
        max_conversations: int = 10,
        max_messages: int = 50,
        max_age_hours: int = 24,
        prune_interval: int = 3600,  # 1 hour in seconds
        storage: Any | None = None
    ):
        """Initialize the conversation manager."""
        self.hass = hass
        self.entry_id = entry_id
        self.max_conversations = max_conversations
        self.max_messages = max_messages
        self.max_age_hours = max_age_hours
        self.prune_interval = prune_interval
        self.conversations: dict[str, Conversation] = {}
        self._loaded = False
        self._prune_task: asyncio.Task | None = None
        self._last_save_time = datetime.now()
        self._save_interval = 300  # 5 minutes in seconds

        # Initialize storage
        self.storage = storage or Store(hass, 1, f"cortex_agent.{entry_id}.conversations")

    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = f"conv_{len(self.conversations) + 1}"
        self.conversations[conversation_id] = Conversation()
        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        message: Message
    ) -> None:
        """Add a message to a conversation."""
        # Create conversation if it doesn't exist
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation()

        # Add message
        self.conversations[conversation_id].messages.append(message)

        # Update timestamp
        self.conversations[conversation_id].updated_at = datetime.now()

        # Prune messages if needed
        if len(self.conversations[conversation_id].messages) > self.max_messages:
            # Keep most recent messages
            self.conversations[conversation_id].messages = self.conversations[conversation_id].messages[-self.max_messages:]

        # Prune conversations if needed
        self._prune_conversations()

        # Schedule auto-save if enough time has passed since last save
        now = datetime.now()
        if (now - self._last_save_time).total_seconds() > self._save_interval:
            self.hass.async_create_task(self.async_save())

    def get_conversation(self, conversation_id: str) -> list[Message]:
        """Get messages for a conversation."""
        if conversation_id not in self.conversations:
            return []

        return self.conversations[conversation_id].messages

    def get_formatted_history(self, conversation_id: str) -> list[dict[str, Any]]:
        """Get formatted history for a conversation suitable for LLM context."""
        messages = self.get_conversation(conversation_id)

        # Format for LLM context
        return [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in messages
        ]

    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a specific conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

    def clear_all_conversations(self) -> None:
        """Clear all conversations."""
        self.conversations = {}

    def get_conversation_summary(self) -> list[dict[str, Any]]:
        """Get a summary of all conversations."""
        summary = []

        for conv_id, conversation in self.conversations.items():
            # Get first and last message for context
            first_message = conversation.messages[0] if conversation.messages else None
            last_message = conversation.messages[-1] if conversation.messages else None

            summary.append({
                "id": conv_id,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "message_count": len(conversation.messages),
                "first_message": {
                    "role": first_message.role.value,
                    "content": first_message.content,
                    "timestamp": first_message.timestamp.isoformat()
                } if first_message else None,
                "last_message": {
                    "role": last_message.role.value,
                    "content": last_message.content,
                    "timestamp": last_message.timestamp.isoformat()
                } if last_message else None
            })

        return summary

    async def async_save(self) -> None:
        """Save conversations to storage."""
        if not self.storage:
            return

        # Convert conversations to serializable format
        conversations_data = {}
        for conv_id, conversation in self.conversations.items():
            messages_data = [
                {
                    "role": message.role.value,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                    "metadata": message.metadata
                }
                for message in conversation.messages
            ]

            conversations_data[conv_id] = {
                "messages": messages_data,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
            }

        data = {
            "conversations": conversations_data
        }

        await self.storage.async_save(data)
        self._last_save_time = datetime.now()

    async def async_load(self) -> None:
        """Load conversations from storage."""
        if self._loaded or not self.storage:
            return

        data = await self.storage.async_load()
        if data and "conversations" in data:
            for conv_id, conv_data in data["conversations"].items():
                messages = [
                    Message(
                        role=MessageRole(msg_data["role"]),
                        content=msg_data["content"],
                        timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        metadata=msg_data.get("metadata", {})
                    )
                    for msg_data in conv_data["messages"]
                ]

                self.conversations[conv_id] = Conversation(
                    messages=messages,
                    created_at=datetime.fromisoformat(conv_data["created_at"]),
                    updated_at=datetime.fromisoformat(conv_data["updated_at"]),
                )

        self._loaded = True

        # Start the background pruning task
        self._start_pruning_task()

    def _prune_conversations(self) -> None:
        """Prune old conversations."""
        # Remove conversations older than max_age_hours
        now = datetime.now()
        to_remove = []

        for conv_id, conv in self.conversations.items():
            updated_at = conv.updated_at
            age_hours = (now - updated_at).total_seconds() / 3600

            if age_hours > self.max_age_hours:
                to_remove.append(conv_id)

        for conv_id in to_remove:
            del self.conversations[conv_id]

        # If still too many conversations, remove oldest ones
        if len(self.conversations) > self.max_conversations:
            sorted_convs = sorted(
                self.conversations.items(),
                key=lambda x: x[1].updated_at
            )

            # Keep only the newest conversations
            to_keep = sorted_convs[-self.max_conversations:]
            self.conversations = dict(to_keep)

    def _start_pruning_task(self) -> None:
        """Start the background pruning task."""
        # Stop existing task if it exists
        self._stop_pruning_task()

        # Create the task and store it
        self._prune_task = asyncio.create_task(self._periodic_prune())
        _LOGGER.debug("Started conversation pruning task")

    def _stop_pruning_task(self) -> None:
        """Stop the background pruning task."""
        if self._prune_task is not None:
            if not self._prune_task.done():
                self._prune_task.cancel()
            self._prune_task = None
            _LOGGER.debug("Stopped conversation pruning task")

    async def _periodic_prune(self) -> None:
        """Periodically prune conversations and save to storage."""
        try:
            while True:
                # Wait for the specified interval
                await asyncio.sleep(self.prune_interval)

                # Prune conversations
                self._prune_conversations()
                _LOGGER.debug("Pruned conversations (periodic)")

                # Save to storage
                await self.async_save()
                _LOGGER.debug("Saved conversations (periodic)")

        except asyncio.CancelledError:
            _LOGGER.debug("Conversation pruning task cancelled")

        except OSError as ex:
            _LOGGER.error("Error in conversation pruning task: %s", ex)

    async def async_unload(self) -> None:
        """Unload the conversation manager and stop background tasks."""
        self._stop_pruning_task()
        await self.async_save()

    def get_conversation_ids(self) -> list[str]:
        """Get all conversation IDs."""
        return list(self.conversations.keys())

    def get_conversation_metadata(self, conversation_id: str) -> dict[str, Any]:
        """Get metadata for a conversation."""
        if conversation_id not in self.conversations:
            return {}

        conversation = self.conversations[conversation_id]
        return {
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "message_count": len(conversation.messages)
        }

    async def get_conversation_with_memories(
        self,
        conversation_id: str,
        memory_handler: Any
    ) -> list[dict[str, Any]]:
        """Get conversation history with relevant memories from memory handler.

        This method retrieves relevant memories from the memory handler and
        combines them with the conversation history for model consumption.

        Args:
            conversation_id: The ID of the conversation
            memory_handler: The memory handler to retrieve memories from

        Returns:
            List of formatted messages including both history and memories
        """
        # Get formatted conversation history
        formatted_history = self.get_formatted_history(conversation_id)

        # Get relevant messages for context
        recent_messages = self.get_conversation(conversation_id)[-5:] if self.get_conversation(conversation_id) else []

        # Get relevant memories
        memories = await memory_handler.retrieve_memories(
            conversation_id=conversation_id,
            recent_messages=recent_messages
        )

        # If no memories, just return the history
        if not memories:
            return formatted_history

        # Insert memories at the beginning, after any system messages
        result = []
        system_messages_end = 0

        # Find where system messages end
        for i, msg in enumerate(formatted_history):
            if msg["role"] != "system":
                system_messages_end = i
                break

        # Add system messages first
        result.extend(formatted_history[:system_messages_end])

        # Add memories as system messages
        memory_messages = [
            {
                "role": "system",
                "content": f"Memory: {memory['content']}",
                "metadata": {"memory": True, "last_accessed": memory.get("last_accessed")}
            }
            for memory in memories
        ]
        result.extend(memory_messages)

        # Add the rest of the conversation
        result.extend(formatted_history[system_messages_end:])

        return result

    async def add_message_and_store_memory(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        memory_handler: Any,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a message to a conversation and store it as a memory.

        This method adds a message to the conversation history and also
        stores it as a memory using the provided memory handler.

        Args:
            conversation_id: The ID of the conversation
            role: The role of the message sender
            content: The message content
            memory_handler: The memory handler to store the memory
            metadata: Optional metadata for the message
        """
        # Create message
        message = Message(role=role, content=content, metadata=metadata or {})

        # Add the message to conversation history
        self.add_message(conversation_id, message)

        # Store as memory if it's a user message (contains potential information)
        if role == MessageRole.USER:
            await memory_handler.store_memory(
                content=content,
                conversation_id=conversation_id,
                metadata=metadata
            )
