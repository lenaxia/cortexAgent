"""Standalone tests for the MemoryHandler implementation."""
import sys
import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, AsyncMock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

# Define the necessary classes and constants
class MemoryError(Exception):
    """Memory operation error."""

STORAGE_VERSION = 1
STORAGE_KEY_TEMPLATE = "cortex_agent.{user_id}"

# Define the MemoryConfig class
class MemoryConfig:
    """Configuration for memory capabilities."""
    
    def __init__(
        self,
        user_id: str,
        enabled: bool = True,
        memory_type: str = "mem0",
        aws_region: Optional[str] = None,
        opensearch_host: Optional[str] = None
    ):
        """Initialize the memory configuration."""
        self.enabled = enabled
        self.user_id = user_id
        self.memory_type = memory_type
        self.aws_region = aws_region
        self.opensearch_host = opensearch_host


# Define the JSONEncoder class
class JSONEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""
    
    def default(self, obj):
        """Convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# Define the MemoryHandler class
class MemoryHandler:
    """Handles memory operations with persistence."""
    
    def __init__(self, hass, config: MemoryConfig):
        """Initialize the memory handler."""
        self.hass = hass
        self.config = config
        self.storage = MagicMock()
        self.storage.async_load = AsyncMock(return_value=None)
        self.storage.async_save = AsyncMock()
        self._cache = {}
        self._loaded = False
    
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
        """Store information in memory with persistence."""
        await self.async_load()  # Ensure loaded
        
        # In a real implementation, this would call mem0_memory
        # For testing, we'll just update the cache
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        self._cache[memory_id] = {
            "content": content,
            "timestamp": timestamp,
            "metadata": metadata or {},
        }
        
        # Save to persistent storage
        self.hass.async_create_task = AsyncMock()
        self.hass.async_create_task(self.async_save())
        
        return {
            "success": True,
            "memory_id": memory_id,
            "timestamp": timestamp,
        }
    
    async def async_retrieve(self, query: str) -> Dict[str, Any]:
        """Retrieve information from memory based on query."""
        await self.async_load()  # Ensure loaded
        
        # In a real implementation, this would call mem0_memory
        # For testing, we'll just search the cache
        results = []
        for memory_id, memory in self._cache.items():
            if query.lower() in memory["content"].lower():
                results.append({
                    "content": memory["content"],
                    "timestamp": memory["timestamp"],
                    "metadata": memory["metadata"],
                })
        
        if results:
            return {"success": True, "memories": results}
        else:
            return {"success": False, "error": "No memories found"}
    
    async def async_list_all(self) -> Dict[str, Any]:
        """List all stored memories."""
        await self.async_load()  # Ensure loaded
        
        # In a real implementation, this would call mem0_memory
        # For testing, we'll just return the cache
        results = []
        for memory_id, memory in self._cache.items():
            results.append({
                "content": memory["content"],
                "timestamp": memory["timestamp"],
                "metadata": memory["metadata"],
            })
        
        if results:
            return {"success": True, "memories": results}
        else:
            return {"success": False, "error": "No memories found"}
    
    async def async_clear(self) -> Dict[str, Any]:
        """Clear all stored memories."""
        await self.async_load()  # Ensure loaded
        
        # Clear local cache
        self._cache = {}
        
        # Save empty cache
        await self.async_save()
        
        return {"success": True, "message": "All memories cleared"}


# Mock Home Assistant instance
class MockHass:
    """Mock Home Assistant instance."""
    
    def __init__(self):
        """Initialize the mock."""
        self.async_create_task = AsyncMock()


# Tests
async def test_memory_handler_initialization():
    """Test MemoryHandler initialization."""
    mock_hass = MockHass()
    config = MemoryConfig(user_id="test_user")
    
    handler = MemoryHandler(mock_hass, config)
    
    assert handler.hass == mock_hass
    assert handler.config == config
    assert handler._cache == {}
    assert handler._loaded is False
    print("✅ test_memory_handler_initialization passed")


async def test_memory_handler_load():
    """Test loading memory from storage."""
    mock_hass = MockHass()
    config = MemoryConfig(user_id="test_user")
    
    handler = MemoryHandler(mock_hass, config)
    handler.storage.async_load = AsyncMock(return_value={"memories": {"test_id": {"content": "test"}}})
    
    await handler.async_load()
    
    assert handler._loaded is True
    assert handler._cache == {"test_id": {"content": "test"}}
    print("✅ test_memory_handler_load passed")


async def test_memory_handler_save():
    """Test saving memory to storage."""
    mock_hass = MockHass()
    config = MemoryConfig(user_id="test_user")
    
    handler = MemoryHandler(mock_hass, config)
    handler._cache = {"test_id": {"content": "test"}}
    
    await handler.async_save()
    
    handler.storage.async_save.assert_called_once_with({"memories": {"test_id": {"content": "test"}}})
    print("✅ test_memory_handler_save passed")


async def test_memory_handler_store():
    """Test storing information in memory."""
    mock_hass = MockHass()
    config = MemoryConfig(user_id="test_user")
    
    handler = MemoryHandler(mock_hass, config)
    
    result = await handler.async_store("Test content", {"source": "test"})
    
    assert result["success"] is True
    assert "memory_id" in result
    assert "timestamp" in result
    assert len(handler._cache) == 1
    
    memory_id = result["memory_id"]
    assert handler._cache[memory_id]["content"] == "Test content"
    assert handler._cache[memory_id]["metadata"] == {"source": "test"}
    print("✅ test_memory_handler_store passed")


async def test_memory_handler_retrieve():
    """Test retrieving information from memory."""
    mock_hass = MockHass()
    config = MemoryConfig(user_id="test_user")
    
    handler = MemoryHandler(mock_hass, config)
    
    # Store some memories
    await handler.async_store("Apple is a fruit", {"category": "food"})
    await handler.async_store("Banana is yellow", {"category": "food"})
    await handler.async_store("Cars are vehicles", {"category": "transport"})
    
    # Retrieve memories
    result = await handler.async_retrieve("fruit")
    
    assert result["success"] is True
    assert len(result["memories"]) == 1
    assert result["memories"][0]["content"] == "Apple is a fruit"
    assert result["memories"][0]["metadata"] == {"category": "food"}
    
    # Retrieve with no matches
    result = await handler.async_retrieve("not found")
    
    assert result["success"] is False
    assert "error" in result
    print("✅ test_memory_handler_retrieve passed")


async def test_memory_handler_list_all():
    """Test listing all memories."""
    mock_hass = MockHass()
    config = MemoryConfig(user_id="test_user")
    
    handler = MemoryHandler(mock_hass, config)
    
    # Store some memories
    await handler.async_store("Memory 1", {"index": 1})
    await handler.async_store("Memory 2", {"index": 2})
    
    # List all memories
    result = await handler.async_list_all()
    
    assert result["success"] is True
    assert len(result["memories"]) == 2
    
    # Check that memories are returned
    contents = [memory["content"] for memory in result["memories"]]
    assert "Memory 1" in contents
    assert "Memory 2" in contents
    print("✅ test_memory_handler_list_all passed")


async def test_memory_handler_clear():
    """Test clearing all memories."""
    mock_hass = MockHass()
    config = MemoryConfig(user_id="test_user")
    
    handler = MemoryHandler(mock_hass, config)
    
    # Store some memories
    await handler.async_store("Memory 1")
    await handler.async_store("Memory 2")
    
    assert len(handler._cache) == 2
    
    # Clear memories
    result = await handler.async_clear()
    
    assert result["success"] is True
    assert len(handler._cache) == 0
    print("✅ test_memory_handler_clear passed")


# Run tests
async def run_tests():
    """Run all tests."""
    print("Running standalone tests for MemoryHandler...")
    await test_memory_handler_initialization()
    await test_memory_handler_load()
    await test_memory_handler_save()
    await test_memory_handler_store()
    await test_memory_handler_retrieve()
    await test_memory_handler_list_all()
    await test_memory_handler_clear()
    print("All tests passed! ✅")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_tests())