"""Integration with Strands Agent library."""
from __future__ import annotations

import logging
import json
from typing import Any, Dict, List, Optional, Callable

from homeassistant.core import HomeAssistant

from .const import (
    CONF_SYSTEM_PROMPT,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
)
from .model_provider import ModelProvider
from .tool_registry import ToolRegistry
from .memory_handler import MemoryHandler
from .mcp_connector import MCPConnector
from .exceptions import ModelProviderError

_LOGGER = logging.getLogger(__name__)

# Import Strands Agent library
try:
    from strands import Agent
    from strands.models import (
        OpenAIModel,
        BedrockModel,
        AnthropicModel,
        LiteLLMModel,
    )
    from strands.types.tools import ToolUse, ToolResult, ToolResultContent
    STRANDS_AVAILABLE = True
except ImportError:
    _LOGGER.warning("Strands Agent library not available. Some features may not work.")
    STRANDS_AVAILABLE = False
    
    # Create mock classes for testing
    class Agent:
        """Mock implementation of Agent."""
        
        def __init__(self, system_prompt=None, tools=None, model=None):
            self.system_prompt = system_prompt
            self.tools = tools or []
            self.model = model
        
        def __call__(self, user_input):
            """Process user input."""
            tool_names = [getattr(t, 'tool_name', str(t)) for t in self.tools]
            return {"message": {"content": [{"text": f"Mock agent response for: {user_input}"}]}}
    
    class ToolUse:
        """Mock implementation of ToolUse."""
        def __init__(self, **kwargs):
            self.data = kwargs
            
        def get(self, key, default=None):
            return self.data.get(key, default)
            
    class ToolResultContent:
        """Mock implementation of ToolResultContent."""
        def __init__(self, text=None):
            self.text = text
            
    class ToolResult:
        """Mock implementation of ToolResult."""
        def __init__(self, toolUseId=None, status=None, content=None):
            self.toolUseId = toolUseId
            self.status = status
            self.content = content or []


