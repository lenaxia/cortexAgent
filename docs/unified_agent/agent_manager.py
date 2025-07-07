"""Agent management for the unified agent."""
from typing import Dict, List, Optional, Any
import logging
import json

from unified_agent.models import AgentConfig, MCPTool, IAgentManager, IMCPConnector, IMemoryHandler

# Import Agent class and BedrockModel
try:
    from strands import Agent
    from strands.models import BedrockModel
except ImportError:
    # Create a mock implementation for testing
    class BedrockModel:
        """Mock implementation of BedrockModel."""
        
        def __init__(self, model_id=None, boto_session=None, **kwargs):
            self.model_id = model_id
            self.boto_session = boto_session
            self.kwargs = kwargs
    
    class Agent:
        """Mock implementation of Agent."""
        
        def __init__(self, system_prompt=None, tools=None, model=None):
            self.system_prompt = system_prompt
            self.tools = tools or []
            self.model = model
        
        def __call__(self, user_input):
            """Process user input."""
            tool_names = [getattr(t, 'tool_name', str(t)) for t in self.tools]
            return f"Mock agent response for: {user_input}\nAvailable tools: {', '.join(tool_names)}"

# Import tools
try:
    from strands_tools import http_request, mem0_memory, use_llm
except ImportError:
    # Create mock implementations for testing
    def http_request(url=None, method=None, **kwargs):
        """Mock implementation of http_request."""
        return {"status": 200, "body": "Mock HTTP response"}
    
    # Import the ToolUse and ToolResult classes for the mock implementation
    try:
        from strands.types.tools import ToolUse, ToolResult, ToolResultContent
    except ImportError:
        # Create simple mock classes if strands is not available
        class ToolUse:
            def __init__(self, **kwargs):
                self.data = kwargs
                
            def get(self, key, default=None):
                return self.data.get(key, default)
                
        class ToolResultContent:
            def __init__(self, text=None):
                self.text = text
                
        class ToolResult:
            def __init__(self, toolUseId=None, status=None, content=None):
                self.toolUseId = toolUseId
                self.status = status
                self.content = content or []
    
    def mem0_memory(tool_use):
        """Mock implementation of mem0_memory."""
        tool_input = tool_use.get("input", {})
        action = tool_input.get("action")
        content = tool_input.get("content")
        query = tool_input.get("query")
        user_id = tool_input.get("user_id")
        tool_use_id = tool_use.get("toolUseId", "mock-id")
        
        if action == "store":
            result = {"status": "success", "message": f"Stored memory: {content}"}
            return ToolResult(
                toolUseId=tool_use_id,
                status="success",
                content=[ToolResultContent(text=json.dumps([result]))]
            )
        elif action == "retrieve":
            memories = [{"content": f"Mock memory for query: {query}"}]
            return ToolResult(
                toolUseId=tool_use_id,
                status="success",
                content=[ToolResultContent(text=json.dumps(memories))]
            )
        elif action == "list":
            memories = [{"content": "Mock memory 1"}, {"content": "Mock memory 2"}]
            return ToolResult(
                toolUseId=tool_use_id,
                status="success",
                content=[ToolResultContent(text=json.dumps(memories))]
            )
        return ToolResult(
            toolUseId=tool_use_id,
            status="error",
            content=[ToolResultContent(text=json.dumps({"message": "Invalid action"}))]
        )
    
    def use_llm(prompt=None, **kwargs):
        """Mock implementation of use_llm."""
        return f"Mock LLM response for: {prompt}"

logger = logging.getLogger(__name__)


class AgentManagerFactory:
    """Factory for creating agent managers."""
    
    @staticmethod
    def create(
        config: AgentConfig, 
        mcp_connector: IMCPConnector, 
        memory_handler: IMemoryHandler,
        aws_profile: Optional[str] = None
    ) -> 'AgentManager':
        """Create a new agent manager."""
        return AgentManager(config, mcp_connector, memory_handler, aws_profile)


