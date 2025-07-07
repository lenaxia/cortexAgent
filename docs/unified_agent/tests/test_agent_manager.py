"""Tests for the agent_manager module."""
import pytest
import re
from unittest.mock import patch, MagicMock, call

from unified_agent.models import AgentConfig, MCPServerConfig, MemoryConfig, MCPTool
from unified_agent.agent_manager import AgentManager
from unified_agent.mcp_models import MCPToolCall


class TestAgentManager:
    """Tests for the AgentManager class."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        config = AgentConfig(
            name="Test Agent",
            system_prompt="You are a test agent",
            mcp_servers=[
                MCPServerConfig(
                    name="test-server",
                    url="https://example.com/mcp"
                )
            ],
            memory=MemoryConfig(user_id="test-user"),
            http_enabled=True
        )
        
        mcp_connector = MagicMock()
        mcp_connector.get_all_tools.return_value = [
            MCPTool(
                server_name="test-server",
                tool_name="test-tool",
                description="A test tool"
            )
        ]
        mcp_connector.get_connected_servers.return_value = ["test-server"]
        
        # Mock client
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.call_tool_sync = MagicMock(return_value={
            "status": "success",
            "tool_use_id": "test-id",
            "content": [{"text": "Test result"}]
        })
        
        mcp_connector.get_client.return_value = mock_client
        
        memory_handler = MagicMock()
        
        return {
            "config": config,
            "mcp_connector": mcp_connector,
            "memory_handler": memory_handler,
            "mock_client": mock_client
        }
    
    @pytest.fixture
    def agent_result_object(self):
        """Create a mock AgentResult object."""
        class MockContent:
            def __init__(self, text):
                self.text = text
                
        class MockMessage:
            def __init__(self, content):
                self.content = content
                
        class MockAgentResult:
            def __init__(self, message):
                self.message = message
                
        return MockAgentResult(MockMessage([MockContent("Test response")]))
    
    @patch("unified_agent.agent_manager.Agent")
    def test_init_creates_agent(self, mock_agent_class, mock_dependencies):
        """Test that init creates an agent."""
        # Initialize agent manager
        AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Check that Agent was created
        mock_agent_class.assert_called_once()
    
    @patch("unified_agent.agent_manager.Agent")
    def test_build_system_prompt(self, mock_agent_class, mock_dependencies):
        """Test building the system prompt."""
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Build system prompt
        prompt = manager._build_system_prompt()
        
        # Check that prompt contains expected information
        assert "You are a test agent" in prompt
        assert "Available MCP tools" in prompt
        assert "test-tool" in prompt
        assert "Memory capabilities" in prompt
        assert "HTTP capabilities" in prompt
    
    @patch("unified_agent.agent_manager.Agent")
    def test_process_input_success(self, mock_agent_class, mock_dependencies):
        """Test processing input successfully."""
        # Set up mock agent
        mock_agent = MagicMock()
        mock_agent.return_value = "Agent response"
        mock_agent_class.return_value = mock_agent
        
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Process input
        result = manager.process_input("Hello, agent")
        
        # Check that agent was called
        mock_agent.assert_called_once_with("Hello, agent")
        
        # Check that result is correct
        assert result["success"] is True
        assert result["response"] == "Agent response"
    
    @patch("unified_agent.agent_manager.Agent")
    def test_process_input_exception(self, mock_agent_class, mock_dependencies):
        """Test processing input when an exception is raised."""
        # Set up mock agent to raise an exception
        mock_agent = MagicMock()
        mock_agent.side_effect = Exception("Test error")
        mock_agent_class.return_value = mock_agent
        
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Process input
        result = manager.process_input("Hello, agent")
        
        # Check that result indicates failure
        assert result["success"] is False
        assert "Test error" in result["error"]
    
    @patch("unified_agent.agent_manager.Agent")
    def test_reload_agent_success(self, mock_agent_class, mock_dependencies):
        """Test reloading the agent successfully."""
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Reset mock to clear call count
        mock_agent_class.reset_mock()
        
        # Reload agent
        result = manager.reload_agent()
        
        # Check that Agent was created again
        mock_agent_class.assert_called_once()
        
        # Check that result is correct
        assert result is True
    
    @patch("unified_agent.agent_manager.Agent")
    def test_reload_agent_exception(self, mock_agent_class, mock_dependencies):
        """Test reloading the agent when an exception is raised."""
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Set up mock to raise an exception
        mock_agent_class.side_effect = Exception("Test error")
        
        # Reload agent
        result = manager.reload_agent()
        
        # Check that result is correct
        assert result is False
    
    @patch("unified_agent.agent_manager.Agent")
    def test_activate_all_clients(self, mock_agent_class, mock_dependencies):
        """Test activating all clients."""
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Create mock clients
        client1 = MagicMock()
        client1.__enter__ = MagicMock(return_value=client1)
        client1.__exit__ = MagicMock(return_value=None)
        
        client2 = MagicMock()
        client2.__enter__ = MagicMock(return_value=client2)
        client2.__exit__ = MagicMock(return_value=None)
        
        clients = [client1, client2]
        
        # Use the context manager
        with manager._activate_all_clients(clients) as active_clients:
            # Check that clients were activated
            client1.__enter__.assert_called_once()
            client2.__enter__.assert_called_once()
            
            # Check that active_clients is correct
            assert active_clients == clients
        
        # Check that clients were deactivated in reverse order
        client2.__exit__.assert_called_once()
        client1.__exit__.assert_called_once()
    
    @patch("unified_agent.agent_manager.Agent")
    def test_extract_text_from_response_agent_result(self, mock_agent_class, mock_dependencies, agent_result_object):
        """Test extracting text from an AgentResult object."""
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Extract text
        text = manager._extract_text_from_response(agent_result_object)
        
        # Check that text is correct
        assert text == "Test response"
    
    @patch("unified_agent.agent_manager.Agent")
    def test_extract_text_from_response_string(self, mock_agent_class, mock_dependencies):
        """Test extracting text from a string."""
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Extract text
        text = manager._extract_text_from_response("Test response")
        
        # Check that text is correct
        assert text == "Test response"
    
    @patch("unified_agent.agent_manager.Agent")
    def test_contains_mcp_blocks(self, mock_agent_class, mock_dependencies):
        """Test checking if text contains MCP blocks."""
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Mock the re.search method to return True for MCP blocks and False otherwise
        with patch("re.search") as mock_search:
            # Set up mock to return True for MCP blocks
            mock_search.return_value = True
            
            # Test with standard MCP block
            text = "Here's a tool call: ```mcp\n{\"tool\": \"test-tool\", \"server\": \"test-server\"}\n```"
            assert manager._contains_mcp_blocks(text) is True
            
            # Test with server-tool format
            text = "Here's a tool call: ```mcp::test-server::test-tool\n{\"arg\": \"value\"}\n```"
            assert manager._contains_mcp_blocks(text) is True
            
            # Test with function-call format
            text = "Here's a tool call: ```MCP:test-tool(arg=\"value\")\n```"
            assert manager._contains_mcp_blocks(text) is True
            
            # Test with simple format
            text = "Here's a tool call: ```mcp\ntool: test-tool\n```"
            assert manager._contains_mcp_blocks(text) is True
            
            # Set up mock to return False for non-MCP blocks
            mock_search.return_value = False
            
            # Test with no MCP blocks
            text = "Here's some text with no MCP blocks."
            assert manager._contains_mcp_blocks(text) is False
    
    @patch("unified_agent.agent_manager.Agent")
    def test_execute_standard_mcp_block(self, mock_agent_class, mock_dependencies):
        """Test executing a standard MCP block."""
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Set up mock client
        mock_client = mock_dependencies["mock_client"]
        mock_client.call_tool_sync.return_value = {
            "status": "success",
            "tool_use_id": "test-id",
            "content": [{"text": "Test result"}]
        }
        
        # Execute MCP block
        match = '{"tool": "test-tool", "server": "test-server", "arguments": {"arg": "value"}}'
        result = manager._execute_standard_mcp_block(match)
        
        # Check that client was called correctly
        mock_client.call_tool_sync.assert_called_once()
        args = mock_client.call_tool_sync.call_args[1]
        assert args["name"] == "test-tool"
        assert args["arguments"] == {"arg": "value"}
        
        # Check that result is correct
        assert result["tool"] == "test-tool"
        assert result["server"] == "test-server"
        assert result["arguments"] == {"arg": "value"}
        assert result["result"]["status"] == "success"
        assert result["result"]["tool_use_id"] == "test-id"
        assert result["result"]["content"][0]["text"] == "Test result"
    
    @patch("unified_agent.agent_manager.Agent")
    def test_create_tool_results_input(self, mock_agent_class, mock_dependencies):
        """Test creating tool results input."""
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Create tool results
        tool_results = [
            {
                "tool": "test-tool-1",
                "server": "test-server",
                "arguments": {"arg": "value"},
                "result": {
                    "status": "success",
                    "tool_use_id": "test-id-1",
                    "content": [{"text": "Test result 1"}]
                }
            },
            {
                "tool": "test-tool-2",
                "server": "test-server",
                "arguments": {"arg": "value"},
                "result": {
                    "status": "success",
                    "tool_use_id": "test-id-2",
                    "content": [{"text": "Test result 2"}]
                }
            }
        ]
        
        # Create input
        input_text = manager._create_tool_results_input(tool_results)
        
        # Check that input contains expected information
        assert "I've executed the tools you requested" in input_text
        assert "Tool: test-tool-1" in input_text
        assert "Tool: test-tool-2" in input_text
        assert "Test result 1" in input_text
        assert "Test result 2" in input_text
        assert "Please analyze these results and provide a response" in input_text
    
    @patch("unified_agent.agent_manager.Agent")
    def test_execute_mcp_blocks(self, mock_agent_class, mock_dependencies):
        """Test executing MCP blocks."""
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Mock the executor methods
        manager._execute_standard_mcp_block = MagicMock(return_value={
            "tool": "test-tool",
            "server": "test-server",
            "arguments": {"arg": "value"},
            "result": {
                "status": "success",
                "tool_use_id": "test-id",
                "content": [{"text": "Test result"}]
            }
        })
        manager._execute_server_tool_mcp_block = MagicMock(return_value=None)
        manager._execute_function_mcp_block = MagicMock(return_value=None)
        manager._execute_simple_mcp_block = MagicMock(return_value=None)
        
        # Mock re.findall to return matches
        with patch("re.findall") as mock_findall:
            mock_findall.side_effect = [
                [('{"tool": "test-tool", "server": "test-server", "arguments": {"arg": "value"}}')],  # Standard MCP block
                [],  # Server-tool format (no matches)
                [],  # Function-call format (no matches)
                [],  # Simple format (no matches)
                []   # Simple format (no matches)
            ]
            
            # Execute MCP blocks
            text = "Here's a tool call: ```mcp\n{\"tool\": \"test-tool\", \"server\": \"test-server\", \"arguments\": {\"arg\": \"value\"}}\n```"
            results = manager._execute_mcp_blocks(text)
            
            # Check that executor methods were called correctly
            manager._execute_standard_mcp_block.assert_called_once_with(
                '{"tool": "test-tool", "server": "test-server", "arguments": {"arg": "value"}}'
            )
            manager._execute_server_tool_mcp_block.assert_not_called()
            manager._execute_function_mcp_block.assert_not_called()
            manager._execute_simple_mcp_block.assert_not_called()
            
            # Check that results are correct
            assert len(results) == 1
            assert results[0]["tool"] == "test-tool"
            assert results[0]["server"] == "test-server"
            assert results[0]["arguments"] == {"arg": "value"}
            assert results[0]["result"]["status"] == "success"
            assert results[0]["result"]["tool_use_id"] == "test-id"
            assert results[0]["result"]["content"][0]["text"] == "Test result"
    
    @patch("unified_agent.agent_manager.Agent")
    def test_agentic_loop_no_tool_calls(self, mock_agent_class, mock_dependencies):
        """Test the agentic loop with no tool calls."""
        # Set up mock agent
        mock_agent = MagicMock()
        mock_agent.return_value = "Agent response"
        mock_agent_class.return_value = mock_agent
        
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Mock methods
        manager._extract_text_from_response = MagicMock(return_value="Agent response")
        manager._contains_mcp_blocks = MagicMock(return_value=False)
        
        # Process input
        result = manager.process_input("Hello, agent")
        
        # Check that agent was called
        mock_agent.assert_called_once_with("Hello, agent")
        
        # Check that methods were called correctly
        manager._extract_text_from_response.assert_called_once_with("Agent response")
        manager._contains_mcp_blocks.assert_called_once_with("Agent response")
        
        # Check that result is correct
        assert result["success"] is True
        assert result["response"] == "Agent response"
    
    @patch("unified_agent.agent_manager.Agent")
    def test_agentic_loop_with_tool_calls(self, mock_agent_class, mock_dependencies):
        """Test the agentic loop with tool calls."""
        # Set up mock agent
        mock_agent = MagicMock()
        mock_agent.side_effect = ["Agent response with tool call", "Final agent response"]
        mock_agent_class.return_value = mock_agent
        
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Mock methods
        manager._extract_text_from_response = MagicMock(side_effect=["Agent response with tool call", "Final agent response"])
        manager._contains_mcp_blocks = MagicMock(side_effect=[True, False])
        manager._execute_mcp_blocks = MagicMock(return_value=[{
            "tool": "test-tool",
            "server": "test-server",
            "arguments": {"arg": "value"},
            "result": {
                "status": "success",
                "tool_use_id": "test-id",
                "content": [{"text": "Test result"}]
            }
        }])
        manager._create_tool_results_input = MagicMock(return_value="Tool results input")
        
        # Process input
        result = manager.process_input("Hello, agent")
        
        # Check that agent was called correctly
        assert mock_agent.call_count == 2
        mock_agent.assert_has_calls([
            call("Hello, agent"),
            call("Tool results input")
        ])
        
        # Check that methods were called correctly
        assert manager._extract_text_from_response.call_count == 2
        assert manager._contains_mcp_blocks.call_count == 2
        manager._execute_mcp_blocks.assert_called_once_with("Agent response with tool call")
        manager._create_tool_results_input.assert_called_once()
        
        # Check that result is correct
        assert result["success"] is True
        assert result["response"] == "Final agent response"
    
    @patch("unified_agent.agent_manager.Agent")
    def test_agentic_loop_max_iterations(self, mock_agent_class, mock_dependencies):
        """Test the agentic loop with maximum iterations."""
        # Set up mock agent
        mock_agent = MagicMock()
        mock_agent.return_value = "Agent response with tool call"
        mock_agent_class.return_value = mock_agent
        
        # Initialize agent manager
        manager = AgentManager(
            mock_dependencies["config"],
            mock_dependencies["mcp_connector"],
            mock_dependencies["memory_handler"]
        )
        
        # Mock methods
        manager._extract_text_from_response = MagicMock(return_value="Agent response with tool call")
        manager._contains_mcp_blocks = MagicMock(return_value=True)
        manager._execute_mcp_blocks = MagicMock(return_value=[{
            "tool": "test-tool",
            "server": "test-server",
            "arguments": {"arg": "value"},
            "result": {
                "status": "success",
                "tool_use_id": "test-id",
                "content": [{"text": "Test result"}]
            }
        }])
        manager._create_tool_results_input = MagicMock(return_value="Tool results input")
        
        # Process input
        result = manager.process_input("Hello, agent")
        
        # Check that agent was called the maximum number of times
        assert mock_agent.call_count == 5
        
        # Check that methods were called correctly
        assert manager._extract_text_from_response.call_count == 5
        assert manager._contains_mcp_blocks.call_count == 5
        assert manager._execute_mcp_blocks.call_count == 5
        assert manager._create_tool_results_input.call_count == 5
        
        # Check that result is correct
        assert result["success"] is True
        assert result["response"] == "Agent response with tool call"
