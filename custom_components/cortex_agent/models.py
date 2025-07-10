"""Data models and interfaces for the CortexAgent integration."""
from __future__ import annotations

from typing import Dict, List, Optional, Union, Any, Protocol, runtime_checkable
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field, validator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry


class ModelProviderType(str, Enum):
    """Type of model provider."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    LITELLM = "litellm"


class MCPServerType(str, Enum):
    """Type of MCP server connection."""
    LOCAL = "local"
    REMOTE = "remote"


class MessageRole(str, Enum):
    """Role in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

@dataclass
class Message:
    """Message in a conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

# Alias for backward compatibility
ConversationRole = MessageRole


class ToolExecutionStatus(str, Enum):
    """Status of tool execution."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    name: str
    description: str
    category: str = "uncategorized"
    permissions: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    status: ToolExecutionStatus = ToolExecutionStatus.SUCCESS

    def __post_init__(self):
        """Set status based on success."""
        if not self.success:
            self.status = ToolExecutionStatus.ERROR


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server connection."""
    name: str = Field(..., description="Unique name for this MCP server")
    url: str = Field(..., description="URL of the MCP server")
    server_type: MCPServerType = Field(default=MCPServerType.REMOTE, description="Type of server connection")
    auth_token: Optional[str] = Field(None, description="Authentication token if required")
    enabled: bool = Field(default=True, description="Whether this server is enabled")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://', 'ws://', 'wss://')):
            raise ValueError('URL must start with http://, https://, ws://, or wss://')
        return v


class MemoryConfig(BaseModel):
    """Configuration for memory capabilities."""
    enabled: bool = Field(default=True, description="Whether memory is enabled")
    user_id: str = Field(..., description="User ID for memory storage")
    memory_type: str = Field(default="mem0", description="Type of memory to use")


class ConversationEntry(BaseModel):
    """Entry in a conversation."""
    role: ConversationRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for the agent."""
    name: str = Field(default="CortexAgent", description="Name of the agent")
    system_prompt: str = Field(..., description="System prompt for the agent")
    provider: ModelProviderType = Field(..., description="Model provider type")
    model_id: str = Field(..., description="Model ID to use")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    max_tokens: int = Field(default=1500, description="Maximum tokens for response")
    temperature: float = Field(default=0.7, description="Temperature for response generation")
    memory_enabled: bool = Field(default=False, description="Whether memory is enabled")
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list, description="MCP servers to connect to")
    custom_tools: List[Dict[str, Any]] = Field(default_factory=list, description="Custom tools configuration")
    
    class Config:
        """Pydantic config."""
        validate_assignment = True


@runtime_checkable
class IModelProvider(Protocol):
    """Interface for model providers."""
    
    @property
    def provider_type(self) -> ModelProviderType:
        """Get the provider type."""
        ...
    
    @property
    def name(self) -> str:
        """Get the provider name."""
        ...
    
    @property
    def connected(self) -> bool:
        """Check if provider is connected."""
        ...
    
    async def generate_response(self, messages: List[Dict[str, Any]], tools: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Generate a response from the model."""
        ...
    
    async def test_connection(self) -> bool:
        """Test the connection to the provider."""
        ...


@runtime_checkable
class IConversationManager(Protocol):
    """Interface for conversation management."""
    
    def add_entry(self, role: ConversationRole, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add an entry to the conversation."""
        ...
    
    def get_history(self, limit: Optional[int] = None) -> List[ConversationEntry]:
        """Get conversation history."""
        ...
    
    def get_formatted_history(self) -> List[Dict[str, Any]]:
        """Get formatted history for model consumption."""
        ...
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        ...
    
    async def save(self) -> None:
        """Save conversation to storage."""
        ...
    
    async def load(self) -> None:
        """Load conversation from storage."""
        ...


@runtime_checkable
class IToolManager(Protocol):
    """Interface for tool management."""
    
    async def get_available_tools(self) -> List[Any]:
        """Get all available tools."""
        ...
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool with given arguments."""
        ...
    
    def register_tool(self, tool_name: str, tool_function: Any, metadata: Optional[ToolMetadata] = None) -> None:
        """Register a new tool."""
        ...
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        ...


@runtime_checkable
class IMCPConnector(Protocol):
    """Interface for MCP server connections."""
    
    async def connect(self, config: MCPServerConfig) -> bool:
        """Connect to an MCP server."""
        ...
    
    async def disconnect(self, server_name: str) -> bool:
        """Disconnect from an MCP server."""
        ...
    
    async def get_available_tools(self, server_name: Optional[str] = None) -> List[Any]:
        """Get available tools from MCP servers."""
        ...
    
    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool on an MCP server."""
        ...
    
    def get_connected_servers(self) -> List[str]:
        """Get list of connected server names."""
        ...


@runtime_checkable
class IMemoryHandler(Protocol):
    """Interface for memory operations."""
    
    async def store(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store information in memory."""
        ...
    
    async def retrieve(self, query: str) -> Dict[str, Any]:
        """Retrieve information from memory based on query."""
        ...
    
    async def list_all(self) -> Dict[str, Any]:
        """List all stored memories."""
        ...
    
    async def clear(self) -> Dict[str, Any]:
        """Clear all stored memories."""
        ...


class AgentMetrics(BaseModel):
    """Metrics for agent performance."""
    requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    tool_usage: Dict[str, int] = Field(default_factory=dict)
    response_times: List[float] = Field(default_factory=list)
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"prompt": 0, "completion": 0, "total": 0})
    errors: Dict[str, int] = Field(default_factory=lambda: {"api": 0, "rate_limit": 0, "network": 0, "timeout": 0, "other": 0})
    last_reset: datetime = Field(default_factory=datetime.now)
    
    def record_request(self, successful: bool = True, response_time: Optional[float] = None, error_type: Optional[str] = None) -> None:
        """Record a request."""
        self.requests += 1
        
        if successful:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if error_type and error_type in self.errors:
                self.errors[error_type] += 1
            else:
                self.errors["other"] += 1
        
        if response_time is not None:
            self.response_times.append(response_time)
            # Keep only the last 100 response times
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-100:]
    
    def record_tool_usage(self, tool_name: str) -> None:
        """Record tool usage."""
        if tool_name not in self.tool_usage:
            self.tool_usage[tool_name] = 0
        self.tool_usage[tool_name] += 1
    
    def record_token_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Record token usage."""
        self.token_usage["prompt"] += prompt_tokens
        self.token_usage["completion"] += completion_tokens
        self.token_usage["total"] += prompt_tokens + completion_tokens
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.requests == 0:
            return 0.0
        return self.successful_requests / self.requests
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.tool_usage = {}
        self.response_times = []
        self.token_usage = {"prompt": 0, "completion": 0, "total": 0}
        self.errors = {"api": 0, "rate_limit": 0, "network": 0, "timeout": 0, "other": 0}
        self.last_reset = datetime.now()