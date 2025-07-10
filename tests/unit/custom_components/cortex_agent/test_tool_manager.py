"""Tests for the CortexAgent tool_manager module."""
from unittest.mock import MagicMock, patch, AsyncMock
import json

import pytest

from custom_components.cortex_agent.tool_manager import (
    ToolManager,
    ToolExecutionResult,
)
from custom_components.cortex_agent.tool_registry import (
    ToolRegistry,
    Tool,
    ToolParameter,
    ToolParameterType,
)
from custom_components.cortex_agent.exceptions import ToolManagerError, ToolRegistryError


@pytest.fixture
def mock_hass():
    """Fixture to provide a mock hass instance."""
    return MagicMock()


@pytest.fixture
def mock_tool_registry():
    """Fixture to provide a mock tool registry."""
    registry = MagicMock(spec=ToolRegistry)
    registry.tools = {}
    return registry


def test_tool_execution_result_init():
    """Test the initialization of a ToolExecutionResult."""
    # Create a tool execution result
    result = ToolExecutionResult(
        tool_name="test_tool",
        success=True,
        result={"key": "value"},
        error=None,
    )
    
    # Check the result properties
    assert result.tool_name == "test_tool"
    assert result.success is True
    assert result.result == {"key": "value"}
    assert result.error is None


def test_tool_execution_result_to_dict():
    """Test the to_dict method of ToolExecutionResult."""
    # Create a tool execution result
    result = ToolExecutionResult(
        tool_name="test_tool",
        success=True,
        result={"key": "value"},
        error=None,
    )
    
    # Convert to dict
    result_dict = result.to_dict()
    
    # Check the dict
    assert result_dict["tool_name"] == "test_tool"
    assert result_dict["success"] is True
    assert result_dict["result"] == {"key": "value"}
    assert "error" not in result_dict


def test_tool_execution_result_to_dict_with_error():
    """Test the to_dict method of ToolExecutionResult with an error."""
    # Create a tool execution result with an error
    result = ToolExecutionResult(
        tool_name="test_tool",
        success=False,
        result=None,
        error="Test error",
    )
    
    # Convert to dict
    result_dict = result.to_dict()
    
    # Check the dict
    assert result_dict["tool_name"] == "test_tool"
    assert result_dict["success"] is False
    assert "result" not in result_dict
    assert result_dict["error"] == "Test error"


def test_tool_manager_init(mock_hass, mock_tool_registry):
    """Test the initialization of a ToolManager."""
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Check the manager properties
    assert manager.hass == mock_hass
    assert manager.registry == mock_tool_registry


def test_tool_manager_register_tool(mock_hass, mock_tool_registry):
    """Test the register_tool method of ToolManager."""
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Create a tool function
    def test_tool_function(hass, param1):
        return {"result": param1}
    
    # Register a tool
    manager.register_tool(
        name="test_tool",
        description="A test tool",
        function=test_tool_function,
        parameters=[
            {
                "name": "param1",
                "description": "A test parameter",
                "type": "string",
                "required": True,
            },
        ],
    )
    
    # Check that register_tool was called on the registry
    mock_tool_registry.register_tool.assert_called_once()
    args, kwargs = mock_tool_registry.register_tool.call_args
    
    assert kwargs["name"] == "test_tool"
    assert kwargs["description"] == "A test tool"
    assert callable(kwargs["function"])
    assert len(kwargs["parameters"]) == 1
    assert isinstance(kwargs["parameters"][0], ToolParameter)
    assert kwargs["parameters"][0].name == "param1"
    assert kwargs["parameters"][0].description == "A test parameter"
    assert kwargs["parameters"][0].parameter_type == ToolParameterType.STRING
    assert kwargs["parameters"][0].required is True


def test_tool_manager_register_tool_invalid_parameter(mock_hass, mock_tool_registry):
    """Test the register_tool method with an invalid parameter."""
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Try to register a tool with an invalid parameter
    with pytest.raises(ToolManagerError):
        manager.register_tool(
            name="test_tool",
            description="A test tool",
            function=lambda hass, param1: {"result": param1},
            parameters=[
                {
                    "name": "param1",
                    "description": "A test parameter",
                    "type": "invalid_type",
                    "required": True,
                },
            ],
        )


