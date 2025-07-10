# CortexAgent Home Assistant Integration

## Overview

CortexAgent is a powerful AI assistant integration for Home Assistant that leverages the Strands Agent framework. It enables users to create and configure multiple AI assistants with different settings, supporting various model providers, tool management, memory capabilities, and MCP server connections.

## Features

- **Multiple Model Providers**: Support for Amazon Bedrock, OpenAI, Anthropic, and custom endpoints via LiteLLM
- **Tool Management**: Built-in tools, MCP server tools, and custom tools
- **Memory Capabilities**: Persistent memory through mem0_memory tool
- **Conversation Integration**: Seamless integration with Home Assistant's conversation platform
- **Custom Tools**: Create and manage custom tools through the UI
- **Entity Control**: Control Home Assistant entities through natural language
- **Asynchronous Architecture**: Fully asynchronous design compatible with Home Assistant
- **Frontend Integration**: Custom cards and panels for conversation, tools, and MCP servers
- **WebSocket API**: Real-time updates and interaction with the integration

## Installation

1. Add this repository to HACS as a custom repository
2. Install the "CortexAgent" integration from HACS
3. Restart Home Assistant
4. Add the integration through the Home Assistant UI (Settings > Devices & Services > Add Integration)

## Configuration

The integration can be configured through the Home Assistant UI. The following options are available:

### Model Provider

- **Provider**: Select from OpenAI, Anthropic, Amazon Bedrock, or LiteLLM
- **Model ID**: Select the model to use
- **API Key**: API key for the selected provider (not required for Amazon Bedrock)
- **System Prompt**: The system prompt to use for the agent
- **Max Tokens**: Maximum tokens for response generation
- **Temperature**: Temperature for response generation

### Memory

- **Enable Memory**: Enable or disable memory capabilities
- **User ID**: User ID for memory storage

### MCP Servers

- **Add Server**: Add a new MCP server
  - **Name**: Name for the server
  - **URL**: URL of the MCP server
  - **Server Type**: Local or Remote
  - **Auth Token**: Authentication token if required

### Custom Tools

- **Add Tool**: Add a custom tool
  - **Name**: Name for the tool
  - **Description**: Description of the tool
  - **Type**: Function or Module
  - **Code**: Code for function tools
  - **Path**: Path for module tools
  - **Parameters**: Parameters for the tool

## Services

The integration provides the following services:

- **cortex_agent.reload**: Reload the agent with updated configuration
- **cortex_agent.connect_mcp_server**: Connect to an MCP server
- **cortex_agent.disconnect_mcp_server**: Disconnect from an MCP server
- **cortex_agent.add_tool**: Add a custom tool
- **cortex_agent.remove_tool**: Remove a custom tool
- **cortex_agent.clear_conversation**: Clear conversation history
- **cortex_agent.get_agent_metrics**: Get metrics for an agent
- **cortex_agent.reset_agent_metrics**: Reset metrics for an agent
- **cortex_agent.generate_tool_documentation**: Generate documentation for available tools

## Usage

Once configured, the agent will be available as a conversation agent in Home Assistant. You can interact with it through:

- The conversation panel in the Home Assistant UI
- Voice commands through the voice assistant
- The conversation.process service
- The dedicated Cortex Agent panel in the sidebar
- Custom Lovelace cards for conversation, tools, and MCP servers

### Lovelace Cards

The integration provides the following custom Lovelace cards:

- **cortex-conversation-card**: A card for interacting with the agent through conversations
- **cortex-tools-card**: A card for managing and exploring available tools
- **cortex-mcp-servers-card**: A card for managing MCP server connections

Example configuration:

```yaml
type: custom:cortex-conversation-card
entry_id: YOUR_ENTRY_ID
```

## Built-in Tools

The integration comes with several built-in tools:

### Home Assistant Tools

- **get_state**: Get the state of one or more entities
- **set_state**: Set the state of an entity
- **call_service**: Call a Home Assistant service
- **get_services**: Get available services
- **get_entities**: Get available entities

### Memory Tools

- **store_memory**: Store information in memory
- **retrieve_memory**: Retrieve information from memory
- **list_memories**: List all stored memories
- **clear_memories**: Clear all stored memories

### HTTP Tools

- **http_get**: Make an HTTP GET request
- **http_post**: Make an HTTP POST request
- **http_put**: Make an HTTP PUT request
- **http_delete**: Make an HTTP DELETE request

### Utility Tools

- **get_time**: Get the current time
- **get_date**: Get the current date
- **calculate**: Perform a calculation
- **format_text**: Format text

## Development

This integration is developed using test-driven development practices. All components have corresponding test files to ensure functionality.

### Project Structure

```
custom_components/cortex_agent/
├── __init__.py              # Main entry point
├── manifest.json            # Integration metadata
├── config_flow.py           # Configuration UI flow
├── const.py                 # Constants
├── services.yaml            # Service descriptions
├── strings.json             # Translation strings
├── agent_manager.py         # Agent management
├── mcp_connector.py         # MCP server connection
├── model_provider.py        # Model provider management
├── tool_manager.py          # Tool management
├── tool_registry.py         # Tool registration system
├── conversation.py          # Conversation platform integration
├── conversation_manager.py  # Conversation history management
├── memory_handler.py        # Memory operations
├── event_listener.py        # Home Assistant event integration
├── metrics.py               # Metrics and telemetry
├── documentation.py         # Documentation generation
├── exceptions.py            # Custom exceptions
├── helpers.py               # Helper functions
├── coordinator.py           # Data update coordinator
├── entity.py                # Entity definitions
├── diagnostics.py           # Diagnostics support
├── system_health.py         # System health support
├── websocket_api.py         # WebSocket API
├── frontend.py              # Frontend resources
├── repairs.py               # Repairs platform integration
└── tools/                   # Built-in tools directory
    ├── __init__.py
    ├── memory_tools.py
    ├── http_tools.py
    ├── ha_tools.py          # Home Assistant specific tools
    └── utility_tools.py
└── frontend/                # Frontend components
    ├── index.js
    ├── cortex-conversation-card.js
    ├── cortex-tools-card.js
    └── cortex-mcp-servers-card.js
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.