class AgentManager:
    """Manages the unified agent with dynamic tool loading."""
    
    def __init__(
        self, 
        config: AgentConfig, 
        mcp_connector: IMCPConnector, 
        memory_handler: IMemoryHandler,
        aws_profile: Optional[str] = None
    ):
        self.config = config
        self.mcp_connector = mcp_connector
        self.memory_handler = memory_handler
        
        # Use the AWS profile from the command line if provided, otherwise use from config
        self.aws_profile = aws_profile if aws_profile is not None else config.aws_profile
        
        # Log which AWS profile is being used
        if self.aws_profile:
            logger.info(f"AgentManager using AWS profile: {self.aws_profile}")
            if aws_profile:
                logger.info("AWS profile from command line arguments")
            else:
                logger.info(f"AWS profile from config file: {config.aws_profile}")
                
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Any:
        """Create an agent with the configured tools."""
        # Collect all tools
        tools = []
        
        # Add memory tools if enabled
        if self.config.memory and self.config.memory.enabled:
            tools.append(mem0_memory)
            tools.append(use_llm)
            
        # Add HTTP tools if enabled
        if self.config.http_enabled:
            tools.append(http_request)
            
        # Add MCP tools
        mcp_tools = self.mcp_connector.get_all_tools()
        tools.extend(mcp_tools)
        
        # Create the agent
        system_prompt = self._build_system_prompt()
        
        # Set up AWS credentials if profile is specified
        model = None
        if self.aws_profile:
            try:
                import boto3
                import os
                
                # Set the AWS_PROFILE environment variable
                os.environ["AWS_PROFILE"] = self.aws_profile
                
                # Create a boto3 session with the specified profile
                session = boto3.Session(profile_name=self.aws_profile)
                
                # Create a BedrockModel with the boto3 session
                model = BedrockModel(
                    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                    boto_session=session
                )
                
                logger.info(f"Created BedrockModel with boto3 session for profile: {self.aws_profile}")
            except Exception as e:
                logger.error(f"Error creating BedrockModel: {str(e)}")
        
        # Create the agent with the BedrockModel if available
        agent = Agent(system_prompt=system_prompt, tools=tools, model=model)
        
        logger.info(f"Created agent with {len(tools)} tools")
        return agent
    
    def _build_system_prompt(self) -> str:
        """Build a comprehensive system prompt based on configuration."""
        from unified_agent.mcp_prompt import create_mcp_system_prompt
        
        base_prompt = self.config.system_prompt
        
        # Get connected servers and tools
        connected_servers = self.mcp_connector.get_connected_servers()
        logger.info(f"Connected MCP servers: {connected_servers}")
        for server in connected_servers:
            logger.info(f"Adding MCP server to system prompt: {server}")
        
        # Get MCP tools
        mcp_tools = self.mcp_connector.get_all_tools()
        
        # Create the MCP-specific part of the prompt
        mcp_prompt = create_mcp_system_prompt(base_prompt, connected_servers, mcp_tools)
        
        # Add additional capabilities
        additional_capabilities = []
        
        # Memory capabilities
        if self.config.memory and self.config.memory.enabled:
            additional_capabilities.append("\nMemory capabilities:")
            additional_capabilities.append("- Store information for later retrieval")
            additional_capabilities.append("- Retrieve relevant memories based on context")
            additional_capabilities.append("- List all stored memories")
        
        # HTTP capabilities
        if self.config.http_enabled:
            additional_capabilities.append("\nHTTP capabilities:")
            additional_capabilities.append("- Make HTTP requests to external APIs")
            additional_capabilities.append("- Process and display response data")
        
        # Combine everything
        full_prompt = mcp_prompt
        if additional_capabilities:
            full_prompt += "\n\n" + "\n".join(additional_capabilities)
            
        return full_prompt
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input through the agent using an agentic loop."""
        try:
            # Get all connected MCP servers
            server_names = self.mcp_connector.get_connected_servers()
            
            # Get all clients
            clients = [self.mcp_connector.get_client(name) for name in server_names]
            clients = [client for client in clients if client is not None]
            
            # Initialize the agentic loop
            max_iterations = 5  # Prevent infinite loops
            current_input = user_input
            final_response = None
            
            # Use nested context managers for all clients
            with self._activate_all_clients(clients) as active_clients:
                # Run the agentic loop
                for iteration in range(max_iterations):
                    logger.info(f"Agentic loop iteration {iteration + 1}/{max_iterations}")
                    
                    # Process the current input with the agent
                    response = self.agent(current_input)
                    
                    # Extract the text content from the response
                    text_content = self._extract_text_from_response(response)
                    
                    # Check if the response contains MCP tool calls
                    if self._contains_mcp_blocks(text_content):
                        # Process the MCP tool calls and get the results
                        tool_results = self._execute_mcp_blocks(text_content)
                        
                        # If no tool calls were made, break the loop
                        if not tool_results:
                            final_response = text_content
                            break
                        
                        # Create a new input for the agent with the tool results
                        current_input = self._create_tool_results_input(tool_results)
                    else:
                        # No tool calls, this is the final response
                        final_response = text_content
                        break
                
                # If we reached the maximum iterations without a final response, use the last response
                if final_response is None:
                    final_response = text_content
            
            return {"success": True, "response": final_response}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing input: {error_msg}")

            # Handle AWS credential errors
            if "ExpiredTokenException" in error_msg:
                error_msg = (
                    "AWS credentials have expired. Please refresh your credentials or "
                    "specify a valid AWS profile using the --aws-profile option."
                )

            return {"success": False, "error": error_msg}
    
    def _activate_all_clients(self, clients):
        """Context manager to activate all MCP clients."""
        class ClientActivator:
            def __init__(self, clients_list):
                self.clients = clients_list
                
            def __enter__(self):
                # Activate all clients
                for client in self.clients:
                    client.__enter__()
                return self.clients
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                # Deactivate all clients in reverse order
                for client in reversed(self.clients):
                    client.__exit__(exc_type, exc_val, exc_tb)
        
        return ClientActivator(clients)
    
    def _extract_text_from_response(self, response):
        """Extract text content from an agent response."""
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
            except Exception as e:
                logger.error(f"Error extracting text from AgentResult: {str(e)}")
                return str(response)
        
        # If it's a string, return it directly
        if isinstance(response, str):
            return response
            
        # If we don't know how to handle it, convert it to a string
        return str(response)
    
    def _contains_mcp_blocks(self, text):
        """Check if the text contains MCP code blocks."""
        import re
        
        # Define patterns to match MCP code blocks
        patterns = [
            r"```mcp\s*([\s\S]*?)```",  # Standard mcp code block
            r"```mcp::(\w+)::(\w+)\s*([\s\S]*?)```",  # Server-tool format
            r"```\s*MCP:(\w+)\((.*?)\)\s*```",  # Function-call format
            r"```\s*mcp\s*\n\s*tool:\s*(\w+)\s*\n\s*```",  # ```mcp\ntool: ToolName\n```
            r"```\s*tool:\s*(\w+)\s*```",  # ```tool: ToolName```
        ]
        
        # Check each pattern
        for pattern in patterns:
            if re.search(pattern, text):
                return True
                
        return False
    
    def _execute_mcp_blocks(self, text):
        """Execute MCP code blocks and return the results."""
        import re
        import json
        
        # Define patterns to match MCP code blocks
        patterns = [
            (r"```mcp\s*([\s\S]*?)```", self._execute_standard_mcp_block),  # Standard mcp code block
            (r"```mcp::(\w+)::(\w+)\s*([\s\S]*?)```", self._execute_server_tool_mcp_block),  # Server-tool format
            (r"```\s*MCP:(\w+)\((.*?)\)\s*```", self._execute_function_mcp_block),  # Function-call format
            (r"```\s*mcp\s*\n\s*tool:\s*(\w+)\s*\n\s*```", self._execute_simple_mcp_block),  # ```mcp\ntool: ToolName\n```
            (r"```\s*tool:\s*(\w+)\s*```", self._execute_simple_mcp_block),  # ```tool: ToolName```
        ]
        
        # Results of all tool calls
        tool_results = []
        
        # Process each pattern
        for pattern, executor in patterns:
            # Find all matches
            matches = re.findall(pattern, text)
            
            # If no matches, try the next pattern
            if not matches:
                continue
                
            # Process each match
            for match in matches:
                result = executor(match)
                if result:
                    tool_results.append(result)
        
        return tool_results
    
    def _execute_standard_mcp_block(self, match):
        """Execute a standard MCP code block."""
        import json
        from unified_agent.mcp_models import MCPToolCall
        
        try:
            # Parse the JSON
            try:
                raw_data = json.loads(match.strip())
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON: {str(e)}")
                logger.warning(f"JSON content: '{match.strip()}'")
                return None
            
            # Handle different key formats
            # Map "name" or "action" to "tool" if needed
            if "name" in raw_data and "tool" not in raw_data:
                raw_data["tool"] = raw_data["name"]
            elif "action" in raw_data and "tool" not in raw_data:
                raw_data["tool"] = raw_data["action"]
            
            # If server name is not provided, try to find it
            if "server" not in raw_data and "tool" in raw_data:
                server_name = self._find_server_for_tool(raw_data["tool"])
                if server_name:
                    raw_data["server"] = server_name
                else:
                    logger.error(f"Could not determine server for tool: {raw_data['tool']}")
                    return None
            
            # Map "args" to "arguments" if needed
            if "args" in raw_data and "arguments" not in raw_data:
                raw_data["arguments"] = raw_data["args"]
            
            # Validate with Pydantic model
            try:
                tool_call = MCPToolCall(**raw_data)
            except Exception as e:
                logger.warning(f"Invalid MCP tool call: {str(e)}")
                return None
            
            # Get the client for the server
            client = self.mcp_connector.get_client(tool_call.server)
            if not client:
                logger.warning(f"No client found for server: {tool_call.server}")
                return None
            
            # Call the tool
            logger.info(f"Calling MCP tool: {tool_call.tool} on server: {tool_call.server} with args: {tool_call.arguments}")
            
            # Generate a unique tool use ID
            import uuid
            tool_use_id = str(uuid.uuid4())
            
            # Call the tool
            result = client.call_tool_sync(
                tool_use_id=tool_use_id,
                name=tool_call.tool,
                arguments=tool_call.arguments
            )
            
            logger.info(f"MCP tool call successful: {tool_call.tool}")
            
            # Return the tool call and result
            return {
                "tool": tool_call.tool,
                "server": tool_call.server,
                "arguments": tool_call.arguments,
                "result": result
            }
                
        except Exception as e:
            logger.error(f"Error executing MCP tool call: {str(e)}")
            return None
    
    def _execute_server_tool_mcp_block(self, match):
        """Execute a server-tool format MCP code block."""
        import json
        
        try:
            server_name, tool_name, args_str = match
            
            # Parse the arguments JSON if present
            args = {}
            if args_str.strip():
                try:
                    args = json.loads(args_str.strip())
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse arguments JSON: {str(e)}")
                    logger.warning(f"Arguments content: '{args_str.strip()}'")
            
            # Get the client for the server
            client = self.mcp_connector.get_client(server_name)
            if not client:
                logger.warning(f"No client found for server: {server_name}")
                return None
                
            # Call the tool
            logger.info(f"Calling MCP tool: {tool_name} on server: {server_name} with args: {args}")
            
            # Generate a unique tool use ID
            import uuid
            tool_use_id = str(uuid.uuid4())
            
            # Call the tool
            result = client.call_tool_sync(
                tool_use_id=tool_use_id,
                name=tool_name,
                arguments=args
            )
            
            logger.info(f"MCP tool call successful: {tool_name}")
            
            # Return the tool call and result
            return {
                "tool": tool_name,
                "server": server_name,
                "arguments": args,
                "result": result
            }
                
        except Exception as e:
            logger.error(f"Error executing MCP tool call: {str(e)}")
            return None
    
    def _execute_function_mcp_block(self, match):
        """Execute a function-call format MCP code block."""
        import ast
        import json
        
        try:
            tool_name, args_str = match
            
            # Parse the arguments
            # Convert the args string to a dictionary
            args = {}
            if args_str.strip():
                # Add curly braces to make it a dictionary literal
                dict_str = "{" + args_str + "}"
                # Replace = with : to make it valid JSON
                dict_str = dict_str.replace("=", ":")
                # Use ast.literal_eval to safely evaluate the string
                try:
                    args = ast.literal_eval(dict_str)
                except Exception as e:
                    logger.warning(f"Failed to parse arguments with ast.literal_eval: {str(e)}")
                    # Try with json.loads as a fallback
                    try:
                        args = json.loads(dict_str)
                    except Exception as e2:
                        logger.warning(f"Failed to parse arguments with json.loads: {str(e2)}")
                        # Use empty args as a last resort
                        args = {}
            
            # Find the server that provides this tool
            server_name = self._find_server_for_tool(tool_name)
            if not server_name:
                logger.error(f"Could not find server for tool: {tool_name}")
                return None
            
            # Get the client for the server
            client = self.mcp_connector.get_client(server_name)
            if not client:
                logger.warning(f"No client found for server: {server_name}")
                return None
                
            # Call the tool
            logger.info(f"Calling MCP tool: {tool_name} on server: {server_name} with args: {args}")
            
            # Generate a unique tool use ID
            import uuid
            tool_use_id = str(uuid.uuid4())
            
            # Call the tool
            result = client.call_tool_sync(
                tool_use_id=tool_use_id,
                name=tool_name,
                arguments=args
            )
            
            logger.info(f"MCP tool call successful: {tool_name}")
            
            # Return the tool call and result
            return {
                "tool": tool_name,
                "server": server_name,
                "arguments": args,
                "result": result
            }
                
        except Exception as e:
            logger.error(f"Error executing MCP tool call: {str(e)}")
            return None
    
    def _execute_simple_mcp_block(self, match):
        """Execute a simple MCP code block."""
        try:
            tool_name = match
            
            # Find the server that provides this tool
            server_name = self._find_server_for_tool(tool_name)
            if not server_name:
                logger.error(f"Could not find server for tool: {tool_name}")
                return None
            
            # Get the client for the server
            client = self.mcp_connector.get_client(server_name)
            if not client:
                logger.warning(f"No client found for server: {server_name}")
                return None
                
            # Call the tool with empty arguments
            logger.info(f"Calling MCP tool: {tool_name} on server: {server_name} with empty args")
            
            # Generate a unique tool use ID
            import uuid
            tool_use_id = str(uuid.uuid4())
            
            # Call the tool
            result = client.call_tool_sync(
                tool_use_id=tool_use_id,
                name=tool_name,
                arguments={}
            )
            
            logger.info(f"MCP tool call successful: {tool_name}")
            
            # Return the tool call and result
            return {
                "tool": tool_name,
                "server": server_name,
                "arguments": {},
                "result": result
            }
                
        except Exception as e:
            logger.error(f"Error executing MCP tool call: {str(e)}")
            return None
    
    def _create_tool_results_input(self, tool_results):
        """Create a new input for the agent with the tool results."""
        import json
        
        # Format the tool results as a string
        tool_results_str = "I've executed the tools you requested. Here are the results:\n\n"
        
        for result in tool_results:
            tool_name = result["tool"]
            result_json = json.dumps(result["result"], indent=2)
            tool_results_str += f"Tool: {tool_name}\n```json\n{result_json}\n```\n\n"
        
        tool_results_str += "Please analyze these results and provide a response."
        
        return tool_results_str
    
    def _process_mcp_blocks(self, response):
        """Process MCP code blocks in the response and execute MCP tool calls."""
        import re
        import json
        
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
                
                # Process the text content
                processed_text = self._process_mcp_text(text_content)
                
                # Return the processed text
                return processed_text
            except Exception as e:
                logger.error(f"Error processing AgentResult: {str(e)}")
                return response
        
        # If it's a string, process it directly
        if isinstance(response, str):
            return self._process_mcp_text(response)
            
        # If we don't know how to handle it, return it as is
        return response
        
    def _process_mcp_text(self, text: str) -> str:
        """Process MCP code blocks in the text and execute MCP tool calls."""
        import re
        import json
        
        # First, try to process JSON format MCP blocks
        text = self._process_json_mcp_blocks(text)
        
        # Then, try to process function-call format MCP blocks
        text = self._process_function_mcp_blocks(text)
        
        # Finally, try to process simple tool name format blocks
        text = self._process_simple_mcp_blocks(text)
        
        return text
        
    def _process_function_mcp_blocks(self, text: str) -> str:
        """Process function-call format MCP blocks."""
        import re
        import json
        import ast
        
        # Define a pattern to match MCP function calls
        # Format: MCP:ToolName(arg1="value1", arg2="value2")
        pattern = r"```\s*MCP:(\w+)\((.*?)\)\s*```"
        
        # Find all matches
        matches = re.findall(pattern, text)
        
        # If no matches, return the original text
        if not matches:
            return text
            
        # Process each match
        for tool_name, args_str in matches:
            try:
                # Parse the arguments
                # Convert the args string to a dictionary
                args = {}
                if args_str.strip():
                    # Add curly braces to make it a dictionary literal
                    dict_str = "{" + args_str + "}"
                    # Replace = with : to make it valid JSON
                    dict_str = dict_str.replace("=", ":")
                    # Use ast.literal_eval to safely evaluate the string
                    try:
                        args = ast.literal_eval(dict_str)
                    except Exception as e:
                        logger.warning(f"Failed to parse arguments with ast.literal_eval: {str(e)}")
                        # Try with json.loads as a fallback
                        try:
                            args = json.loads(dict_str)
                        except Exception as e2:
                            logger.warning(f"Failed to parse arguments with json.loads: {str(e2)}")
                            # Use empty args as a last resort
                            args = {}
                
                # Find the server that provides this tool
                server_name = self._find_server_for_tool(tool_name)
                if not server_name:
                    logger.error(f"Could not find server for tool: {tool_name}")
                    continue
                
                # Get the client for the server
                client = self.mcp_connector.get_client(server_name)
                if not client:
                    logger.warning(f"No client found for server: {server_name}")
                    continue
                    
                # Call the tool
                logger.info(f"Calling MCP tool: {tool_name} on server: {server_name} with args: {args}")
                
                # Use a context manager to ensure the client is active
                with client:
                    # Generate a unique tool use ID
                    import uuid
                    tool_use_id = str(uuid.uuid4())
                    
                    # Call the tool
                    result = client.call_tool_sync(
                        tool_use_id=tool_use_id,
                        name=tool_name,
                        arguments=args
                    )
                    
                    # Format the result
                    result_str = json.dumps(result, indent=2)
                    
                    # Replace the code block with the result
                    code_block = f"```MCP:{tool_name}({args_str})```"
                    
                    # Create a more conversational response based on the tool and result
                    conversational_response = self._create_conversational_response(tool_name, result)
                    
                    result_block = f"```json\n{result_str}\n```\n\n{conversational_response}"
                    text = text.replace(code_block, result_block)
                    
                    logger.info(f"MCP tool call successful: {tool_name}")
                    
            except Exception as e:
                logger.error(f"Error processing MCP tool call: {str(e)}")
                # Replace the code block with an error message
                code_block = f"```MCP:{tool_name}({args_str})```"
                error_block = f"```\nError calling MCP tool: {str(e)}\n```\n\nI encountered an error when trying to use the {tool_name} tool. Let me try a different approach."
                text = text.replace(code_block, error_block)
                
        return text
    
    def _process_json_mcp_blocks(self, text: str) -> str:
        """Process JSON format MCP code blocks."""
        import re
        import json
        
        # Define patterns to match code blocks with the "mcp" language tag
        patterns = [
            # Standard mcp code block
            r"```mcp\s*([\s\S]*?)```",
            
            # Format: ```mcp::server::tool {...}```
            r"```mcp::(\w+)::(\w+)\s*([\s\S]*?)```"
        ]
        
        # Process standard mcp blocks
        text = self._process_standard_mcp_blocks(text)
        
        # Process server-tool format blocks
        text = self._process_server_tool_mcp_blocks(text)
        
        return text
    
    def _process_standard_mcp_blocks(self, text: str) -> str:
        """Process standard JSON format MCP code blocks."""
        import re
        import json
        from unified_agent.mcp_models import MCPToolCall, MCPToolResult
        
        # Define a pattern to match code blocks with the "mcp" language tag
        pattern = r"```mcp\s*([\s\S]*?)```"
        
        # Find all matches
        matches = re.findall(pattern, text)
        
        # If no matches, return the original text
        if not matches:
            return text
        
        # Process each match
        for match in matches:
            try:
                # Parse the JSON
                try:
                    raw_data = json.loads(match.strip())
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON: {str(e)}")
                    logger.warning(f"JSON content: '{match.strip()}'")
                    continue
                
                # Handle different key formats
                # Map "name" or "action" to "tool" if needed
                if "name" in raw_data and "tool" not in raw_data:
                    raw_data["tool"] = raw_data["name"]
                elif "action" in raw_data and "tool" not in raw_data:
                    raw_data["tool"] = raw_data["action"]
                
                # If server name is not provided, try to find it
                if "server" not in raw_data and "tool" in raw_data:
                    server_name = self._find_server_for_tool(raw_data["tool"])
                    if server_name:
                        raw_data["server"] = server_name
                    else:
                        logger.error(f"Could not determine server for tool: {raw_data['tool']}")
                        continue
                
                # Map "args" to "arguments" if needed
                if "args" in raw_data and "arguments" not in raw_data:
                    raw_data["arguments"] = raw_data["args"]
                
                # Validate with Pydantic model
                try:
                    tool_call = MCPToolCall(**raw_data)
                except Exception as e:
                    logger.warning(f"Invalid MCP tool call: {str(e)}")
                    continue
                
                # Get the client for the server
                client = self.mcp_connector.get_client(tool_call.server)
                if not client:
                    logger.warning(f"No client found for server: {tool_call.server}")
                    continue
                
                # Call the tool
                logger.info(f"Calling MCP tool: {tool_call.tool} on server: {tool_call.server} with args: {tool_call.arguments}")
                
                # Use a context manager to ensure the client is active
                with client:
                    # Generate a unique tool use ID
                    import uuid
                    tool_use_id = str(uuid.uuid4())
                    
                    # Call the tool
                    result = client.call_tool_sync(
                        tool_use_id=tool_use_id,
                        name=tool_call.tool,
                        arguments=tool_call.arguments
                    )
                    
                    # Validate result with Pydantic model
                    try:
                        # Convert result to MCPToolResult model
                        tool_result = MCPToolResult(**result)
                    except Exception as e:
                        logger.warning(f"Invalid MCP tool result: {str(e)}")
                        # Continue with the raw result if validation fails
                        tool_result = None
                    
                    # Format the result
                    result_str = json.dumps(result, indent=2)
                    
                    # Replace the code block with the result
                    code_block = f"```mcp\n{match.strip()}\n```"
                    
                    # Create a more conversational response based on the tool and result
                    conversational_response = self._create_conversational_response(tool_call.tool, result)
                    
                    result_block = f"```json\n{result_str}\n```\n\n{conversational_response}"
                    text = text.replace(code_block, result_block)
                    
                    logger.info(f"MCP tool call successful: {tool_call.tool}")
                    
            except Exception as e:
                logger.error(f"Error processing MCP tool call: {str(e)}")
                # Replace the code block with an error message
                code_block = f"```mcp\n{match.strip()}\n```"
                error_block = f"```\nError calling MCP tool: {str(e)}\n```\n\nI encountered an error when trying to use the MCP tool. Let me try a different approach."
                text = text.replace(code_block, error_block)
                
        return text
    
    def _process_server_tool_mcp_blocks(self, text: str) -> str:
        """Process MCP code blocks in the format ```mcp::server::tool {...}```."""
        import re
        import json
        
        # Define a pattern to match code blocks with the server::tool format
        pattern = r"```mcp::(\w+)::(\w+)\s*([\s\S]*?)```"
        
        # Find all matches
        matches = re.findall(pattern, text)
        
        # If no matches, return the original text
        if not matches:
            return text
            
        # Process each match
        for server_name, tool_name, args_str in matches:
            try:
                # Parse the arguments JSON if present
                args = {}
                if args_str.strip():
                    try:
                        args = json.loads(args_str.strip())
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse arguments JSON: {str(e)}")
                        logger.warning(f"Arguments content: '{args_str.strip()}'")
                
                # Get the client for the server
                client = self.mcp_connector.get_client(server_name)
                if not client:
                    logger.warning(f"No client found for server: {server_name}")
                    continue
                    
                # Call the tool
                logger.info(f"Calling MCP tool: {tool_name} on server: {server_name} with args: {args}")
                
                # Use a context manager to ensure the client is active
                with client:
                    # Generate a unique tool use ID
                    import uuid
                    tool_use_id = str(uuid.uuid4())
                    
                    # Call the tool
                    result = client.call_tool_sync(
                        tool_use_id=tool_use_id,
                        name=tool_name,
                        arguments=args
                    )
                    
                    # Format the result
                    result_str = json.dumps(result, indent=2)
                    
                    # Replace the code block with the result
                    code_block = f"```mcp::{server_name}::{tool_name}\n{args_str.strip()}\n```"
                    
                    # Create a more conversational response based on the tool and result
                    conversational_response = self._create_conversational_response(tool_name, result)
                    
                    result_block = f"```json\n{result_str}\n```\n\n{conversational_response}"
                    text = text.replace(code_block, result_block)
                    
                    logger.info(f"MCP tool call successful: {tool_name}")
                    
            except Exception as e:
                logger.error(f"Error processing MCP tool call: {str(e)}")
                # Replace the code block with an error message
                code_block = f"```mcp::{server_name}::{tool_name}\n{args_str.strip()}\n```"
                error_block = f"```\nError calling MCP tool: {str(e)}\n```\n\nI encountered an error when trying to use the {tool_name} tool. Let me try a different approach."
                text = text.replace(code_block, error_block)
                
        return text
    
    def _process_simple_mcp_blocks(self, text: str) -> str:
        """Process simple MCP code blocks with just the tool name."""
        import re
        import json
        
        # Define patterns to match simple tool calls
        patterns = [
            r"```\s*mcp\s*\n\s*tool:\s*(\w+)\s*\n\s*```",  # ```mcp\ntool: ToolName\n```
            r"```\s*tool:\s*(\w+)\s*```",                  # ```tool: ToolName```
            r"```\s*(\w+)\s*```"                           # ```ToolName```
        ]
        
        for pattern in patterns:
            # Find all matches
            matches = re.findall(pattern, text)
            
            # If no matches, try the next pattern
            if not matches:
                continue
                
            # Process each match
            for tool_name in matches:
                try:
                    # Find the server that provides this tool
                    server_name = self._find_server_for_tool(tool_name)
                    if not server_name:
                        logger.error(f"Could not find server for tool: {tool_name}")
                        continue
                    # Find the server that provides this tool
                    server_name = self._find_server_for_tool(tool_name)
                    if not server_name:
                        logger.error(f"Could not find server for tool: {tool_name}")
                        continue
                    
                    # Get the client for the server
                    client = self.mcp_connector.get_client(server_name)
                    if not client:
                        logger.warning(f"No client found for server: {server_name}")
                        continue
                        
                    # Call the tool with empty arguments
                    logger.info(f"Calling MCP tool: {tool_name} on server: {server_name} with empty args")
                    
                    # Use a context manager to ensure the client is active
                    with client:
                        # Generate a unique tool use ID
                        import uuid
                        tool_use_id = str(uuid.uuid4())
                        
                        # Call the tool
                        result = client.call_tool_sync(
                            tool_use_id=tool_use_id,
                            name=tool_name,
                            arguments={}
                        )
                        
                        # Format the result
                        result_str = json.dumps(result, indent=2)
                        
                        # Replace the code block with the result
                        if "tool:" in pattern:
                            code_block = f"```mcp\ntool: {tool_name}\n```" if "mcp" in pattern else f"```tool: {tool_name}```"
                        else:
                            code_block = f"```{tool_name}```"
                        
                        # Create a more conversational response based on the tool and result
                        conversational_response = self._create_conversational_response(tool_name, result)
                        
                        result_block = f"```json\n{result_str}\n```\n\n{conversational_response}"
                        text = text.replace(code_block, result_block)
                        
                        logger.info(f"MCP tool call successful: {tool_name}")
                        
                except Exception as e:
                    logger.error(f"Error processing simple MCP tool call: {str(e)}")
                    # Replace the code block with an error message
                    if "tool:" in pattern:
                        code_block = f"```mcp\ntool: {tool_name}\n```" if "mcp" in pattern else f"```tool: {tool_name}```"
                    else:
                        code_block = f"```{tool_name}```"
                    error_block = f"```\nError calling MCP tool: {str(e)}\n```\n\nI encountered an error when trying to use the {tool_name} tool. Let me try a different approach."
                    text = text.replace(code_block, error_block)
        
        return text
    
    def _find_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Find the server that provides a specific tool."""
        # Get all tools from all servers
        all_tools = self.mcp_connector.get_all_tools()
        
        # Find the tool with the matching name
        for tool in all_tools:
            if tool.tool_name == tool_name:
                return tool.server_name
                
        return None
    
    def _create_conversational_response(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Create a conversational response based on the tool and result."""
        # Check if the result was successful
        if result.get("status") == "error":
            return f"I encountered an error when using the {tool_name} tool: {result.get('error', 'Unknown error')}"
        
        # No special handling for specific tools - let the agent interpret the results
        # Just return an empty string so the raw JSON result is shown to the agent
        return ""
    
    # Remove the _interpret_live_context method as we're letting the agent interpret the result
    
    
    def reload_agent(self) -> bool:
        """Reload the agent with updated configuration."""
        try:
            # Simply recreate the agent using _create_agent
            # which will handle the AWS profile and credentials
            self.agent = self._create_agent()
            return True
        except Exception as e:
            logger.error(f"Failed to reload agent: {str(e)}")
            return False
