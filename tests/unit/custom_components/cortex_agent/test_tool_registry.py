"""Tests for the CortexAgent tool_registry module."""
from unittest.mock import MagicMock, patch
import json

import pytest

from custom_components.cortex_agent.tool_registry import (
    ToolRegistry,
    Tool,
    ToolParameter,
    ToolParameterType,
)
from custom_components.cortex_agent.exceptions import ToolRegistryError


def test_tool_parameter_init():
    """Test the initialization of a ToolParameter."""
    # Create a tool parameter
    param = ToolParameter(
        name="param1",
        description="A test parameter",
        parameter_type=ToolParameterType.STRING,
        required=True,
        default=None,
    )
    
    # Check the parameter properties
    assert param.name == "param1"
    assert param.description == "A test parameter"
    assert param.parameter_type == ToolParameterType.STRING
    assert param.required is True
    assert param.default is None


def test_tool_parameter_to_dict():
    """Test the to_dict method of ToolParameter."""
    # Create a tool parameter
    param = ToolParameter(
        name="param1",
        description="A test parameter",
        parameter_type=ToolParameterType.STRING,
        required=True,
        default=None,
    )
    
    # Convert to dict
    param_dict = param.to_dict()
    
    # Check the dict
    assert param_dict["name"] == "param1"
    assert param_dict["description"] == "A test parameter"
    assert param_dict["type"] == "string"
    assert param_dict["required"] is True
    assert "default" not in param_dict


def test_tool_parameter_to_dict_with_default():
    """Test the to_dict method of ToolParameter with a default value."""
    # Create a tool parameter with a default value
    param = ToolParameter(
        name="param1",
        description="A test parameter",
        parameter_type=ToolParameterType.STRING,
        required=False,
        default="default_value",
    )
    
    # Convert to dict
    param_dict = param.to_dict()
    
    # Check the dict
    assert param_dict["name"] == "param1"
    assert param_dict["description"] == "A test parameter"
    assert param_dict["type"] == "string"
    assert param_dict["required"] is False
    assert param_dict["default"] == "default_value"


def test_tool_parameter_from_dict():
    """Test the from_dict method of ToolParameter."""
    # Create a dict
    param_dict = {
        "name": "param1",
        "description": "A test parameter",
        "type": "string",
        "required": True,
    }
    
    # Convert to ToolParameter
    param = ToolParameter.from_dict(param_dict)
    
    # Check the parameter
    assert param.name == "param1"
    assert param.description == "A test parameter"
    assert param.parameter_type == ToolParameterType.STRING
    assert param.required is True
    assert param.default is None


def test_tool_parameter_from_dict_with_default():
    """Test the from_dict method of ToolParameter with a default value."""
    # Create a dict with a default value
    param_dict = {
        "name": "param1",
        "description": "A test parameter",
        "type": "string",
        "required": False,
        "default": "default_value",
    }
    
    # Convert to ToolParameter
    param = ToolParameter.from_dict(param_dict)
    
    # Check the parameter
    assert param.name == "param1"
    assert param.description == "A test parameter"
    assert param.parameter_type == ToolParameterType.STRING
    assert param.required is False
    assert param.default == "default_value"


def test_tool_parameter_from_dict_invalid_type():
    """Test the from_dict method of ToolParameter with an invalid type."""
    # Create a dict with an invalid type
    param_dict = {
        "name": "param1",
        "description": "A test parameter",
        "type": "invalid_type",
        "required": True,
    }
    
    # Try to convert to ToolParameter
    with pytest.raises(ValueError):
        ToolParameter.from_dict(param_dict)


def test_tool_init():
    """Test the initialization of a Tool."""
    # Create a tool
    tool = Tool(
        name="test_tool",
        description="A test tool",
        function=lambda: None,
        parameters=[
            ToolParameter(
                name="param1",
                description="A test parameter",
                parameter_type=ToolParameterType.STRING,
                required=True,
                default=None,
            ),
        ],
    )
    
    # Check the tool properties
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert callable(tool.function)
    assert len(tool.parameters) == 1
    assert tool.parameters[0].name == "param1"


def test_tool_to_dict():
    """Test the to_dict method of Tool."""
    # Create a tool
    tool = Tool(
        name="test_tool",
        description="A test tool",
        function=lambda: None,
        parameters=[
            ToolParameter(
                name="param1",
                description="A test parameter",
                parameter_type=ToolParameterType.STRING,
                required=True,
                default=None,
            ),
        ],
    )
    
    # Convert to dict
    tool_dict = tool.to_dict()
    
    # Check the dict
    assert tool_dict["name"] == "test_tool"
    assert tool_dict["description"] == "A test tool"
    assert len(tool_dict["parameters"]) == 1
    assert tool_dict["parameters"][0]["name"] == "param1"
    assert tool_dict["parameters"][0]["description"] == "A test parameter"
    assert tool_dict["parameters"][0]["type"] == "string"
    assert tool_dict["parameters"][0]["required"] is True


def test_tool_registry_init():
    """Test the initialization of a ToolRegistry."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Check the registry properties
    assert registry.tools == {}


def test_tool_registry_register_tool():
    """Test the register_tool method of ToolRegistry."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Create a tool function
    def test_tool_function(param1):
        return {"result": param1}
    
    # Register a tool
    registry.register_tool(
        name="test_tool",
        description="A test tool",
        function=test_tool_function,
        parameters=[
            ToolParameter(
                name="param1",
                description="A test parameter",
                parameter_type=ToolParameterType.STRING,
                required=True,
                default=None,
            ),
        ],
    )
    
    # Check that the tool was registered
    assert "test_tool" in registry.tools
    
    tool = registry.tools["test_tool"]
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert tool.function == test_tool_function
    assert len(tool.parameters) == 1
    assert tool.parameters[0].name == "param1"


