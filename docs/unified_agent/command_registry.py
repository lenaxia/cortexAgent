"""Command registry for the unified agent CLI."""
from typing import Dict, List, Optional, Any
import logging

from unified_agent.models import ICommand, CommandResult

logger = logging.getLogger(__name__)


class CommandRegistry:
    """Registry for CLI commands."""
    
    def __init__(self):
        self.commands: Dict[str, ICommand] = {}
    
    def register(self, name: str, command: ICommand) -> None:
        """Register a command with the given name."""
        self.commands[name] = command
        logger.debug(f"Registered command: {name}")
    
    def get_command(self, name: str) -> Optional[ICommand]:
        """Get a command by name."""
        return self.commands.get(name)
    
    def execute(self, name: str, args: List[str]) -> CommandResult:
        """Execute a command by name with the given arguments."""
        command = self.get_command(name)
        if not command:
            return CommandResult(
                success=False, 
                message=f"Unknown command: {name}"
            )
        
        try:
            return command.execute(args)
        except Exception as e:
            logger.error(f"Error executing command {name}: {str(e)}")
            return CommandResult(
                success=False, 
                message=f"Error executing command: {str(e)}"
            )
    
    def get_command_names(self) -> List[str]:
        """Get all registered command names."""
        return list(self.commands.keys())
