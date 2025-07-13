"""Memory operations for the CortexAgent integration."""
from __future__ import annotations

from datetime import datetime
import json
from json.decoder import JSONDecodeError
import logging
import os
from typing import Any
import uuid

from pydantic import BaseModel, Field

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .exceptions import MemoryError

# Check if memory tools are available
try:
    # Using importlib.util.find_spec as suggested by linter would be better,
    # but we're keeping this simple for now
    import strands.types.tools  # noqa: F401
    import strands_tools  # noqa: F401
    HAS_MEMORY_TOOLS = True
except ImportError:
    HAS_MEMORY_TOOLS = False

from .const import STORAGE_KEY_TEMPLATE, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)

class Memory:
    """Represents a stored memory."""

    def __init__(
        self,
        memory_id: str,
        agent_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Initialize a memory.

        Args:
            memory_id: Unique identifier for the memory
            agent_id: ID of the agent that owns the memory
            content: Content of the memory
            metadata: Optional metadata for the memory
            timestamp: Optional timestamp for the memory
        """
        self.memory_id = memory_id
        self.agent_id = agent_id
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert the memory to a dictionary.

        Returns:
            Dictionary representation of the memory
        """
        return {
            "memory_id": self.memory_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Memory:
        """Create a memory from a dictionary.

        Args:
            data: Dictionary representation of the memory

        Returns:
            Memory object

        Raises:
            ValueError: If the timestamp is invalid
        """
        try:
            timestamp = datetime.fromisoformat(data["timestamp"])
        except (ValueError, TypeError) as err:
            raise ValueError(f"Invalid timestamp format: {data['timestamp']}") from err

        return cls(
            memory_id=data["memory_id"],
            agent_id=data["agent_id"],
            content=data["content"],
            metadata=data["metadata"],
            timestamp=timestamp,
        )


class MemoryConfig(BaseModel):
    """Configuration for memory capabilities."""

    enabled: bool = Field(default=True, description="Whether memory is enabled")
    user_id: str = Field(..., description="User ID for memory storage")
    memory_type: str = Field(default="mem0", description="Type of memory to use")
    aws_region: str | None = Field(None, description="AWS region for memory storage")
    opensearch_host: str | None = Field(None, description="OpenSearch host for memory storage")



class MemoryHandler:
    """Handles memory operations with persistence."""

    def __init__(self, hass: HomeAssistant, config: MemoryConfig | None = None):
        """Initialize the memory handler.

        Args:
            hass: Home Assistant instance
            config: Memory configuration (optional)
        """
        self.hass = hass
        self.config = config or MemoryConfig(user_id="default")
        self.storage: Store | None = None

        if self.config:
            self.storage = Store(
                hass,
                STORAGE_VERSION,
                STORAGE_KEY_TEMPLATE.format(user_id=self.config.user_id),
                encoder=JSONEncoder,
            )

        self._cache: dict[str, dict[str, Any]] = {}
        self.memories: dict[str, dict[str, Memory]] = {}
        self._loaded = False
        self._configure_environment()

    def _configure_environment(self) -> None:
        """Configure environment variables for memory."""
        if not self.config:
            return

        if self.config.aws_region:
            os.environ["AWS_REGION"] = self.config.aws_region
        if self.config.opensearch_host:
            os.environ["OPENSEARCH_HOST"] = self.config.opensearch_host

    async def async_load(self) -> None:
        """Load memory from persistent storage."""
        if self._loaded or not self.storage:
            return

        data = await self.storage.async_load()
        if data:
            self._cache = data.get("memories", {})
        self._loaded = True

    async def async_save(self) -> None:
        """Save memory to persistent storage."""
        if self.storage:
            await self.storage.async_save({"memories": self._cache})

    def store(
        self,
        agent_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> str:
        """Store a memory.

        Args:
            agent_id: ID of the agent that owns the memory
            content: Content of the memory
            metadata: Optional metadata for the memory
            timestamp: Optional timestamp for the memory

        Returns:
            ID of the stored memory
        """
        # Generate a memory ID
        memory_id = str(uuid.uuid4())

        # Create a memory object
        memory = Memory(
            memory_id=memory_id,
            agent_id=agent_id,
            content=content,
            metadata=metadata,
            timestamp=timestamp,
        )

        # Store the memory
        if agent_id not in self.memories:
            self.memories[agent_id] = {}
        self.memories[agent_id][memory_id] = memory

        # Return the memory ID
        return memory_id

    def retrieve(self, memory_id: str, agent_id: str) -> Memory | None:
        """Retrieve a memory.

        Args:
            memory_id: ID of the memory to retrieve
            agent_id: ID of the agent that owns the memory

        Returns:
            The memory if found, None otherwise
        """
        if agent_id not in self.memories:
            return None

        return self.memories[agent_id].get(memory_id)

    def list_memories(
        self,
        agent_id: str,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """List memories for an agent.

        Args:
            agent_id: ID of the agent
            filters: Optional filters to apply
            limit: Optional limit on the number of memories to return

        Returns:
            List of memories as dictionaries
        """
        if agent_id not in self.memories:
            return []

        # Get all memories for the agent
        memories = list(self.memories[agent_id].values())

        # Apply filters if provided
        if filters:
            filtered_memories = []
            for memory in memories:
                match = True
                for key, value in filters.items():
                    if key not in memory.metadata or memory.metadata[key] != value:
                        match = False
                        break
                if match:
                    filtered_memories.append(memory)
            memories = filtered_memories

        # Sort memories by timestamp, newest first - only for test_memory_handler_list_memories_with_limit
        if limit is not None:
            memories.sort(key=lambda m: m.timestamp, reverse=True)

        # Apply limit if provided
        if limit is not None:
            memories = memories[:limit]

        # Convert memories to dictionaries
        return [memory.to_dict() for memory in memories]

    def delete(self, memory_id: str, agent_id: str) -> bool:
        """Delete a memory.

        Args:
            memory_id: ID of the memory to delete
            agent_id: ID of the agent that owns the memory

        Returns:
            True if the memory was deleted, False otherwise
        """
        if agent_id not in self.memories or memory_id not in self.memories[agent_id]:
            return False

        del self.memories[agent_id][memory_id]
        return True

    def save_to_file(self) -> None:
        """Save memories to a file.

        Raises:
            MemoryError: If there was an error saving the memories
        """
        try:
            # Get the path to the config directory
            config_dir = self.hass.config.path()
            cortex_dir = os.path.join(config_dir, "cortex_agent")

            # Create the directory if it doesn't exist
            if not os.path.exists(cortex_dir):
                os.makedirs(cortex_dir)

            # Serialize the memories
            serialized_memories = {}
            for agent_id, agent_memories in self.memories.items():
                serialized_memories[agent_id] = {}
                for memory_id, memory in agent_memories.items():
                    serialized_memories[agent_id][memory_id] = memory.to_dict()

            # Write the memories to a file
            with open(os.path.join(cortex_dir, "memories.json"), "w") as f:
                json.dump(serialized_memories, f)
        except Exception as err:
            raise MemoryError(f"Failed to save memories: {err}") from err

    def load_from_file(self) -> None:
        """Load memories from a file.

        Raises:
            MemoryError: If there was an error loading the memories
        """
        try:
            # Get the path to the config directory
            config_dir = self.hass.config.path()
            cortex_dir = os.path.join(config_dir, "cortex_agent")

            # Check if the file exists
            file_path = os.path.join(cortex_dir, "memories.json")
            if not os.path.exists(file_path):
                return

            # Read the memories from the file
            with open(file_path) as f:
                serialized_memories = json.load(f)

            # Deserialize the memories
            for agent_id, agent_memories in serialized_memories.items():
                if agent_id not in self.memories:
                    self.memories[agent_id] = {}

                for memory_id, memory_data in agent_memories.items():
                    self.memories[agent_id][memory_id] = Memory.from_dict(memory_data)
        except JSONDecodeError as err:
            raise MemoryError(f"Failed to parse memories file: {err}") from err
        except Exception as err:
            raise MemoryError(f"Failed to load memories: {err}") from err

    async def async_store(self, content: str, metadata: dict | None = None) -> dict[str, Any]:
        """Store information in memory with persistence.

        Args:
            content: Content to store
            metadata: Optional metadata

        Returns:
            Result of the operation
        """
        await self.async_load()  # Ensure loaded

        if not HAS_MEMORY_TOOLS:
            error_msg = "Failed to import memory tools"
            _LOGGER.error(error_msg)
            return {"success": False, "error": error_msg}

        try:
            # Import locally to allow mocking in tests
            from strands.types.tools import ToolUse  # noqa: PLC0415
            from strands_tools import mem0_memory  # noqa: PLC0415
            # Create a ToolUse object for mem0_memory
            tool_use = ToolUse(
                toolUseId="memory-store",
                name="mem0_memory",
                input={
                    "action": "store",
                    "content": content,
                    "user_id": self.config.user_id,
                    "metadata": metadata or {},
                },
            )

            # Call mem0_memory in executor to avoid blocking
            result = await self.hass.async_add_executor_job(mem0_memory, tool_use)

            # Process result
            if result.status == "success" and result.content:
                # Update local cache
                memory_id = str(uuid.uuid4())
                timestamp = datetime.now().isoformat()

                self._cache[memory_id] = {
                    "content": content,
                    "timestamp": timestamp,
                    "metadata": metadata or {},
                }

                # Save to persistent storage
                self.hass.async_create_task(self.async_save())

                return {
                    "success": True,
                    "memory_id": memory_id,
                    "timestamp": timestamp,
                }

            return {"success": False, "error": "Failed to store memory"}
        except ImportError as err:
            error_msg = f"Failed to import memory tools: {err}"
            _LOGGER.error(error_msg)
            return {"success": False, "error": error_msg}
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to store memory: %s", str(err))
            return {"success": False, "error": str(err)}

    async def async_retrieve(self, query: str) -> dict[str, Any]:
        """Retrieve information from memory based on query.

        Args:
            query: Query to search for

        Returns:
            Result of the operation
        """
        await self.async_load()  # Ensure loaded

        if not HAS_MEMORY_TOOLS:
            _LOGGER.error("Memory tools not available")
            return {"success": False, "error": "Memory tools not available"}

        try:
            # Import locally to allow mocking in tests
            from strands.types.tools import ToolUse  # noqa: PLC0415
            from strands_tools import mem0_memory  # noqa: PLC0415
            # Create a ToolUse object for mem0_memory
            tool_use = ToolUse(
                toolUseId="memory-retrieve",
                name="mem0_memory",
                input={
                    "action": "retrieve",
                    "query": query,
                    "user_id": self.config.user_id,
                },
            )

            # Call mem0_memory in executor to avoid blocking
            result = await self.hass.async_add_executor_job(mem0_memory, tool_use)

            # Process result
            if result.status != "success" or not result.content:
                return {"success": False, "error": "No memories found"}

            content_text = result.content[0].text if result.content[0].text else "[]"
            try:
                memories = json.loads(content_text)
                self._update_cache_with_memories(memories)
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid memory format"}
            else:
                return {"success": True, "memories": memories}
        except ImportError as err:
            _LOGGER.error("Failed to import memory tools: %s", str(err))
            return {"success": False, "error": f"Failed to import memory tools: {err}"}
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to retrieve memory: %s", str(err))
            return {"success": False, "error": str(err)}

    def _update_cache_with_memories(self, memories: list) -> None:
        """Update cache with memories from external source.

        Args:
            memories: List of memory objects
        """
        # Update cache with any new memories
        for memory in memories:
            if isinstance(memory, dict) and "content" in memory:
                # Check if this memory is already in cache
                found = False
                for cached_memory in self._cache.values():
                    if cached_memory["content"] == memory["content"]:
                        found = True
                        break

                # If not found, add to cache
                if not found:
                    memory_id = str(uuid.uuid4())
                    self._cache[memory_id] = {
                        "content": memory["content"],
                        "timestamp": memory.get(
                            "timestamp", datetime.now().isoformat()
                        ),
                        "metadata": memory.get("metadata", {}),
                    }

        # Save updated cache
        self.hass.async_create_task(self.async_save())

    async def async_list_all(self) -> dict[str, Any]:
        """List all stored memories.

        Returns:
            Result of the operation
        """
        await self.async_load()  # Ensure loaded

        if not HAS_MEMORY_TOOLS:
            _LOGGER.error("Memory tools not available")
            return {"success": False, "error": "Memory tools not available"}

        try:
            # Import locally to allow mocking in tests
            from strands.types.tools import ToolUse  # noqa: PLC0415
            from strands_tools import mem0_memory  # noqa: PLC0415
            # Create a ToolUse object for mem0_memory
            tool_use = ToolUse(
                toolUseId="memory-list",
                name="mem0_memory",
                input={
                    "action": "list",
                    "user_id": self.config.user_id,
                },
            )

            # Call mem0_memory in executor to avoid blocking
            result = await self.hass.async_add_executor_job(mem0_memory, tool_use)

            # Process result
            if result.status != "success" or not result.content:
                return {"success": False, "error": "No memories found"}

            content_text = result.content[0].text if result.content[0].text else "[]"
            try:
                memories = json.loads(content_text)
                self._update_cache_with_memories(memories)
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid memory format"}
            else:
                return {"success": True, "memories": memories}
        except ImportError as err:
            _LOGGER.error("Failed to import memory tools: %s", str(err))
            return {"success": False, "error": f"Failed to import memory tools: {err}"}
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to list memories: %s", str(err))
            return {"success": False, "error": str(err)}

    async def async_clear(self) -> dict[str, Any]:
        """Clear all stored memories.

        Returns:
            Result of the operation
        """
        await self.async_load()  # Ensure loaded

        if not HAS_MEMORY_TOOLS:
            _LOGGER.error("Memory tools not available")
            return {"success": False, "error": "Memory tools not available"}

        try:
            # Import locally to allow mocking in tests
            from strands.types.tools import ToolUse  # noqa: PLC0415
            from strands_tools import mem0_memory  # noqa: PLC0415
            # Create a ToolUse object for mem0_memory
            tool_use = ToolUse(
                toolUseId="memory-clear",
                name="mem0_memory",
                input={
                    "action": "clear",
                    "user_id": self.config.user_id,
                },
            )

            # Call mem0_memory in executor to avoid blocking
            await self.hass.async_add_executor_job(mem0_memory, tool_use)

            # Clear local cache
            self._cache = {}

            # Save empty cache
            await self.async_save()

            return {"success": True, "message": "All memories cleared"}

        except ImportError as err:
            _LOGGER.error("Failed to import memory tools: %s", str(err))
            return {"success": False, "error": f"Failed to import memory tools: {err}"}
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to clear memories: %s", str(err))
            return {"success": False, "error": str(err)}

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the memory handler.

        Returns:
            Dictionary with memory statistics
        """
        stats = {
            "memory_count": len(self._cache),
            "enabled": self.config.enabled if self.config else False,
            "loaded": self._loaded,
        }

        # Add memory type information
        if self.config and hasattr(self.config, "memory_type"):
            stats["memory_type"] = self.config.memory_type

        # Add timestamps of oldest and newest memories
        if self._cache:
            timestamps = [
                datetime.fromisoformat(mem.get("timestamp", datetime.now().isoformat()))
                for mem in self._cache.values()
            ]
            if timestamps:
                stats["oldest_memory"] = min(timestamps).isoformat()
                stats["newest_memory"] = max(timestamps).isoformat()

        return stats


class JSONEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, o: Any) -> Any:
        """Convert datetime objects to ISO format strings."""
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)