class StrandsIntegration:
    """Integration with Strands Agent library."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        model_provider: ModelProvider,
        tool_registry: ToolRegistry,
        memory_handler: Optional[MemoryHandler] = None,
        mcp_connector: Optional[MCPConnector] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        """Initialize the integration."""
        self.hass = hass
        self.model_provider = model_provider
        self.tool_registry = tool_registry
        self.memory_handler = memory_handler
        self.mcp_connector = mcp_connector
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Create Strands Agent
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create a Strands Agent."""
        if not STRANDS_AVAILABLE:
            _LOGGER.warning("Strands Agent library not available. Using mock implementation.")
            return Agent(system_prompt=self.system_prompt)
        
        # Collect all tools
        tools = []
        
        # Add local tools
        local_tools = self._create_local_tools()
        tools.extend(local_tools)
        
        # Add memory tools if available
        if self.memory_handler:
            memory_tools = self._create_memory_tools()
            tools.extend(memory_tools)
        
        # Add MCP tools if available
        if self.mcp_connector:
            mcp_tools = self._create_mcp_tools()
            tools.extend(mcp_tools)
        
        # Create model
        model = self._create_model()
        
        # Create agent
        agent = Agent(
            system_prompt=self.system_prompt,
            tools=tools,
            model=model,
        )
        
        return agent
    
    def _create_model(self) -> Any:
        """Create a model for the agent."""
        if not STRANDS_AVAILABLE:
            return None
        
        try:
            # Get model configuration from model provider
            model_config = self.model_provider.config
            provider = model_config.get("provider")
            
            if provider == "openai":
                return OpenAIModel(
                    api_key=model_config.get("api_key"),
                    model_id=model_config.get("model_id", "gpt-4o"),
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    organization=model_config.get("org_id"),
                )
            elif provider == "bedrock":
                import boto3
                
                aws_profile = model_config.get("aws_profile")
                aws_region = model_config.get("aws_region", "us-west-2")
                
                # Create boto3 session with profile if specified
                if aws_profile:
                    session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
                else:
                    session = boto3.Session(region_name=aws_region)
                
                return BedrockModel(
                    model_id=model_config.get("model_id", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"),
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    boto_session=session,
                )
            elif provider == "anthropic":
                return AnthropicModel(
                    api_key=model_config.get("api_key"),
                    model_id=model_config.get("model_id", "claude-3-7-sonnet-20250219"),
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
            elif provider == "litellm":
                return LiteLLMModel(
                    api_key=model_config.get("api_key"),
                    model_id=model_config.get("model_id"),
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    base_url=model_config.get("base_url"),
                )
            else:
                _LOGGER.error("Unsupported provider: %s", provider)
                return None
        except Exception as ex:
            _LOGGER.error("Error creating model: %s", ex)
            return None
    
    def _create_local_tools(self) -> List[Callable]:
        """Create local tools for the agent."""
        if not STRANDS_AVAILABLE:
            return []
        
        tools = []
        
        # Get all tools from the tool registry
        registered_tools = self.tool_registry.get_all_tools()
        
        # Create a wrapper function for each tool
        for tool in registered_tools:
            tool_name = tool["name"]
            tool_function = tool["function"]
            
            # Create a wrapper function that matches the Strands Agent tool interface
            async def tool_wrapper(tool_use, tool_name=tool_name, tool_function=tool_function):
                try:
                    # Extract arguments from tool use
                    arguments = tool_use.get("input", {})
                    
                    # Call the tool function
                    result = await tool_function(self.hass, arguments)
                    
                    # Create a tool result
                    return ToolResult(
                        toolUseId=tool_use.get("toolUseId", ""),
                        status="success",
                        content=[ToolResultContent(text=json.dumps(result))]
                    )
                except Exception as ex:
                    _LOGGER.error("Error executing tool %s: %s", tool_name, ex)
                    return ToolResult(
                        toolUseId=tool_use.get("toolUseId", ""),
                        status="error",
                        content=[ToolResultContent(text=json.dumps({"error": str(ex)}))]
                    )
            
            # Set tool name and description
            tool_wrapper.tool_name = tool_name
            tool_wrapper.description = tool["description"]
            tool_wrapper.parameters = tool["parameters"]
            
            tools.append(tool_wrapper)
        
        return tools
    
    def _create_memory_tools(self) -> List[Callable]:
        """Create memory tools for the agent."""
        if not STRANDS_AVAILABLE or not self.memory_handler:
            return []
        
        # Import mem0_memory from strands_tools if available
        try:
            from strands_tools import mem0_memory, use_llm
            return [mem0_memory, use_llm]
        except ImportError:
            _LOGGER.warning("strands_tools not available. Memory tools will not be available.")
            return []
    
    def _create_mcp_tools(self) -> List[Callable]:
        """Create MCP tools for the agent."""
        if not STRANDS_AVAILABLE or not self.mcp_connector:
            return []
        
        tools = []
        
        # Get all MCP tools
        mcp_tools = self.mcp_connector.get_all_tools()
        
        # Create a wrapper function for each MCP tool
        for tool in mcp_tools:
            server_name = tool.server_name
            tool_name = tool.tool_name
            
            # Create a wrapper function that matches the Strands Agent tool interface
            async def mcp_tool_wrapper(tool_use, server_name=server_name, tool_name=tool_name):
                try:
                    # Extract arguments from tool use
                    arguments = tool_use.get("input", {})
                    
                    # Call the MCP tool
                    result = await self.mcp_connector.async_execute_tool(
                        server_name=server_name,
                        tool_name=tool_name,
                        arguments=arguments,
                    )
                    
                    # Create a tool result
                    return ToolResult(
                        toolUseId=tool_use.get("toolUseId", ""),
                        status="success",
                        content=[ToolResultContent(text=json.dumps(result))]
                    )
                except Exception as ex:
                    _LOGGER.error("Error executing MCP tool %s: %s", tool_name, ex)
                    return ToolResult(
                        toolUseId=tool_use.get("toolUseId", ""),
                        status="error",
                        content=[ToolResultContent(text=json.dumps({"error": str(ex)}))]
                    )
            
            # Set tool name and description
            mcp_tool_wrapper.tool_name = f"mcp_{server_name}_{tool_name}"
            mcp_tool_wrapper.description = tool.description
            mcp_tool_wrapper.parameters = tool.parameters
            
            tools.append(mcp_tool_wrapper)
        
        return tools
    
    async def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input and return a response."""
        if not STRANDS_AVAILABLE:
            # Fall back to model provider
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input},
            ]
            
            try:
                response = await self.model_provider.generate_response(
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                
                return {"content": response.get("content", "I'm sorry, I couldn't generate a response.")}
            except Exception as ex:
                _LOGGER.error("Error generating response: %s", ex)
                return {"error": str(ex)}
        
        try:
            # Process input with Strands Agent
            response = self.agent(user_input)
            
            # Extract text content from response
            text_content = self._extract_text_from_response(response)
            
            return {"content": text_content}
        except Exception as ex:
            _LOGGER.error("Error processing input with Strands Agent: %s", ex)
            return {"error": str(ex)}
    
    def _extract_text_from_response(self, response: Any) -> str:
        """Extract text content from a Strands Agent response."""
        # Handle AgentResult objects
        if hasattr(response, 'message'):
            # Extract the text content from the message
            try:
                # Try to get the text content from the message
                text_content = ""
                
                # Handle different response structures
                if hasattr(response.message, 'content'):
                    # Strands Agent response structure
                    for content in response.message.content:
                        if hasattr(content, 'text'):
                            text_content += content.text
                elif isinstance(response.message, dict) and 'content' in response.message:
                    # Alternative response structure
                    for content in response.message['content']:
                        if isinstance(content, dict) and 'text' in content:
                            text_content += content['text']
                
                return text_content
            except Exception as ex:
                _LOGGER.error("Error extracting text from AgentResult: %s", ex)
                return str(response)
        
        # If it's a string, return it directly
        if isinstance(response, str):
            return response
            
        # If we don't know how to handle it, convert it to a string
        return str(response)
    
    def reload(self) -> bool:
        """Reload the agent with updated configuration."""
        try:
            self.agent = self._create_agent()
            return True
        except Exception as ex:
            _LOGGER.error("Error reloading agent: %s", ex)
            return False