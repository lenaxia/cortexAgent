"""Constants for the CortexAgent integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "cortex_agent"
DEFAULT_NAME: Final = "Cortex Agent"

# Configuration keys
CONF_PROVIDER: Final = "provider"
CONF_MODEL_ID: Final = "model_id"
CONF_API_KEY: Final = "api_key"
CONF_SYSTEM_PROMPT: Final = "system_prompt"
CONF_MAX_TOKENS: Final = "max_tokens"
CONF_TEMPERATURE: Final = "temperature"
CONF_USE_STRANDS_AGENT: Final = "use_strands_agent"
CONF_MEMORY_ENABLED: Final = "memory_enabled"
CONF_MCP_SERVERS: Final = "mcp_servers"
CONF_CUSTOM_TOOLS: Final = "custom_tools"
CONF_LISTEN_EVENTS: Final = "listen_events"
CONF_LISTEN_STATES: Final = "listen_states"
CONF_TIME_PATTERNS: Final = "time_patterns"
CONF_EVENTS: Final = "events"

# Additional provider-specific config keys
CONF_ORG_ID: Final = "org_id"
CONF_AWS_PROFILE: Final = "aws_profile"
CONF_AWS_REGION: Final = "aws_region"
CONF_BASE_URL: Final = "base_url"

# Default values
DEFAULT_SYSTEM_PROMPT: Final = "You are a helpful AI assistant integrated with Home Assistant."
DEFAULT_MAX_TOKENS: Final = 1500
DEFAULT_TEMPERATURE: Final = 0.7
DEFAULT_USE_STRANDS_AGENT: Final = False

# Model providers
PROVIDER_OPENAI: Final = "openai"
PROVIDER_ANTHROPIC: Final = "anthropic"
PROVIDER_BEDROCK: Final = "bedrock"
PROVIDER_LITELLM: Final = "litellm"

PROVIDERS: Final = [
    PROVIDER_OPENAI,
    PROVIDER_ANTHROPIC,
    PROVIDER_BEDROCK,
    PROVIDER_LITELLM
]

# Model validation
MODEL_VALIDATORS: Final = {
    PROVIDER_OPENAI: {
        "models": [
            "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"
        ],
        "max_tokens_range": (1, 4096),
        "temperature_range": (0, 1)
    },
    PROVIDER_BEDROCK: {
        "models": [
            "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
            "us.anthropic.claude-3-haiku-20240307-v1:0"
        ],
        "max_tokens_range": (1, 4096),
        "temperature_range": (0, 1)
    },
    PROVIDER_ANTHROPIC: {
        "models": [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20240620",
            "claude-3-haiku-20240307"
        ],
        "max_tokens_range": (1, 4096),
        "temperature_range": (0, 1)
    },
    PROVIDER_LITELLM: {
        "models": [],  # Any string is allowed for custom endpoints
        "max_tokens_range": (1, 8192),
        "temperature_range": (0, 2)
    }
}

# Services
SERVICE_RELOAD: Final = "reload"
SERVICE_CONNECT_MCP_SERVER: Final = "connect_mcp_server"
SERVICE_DISCONNECT_MCP_SERVER: Final = "disconnect_mcp_server"
SERVICE_ADD_TOOL: Final = "add_tool"
SERVICE_REMOVE_TOOL: Final = "remove_tool"
SERVICE_CLEAR_CONVERSATION: Final = "clear_conversation"
SERVICE_GET_METRICS: Final = "get_agent_metrics"
SERVICE_RESET_METRICS: Final = "reset_agent_metrics"
SERVICE_GENERATE_DOCS: Final = "generate_tool_documentation"

# Data storage
STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = f"{DOMAIN}.storage"
STORAGE_KEY_CONVERSATIONS: Final = f"{DOMAIN}.conversations"
STORAGE_KEY_TEMPLATE: Final = f"{DOMAIN}.{{user_id}}"

# Data keys
DATA_AGENT: Final = "agent"
DATA_COORDINATOR: Final = "coordinator"

# Attribute names
ATTR_ENTITY_ID: Final = "entity_id"
ATTR_CONVERSATION_ID: Final = "conversation_id"
ATTR_FORMAT: Final = "format"
ATTR_AUTH_TOKEN: Final = "auth_token"
ATTR_NAME: Final = "name"
ATTR_SERVER_TYPE: Final = "server_type"
ATTR_URL: Final = "url"

# MCP Server types
SERVER_TYPE_SSE: Final = "sse"
SERVER_TYPE_STREAMABLE_HTTP: Final = "streamable_http"
SERVER_TYPE_STDIO: Final = "stdio"