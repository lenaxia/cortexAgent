"""Tests for the CortexAgent memory handler."""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import json
from datetime import datetime

from homeassistant.core import HomeAssistant

from custom_components.cortex_agent.memory_handler import (
    MemoryHandler,
    MemoryConfig,
    JSONEncoder,
)
from custom_components.cortex_agent.exceptions import MemoryError


@pytest.fixture
async def mock_hass():
    """Create a real Home Assistant instance for testing."""
    from tests.common import async_test_home_assistant
    
    async with async_test_home_assistant() as hass:
        # We still need to mock these methods to avoid actual execution
        hass.async_add_executor_job = AsyncMock()
        hass.async_create_task = AsyncMock()
        yield hass


@pytest.fixture
def mock_store():
    """Mock Store."""
    with patch("custom_components.cortex_agent.memory_handler.Store") as mock:
        store_instance = MagicMock()
        store_instance.async_load = AsyncMock(return_value=None)
        store_instance.async_save = AsyncMock()
        mock.return_value = store_instance
        yield mock


@pytest.fixture
def mock_mem0_memory():
    """Mock mem0_memory tool."""
    with patch("strands_tools.mem0_memory") as mock:
        yield mock


@pytest.fixture
def mock_tool_use():
    """Mock ToolUse."""
    with patch("strands.types.tools.ToolUse") as mock:
        yield mock


@pytest.fixture
def mock_tool_result():
    """Mock ToolResult."""
    result = MagicMock()
    result.status = "success"
    result.content = [MagicMock()]
    result.content[0].text = json.dumps([{"content": "Test memory"}])
    return result


@pytest.fixture
def memory_config():
    """Create a memory configuration."""
    return MemoryConfig(
        enabled=True,
        user_id="test-user",
        memory_type="mem0",
    )


