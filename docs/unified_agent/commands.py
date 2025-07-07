"""Command implementations for the unified agent CLI."""
from typing import Dict, List, Optional, Any
import logging
import json

from unified_agent.models import (
    CommandResult, ICommand, IConfigManager, IMCPConnector, 
    MCPServerConfig, MCPServerType, IMemoryHandler, IAgentManager,
    AgentConfig
)

logger = logging.getLogger(__name__)


class HelpCommand(ICommand):
    """Command to show help information."""
    
    def execute(self, args: List[str]) -> CommandResult:
        help_text = """
Available Commands:
  /help                 Show this help message
  /connect <url> <type> Connect to an MCP server (type: sse, streamable-http)
  /disconnect <name>    Disconnect from an MCP server
  /list-servers         List connected MCP servers
  /list-tools           List available tools
  /remember <text>      Store information in memory
  /recall <query>       Retrieve information from memory
  /memories             List all stored memories
  /config               Show current configuration
  /reload               Reload the agent with updated configuration
  /aws-profile [name]   Show or set the AWS profile
  
Any other input will be processed by the agent.
"""
        return CommandResult(success=True, message="Help Information", data=help_text)


class ConnectCommand(ICommand):
    """Command to connect to an MCP server."""
    
    def __init__(
        self, 
        mcp_connector: IMCPConnector, 
        config_manager: IConfigManager,
        agent_manager: IAgentManager
    ):
        self.mcp_connector = mcp_connector
        self.config_manager = config_manager
        self.agent_manager = agent_manager
    
    def execute(self, args: List[str]) -> CommandResult:
        if len(args) < 1:
            return CommandResult(success=False, message="Usage: /connect <url> [type] [name]")
            
        url = args[0]
        server_type = args[1] if len(args) > 1 else "sse"
        name = args[2] if len(args) > 2 else f"server_{len(self.config_manager.config.mcp_servers) + 1}"
        
        try:
            # Validate server type
            server_type_enum = MCPServerType(server_type)
            
            # Create server config
            server_config = MCPServerConfig(
                name=name,
                url=url,
                server_type=server_type_enum
            )
            
            # Connect to server
            if self.mcp_connector.connect(server_config):
                # Save to config if successful
                self.config_manager.add_mcp_server(server_config)
                # Reload agent to include new tools
                if self.agent_manager.reload_agent():
                    logger.info(f"Reloaded agent after connecting to MCP server: {name}")
                    return CommandResult(success=True, message=f"Connected to MCP server: {name}")
                else:
                    return CommandResult(success=True, message=f"Connected to MCP server: {name}, but failed to reload agent")
            else:
                return CommandResult(success=False, message=f"Failed to connect to MCP server: {url}")
                
        except ValueError:
            return CommandResult(success=False, message=f"Invalid server type: {server_type}. Use 'sse' or 'streamable-http'")
        except Exception as e:
            return CommandResult(success=False, message=f"Error connecting to server: {str(e)}")


class DisconnectCommand(ICommand):
    """Command to disconnect from an MCP server."""
    
    def __init__(
        self, 
        mcp_connector: IMCPConnector, 
        config_manager: IConfigManager,
        agent_manager: IAgentManager
    ):
        self.mcp_connector = mcp_connector
        self.config_manager = config_manager
        self.agent_manager = agent_manager
    
    def execute(self, args: List[str]) -> CommandResult:
        if len(args) < 1:
            return CommandResult(success=False, message="Usage: /disconnect <name>")
            
        server_name = args[0]
        
        if self.mcp_connector.disconnect(server_name):
            self.config_manager.remove_mcp_server(server_name)
            self.agent_manager.reload_agent()
            return CommandResult(success=True, message=f"Disconnected from MCP server: {server_name}")
        else:
            return CommandResult(success=False, message=f"Failed to disconnect from server: {server_name}")


class ListServersCommand(ICommand):
    """Command to list connected MCP servers."""
    
    def __init__(self, config_manager: IConfigManager, mcp_connector: IMCPConnector):
        self.config_manager = config_manager
        self.mcp_connector = mcp_connector
    
    def execute(self, args: List[str]) -> CommandResult:
        servers = self.config_manager.config.mcp_servers
        if not servers:
            return CommandResult(success=True, message="No MCP servers configured")
            
        server_info = "\nConfigured MCP Servers:\n"
        connected_servers = self.mcp_connector.get_connected_servers()
        
        for server in servers:
            status = "Connected" if server.name in connected_servers else "Disconnected"
            server_info += f"- {server.name}: {server.url} ({server.server_type}) - {status}\n"
            
        return CommandResult(success=True, message="MCP Servers", data=server_info)


