"""CLI interface for the unified agent."""
import logging
import readline  # For command history
from typing import List, Dict, Any, Optional
import shlex

from unified_agent.models import IAgentManager, CommandResult
from unified_agent.command_registry import CommandRegistry

logger = logging.getLogger(__name__)


class CLIInterface:
    """Command-line interface for the unified agent."""
    
    def __init__(
        self, 
        command_registry: CommandRegistry, 
        agent_manager: IAgentManager
    ):
        self.command_registry = command_registry
        self.agent_manager = agent_manager
        
    def run(self) -> None:
        """Run the CLI interface."""
        self._print_welcome_message()
        
        while True:
            try:
                user_input = input("\n> ")
                
                if user_input.lower() == "exit":
                    print("\nGoodbye! 👋")
                    break
                
                # Process commands or agent input
                if user_input.startswith("/"):
                    self._handle_command(user_input[1:])
                else:
                    self._process_agent_input(user_input)
                    
            except KeyboardInterrupt:
                print("\n\nExecution interrupted.")
                break
            except Exception as e:
                logger.error(f"Error: {str(e)}")
                print(f"\nAn error occurred: {str(e)}")
    
    def _print_welcome_message(self) -> None:
        """Print welcome message."""
        print("\n🤖 Unified Agent CLI 🤖\n")
        print("Type 'help' for available commands or 'exit' to quit.")
        print("Any other input will be processed by the agent.\n")
    
    def _handle_command(self, command_str: str) -> None:
        """Handle CLI commands."""
        try:
            # Parse command and arguments
            parts = shlex.split(command_str)
            if not parts:
                return
                
            command = parts[0].lower()
            args = parts[1:]
            
            # Execute command
            result = self.command_registry.execute(command, args)
            self._display_command_result(result)
            
        except Exception as e:
            logger.error(f"Error handling command: {str(e)}")
            print(f"\n❌ Error handling command: {str(e)}")
    
    def _display_command_result(self, result: CommandResult) -> None:
        """Display the result of a command execution."""
        if result.success:
            print(f"\n✅ {result.message}")
            if result.data:
                print(result.data)
        else:
            print(f"\n❌ {result.message}")
    
    def _process_agent_input(self, user_input: str) -> None:
        """Process input through the agent."""
        # Check for empty input
        if not user_input.strip():
            print("\n❌ Error: Empty input. Please enter a valid query or command.")
            return
            
        print("\nProcessing...")
        result = self.agent_manager.process_input(user_input)

        if result["success"]:
            response = result["response"]
            print(f"\n{response}")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