class TestMemoryHandler:
    """Test the memory handler."""

    def test_init(self, mock_hass, mock_store, memory_config):
        """Test initialization."""
        handler = MemoryHandler(mock_hass, memory_config)
        
        assert handler.hass == mock_hass
        assert handler.config == memory_config
        assert handler._cache == {}
        assert handler._loaded is False
        
        mock_store.assert_called_once()

    async def test_async_load(self, mock_hass, mock_store, memory_config):
        """Test loading memory from storage."""
        mock_store().async_load.return_value = {"memories": {"id1": {"content": "test"}}}
        
        handler = MemoryHandler(mock_hass, memory_config)
        await handler.async_load()
        
        assert handler._loaded is True
        assert handler._cache == {"id1": {"content": "test"}}
        mock_store().async_load.assert_called_once()
        
        # Test loading again (should not reload)
        await handler.async_load()
        mock_store().async_load.assert_called_once()

    async def test_async_save(self, mock_hass, mock_store, memory_config):
        """Test saving memory to storage."""
        handler = MemoryHandler(mock_hass, memory_config)
        handler._cache = {"id1": {"content": "test"}}
        
        await handler.async_save()
        
        mock_store().async_save.assert_called_once_with({"memories": {"id1": {"content": "test"}}})

    async def test_async_store_success(
        self, mock_hass, mock_store, mock_mem0_memory, mock_tool_use, mock_tool_result, memory_config
    ):
        """Test storing memory successfully."""
        mock_hass.async_add_executor_job.return_value = mock_tool_result
        mock_mem0_memory.return_value = mock_tool_result
        
        handler = MemoryHandler(mock_hass, memory_config)
        result = await handler.async_store("Test memory")
        
        assert result["success"] is True
        assert "memory_id" in result
        assert "timestamp" in result
        
        mock_tool_use.assert_called_once()
        mock_hass.async_add_executor_job.assert_called_once()
        mock_hass.async_create_task.assert_called_once()

    async def test_async_store_with_metadata(
        self, mock_hass, mock_store, mock_mem0_memory, mock_tool_use, mock_tool_result, memory_config
    ):
        """Test storing memory with metadata."""
        mock_hass.async_add_executor_job.return_value = mock_tool_result
        mock_mem0_memory.return_value = mock_tool_result
        
        handler = MemoryHandler(mock_hass, memory_config)
        metadata = {"source": "test", "tags": ["important"]}
        result = await handler.async_store("Test memory", metadata)
        
        assert result["success"] is True
        
        # Check that metadata was passed to the tool
        tool_use_call = mock_tool_use.call_args[1]
        assert tool_use_call["input"]["metadata"] == metadata
        
        # Check that metadata was stored in cache
        memory_id = result["memory_id"]
        assert handler._cache[memory_id]["metadata"] == metadata

    async def test_async_store_failure(
        self, mock_hass, mock_store, mock_mem0_memory, mock_tool_use, memory_config
    ):
        """Test storing memory failure."""
        # Create a failed result
        failed_result = MagicMock()
        failed_result.status = "error"
        failed_result.content = []
        
        mock_hass.async_add_executor_job.return_value = failed_result
        mock_mem0_memory.return_value = failed_result
        
        handler = MemoryHandler(mock_hass, memory_config)
        result = await handler.async_store("Test memory")
        
        assert result["success"] is False
        assert "error" in result

    async def test_async_retrieve_success(
        self, mock_hass, mock_store, mock_mem0_memory, mock_tool_use, mock_tool_result, memory_config
    ):
        """Test retrieving memory successfully."""
        mock_hass.async_add_executor_job.return_value = mock_tool_result
        mock_mem0_memory.return_value = mock_tool_result
        
        handler = MemoryHandler(mock_hass, memory_config)
        result = await handler.async_retrieve("test query")
        
        assert result["success"] is True
        assert "memories" in result
        assert isinstance(result["memories"], list)
        
        mock_tool_use.assert_called_once()
        mock_hass.async_add_executor_job.assert_called_once()

    async def test_async_retrieve_failure(
        self, mock_hass, mock_store, mock_mem0_memory, mock_tool_use, memory_config
    ):
        """Test retrieving memory failure."""
        # Create a failed result
        failed_result = MagicMock()
        failed_result.status = "error"
        failed_result.content = []
        
        mock_hass.async_add_executor_job.return_value = failed_result
        mock_mem0_memory.return_value = failed_result
        
        handler = MemoryHandler(mock_hass, memory_config)
        result = await handler.async_retrieve("test query")
        
        assert result["success"] is False
        assert "error" in result

    async def test_async_list_all_success(
        self, mock_hass, mock_store, mock_mem0_memory, mock_tool_use, mock_tool_result, memory_config
    ):
        """Test listing all memories successfully."""
        mock_hass.async_add_executor_job.return_value = mock_tool_result
        mock_mem0_memory.return_value = mock_tool_result
        
        handler = MemoryHandler(mock_hass, memory_config)
        result = await handler.async_list_all()
        
        assert result["success"] is True
        assert "memories" in result
        assert isinstance(result["memories"], list)
        
        mock_tool_use.assert_called_once()
        mock_hass.async_add_executor_job.assert_called_once()

    async def test_async_clear_success(
        self, mock_hass, mock_store, mock_mem0_memory, mock_tool_use, mock_tool_result, memory_config
    ):
        """Test clearing all memories successfully."""
        mock_hass.async_add_executor_job.return_value = mock_tool_result
        mock_mem0_memory.return_value = mock_tool_result
        
        handler = MemoryHandler(mock_hass, memory_config)
        handler._cache = {"id1": {"content": "test"}}
        
        result = await handler.async_clear()
        
        assert result["success"] is True
        assert handler._cache == {}
        
        mock_tool_use.assert_called_once()
        mock_hass.async_add_executor_job.assert_called_once()
        mock_store().async_save.assert_called_once()

    async def test_import_error_handling(self, mock_hass, mock_store, memory_config):
        """Test handling of import errors when memory module is not available."""
        import sys
        
        # Save the original module if it exists
        original_module = sys.modules.get('strands_tools', None)
        
        try:
            # Remove the module to cause an ImportError
            if 'strands_tools' in sys.modules:
                del sys.modules['strands_tools']
            
            # Create the handler
            handler = MemoryHandler(mock_hass, memory_config)
            
            # The method should return an error dictionary instead of raising an exception
            result = await handler.async_store("Test memory")
            
            # Verify the result contains the expected error
            assert result["success"] is False
            assert "Failed to import memory tools" in result["error"] or result["error"] == "Failed to store memory"
            
        finally:
            # Restore the original module if it existed
            if original_module is not None:
                sys.modules['strands_tools'] = original_module


class TestJSONEncoder:
    """Test the JSONEncoder."""

    def test_datetime_encoding(self):
        """Test encoding datetime objects."""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        encoder = JSONEncoder()
        
        result = encoder.default(dt)
        assert result == dt.isoformat()

    def test_other_types_fallback(self):
        """Test fallback for other types."""
        encoder = JSONEncoder()
        
        with pytest.raises(TypeError):
            encoder.default(object())