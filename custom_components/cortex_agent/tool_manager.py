"""Tool management for the CortexAgent integration."""
from __future__ import annotations

from collections.abc import Callable
import importlib
import importlib.util
import inspect
import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_CUSTOM_TOOLS, TOOL_TYPE_FUNCTION, TOOL_TYPE_MODULE
from .exceptions import ToolExecutionError
from .tool_registry import ToolRegistry
from .tools import ha_tools, http_tools, memory_tools, utility_tools

_LOGGER = logging.getLogger(__name__)


class ToolManager:
    """Manages tools for the agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, tool_registry: ToolRegistry):
        """Initialize the tool manager.

        Args:
            hass: Home Assistant instance
            entry: Config entry
            tool_registry: Tool registry
        """
        self.hass = hass
        self.entry = entry
        self.tool_registry = tool_registry

    async def async_setup(self) -> None:
        """Set up built-in and custom tools."""
        # Register built-in tools
        await self._register_builtin_tools()

        # Register custom tools
        await self._register_custom_tools()

    async def _register_builtin_tools(self) -> None:
        """Register built-in tools."""
        # Register Home Assistant tools
        if ha_tools is not None:
            _LOGGER.info("Registered Home Assistant tools")
        else:
            _LOGGER.error("Failed to import Home Assistant tools")

        # Register utility tools
        if utility_tools is not None:
            _LOGGER.info("Registered utility tools")
        else:
            _LOGGER.error("Failed to import utility tools")

        # Register memory tools
        if memory_tools is not None:
            _LOGGER.info("Registered memory tools")
        else:
            _LOGGER.error("Failed to import memory tools")

        # Register HTTP tools
        if http_tools is not None:
            _LOGGER.info("Registered HTTP tools")
        else:
            _LOGGER.error("Failed to import HTTP tools")

    async def _register_custom_tools(self) -> None:
        """Register custom tools from configuration."""
        custom_tools = self.entry.options.get(CONF_CUSTOM_TOOLS, [])

        for tool_config in custom_tools:
            try:
                tool_name = tool_config.get("name")
                tool_type = tool_config.get("type")

                if not tool_name or not tool_type:
                    _LOGGER.error("Invalid custom tool configuration: missing name or type")
                    continue

                if tool_type == TOOL_TYPE_FUNCTION:
                    # Register function-based tool
                    code = tool_config.get("code")
                    if not code:
                        _LOGGER.error("Invalid custom tool configuration: missing code")
                        continue

                    # Create function from code
                    tool_fn = await self._create_function_from_code(tool_name, code)
                    if tool_fn:
                        # Register the tool
                        self.tool_registry.register_tool(
                            tool_name,
                            tool_fn,
                            {
                                "name": tool_name,
                                "description": tool_config.get("description", f"Custom tool: {tool_name}"),
                                "category": "custom",
                                "parameters": tool_config.get("parameters", {}),
                            },
                        )
                        _LOGGER.info("Registered custom function tool: %s", tool_name)

                elif tool_type == TOOL_TYPE_MODULE:
                    # Register module-based tool
                    path = tool_config.get("path")
                    if not path:
                        _LOGGER.error("Invalid custom tool configuration: missing path")
                        continue

                    # Import module and register tools
                    await self._import_module_tools(path)
                    _LOGGER.info("Registered custom module tools from: %s", path)

                else:
                    _LOGGER.error("Invalid custom tool type: %s", tool_type)

            except (ValueError, KeyError, ImportError) as err:
                _LOGGER.error("Error registering custom tool: %s", str(err))

    async def _create_function_from_code(self, name: str, code: str) -> Callable | None:
        """Create a function from code string.

        Args:
            name: Function name
            code: Function code

        Returns:
            Function object or None if failed
        """
        try:
            # Create a namespace for the function
            namespace = {"hass": self.hass}

            # Execute the code in the namespace
            # pylint: disable=exec-used
            # nosec B102 - This is intentional as we need to execute custom tool code
            # ruff: noqa: S102
            exec(code, namespace)  # nosec

            # Get the function from the namespace
            if name in namespace:
                return namespace[name]
            # ruff: noqa: TRY300
            _LOGGER.error("Function %s not found in code", name)
            return None

        except (SyntaxError, NameError, TypeError) as err:
            _LOGGER.error("Error creating function from code: %s", str(err))
            return None

    async def _import_module_tools(self, path: str) -> None:
        """Import tools from a module.

        Args:
            path: Module path
        """
        try:
            # Check if path exists
            if not Path(path).exists():
                _LOGGER.error("Module path does not exist: %s", path)
                return

            # Import the module
            spec = importlib.util.spec_from_file_location("custom_module", path)
            if not spec or not spec.loader:
                _LOGGER.error("Failed to load module spec: %s", path)
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find and register all functions in the module
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj):
                    # Register the function as a tool
                    self.tool_registry.register_tool(
                        name,
                        obj,
                        {
                            "name": name,
                            "description": obj.__doc__ or f"Custom tool: {name}",
                            "category": "custom",
                        },
                    )
                    _LOGGER.info("Registered custom module tool: %s", name)

        except (ImportError, AttributeError, ModuleNotFoundError) as err:
            _LOGGER.error("Error importing module tools: %s", str(err))

    async def async_get_all_tools(self) -> list[Callable]:
        """Get all available tools.

        Returns:
            List of tool functions
        """
        return self.tool_registry.get_all_tools()

    async def async_execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name.

        Args:
            tool_name: Name of the tool
            **kwargs: Tool arguments

        Returns:
            Tool result

        Raises:
            ToolExecutionError: If tool execution fails
        """
        tool_fn = self.tool_registry.get_tool(tool_name)

        if not tool_fn:
            raise ToolExecutionError(tool_name, f"Tool not found: {tool_name}")

        try:
            # Execute the tool
            return await self.hass.async_add_executor_job(tool_fn, **kwargs)
        except Exception as err:
            raise ToolExecutionError(tool_name, str(err)) from err
