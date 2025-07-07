"""Tests for the command_registry module."""
import pytest
from unittest.mock import MagicMock

from unified_agent.models import CommandResult, ICommand
from unified_agent.command_registry import CommandRegistry


class TestCommandRegistry:
    """Tests for the CommandRegistry class."""
    
    @pytest.fixture
    def mock_command(self):
        """Create a mock command."""
        command = MagicMock(spec=ICommand)
        command.execute.return_value = CommandResult(
            success=True,
            message="Command executed successfully"
        )
        return command
    
    def test_register_command(self, mock_command):
        """Test registering a command."""
        # Initialize registry
        registry = CommandRegistry()
        
        # Register command
        registry.register("test", mock_command)
        
        # Check that command was registered
        assert "test" in registry.commands
        assert registry.commands["test"] == mock_command
    
    def test_get_command(self, mock_command):
        """Test getting a command."""
        # Initialize registry
        registry = CommandRegistry()
        
        # Register command
        registry.register("test", mock_command)
        
        # Get command
        command = registry.get_command("test")
        
        # Check that command was returned
        assert command == mock_command
    
    def test_get_nonexistent_command(self):
        """Test getting a command that doesn't exist."""
        # Initialize registry
        registry = CommandRegistry()
        
        # Get command
        command = registry.get_command("nonexistent")
        
        # Check that None was returned
        assert command is None
    
    def test_execute_command(self, mock_command):
        """Test executing a command."""
        # Initialize registry
        registry = CommandRegistry()
        
        # Register command
        registry.register("test", mock_command)
        
        # Execute command
        result = registry.execute("test", ["arg1", "arg2"])
        
        # Check that command was executed
        mock_command.execute.assert_called_once_with(["arg1", "arg2"])
        
        # Check that result was returned
        assert result.success is True
        assert result.message == "Command executed successfully"
    
    def test_execute_nonexistent_command(self):
        """Test executing a command that doesn't exist."""
        # Initialize registry
        registry = CommandRegistry()
        
        # Execute command
        result = registry.execute("nonexistent", [])
        
        # Check that result indicates failure
        assert result.success is False
        assert "Unknown command" in result.message
    
    def test_execute_command_exception(self, mock_command):
        """Test executing a command that raises an exception."""
        # Initialize registry
        registry = CommandRegistry()
        
        # Set up command to raise an exception
        mock_command.execute.side_effect = Exception("Test error")
        
        # Register command
        registry.register("test", mock_command)
        
        # Execute command
        result = registry.execute("test", [])
        
        # Check that result indicates failure
        assert result.success is False
        assert "Test error" in result.message
    
    def test_get_command_names(self, mock_command):
        """Test getting all command names."""
        # Initialize registry
        registry = CommandRegistry()
        
        # Register commands
        registry.register("test1", mock_command)
        registry.register("test2", mock_command)
        
        # Get command names
        names = registry.get_command_names()
        
        # Check that names were returned
        assert len(names) == 2
        assert "test1" in names
        assert "test2" in names
