# Unified Agent CLI

A command-line interface for interacting with Strands Agents, with support for MCP servers, memory capabilities, and HTTP requests.

## Features

- **MCP Server Integration**: Connect to remote MCP servers using SSE or Streamable HTTP
- **Memory Management**: Store and retrieve information using mem0
- **HTTP Capabilities**: Make HTTP requests to external APIs
- **Command-Line Interface**: Interact with the agent through a simple CLI
- **Type Safety**: All components are type-safe using Pydantic models

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd unified-agent
   ```

2. Install the package:
   ```
   pip install -e .
   ```

## Usage

### Starting the CLI

```
unified-agent
```

Or with custom configuration:

```
unified-agent --config /path/to/config.json --log-file /path/to/log.log --debug --aws-profile my-profile
```

### Available Commands

- `/help`: Show help information
- `/connect <url> [type] [name]`: Connect to an MCP server
- `/disconnect <name>`: Disconnect from an MCP server
- `/list-servers`: List connected MCP servers
- `/list-tools`: List available tools
- `/remember <text>`: Store information in memory
- `/recall <query>`: Retrieve information from memory
- `/memories`: List all stored memories
- `/config`: Show current configuration
- `/reload`: Reload the agent with updated configuration
- `/aws-profile [name]`: Show or set the AWS profile

Any other input will be processed by the agent.

### Examples

#### Connecting to an MCP Server

```
> /connect https://example.com/mcp sse my-server
✅ Connected to MCP server: my-server
```

#### Listing Available Tools

```
> /list-tools
✅ Available Tools

my-server:
- add: Add two numbers together
- subtract: Subtract one number from another
- multiply: Multiply two numbers together
- divide: Divide one number by another
```

#### Storing Information in Memory

```
> /remember I prefer window seats on flights
✅ Information stored in memory
```

#### Asking the Agent a Question

```
> What's 42 * 17?

I'll calculate 42 * 17 for you using the multiply tool.

42 * 17 = 714
```

## Configuration

The configuration is stored in `~/.unified_agent/config.json` by default. You can specify a different location using the `--config` option.

### AWS Profiles and Bedrock Integration

The agent integrates with Amazon Bedrock for LLM capabilities and supports AWS profiles for authentication. You can:

1. Set the AWS profile in the configuration file using the `aws_profile` field
2. Override the profile using the `--aws-profile` command line option
3. View or change the profile during runtime using the `/aws-profile` command

The agent uses Amazon Bedrock's Claude 3.7 Sonnet model by default. When an AWS profile is specified, the agent creates a boto3 session with that profile and passes it to the BedrockModel, which handles the authentication with Amazon Bedrock.

If you encounter "ExpiredTokenException" errors, you can refresh your AWS credentials or switch to a different profile.

Example configuration:

```json
{
  "name": "My Agent",
  "system_prompt": "You are a helpful assistant with access to various tools and memory capabilities.",
  "mcp_servers": [
    {
      "name": "calculator",
      "url": "http://localhost:8000/mcp",
      "server_type": "sse",
      "enabled": true
    }
  ],
  "memory": {
    "enabled": true,
    "user_id": "user123",
    "memory_type": "mem0"
  },
  "http_enabled": true,
  "aws_profile": "default"
}
```

## Development

### Running Tests

```
python -m pytest
```

### Project Structure

```
unified_agent/
├── __init__.py
├── main.py                  # Entry point
├── models.py                # Data models and interfaces
├── agent_manager.py         # Agent management
├── cli_interface.py         # CLI interface
├── command_registry.py      # Command registry
├── commands.py              # Command implementations
├── config_manager.py        # Configuration management
├── mcp_connector.py         # MCP server connection
├── memory_handler.py        # Memory operations
└── tests/                   # Test suite
```

## License

MIT