def test_tool_manager_register_tool_registry_error(mock_hass, mock_tool_registry):
    """Test the register_tool method when the registry raises an error."""
    # Set up the mock registry to raise an error
    mock_tool_registry.register_tool.side_effect = ToolRegistryError("Registry error")
    
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Try to register a tool
    with pytest.raises(ToolManagerError):
        manager.register_tool(
            name="test_tool",
            description="A test tool",
            function=lambda hass, param1: {"result": param1},
            parameters=[
                {
                    "name": "param1",
                    "description": "A test parameter",
                    "type": "string",
                    "required": True,
                },
            ],
        )


def test_tool_manager_get_tool(mock_hass, mock_tool_registry):
    """Test the get_tool method of ToolManager."""
    # Set up the mock registry to return a tool
    mock_tool = MagicMock(spec=Tool)
    mock_tool.name = "test_tool"
    mock_tool.description = "A test tool"
    mock_tool.parameters = [
        ToolParameter(
            name="param1",
            description="A test parameter",
            parameter_type=ToolParameterType.STRING,
            required=True,
            default=None,
        ),
    ]
    mock_tool_registry.get_tool.return_value = mock_tool
    
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Get a tool
    tool = manager.get_tool("test_tool")
    
    # Check that get_tool was called on the registry
    mock_tool_registry.get_tool.assert_called_once_with("test_tool")
    
    # Check the tool
    assert tool["name"] == "test_tool"
    assert tool["description"] == "A test tool"
    assert len(tool["parameters"]) == 1
    assert tool["parameters"][0]["name"] == "param1"
    assert tool["parameters"][0]["description"] == "A test parameter"
    assert tool["parameters"][0]["type"] == "string"
    assert tool["parameters"][0]["required"] is True


def test_tool_manager_get_tool_registry_error(mock_hass, mock_tool_registry):
    """Test the get_tool method when the registry raises an error."""
    # Set up the mock registry to raise an error
    mock_tool_registry.get_tool.side_effect = ToolRegistryError("Registry error")
    
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Try to get a tool
    with pytest.raises(ToolManagerError):
        manager.get_tool("test_tool")


def test_tool_manager_list_tools(mock_hass, mock_tool_registry):
    """Test the list_tools method of ToolManager."""
    # Set up the mock registry to return a list of tools
    mock_tool_registry.list_tools.return_value = [
        {
            "name": "test_tool1",
            "description": "A test tool",
            "parameters": [
                {
                    "name": "param1",
                    "description": "A test parameter",
                    "type": "string",
                    "required": True,
                },
            ],
        },
        {
            "name": "test_tool2",
            "description": "Another test tool",
            "parameters": [],
        },
    ]
    
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # List the tools
    tools = manager.list_tools()
    
    # Check that list_tools was called on the registry
    mock_tool_registry.list_tools.assert_called_once()
    
    # Check the tools
    assert len(tools) == 2
    assert tools[0]["name"] == "test_tool1"
    assert tools[0]["description"] == "A test tool"
    assert len(tools[0]["parameters"]) == 1
    assert tools[1]["name"] == "test_tool2"
    assert tools[1]["description"] == "Another test tool"
    assert len(tools[1]["parameters"]) == 0


async def test_tool_manager_execute_tool(mock_hass, mock_tool_registry):
    """Test the execute_tool method of ToolManager."""
    # Set up the mock registry to return a result
    mock_tool_registry.execute_tool.return_value = {"result": "test_value"}
    
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Execute a tool
    result = await manager.execute_tool("test_tool", {"param1": "test_value"})
    
    # Check that execute_tool was called on the registry
    mock_tool_registry.execute_tool.assert_called_once_with("test_tool", {"param1": "test_value"})
    
    # Check the result
    assert result.tool_name == "test_tool"
    assert result.success is True
    assert result.result == {"result": "test_value"}
    assert result.error is None


async def test_tool_manager_execute_tool_registry_error(mock_hass, mock_tool_registry):
    """Test the execute_tool method when the registry raises an error."""
    # Set up the mock registry to raise an error
    mock_tool_registry.execute_tool.side_effect = ToolRegistryError("Registry error")
    
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Execute a tool
    result = await manager.execute_tool("test_tool", {"param1": "test_value"})
    
    # Check that execute_tool was called on the registry
    mock_tool_registry.execute_tool.assert_called_once_with("test_tool", {"param1": "test_value"})
    
    # Check the result
    assert result.tool_name == "test_tool"
    assert result.success is False
    assert result.result is None
    assert result.error == "Registry error"


