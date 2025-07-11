# CortexAgent Home Assistant Integration

## Overview

CortexAgent is a powerful AI assistant integration for Home Assistant that leverages the Strands Agent framework. It enables users to create and configure multiple AI assistants with different settings, supporting various model providers, tool management, memory capabilities, and MCP server connections. The integration meets Home Assistant's Bronze and Silver tier quality standards, ensuring reliability and proper integration with the Home Assistant ecosystem.

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
- **Metrics and Telemetry**: Track usage, performance, and errors
- **MCP Server Support**: Connect to external tool providers via Model Context Protocol
- **Entity Availability Handling**: Proper availability state management for all entities
- **System Health Support**: Integration health monitoring and diagnostics

## Installation

1. Add this repository to HACS as a custom repository
2. Install the "CortexAgent" integration from HACS
3. Restart Home Assistant
4. Add the integration through the Home Assistant UI (Settings > Devices & Services > Add Integration)
5. Configure your preferred model provider and settings

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
  - **URL**: URL of the MCP server or path to executable for stdio servers
  - **Server Type**: SSE, Streamable HTTP, or Stdio
  - **Auth Token**: Authentication token if required (for remote servers)
  - **Command Args**: Command-line arguments (for stdio servers)

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

The agent uses a sophisticated conversation strategy that can handle complex queries, follow-up questions, and context-aware responses. It leverages the memory capabilities to remember past interactions and provide more personalized assistance.

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

## Entity Availability and System Health

### Entity Availability

The integration implements proper entity availability handling for all entities:

- **Base Entity Availability**: The `CortexAgentEntity` class implements an `available` property that checks:
  - Coordinator data update success
  - Presence of coordinator data
  - Agent initialization status

- **Server Entity Availability**: The `CortexAgentServerEntity` class extends the base availability check to also verify:
  - Presence of server data in the coordinator
  - Server existence in the list of connected servers

This ensures that entities properly report their availability state to Home Assistant, improving the reliability and user experience of the integration.

### System Health

The integration supports Home Assistant's system health component, providing:

- **Connectivity Checks**: Verification of connections to model providers and MCP servers
- **Status Information**: Current status of the agent and its components
- **Diagnostics**: Information about the integration's configuration and state

System health information can be accessed through Home Assistant's System Health panel (Configuration > Info > System Health).

## Development

This integration is developed using test-driven development practices. All components have corresponding test files to ensure functionality.

### Project Structure

```
custom_components/cortex_agent/
├── __init__.py              # Main entry point
├── manifest.json            # Integration metadata with quality_scale
├── config_flow.py           # Configuration UI flow
├── const.py                 # Constants
├── services.yaml            # Service descriptions
├── strings.json             # Translation strings with system health
├── conversation_strategy.py # Conversation strategy implementation
├── conversation.py          # Conversation platform integration
├── conversation_manager.py  # Conversation history management
├── mcp_connector.py         # MCP server connection
├── model_provider.py        # Model provider management
├── models.py                # Data models and interfaces
├── tool_registry.py         # Tool registration system
├── tools.py                 # Tool management
├── memory_handler.py        # Memory operations
├── event_listener.py        # Home Assistant event integration
├── metrics.py               # Metrics and telemetry
├── documentation.py         # Documentation generation
├── exceptions.py            # Custom exceptions
├── coordinator.py           # Data update coordinator
├── entity.py                # Entity definitions with availability handling
├── diagnostics.py           # Diagnostics support
├── system_health.py         # System health support with connectivity checks
├── websocket_api.py         # WebSocket API
├── frontend.py              # Frontend resources
├── strands_integration.py   # Strands framework integration
├── quality_scale.yaml       # Quality scale tracking
├── DEVELOPERS.md            # Developer documentation
├── README.md                # User documentation
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

### Testing

The integration includes comprehensive tests for all components:

```
tests/test_cortex_agent/
├── test_init.py             # Tests for initialization
├── test_config_flow.py      # Tests for configuration flow
├── test_config_flow_e2e.py  # End-to-end tests for configuration
├── test_model_provider.py   # Tests for model providers
├── test_tool_registry.py    # Tests for tool registry
├── test_tools.py            # Tests for tools
├── test_mcp_connector.py    # Tests for MCP connector
├── test_metrics.py          # Tests for metrics
├── test_documentation.py    # Tests for documentation generation
└── conftest.py              # Test fixtures and utilities
```

### Model Context Protocol (MCP)

The integration supports the Model Context Protocol (MCP) for connecting to external tool providers. MCP servers can be one of three types:

1. **SSE (Server-Sent Events)**: Remote servers that communicate over HTTP using Server-Sent Events
2. **Streamable HTTP**: Remote servers that communicate over HTTP with streaming capabilities
3. **Stdio (Standard Input/Output)**: Local servers that run on the user's machine and communicate via standard input/output

MCP servers provide additional tools and resources that extend the agent's capabilities. The integration includes a robust connector system for managing these connections and executing tools.

For detailed information about MCP server configuration and architecture, see:
- [MCP Server Configuration](../../docs/mcp_servers.md)
- [MCP Server Architecture](../../docs/mcp_server_architecture.md)

The integration provides a dedicated Lovelace card for managing MCP servers:

```yaml
type: custom:cortex-mcp-servers-card
entry_id: YOUR_ENTRY_ID
```

This card allows you to:
- View connected MCP servers
- Connect to new servers
- Disconnect from existing servers
- View available tools from each server

### Metrics and Telemetry

The integration includes a metrics system that tracks:

- Request counts and success rates
- Tool usage statistics
- Response times
- Token usage
- Error rates by type

These metrics can be accessed through the `cortex_agent.get_agent_metrics` service and are useful for monitoring the performance and usage of the agent.

## Quality Scale

The CortexAgent integration meets Home Assistant's [Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale) requirements for Bronze and Silver tiers:

### Bronze Tier Requirements (Completed)

- ✅ Stable and working
- ✅ Formatted according to Black
- ✅ Passes CI (lint, mypy, hassfest, pytest)
- ✅ Documented in the proper format
- ✅ Registration of services/entities via appropriate platform
- ✅ Using appropriate dependency versions
- ✅ Using standard Home Assistant configuration and service schemas
- ✅ Using unique_id for entities
- ✅ Entities have device info where possible
- ✅ Entities have proper availability
- ✅ Entities have proper device classes where appropriate
- ✅ Entities have entity categories where appropriate
- ✅ Entities have unit of measurement where appropriate
- ✅ Entities have proper state classes where appropriate
- ✅ Entities have icons where appropriate
- ✅ Integration manifest includes all required keys
- ✅ Integration manifest has quality_scale: bronze

### Silver Tier Requirements (Completed)

- ✅ Entities have translations
- ✅ Services have translations
- ✅ Supports entity configuration via config_flow
- ✅ Config flow has translations
- ✅ Config flow uses unique IDs where appropriate
- ✅ Supports config entry unloading
- ✅ Tests for the config flow
- ✅ Tests for the integration
- ✅ Tests for the entity
- ✅ Tests for the platform
- ✅ Supports system health
- ✅ Integration manifest has quality_scale: silver

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please see the DEVELOPERS.md file for guidelines on contributing to this project.