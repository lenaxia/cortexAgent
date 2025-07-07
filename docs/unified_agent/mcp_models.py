"""Pydantic models for MCP tool calls."""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class MCPToolCall(BaseModel):
    """Model for MCP tool calls."""
    tool: str = Field(..., description="Name of the tool to call")
    server: str = Field(..., description="Name of the server providing the tool")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")


class MCPToolResult(BaseModel):
    """Model for MCP tool results."""
    status: str = Field(..., description="Status of the tool call (success or error)")
    tool_use_id: str = Field(..., description="ID of the tool use")
    content: Optional[list] = Field(None, description="Content returned by the tool")
    error: Optional[str] = Field(None, description="Error message if the tool call failed")
