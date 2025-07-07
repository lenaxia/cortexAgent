"""Memory operations for the unified agent."""
from typing import Dict, List, Optional, Any
import logging
import os
import json
from pathlib import Path

from unified_agent.models import MemoryConfig, IMemoryHandler

# Import mem0_memory from strands_tools
try:
    from strands_tools import mem0_memory
    from strands.types.tools import ToolUse, ToolResult
except ImportError:
    raise ImportError(
        "The strands-agents-tools package is required for memory operations. "
        "Please install it using: pip install strands-agents-tools[mem0_memory]"
    )

logger = logging.getLogger(__name__)


class MemoryHandlerFactory:
    """Factory for creating memory handlers."""
    
    @staticmethod
    def create(config: Optional[MemoryConfig] = None) -> 'MemoryHandler':
        """Create a new memory handler."""
        return MemoryHandler(config)


class MemoryHandler:
    """Handles memory operations using mem0."""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config
        self._configure_environment()
        
    def _configure_environment(self) -> None:
        """Configure environment variables for memory."""
        if not self.config:
            return
            
        if self.config.aws_region:
            os.environ["AWS_REGION"] = self.config.aws_region
        if self.config.opensearch_host:
            os.environ["OPENSEARCH_HOST"] = self.config.opensearch_host
    
    def store(self, content: str) -> Dict[str, Any]:
        """Store information in memory."""
        if not self.config or not self.config.enabled:
            logger.warning("Memory is not enabled")
            return {"success": False, "error": "Memory is not enabled"}
            
        try:
            # Create a ToolUse object for mem0_memory
            tool_use = ToolUse(
                toolUseId="memory-store",
                name="mem0_memory",
                input={
                    "action": "store",
                    "content": content,
                    "user_id": self.config.user_id
                }
            )
            
            # Call mem0_memory
            result = mem0_memory(tool_use)
            
            # Extract the result content
            if result.status == "success" and result.content:
                content_text = result.content[0].text if result.content[0].text else "{}"
                try:
                    result_data = json.loads(content_text)
                except json.JSONDecodeError:
                    result_data = {"message": content_text}
            else:
                result_data = {"message": "No content returned"}
                
            logger.info(f"Stored memory: {content[:50]}...")
            return {"success": True, "result": result_data}
        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def retrieve(self, query: str) -> Dict[str, Any]:
        """Retrieve information from memory based on query."""
        if not self.config or not self.config.enabled:
            logger.warning("Memory is not enabled")
            return {"success": False, "error": "Memory is not enabled"}
            
        try:
            # Create a ToolUse object for mem0_memory
            tool_use = ToolUse(
                toolUseId="memory-retrieve",
                name="mem0_memory",
                input={
                    "action": "retrieve",
                    "query": query,
                    "user_id": self.config.user_id
                }
            )
            
            # Call mem0_memory
            result = mem0_memory(tool_use)
            
            # Extract the result content
            if result.status == "success" and result.content:
                content_text = result.content[0].text if result.content[0].text else "{}"
                try:
                    result_data = json.loads(content_text)
                except json.JSONDecodeError:
                    result_data = {"message": content_text}
            else:
                result_data = {"message": "No content returned"}
                
            logger.info(f"Retrieved memories for query: {query}")
            return {"success": True, "result": result_data}
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def list_all(self) -> Dict[str, Any]:
        """List all stored memories."""
        if not self.config or not self.config.enabled:
            logger.warning("Memory is not enabled")
            return {"success": False, "error": "Memory is not enabled"}
            
        try:
            # Create a ToolUse object for mem0_memory
            tool_use = ToolUse(
                toolUseId="memory-list",
                name="mem0_memory",
                input={
                    "action": "list",
                    "user_id": self.config.user_id
                }
            )
            
            # Call mem0_memory
            result = mem0_memory(tool_use)
            
            # Extract the result content
            if result.status == "success" and result.content:
                content_text = result.content[0].text if result.content[0].text else "{}"
                try:
                    result_data = json.loads(content_text)
                except json.JSONDecodeError:
                    result_data = {"message": content_text}
            else:
                result_data = {"message": "No content returned"}
                
            logger.info("Listed all memories")
            return {"success": True, "result": result_data}
        except Exception as e:
            logger.error(f"Failed to list memories: {str(e)}")
            return {"success": False, "error": str(e)}
