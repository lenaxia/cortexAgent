#!/usr/bin/env python3
"""Main entry point for the unified agent CLI."""
import argparse
import sys
import logging
import os
from typing import Optional

from unified_agent.models import AgentConfig, MemoryConfig
from unified_agent.config_manager import ConfigManagerFactory
from unified_agent.mcp_connector import MCPConnectorFactory
from unified_agent.memory_handler import MemoryHandlerFactory
from unified_agent.agent_manager import AgentManagerFactory
from unified_agent.command_registry import CommandRegistry
from unified_agent.commands import (
    HelpCommand, ConnectCommand, DisconnectCommand, 
    ListServersCommand, ListToolsCommand, RememberCommand,
    RecallCommand, MemoriesCommand, ConfigCommand, ReloadCommand,
    AWSProfileCommand
)
from unified_agent.cli_interface import CLIInterface


def configure_logging(log_file: Optional[str] = None, debug: bool = False) -> None:
    """Configure logging for the application."""
    if log_file:
        log_path = os.path.expanduser(log_file)
        log_dir = os.path.dirname(log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    else:
        log_path = os.path.expanduser("~/.unified_agent/agent.log")
        log_dir = os.path.dirname(log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    # Configure root logger
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(stream=sys.stderr),
            logging.FileHandler(log_path)
        ]
    )
    
    # Set specific loggers to different levels if needed
    logging.getLogger("mcp").setLevel(logging.WARNING)
    logging.getLogger("strands").setLevel(logging.WARNING)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Unified Agent CLI")
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file",
        default="~/.unified_agent/config.json"
    )
    parser.add_argument(
        "--log-file", 
        type=str, 
        help="Path to log file",
        default="~/.unified_agent/agent.log"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    parser.add_argument(
        "--aws-profile",
        type=str,
        help="AWS profile to use for credentials (overrides config file)"
    )
    return parser.parse_args()


def create_application(config_path: str, aws_profile: Optional[str] = None) -> CLIInterface:
    """Create the application with all its components."""
    # Create core components
    config_manager = ConfigManagerFactory.create(config_path)
    mcp_connector = MCPConnectorFactory.create()
    memory_handler = MemoryHandlerFactory.create(config_manager.config.memory)
    
    # Use AWS profile from command line if provided, otherwise use from config
    aws_profile_to_use = aws_profile or config_manager.config.aws_profile
    
    # Log which AWS profile is being used
    if aws_profile_to_use:
        logging.info(f"Using AWS profile: {aws_profile_to_use}")
        if aws_profile:
            logging.info("AWS profile from command line arguments")
        else:
            logging.info(f"AWS profile from config file: {config_manager.config.aws_profile}")
            
        # Set the AWS_PROFILE environment variable
        import os
        os.environ["AWS_PROFILE"] = aws_profile_to_use
        logging.info(f"Set AWS_PROFILE environment variable to: {aws_profile_to_use}")
    
    agent_manager = AgentManagerFactory.create(
        config_manager.config,
        mcp_connector,
        memory_handler,
        aws_profile_to_use
    )
    
    # Create command registry
    command_registry = CommandRegistry()
    
    # Register commands
    command_registry.register("help", HelpCommand())
    command_registry.register("connect", ConnectCommand(
        mcp_connector, config_manager, agent_manager
    ))
    command_registry.register("disconnect", DisconnectCommand(
        mcp_connector, config_manager, agent_manager
    ))
    command_registry.register("list-servers", ListServersCommand(
        config_manager, mcp_connector
    ))
    command_registry.register("list-tools", ListToolsCommand(mcp_connector))
    command_registry.register("remember", RememberCommand(memory_handler))
    command_registry.register("recall", RecallCommand(memory_handler))
    command_registry.register("memories", MemoriesCommand(memory_handler))
    command_registry.register("config", ConfigCommand(config_manager))
    command_registry.register("reload", ReloadCommand(agent_manager))
    command_registry.register("aws-profile", AWSProfileCommand(config_manager, agent_manager))
    
    # Connect to configured MCP servers
    connected_any = False
    for server_config in config_manager.config.mcp_servers:
        if server_config.enabled:
            if mcp_connector.connect(server_config):
                connected_any = True
    
    # Reload the agent if any servers were connected
    if connected_any:
        agent_manager.reload_agent()
        logging.info("Reloaded agent after connecting to MCP servers")
    
    # Create CLI interface
    cli_interface = CLIInterface(command_registry, agent_manager)
    
    return cli_interface


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_args()
    
    # Configure logging
    configure_logging(args.log_file, args.debug)
    
    # Create and run the application
    try:
        app = create_application(args.config, args.aws_profile)
        app.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