def test_tool_registry_register_tool_duplicate():
    """Test the register_tool method with a duplicate tool name."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Register a tool
    registry.register_tool(
        name="test_tool",
        description="A test tool",
        function=lambda: None,
        parameters=[],
    )
    
    # Try to register a tool with the same name
    with pytest.raises(ToolRegistryError):
        registry.register_tool(
            name="test_tool",
            description="Another test tool",
            function=lambda: None,
            parameters=[],
        )


def test_tool_registry_get_tool():
    """Test the get_tool method of ToolRegistry."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Register a tool
    registry.register_tool(
        name="test_tool",
        description="A test tool",
        function=lambda: None,
        parameters=[],
    )
    
    # Get the tool
    tool = registry.get_tool("test_tool")
    
    # Check the tool
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"


def test_tool_registry_get_tool_not_found():
    """Test the get_tool method with a tool that doesn't exist."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Try to get a non-existent tool
    with pytest.raises(ToolRegistryError):
        registry.get_tool("non_existent_tool")


def test_tool_registry_list_tools():
    """Test the list_tools method of ToolRegistry."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Register some tools
    registry.register_tool(
        name="test_tool1",
        description="A test tool",
        function=lambda: None,
        parameters=[],
    )
    
    registry.register_tool(
        name="test_tool2",
        description="Another test tool",
        function=lambda: None,
        parameters=[],
    )
    
    # List the tools
    tools = registry.list_tools()
    
    # Check the tools
    assert len(tools) == 2
    assert tools[0]["name"] == "test_tool1"
    assert tools[0]["description"] == "A test tool"
    assert tools[1]["name"] == "test_tool2"
    assert tools[1]["description"] == "Another test tool"


def test_tool_registry_execute_tool():
    """Test the execute_tool method of ToolRegistry."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Create a tool function
    def test_tool_function(param1):
        return {"result": param1}
    
    # Register a tool
    registry.register_tool(
        name="test_tool",
        description="A test tool",
        function=test_tool_function,
        parameters=[
            ToolParameter(
                name="param1",
                description="A test parameter",
                parameter_type=ToolParameterType.STRING,
                required=True,
                default=None,
            ),
        ],
    )
    
    # Execute the tool
    result = registry.execute_tool("test_tool", {"param1": "test_value"})
    
    # Check the result
    assert result == {"result": "test_value"}


def test_tool_registry_execute_tool_not_found():
    """Test the execute_tool method with a tool that doesn't exist."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Try to execute a non-existent tool
    with pytest.raises(ToolRegistryError):
        registry.execute_tool("non_existent_tool", {})


def test_tool_registry_execute_tool_missing_parameter():
    """Test the execute_tool method with missing required parameters."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Register a tool with a required parameter
    registry.register_tool(
        name="test_tool",
        description="A test tool",
        function=lambda param1: {"result": param1},
        parameters=[
            ToolParameter(
                name="param1",
                description="A test parameter",
                parameter_type=ToolParameterType.STRING,
                required=True,
                default=None,
            ),
        ],
    )
    
    # Try to execute the tool without providing the required parameter
    with pytest.raises(ToolRegistryError):
        registry.execute_tool("test_tool", {})


def test_tool_registry_execute_tool_with_default_parameter():
    """Test the execute_tool method with a parameter that has a default value."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Create a tool function
    def test_tool_function(param1):
        return {"result": param1}
    
    # Register a tool with a parameter that has a default value
    registry.register_tool(
        name="test_tool",
        description="A test tool",
        function=test_tool_function,
        parameters=[
            ToolParameter(
                name="param1",
                description="A test parameter",
                parameter_type=ToolParameterType.STRING,
                required=False,
                default="default_value",
            ),
        ],
    )
    
    # Execute the tool without providing the parameter
    result = registry.execute_tool("test_tool", {})
    
    # Check the result
    assert result == {"result": "default_value"}


def test_tool_registry_execute_tool_with_invalid_parameter_type():
    """Test the execute_tool method with a parameter of the wrong type."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Register a tool with a parameter of type STRING
    registry.register_tool(
        name="test_tool",
        description="A test tool",
        function=lambda param1: {"result": param1},
        parameters=[
            ToolParameter(
                name="param1",
                description="A test parameter",
                parameter_type=ToolParameterType.STRING,
                required=True,
                default=None,
            ),
        ],
    )
    
    # Try to execute the tool with a parameter of the wrong type
    with pytest.raises(ToolRegistryError):
        registry.execute_tool("test_tool", {"param1": 123})


def test_tool_registry_execute_tool_with_exception():
    """Test the execute_tool method with a function that raises an exception."""
    # Create a tool registry
    registry = ToolRegistry()
    
    # Create a tool function that raises an exception
    def test_tool_function(param1):
        raise ValueError("Test error")
    
    # Register a tool
    registry.register_tool(
        name="test_tool",
        description="A test tool",
        function=test_tool_function,
        parameters=[
            ToolParameter(
                name="param1",
                description="A test parameter",
                parameter_type=ToolParameterType.STRING,
                required=True,
                default=None,
            ),
        ],
    )
    
    # Try to execute the tool
    with pytest.raises(ToolRegistryError):
        registry.execute_tool("test_tool", {"param1": "test_value"})