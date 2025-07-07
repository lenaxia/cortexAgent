"""Tests for the memory_handler module."""
import os
import pytest
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from unified_agent.models import MemoryConfig
from unified_agent.memory_handler import MemoryHandler, mem0_memory


class TestMemoryHandler:
    """Tests for the MemoryHandler class."""
    
    @pytest.fixture
    def memory_config(self):
        """Create a memory configuration for testing."""
        return MemoryConfig(
            enabled=True,
            user_id="test-user",
            memory_type="mem0",
            aws_region="us-west-2",
            opensearch_host="test-host"
        )
    
    @pytest.fixture
    def temp_memories_dir(self):
        """Create a temporary directory for memories."""
        temp_dir = tempfile.mkdtemp()
        memories_dir = Path(temp_dir) / ".unified_agent" / "memories"
        memories_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test memories file
        test_memories = {
            "memories": [
                {
                    "id": "1",
                    "content": "Test memory 1",
                    "timestamp": "2025-07-06T01:00:00.000000"
                },
                {
                    "id": "2",
                    "content": "Test memory 2",
                    "timestamp": "2025-07-06T01:01:00.000000"
                }
            ]
        }
        
        test_memories_file = memories_dir / "test-user.json"
        test_memories_file.write_text(json.dumps(test_memories, indent=2))
        
        yield temp_dir
        
        # Clean up
        shutil.rmtree(temp_dir)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_configure_environment(self, memory_config):
        """Test that environment variables are configured correctly."""
        # Initialize memory handler
        MemoryHandler(memory_config)
        
        # Check that environment variables were set
        assert os.environ.get("AWS_REGION") == "us-west-2"
        assert os.environ.get("OPENSEARCH_HOST") == "test-host"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_configure_environment_no_config(self):
        """Test that environment variables are not set when config is None."""
        # Initialize memory handler with no config
        MemoryHandler(None)
        
        # Check that environment variables were not set
        assert "AWS_REGION" not in os.environ
        assert "OPENSEARCH_HOST" not in os.environ
    
    def test_mem0_memory_store(self, temp_memories_dir):
        """Test storing information with mem0_memory."""
        # Set the home directory to the temporary directory
        with patch("pathlib.Path.home", return_value=Path(temp_memories_dir)):
            # Store information
            result = mem0_memory(
                action="store",
                content="Test memory 3",
                user_id="test-user"
            )
            
            # Check that result is correct
            assert result["status"] == "success"
            
            # Check that the memory was stored
            memories_file = Path(temp_memories_dir) / ".unified_agent" / "memories" / "test-user.json"
            memories = json.loads(memories_file.read_text())
            
            assert len(memories["memories"]) == 3
            assert memories["memories"][2]["content"] == "Test memory 3"
    
    def test_mem0_memory_retrieve(self, temp_memories_dir):
        """Test retrieving information with mem0_memory."""
        # Set the home directory to the temporary directory
        with patch("pathlib.Path.home", return_value=Path(temp_memories_dir)):
            # Retrieve information
            result = mem0_memory(
                action="retrieve",
                content="memory 1",
                user_id="test-user"
            )
            
            # Check that result is correct
            assert len(result["memories"]) == 1
            assert result["memories"][0]["content"] == "Test memory 1"
    
    def test_mem0_memory_list(self, temp_memories_dir):
        """Test listing all memories with mem0_memory."""
        # Set the home directory to the temporary directory
        with patch("pathlib.Path.home", return_value=Path(temp_memories_dir)):
            # List all memories
            result = mem0_memory(
                action="list",
                user_id="test-user"
            )
            
            # Check that result is correct
            assert len(result["memories"]) == 2
            assert result["memories"][0]["content"] == "Test memory 1"
            assert result["memories"][1]["content"] == "Test memory 2"
    
    def test_mem0_memory_invalid_action(self):
        """Test mem0_memory with an invalid action."""
        with pytest.raises(ValueError, match="Unknown action: invalid"):
            mem0_memory(
                action="invalid",
                user_id="test-user"
            )
    
    @patch("unified_agent.memory_handler.mem0_memory")
    def test_store(self, mock_mem0_memory, memory_config):
        """Test storing information in memory."""
        # Mock mem0_memory return value
        mock_mem0_memory.return_value = {"status": "success"}
        
        # Initialize memory handler
        memory_handler = MemoryHandler(memory_config)
        
        # Store information
        result = memory_handler.store("Test content")
        
        # Check that mem0_memory was called correctly
        mock_mem0_memory.assert_called_once_with(
            action="store",
            content="Test content",
            user_id="test-user"
        )
        
        # Check that result is correct
        assert result["success"] is True
        assert result["result"] == {"status": "success"}
    
    @patch("unified_agent.memory_handler.mem0_memory")
    def test_store_disabled(self, mock_mem0_memory, memory_config):
        """Test storing information when memory is disabled."""
        # Disable memory
        memory_config.enabled = False
        
        # Initialize memory handler
        memory_handler = MemoryHandler(memory_config)
        
        # Store information
        result = memory_handler.store("Test content")
        
        # Check that mem0_memory was not called
        mock_mem0_memory.assert_not_called()
        
        # Check that result is correct
        assert result["success"] is False
        assert "Memory is not enabled" in result["error"]
    
    @patch("unified_agent.memory_handler.mem0_memory")
    def test_store_no_config(self, mock_mem0_memory):
        """Test storing information when config is None."""
        # Initialize memory handler with no config
        memory_handler = MemoryHandler(None)
        
        # Store information
        result = memory_handler.store("Test content")
        
        # Check that mem0_memory was not called
        mock_mem0_memory.assert_not_called()
        
        # Check that result is correct
        assert result["success"] is False
        assert "Memory is not enabled" in result["error"]
    
    @patch("unified_agent.memory_handler.mem0_memory")
    def test_store_error(self, mock_mem0_memory, memory_config):
        """Test storing information when mem0_memory raises an exception."""
        # Mock mem0_memory to raise an exception
        mock_mem0_memory.side_effect = Exception("Test error")
        
        # Initialize memory handler
        memory_handler = MemoryHandler(memory_config)
        
        # Store information
        result = memory_handler.store("Test content")
        
        # Check that result is correct
        assert result["success"] is False
        assert "Test error" in result["error"]
    
    @patch("unified_agent.memory_handler.mem0_memory")
    def test_retrieve(self, mock_mem0_memory, memory_config):
        """Test retrieving information from memory."""
        # Mock mem0_memory return value
        mock_mem0_memory.return_value = {
            "memories": [
                {"content": "Test memory"}
            ]
        }
        
        # Initialize memory handler
        memory_handler = MemoryHandler(memory_config)
        
        # Retrieve information
        result = memory_handler.retrieve("Test query")
        
        # Check that mem0_memory was called correctly
        mock_mem0_memory.assert_called_once_with(
            action="retrieve",
            content="Test query",
            user_id="test-user"
        )
        
        # Check that result is correct
        assert result["success"] is True
        assert result["result"]["memories"][0]["content"] == "Test memory"
    
    @patch("unified_agent.memory_handler.mem0_memory")
    def test_retrieve_disabled(self, mock_mem0_memory, memory_config):
        """Test retrieving information when memory is disabled."""
        # Disable memory
        memory_config.enabled = False
        
        # Initialize memory handler
        memory_handler = MemoryHandler(memory_config)
        
        # Retrieve information
        result = memory_handler.retrieve("Test query")
        
        # Check that mem0_memory was not called
        mock_mem0_memory.assert_not_called()
        
        # Check that result is correct
        assert result["success"] is False
        assert "Memory is not enabled" in result["error"]
    
    @patch("unified_agent.memory_handler.mem0_memory")
    def test_list_all(self, mock_mem0_memory, memory_config):
        """Test listing all memories."""
        # Mock mem0_memory return value
        mock_mem0_memory.return_value = {
            "memories": [
                {"content": "Memory 1"},
                {"content": "Memory 2"}
            ]
        }
        
        # Initialize memory handler
        memory_handler = MemoryHandler(memory_config)
        
        # List all memories
        result = memory_handler.list_all()
        
        # Check that mem0_memory was called correctly
        mock_mem0_memory.assert_called_once_with(
            action="list",
            user_id="test-user"
        )
        
        # Check that result is correct
        assert result["success"] is True
        assert len(result["result"]["memories"]) == 2
        assert result["result"]["memories"][0]["content"] == "Memory 1"
        assert result["result"]["memories"][1]["content"] == "Memory 2"
    
    def test_integration(self, memory_config, temp_memories_dir):
        """Test the integration of the memory handler with mem0_memory."""
        # Set the home directory to the temporary directory
        with patch("pathlib.Path.home", return_value=Path(temp_memories_dir)):
            # Initialize memory handler
            memory_handler = MemoryHandler(memory_config)
            
            # Store information
            result = memory_handler.store("Test memory 3")
            assert result["success"] is True
            
            # Retrieve information
            result = memory_handler.retrieve("memory 3")
            assert result["success"] is True
            assert len(result["result"]["memories"]) == 1
            assert result["result"]["memories"][0]["content"] == "Test memory 3"
            
            # List all memories
            result = memory_handler.list_all()
            assert result["success"] is True
            assert len(result["result"]["memories"]) == 3
            
            # Check that the memories file contains all memories
            memories_file = Path(temp_memories_dir) / ".unified_agent" / "memories" / "test-user.json"
            memories = json.loads(memories_file.read_text())
            assert len(memories["memories"]) == 3
