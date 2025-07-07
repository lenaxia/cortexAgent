"""Data models and interfaces for the unified agent."""
from typing import Dict, List, Optional, Union, Any, Protocol, runtime_checkable
from enum import Enum
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, validator


class MCPServerType(str, Enum):
    """Type of MCP server connection."""
    SSE = "sse"
    STREAMABLE_HTTP = "streamable-http"
    WEBSOCKET = "websocket"


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server connection."""
    name: str = Field(..., description="Unique name for this MCP server")
    url: str = Field(..., description="URL of the MCP server")
    server_type: MCPServerType = Field(default=MCPServerType.SSE, description="Type of server connection")
    auth_token: Optional[str] = Field(None, description="Authentication token if required")
    enabled: bool = Field(default=True, description="Whether this server is enabled")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class MCPTool(BaseModel):
    """Information about a tool provided by an MCP server."""
    server_name: str = Field(..., description="Name of the server providing this tool")
    tool_name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters the tool accepts")


class MemoryConfig(BaseModel):
    """Configuration for memory capabilities."""
    enabled: bool = Field(default=True, description="Whether memory is enabled")
    user_id: str = Field(..., description="User ID for memory storage")
    memory_type: str = Field(default="mem0", description="Type of memory to use")
    aws_region: Optional[str] = Field(None, description="AWS region for memory storage")
    opensearch_host: Optional[str] = Field(None, description="OpenSearch host for memory storage")


class AgentConfig(BaseModel):
    """Configuration for the unified agent."""
    name: str = Field(default="Unified Agent", description="Name of the agent")
    system_prompt: str = Field(..., description="System prompt for the agent")
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list, description="MCP servers to connect to")
    memory: Optional[MemoryConfig] = Field(None, description="Memory configuration")
    http_enabled: bool = Field(default=False, description="Whether HTTP capabilities are enabled")
    aws_profile: Optional[str] = Field(None, description="AWS profile to use for credentials")
    
    class Config:
        validate_assignment = True


class CommandResult(BaseModel):
    """Result of a command execution."""
    success: bool
    message: str
    data: Optional[Any] = None


@runtime_checkable
class IMCPConnector(Protocol):
    """Interface for MCP server connections."""
    def connect(self, config: MCPServerConfig) -> bool: ...
    def disconnect(self, server_name: str) -> bool: ...
    def get_all_tools(self) -> List[MCPTool]: ...
    def get_connected_servers(self) -> List[str]: ...


@runtime_checkable
class IMemoryHandler(Protocol):
    """Interface for memory operations."""
    def store(self, content: str) -> Dict[str, Any]: ...
    def retrieve(self, query: str) -> Dict[str, Any]: ...
    def list_all(self) -> Dict[str, Any]: ...


@runtime_checkable
class IConfigManager(Protocol):
    """Interface for configuration management."""
    @property
    def config(self) -> AgentConfig: ...
    def save_config(self) -> bool: ...
    def add_mcp_server(self, server_config: MCPServerConfig) -> bool: ...
    def remove_mcp_server(self, server_name: str) -> bool: ...
    def update_memory_config(self, memory_config: MemoryConfig) -> bool: ...


@runtime_checkable
class IAgentManager(Protocol):
    """Interface for agent management."""
    def process_input(self, user_input: str) -> Dict[str, Any]: ...
    def reload_agent(self) -> bool: ...


class ICommand(ABC):
    """Interface for CLI commands."""
    @abstractmethod
    def execute(self, args: List[str]) -> CommandResult:
        """Execute the command with the given arguments."""
        pass
