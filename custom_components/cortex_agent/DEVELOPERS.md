# CortexAgent Developer Documentation

This document provides information for developers who want to extend or modify the CortexAgent integration.

## Architecture Overview

The CortexAgent integration is built on a modular architecture with several key components:

1. **Model Provider**: Handles communication with AI model providers (OpenAI, Anthropic, Bedrock, LiteLLM)
2. **Conversation Manager**: Manages conversation history and pruning
3. **Tool Registry**: Manages tool registration and execution
4. **Memory Handler**: Handles memory storage and retrieval
5. **MCP Connector**: Manages connections to MCP servers and tool execution
6. **WebSocket API**: Provides real-time communication with the frontend
7. **Frontend Components**: Custom Lovelace cards and panels
8. **Entity System**: Manages entity availability and state updates
9. **System Health**: Provides integration health monitoring and diagnostics

## Extending the Integration

### Adding a New Model Provider

To add a new model provider, follow these steps:

1. Add a new provider class in `model_provider.py` that extends the `ModelProvider` base class
2. Implement the required methods:
   - `async_generate_response`: Generate a response from the model
   - `async_validate_credentials`: Validate the provider credentials
3. Add the provider to the `create_model_provider` factory function
4. Update the `MODEL_VALIDATORS` constant in `const.py` to include the new provider

Example:

```python
class NewProvider(ModelProvider):
    """New model provider implementation."""

    def __init__(self, config: Dict[str, Any], hass: HomeAssistant) -> None:
        """Initialize the provider."""
        super().__init__(config, hass)
        self.client = None
        
    async def async_setup(self) -> None:
        """Set up the provider."""
        # Initialize the client
        self.client = YourClient(self.config["api_key"])
        
    async def async_generate_response(
        self, messages: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        """Generate a response from the model."""
        # Implement response generation
        response = await self.client.generate(messages, **kwargs)
        return {
            "content": response.text,
            "role": "assistant",
        }
        
    async def async_validate_credentials(self) -> bool:
        """Validate the provider credentials."""
        try:
            # Implement validation
            await self.client.validate()
            return True
        except Exception:
            return False
```

### Adding a New Tool

To add a new tool, you can either:

1. Add it to one of the existing tool modules in the `tools` directory
2. Create a new tool module in the `tools` directory

Example:

```python
async def my_new_tool(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
    """My new tool implementation."""
    # Implement tool functionality
    result = do_something(args.get("input"))
    return {"result": result}

def register_my_tools(tool_registry) -> None:
    """Register my tools with the tool registry."""
    tool_registry.register_tool(
        name="my_new_tool",
        description="A description of what my tool does",
        function=my_new_tool,
        parameters={
            "input": {
                "type": "string",
                "description": "The input for the tool",
            },
        },
        category="my_category",
    )
```

Then update the `register_built_in_tools` function in `tools/__init__.py` to include your new tool module.

### Working with the MCP Connector

The `MCPConnector` class manages connections to MCP servers and provides methods for executing tools. To work with the MCP connector:

1. Access the connector from the integration's data:

```python
connector = hass.data[DOMAIN][entry.entry_id][DATA_MCP_CONNECTOR]
```

2. Connect to an MCP server:

```python
server_config = {
    "name": "my-server",
    "url": "http://localhost:8000/mcp",
    "server_type": "sse",
    "auth_token": "my-token",
}
await connector.async_connect(server_config)
```

3. Get available tools:

```python
# Get all tools from all servers
all_tools = await connector.async_get_all_tools()

# Get tools from a specific server
server_tools = await connector.async_get_server_tools("my-server")
```

4. Execute a tool:

```python
result = await connector.async_execute_tool(
    "my-server",
    "my-tool",
    {"param1": "value1", "param2": "value2"}
)
```

5. Register a callback for tool execution:

```python
def my_callback(server_name, tool_name, arguments, result):
    """Handle tool execution event."""
    _LOGGER.info("Tool %s executed on server %s", tool_name, server_name)
    
connector.register_execution_callback("my-server", my_callback)
```

6. Disconnect from a server:

```python
await connector.async_disconnect("my-server")
```

The connector uses a context manager pattern when interacting with MCP clients to ensure proper resource management:

```python
with client:
    # Perform operations with the client
    result = client.some_operation()
```

This is particularly important for stdio servers where processes need to be properly terminated.

### Adding a New Frontend Component

To add a new frontend component:

1. Create a new JavaScript file in the `frontend` directory
2. Register the component in `frontend/index.js`
3. Update the `async_register_frontend` function in `frontend.py` to include your new component

Example:

```javascript
// frontend/my-new-card.js
import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

class MyNewCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
    };
  }

  render() {
    return html`
      <ha-card>
        <div class="card-content">
          My new card content
        </div>
      </ha-card>
    `;
  }

  static get styles() {
    return css`
      ha-card {
        padding: 16px;
      }
    `;
  }
}

customElements.define("my-new-card", MyNewCard);
```

## Testing

The integration uses pytest for testing. Tests are organized in the following directories:

- `tests/unit`: Unit tests for individual components
- `tests/standalone`: Standalone tests that don't require Home Assistant

To run the tests:

```bash
# Run all tests
pytest tests/

# Run specific tests
pytest tests/unit/custom_components/cortex_agent/test_model_provider.py
```

### Writing Tests

When adding new functionality, always add corresponding tests. Follow these guidelines:

1. Use test-driven development (TDD) where possible
2. Write both happy path and error path tests
3. Use mocks for external dependencies
4. Keep tests isolated and independent

Example:

```python
async def test_my_new_tool():
    """Test my new tool."""
    # Arrange
    hass = MagicMock()
    args = {"input": "test"}
    
    # Act
    result = await my_new_tool(hass, args)
    
    # Assert
    assert "result" in result
    assert result["result"] == "expected output"
```

## WebSocket API

The WebSocket API provides real-time communication with the frontend. To add a new WebSocket command:

1. Add a new command function in `websocket_api.py`
2. Register the command in the `async_register_websocket_commands` function

Example:

```python
@websocket_api.websocket_command({
    vol.Required("type"): "cortex_agent/my_command",
    vol.Required("entry_id"): str,
    vol.Optional("param"): str,
})
@callback
async def ws_my_command(
    hass: HomeAssistant, connection: ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Handle my command."""
    entry_id = msg["entry_id"]
    param = msg.get("param")
    
    # Implement command logic
    result = do_something(entry_id, param)
    
    connection.send_result(msg["id"], {"result": result})
```

## Working with Entity Availability

The integration implements a robust entity availability system through two main classes:

### CortexAgentEntity

The base entity class implements an `available` property that checks:

```python
@property
def available(self) -> bool:
    """Return if entity is available."""
    # First check the parent class availability (coordinator.last_update_success)
    if not super().available:
        return False
        
    # Check if the coordinator has data
    if not self.coordinator.data:
        return False
        
    # Check if the agent is initialized
    if not self.coordinator._agent:
        return False
        
    return True
```

### CortexAgentServerEntity

The server entity class extends the base availability check:

```python
@property
def available(self) -> bool:
    """Return if entity is available."""
    # First check the parent class availability
    if not super().available:
        return False
        
    # Check if the server exists in the coordinator data
    if not self.coordinator.data or "servers" not in self.coordinator.data:
        return False
        
    # Check if the server is in the list of servers
    if self._server_name not in self.coordinator.data["servers"]:
        return False
        
    return True
```

When creating new entity types, extend one of these classes and override the `available` property if needed.

## Working with System Health

The integration supports Home Assistant's system health component through the `system_health.py` module:

```python
async def async_get_system_health_info(hass, controller):
    """Get system health information."""
    info = {
        "agent_status": "active" if _is_agent_active(hass) else "inactive",
        "model_provider": _get_model_provider_info(hass),
        "mcp_servers": _get_mcp_servers_info(hass),
    }
    
    # Add connectivity checks
    for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
        if DATA_AGENT not in entry_data:
            continue
            
        agent = entry_data[DATA_AGENT]
        model_provider = entry_data.get("model_provider")
        
        if model_provider:
            try:
                await model_provider.async_validate_credentials()
                info["model_provider_connection"] = "connected"
            except Exception:
                info["model_provider_connection"] = "disconnected"
    
    return info
```

To extend system health information:

1. Add new keys to the info dictionary in `async_get_system_health_info`
2. Add corresponding translations in `strings.json`

## Best Practices

1. **Error Handling**: Use custom exceptions from `exceptions.py` for specific error cases
2. **Async/Await**: Use async/await for all I/O operations
3. **Type Hints**: Use type hints for all functions and methods
4. **Documentation**: Add docstrings to all functions, methods, and classes
5. **Constants**: Define constants in `const.py` rather than using magic values
6. **Dependency Injection**: Use dependency injection to make components testable
7. **Logging**: Use the logger for appropriate logging levels
8. **Entity Availability**: Always implement proper availability checks for entities
9. **System Health**: Add relevant health checks for new components

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
2. **API Rate Limits**: Implement rate limiting and backoff strategies
3. **Memory Leaks**: Be careful with event listeners and subscriptions
4. **Frontend Issues**: Check browser console for errors

### Debugging

1. Enable debug logging in Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.cortex_agent: debug
```

2. Use the Home Assistant Developer Tools to inspect states and services
3. Use the browser developer tools to debug frontend issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the tests
6. Submit a pull request

Please follow the existing code style and conventions.