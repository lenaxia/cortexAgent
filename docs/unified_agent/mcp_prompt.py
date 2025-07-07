"""MCP prompt utilities for the unified agent."""
from typing import List
from unified_agent.models import MCPTool

def create_mcp_system_prompt(base_prompt: str, mcp_servers: List[str], mcp_tools: List[MCPTool]) -> str:
    """Create a system prompt with explicit MCP tool usage instructions."""
    tool_descriptions = []
    
    # Connected MCP servers
    if mcp_servers:
        tool_descriptions.append("\nConnected MCP servers:")
        for server in mcp_servers:
            tool_descriptions.append(f"- {server}")
    
    # MCP tools
    if mcp_tools:
        tool_descriptions.append("\nAvailable MCP tools:")
        for tool in mcp_tools:
            tool_descriptions.append(f"- {tool.tool_name} ({tool.server_name}): {tool.description}")
    
    # Add explicit instructions for MCP tool usage
    tool_descriptions.append("\nIMPORTANT: When using MCP tools, you MUST use the following JSON format:")
    tool_descriptions.append("```mcp")
    tool_descriptions.append('{')
    tool_descriptions.append('  "tool": "ToolName",')
    tool_descriptions.append('  "server": "ServerName",')
    tool_descriptions.append('  "arguments": {')
    tool_descriptions.append('    "param1": "value1",')
    tool_descriptions.append('    "param2": "value2"')
    tool_descriptions.append('  }')
    tool_descriptions.append('}')
    tool_descriptions.append("```")
    tool_descriptions.append("Replace ToolName with the actual tool name, ServerName with the server name, and include any required parameters.")
    tool_descriptions.append("Do NOT use any other format for tool calls, such as TypeScript or function-style calls.")
    
    # Combine everything
    full_prompt = base_prompt
    if tool_descriptions:
        full_prompt += "\n\n" + "\n".join(tool_descriptions)
        
    return full_prompt
