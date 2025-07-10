"""Memory operations for the CortexAgent integration."""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from pydantic import BaseModel, Field

from .const import STORAGE_KEY_TEMPLATE, STORAGE_VERSION
from .exceptions import MemoryError

_LOGGER = logging.getLogger(__name__)


class MemoryConfig(BaseModel):
    """Configuration for memory capabilities."""

    enabled: bool = Field(default=True, description="Whether memory is enabled")
    user_id: str = Field(..., description="User ID for memory storage")
    memory_type: str = Field(default="mem0", description="Type of memory to use")
    aws_region: Optional[str] = Field(None, description="AWS region for memory storage")
    opensearch_host: Optional[str] = Field(None, description="OpenSearch host for memory storage")


class MemoryHandler:
    """Handles memory operations with persistence."""

    def __init__(self, hass: HomeAssistant, config: MemoryConfig):
        """Initialize the memory handler.
        
        Args:
            hass: Home Assistant instance
            config: Memory configuration
        """
        self.hass = hass
        self.config = config
        self.storage = Store(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY_TEMPLATE.format(user_id=config.user_id),
            encoder=JSONEncoder,
        )
        self._cache = {}
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
        if self._loaded:
            return

        data = await self.storage.async_load()
        if data:
            self._cache = data.get("memories", {})
        self._loaded = True

    async def async_save(self) -> None:
        """Save memory to persistent storage."""
        await self.storage.async_save({"memories": self._cache})

    async def async_store(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Store information in memory with persistence.
        
        Args:
            content: Content to store
            metadata: Optional metadata
            
        Returns:
            Result of the operation
        """
        await self.async_load()  # Ensure loaded

        try:
            # Import mem0_memory
            try:
                from strands_tools import mem0_memory
                from strands.types.tools import ToolUse
            except ImportError as err:
                _LOGGER.error("Failed to import memory tools: %s", str(err))
                raise MemoryError(f"Failed to import memory tools: {str(err)}")

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
            else:
                return {"success": False, "error": "Failed to store memory"}

        except Exception as err:
            _LOGGER.error("Failed to store memory: %s", str(err))
            return {"success": False, "error": str(err)}

    async def async_retrieve(self, query: str) -> Dict[str, Any]:
        """Retrieve information from memory based on query.
        
        Args:
            query: Query to search for
            
        Returns:
            Result of the operation
        """
        await self.async_load()  # Ensure loaded

        try:
            # Import mem0_memory
            try:
                from strands_tools import mem0_memory
                from strands.types.tools import ToolUse
            except ImportError as err:
                _LOGGER.error("Failed to import memory tools: %s", str(err))
                raise MemoryError(f"Failed to import memory tools: {str(err)}")

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
            if result.status == "success" and result.content:
                content_text = result.content[0].text if result.content[0].text else "[]"
                try:
                    memories = json.loads(content_text)

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

                    return {"success": True, "memories": memories}
                except json.JSONDecodeError:
                    return {"success": False, "error": "Invalid memory format"}
            else:
                return {"success": False, "error": "No memories found"}

        except Exception as err:
            _LOGGER.error("Failed to retrieve memory: %s", str(err))
            return {"success": False, "error": str(err)}

    async def async_list_all(self) -> Dict[str, Any]:
        """List all stored memories.
        
        Returns:
            Result of the operation
        """
        await self.async_load()  # Ensure loaded

        try:
            # Import mem0_memory
            try:
                from strands_tools import mem0_memory
                from strands.types.tools import ToolUse
            except ImportError as err:
                _LOGGER.error("Failed to import memory tools: %s", str(err))
                raise MemoryError(f"Failed to import memory tools: {str(err)}")

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
            if result.status == "success" and result.content:
                content_text = result.content[0].text if result.content[0].text else "[]"
                try:
                    memories = json.loads(content_text)

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

                    return {"success": True, "memories": memories}
                except json.JSONDecodeError:
                    return {"success": False, "error": "Invalid memory format"}
            else:
                return {"success": False, "error": "No memories found"}

        except Exception as err:
            _LOGGER.error("Failed to list memories: %s", str(err))
            return {"success": False, "error": str(err)}

    async def async_clear(self) -> Dict[str, Any]:
        """Clear all stored memories.
        
        Returns:
            Result of the operation
        """
        await self.async_load()  # Ensure loaded

        try:
            # Import mem0_memory
            try:
                from strands_tools import mem0_memory
                from strands.types.tools import ToolUse
            except ImportError as err:
                _LOGGER.error("Failed to import memory tools: %s", str(err))
                raise MemoryError(f"Failed to import memory tools: {str(err)}")

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
            result = await self.hass.async_add_executor_job(mem0_memory, tool_use)

            # Clear local cache
            self._cache = {}

            # Save empty cache
            await self.async_save()

            return {"success": True, "message": "All memories cleared"}

        except Exception as err:
            _LOGGER.error("Failed to clear memories: %s", str(err))
            return {"success": False, "error": str(err)}


class JSONEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj):
        """Convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)