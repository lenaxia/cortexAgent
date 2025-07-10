"""Test the Cortex Agent constants."""
from custom_components.cortex_agent import const

def test_domain_constants():
    """Test domain and naming constants."""
    assert const.DOMAIN == "cortex_agent"
    assert const.DEFAULT_NAME == "Cortex Agent"

def test_configuration_constants():
    """Test configuration key constants."""
    assert const.CONF_PROVIDER == "provider"
    assert const.CONF_MODEL_ID == "model_id"
    assert const.CONF_API_KEY == "api_key"
    assert const.CONF_SYSTEM_PROMPT == "system_prompt"
    assert const.CONF_MAX_TOKENS == "max_tokens"
    assert const.CONF_TEMPERATURE == "temperature"
    assert const.CONF_MEMORY_ENABLED == "memory_enabled"
    assert const.CONF_MCP_SERVERS == "mcp_servers"
    assert const.CONF_CUSTOM_TOOLS == "custom_tools"

def test_default_values():
    """Test default value constants."""
    assert const.DEFAULT_SYSTEM_PROMPT == "You are a helpful AI assistant integrated with Home Assistant."
    assert const.DEFAULT_MAX_TOKENS == 1500
    assert const.DEFAULT_TEMPERATURE == 0.7

def test_model_providers():
    """Test model provider constants."""
    assert const.PROVIDER_OPENAI == "openai"
    assert const.PROVIDER_ANTHROPIC == "anthropic"
    assert const.PROVIDER_BEDROCK == "bedrock"
    assert const.PROVIDER_LITELLM == "litellm"
    assert len(const.PROVIDERS) == 4
    assert all(provider in const.PROVIDERS for provider in [
        const.PROVIDER_OPENAI,
        const.PROVIDER_ANTHROPIC,
        const.PROVIDER_BEDROCK,
        const.PROVIDER_LITELLM
    ])

def test_service_constants():
    """Test service name constants."""
    assert const.SERVICE_RELOAD == "reload"
    assert const.SERVICE_CONNECT_MCP_SERVER == "connect_mcp_server"
    assert const.SERVICE_DISCONNECT_MCP_SERVER == "disconnect_mcp_server"
    assert const.SERVICE_ADD_TOOL == "add_tool"
    assert const.SERVICE_REMOVE_TOOL == "remove_tool"
    assert const.SERVICE_CLEAR_CONVERSATION == "clear_conversation"

def test_storage_constants():
    """Test storage-related constants."""
    assert const.STORAGE_VERSION == 1
    assert const.STORAGE_KEY == "cortex_agent.storage"
    assert const.STORAGE_KEY_CONVERSATIONS == "cortex_agent.conversations"