async def test_tool_manager_execute_tool_exception(mock_hass, mock_tool_registry):
    """Test the execute_tool method when an unexpected exception is raised."""
    # Set up the mock registry to raise an exception
    mock_tool_registry.execute_tool.side_effect = Exception("Unexpected error")
    
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Execute a tool
    result = await manager.execute_tool("test_tool", {"param1": "test_value"})
    
    # Check that execute_tool was called on the registry
    mock_tool_registry.execute_tool.assert_called_once_with("test_tool", {"param1": "test_value"})
    
    # Check the result
    assert result.tool_name == "test_tool"
    assert result.success is False
    assert result.result is None
    assert result.error == "Unexpected error"


@patch("custom_components.cortex_agent.tool_manager.ToolRegistry")
def test_tool_manager_init_with_default_registry(mock_tool_registry_class, mock_hass):
    """Test the initialization of a ToolManager with a default registry."""
    # Set up the mock registry class
    mock_registry = MagicMock(spec=ToolRegistry)
    mock_tool_registry_class.return_value = mock_registry
    
    # Create a tool manager without providing a registry
    manager = ToolManager(mock_hass)
    
    # Check that a registry was created
    mock_tool_registry_class.assert_called_once()
    
    # Check the manager properties
    assert manager.hass == mock_hass
    assert manager.registry == mock_registry


def test_tool_manager_register_builtin_tools(mock_hass, mock_tool_registry):
    """Test the register_builtin_tools method of ToolManager."""
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Register builtin tools
    manager.register_builtin_tools()
    
    # Check that register_tool was called on the registry
    assert mock_tool_registry.register_tool.call_count > 0


@patch("custom_components.cortex_agent.tool_manager.importlib.import_module")
def test_tool_manager_register_tools_from_module(mock_import_module, mock_hass, mock_tool_registry):
    """Test the register_tools_from_module method of ToolManager."""
    # Set up the mock module
    mock_module = MagicMock()
    mock_module.tool_registry = MagicMock(spec=ToolRegistry)
    mock_module.tool_registry.tools = {
        "test_tool": MagicMock(spec=Tool),
    }
    mock_import_module.return_value = mock_module
    
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Register tools from a module
    manager.register_tools_from_module("test_module")
    
    # Check that import_module was called with the right arguments
    mock_import_module.assert_called_once_with("test_module")
    
    # Check that register_tool was called on the registry
    assert mock_tool_registry.register_tool.call_count > 0


@patch("custom_components.cortex_agent.tool_manager.importlib.import_module")
def test_tool_manager_register_tools_from_module_no_registry(mock_import_module, mock_hass, mock_tool_registry):
    """Test the register_tools_from_module method when the module has no tool_registry."""
    # Set up the mock module without a tool_registry
    mock_module = MagicMock()
    mock_module.tool_registry = None
    mock_import_module.return_value = mock_module
    
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Register tools from a module
    manager.register_tools_from_module("test_module")
    
    # Check that import_module was called with the right arguments
    mock_import_module.assert_called_once_with("test_module")
    
    # Check that register_tool was not called on the registry
    mock_tool_registry.register_tool.assert_not_called()


@patch("custom_components.cortex_agent.tool_manager.importlib.import_module")
def test_tool_manager_register_tools_from_module_import_error(mock_import_module, mock_hass, mock_tool_registry):
    """Test the register_tools_from_module method when import_module raises an error."""
    # Set up the mock import_module to raise an error
    mock_import_module.side_effect = ImportError("Module not found")
    
    # Create a tool manager
    manager = ToolManager(mock_hass, mock_tool_registry)
    
    # Try to register tools from a module
    with pytest.raises(ToolManagerError):
        manager.register_tools_from_module("test_module")
    
    # Check that import_module was called with the right arguments
    mock_import_module.assert_called_once_with("test_module")
    
    # Check that register_tool was not called on the registry
    mock_tool_registry.register_tool.assert_not_called()