"""Tests for the cli_interface module."""
import pytest
from unittest.mock import patch, MagicMock, call

from unified_agent.models import CommandResult, IAgentManager
from unified_agent.command_registry import CommandRegistry
from unified_agent.cli_interface import CLIInterface


class TestCLIInterface:
    """Tests for the CLIInterface class."""
    
    @pytest.fixture
    def mock_command_registry(self):
        """Create a mock command registry."""
        registry = MagicMock(spec=CommandRegistry)
        registry.execute.return_value = CommandResult(
            success=True,
            message="Command executed successfully"
        )
        registry.get_command_names.return_value = ["help", "connect", "disconnect"]
        return registry
    
    @pytest.fixture
    def mock_agent_manager(self):
        """Create a mock agent manager."""
        manager = MagicMock(spec=IAgentManager)
        manager.process_input.return_value = {
            "success": True,
            "response": "Agent response"
        }
        return manager
    
    @patch("builtins.print")
    def test_handle_command(self, mock_print, mock_command_registry, mock_agent_manager):
        """Test handling a command."""
        # Initialize interface
        interface = CLIInterface(mock_command_registry, mock_agent_manager)
        
        # Handle command
        interface._handle_command("help")
        
        # Check that command registry was called correctly
        mock_command_registry.execute.assert_called_once_with("help", [])
        
        # Check that result was displayed
        mock_print.assert_any_call("\n✅ Command executed successfully")
    
    @patch("builtins.print")
    def test_handle_command_with_args(self, mock_print, mock_command_registry, mock_agent_manager):
        """Test handling a command with arguments."""
        # Initialize interface
        interface = CLIInterface(mock_command_registry, mock_agent_manager)
        
        # Handle command
        interface._handle_command("connect https://example.com/mcp sse test-server")
        
        # Check that command registry was called correctly
        mock_command_registry.execute.assert_called_once_with(
            "connect", ["https://example.com/mcp", "sse", "test-server"]
        )
    
    @patch("builtins.print")
    def test_handle_command_failure(self, mock_print, mock_command_registry, mock_agent_manager):
        """Test handling a command that fails."""
        # Set up mock to return failure
        mock_command_registry.execute.return_value = CommandResult(
            success=False,
            message="Command failed"
        )
        
        # Initialize interface
        interface = CLIInterface(mock_command_registry, mock_agent_manager)
        
        # Handle command
        interface._handle_command("help")
        
        # Check that result was displayed
        mock_print.assert_any_call("\n❌ Command failed")
    
    @patch("builtins.print")
    def test_process_agent_input(self, mock_print, mock_command_registry, mock_agent_manager):
        """Test processing agent input."""
        # Initialize interface
        interface = CLIInterface(mock_command_registry, mock_agent_manager)
        
        # Process input
        interface._process_agent_input("Hello, agent")
        
        # Check that agent manager was called correctly
        mock_agent_manager.process_input.assert_called_once_with("Hello, agent")
        
        # Check that response was displayed
        mock_print.assert_any_call("\nProcessing...")
        mock_print.assert_any_call("\nAgent response")
    
    @patch("builtins.print")
    def test_process_agent_input_failure(self, mock_print, mock_command_registry, mock_agent_manager):
        """Test processing agent input when it fails."""
        # Set up mock to return failure
        mock_agent_manager.process_input.return_value = {
            "success": False,
            "error": "Agent error"
        }
        
        # Initialize interface
        interface = CLIInterface(mock_command_registry, mock_agent_manager)
        
        # Process input
        interface._process_agent_input("Hello, agent")
        
        # Check that error was displayed
        mock_print.assert_any_call("\n❌ Error: Agent error")
    
    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_exit(self, mock_print, mock_input, mock_command_registry, mock_agent_manager):
        """Test running the interface and exiting."""
        # Set up mock to return exit
        mock_input.return_value = "exit"
        
        # Initialize interface
        interface = CLIInterface(mock_command_registry, mock_agent_manager)
        
        # Run interface
        interface.run()
        
        # Check that welcome message was displayed
        mock_print.assert_any_call("\n🤖 Unified Agent CLI 🤖\n")
        
        # Check that exit message was displayed
        mock_print.assert_any_call("\nGoodbye! 👋")
    
    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_command(self, mock_print, mock_input, mock_command_registry, mock_agent_manager):
        """Test running the interface and executing a command."""
        # Set up mock to return command then exit
        mock_input.side_effect = ["/help", "exit"]
        
        # Initialize interface
        interface = CLIInterface(mock_command_registry, mock_agent_manager)
        
        # Run interface
        interface.run()
        
        # Check that command was handled
        mock_command_registry.execute.assert_called_once_with("help", [])
    
    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_agent_input(self, mock_print, mock_input, mock_command_registry, mock_agent_manager):
        """Test running the interface and processing agent input."""
        # Set up mock to return agent input then exit
        mock_input.side_effect = ["Hello, agent", "exit"]
        
        # Initialize interface
        interface = CLIInterface(mock_command_registry, mock_agent_manager)
        
        # Run interface
        interface.run()
        
        # Check that agent input was processed
        mock_agent_manager.process_input.assert_called_once_with("Hello, agent")
    
    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_keyboard_interrupt(self, mock_print, mock_input, mock_command_registry, mock_agent_manager):
        """Test running the interface and handling keyboard interrupt."""
        # Set up mock to raise keyboard interrupt
        mock_input.side_effect = KeyboardInterrupt()
        
        # Initialize interface
        interface = CLIInterface(mock_command_registry, mock_agent_manager)
        
        # Run interface
        interface.run()
        
        # Check that interrupt message was displayed
        mock_print.assert_any_call("\n\nExecution interrupted.")
    
    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_exception(self, mock_print, mock_input, mock_command_registry, mock_agent_manager):
        """Test running the interface and handling exception."""
        # Set up mock to raise exception then return exit to prevent hanging
        mock_input.side_effect = [Exception("Test error"), "exit"]
        
        # Initialize interface
        interface = CLIInterface(mock_command_registry, mock_agent_manager)
        
        # Run interface
        interface.run()
        
        # Check that error message was displayed
        mock_print.assert_any_call("\nAn error occurred: Test error")