class ListToolsCommand(ICommand):
    """Command to list available tools."""
    
    def __init__(self, mcp_connector: IMCPConnector):
        self.mcp_connector = mcp_connector
    
    def execute(self, args: List[str]) -> CommandResult:
        tools = self.mcp_connector.get_all_tools()
        
        if not tools:
            return CommandResult(success=True, message="No tools available from MCP servers")
            
        tool_info = "\nAvailable MCP Tools:\n"
        by_server = {}
        
        for tool in tools:
            if tool.server_name not in by_server:
                by_server[tool.server_name] = []
            by_server[tool.server_name].append(tool)
            
        for server_name, server_tools in by_server.items():
            tool_info += f"\n{server_name}:\n"
            for tool in server_tools:
                tool_info += f"- {tool.tool_name}: {tool.description}\n"
                
        return CommandResult(success=True, message="Available Tools", data=tool_info)


class RememberCommand(ICommand):
    """Command to store information in memory."""
    
    def __init__(self, memory_handler: IMemoryHandler):
        self.memory_handler = memory_handler
    
    def execute(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(success=False, message="Usage: /remember <text>")
            
        content = " ".join(args)
        result = self.memory_handler.store(content)
        
        if result["success"]:
            return CommandResult(success=True, message="Information stored in memory")
        else:
            return CommandResult(success=False, message=f"Failed to store memory: {result.get('error', 'Unknown error')}")


class RecallCommand(ICommand):
    """Command to retrieve information from memory."""
    
    def __init__(self, memory_handler: IMemoryHandler):
        self.memory_handler = memory_handler
    
    def execute(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(success=False, message="Usage: /recall <query>")
            
        query = " ".join(args)
        result = self.memory_handler.retrieve(query)
        
        if result["success"]:
            memories = result.get("result", {}).get("memories", [])
            if not memories:
                return CommandResult(success=True, message="No relevant memories found")
                
            memory_text = "\nRetrieved Memories:\n"
            for i, memory in enumerate(memories, 1):
                memory_text += f"{i}. {memory.get('content', 'No content')}\n"
                
            return CommandResult(success=True, message="Retrieved memories", data=memory_text)
        else:
            return CommandResult(success=False, message=f"Failed to retrieve memories: {result.get('error', 'Unknown error')}")


class MemoriesCommand(ICommand):
    """Command to list all stored memories."""
    
    def __init__(self, memory_handler: IMemoryHandler):
        self.memory_handler = memory_handler
    
    def execute(self, args: List[str]) -> CommandResult:
        result = self.memory_handler.list_all()
        
        if result["success"]:
            memories = result.get("result", {}).get("memories", [])
            if not memories:
                return CommandResult(success=True, message="No memories stored")
                
            memory_text = "\nAll Stored Memories:\n"
            for i, memory in enumerate(memories, 1):
                memory_text += f"{i}. {memory.get('content', 'No content')}\n"
                
            return CommandResult(success=True, message="All memories", data=memory_text)
        else:
            return CommandResult(success=False, message=f"Failed to list memories: {result.get('error', 'Unknown error')}")


class ConfigCommand(ICommand):
    """Command to show current configuration."""
    
    def __init__(self, config_manager: IConfigManager):
        self.config_manager = config_manager
    
    def execute(self, args: List[str]) -> CommandResult:
        config_dict = self.config_manager.config.dict()
        config_text = json.dumps(config_dict, indent=2)
        return CommandResult(success=True, message="Current Configuration", data=config_text)


class ReloadCommand(ICommand):
    """Command to reload the agent with updated configuration."""
    
    def __init__(self, agent_manager: IAgentManager):
        self.agent_manager = agent_manager
    
    def execute(self, args: List[str]) -> CommandResult:
        if self.agent_manager.reload_agent():
            return CommandResult(success=True, message="Agent reloaded with updated configuration")
        else:
            return CommandResult(success=False, message="Failed to reload agent")


class AWSProfileCommand(ICommand):
    """Command to set the AWS profile in the configuration."""
    
    def __init__(self, config_manager: IConfigManager, agent_manager: IAgentManager):
        self.config_manager = config_manager
        self.agent_manager = agent_manager
    
    def execute(self, args: List[str]) -> CommandResult:
        if not args:
            # Show current AWS profile
            current_profile = self.config_manager.config.aws_profile
            if current_profile:
                return CommandResult(success=True, message=f"Current AWS profile: {current_profile}")
            else:
                return CommandResult(success=True, message="No AWS profile configured")
        
        # Set new AWS profile
        profile_name = args[0]
        
        # Update the config
        config = self.config_manager.config
        config.aws_profile = profile_name
        
        # Save the config
        if self.config_manager.save_config():
            # Reload the agent to use the new profile
            self.agent_manager.reload_agent()
            return CommandResult(success=True, message=f"AWS profile set to: {profile_name}")
        else:
            return CommandResult(success=False, message="Failed to save configuration")
