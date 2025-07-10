"""Tests for token counting in model providers."""
import sys
import pytest
from unittest.mock import patch, MagicMock

from custom_components.cortex_agent.model_provider import (
    ModelProvider,
    OpenAIModelProvider,
    BedrockModelProvider,
    AnthropicModelProvider,
    LiteLLMModelProvider,
)


class TestTokenCounting:
    """Test token counting in model providers."""

    async def test_openai_count_tokens(self):
        """Test OpenAI token counting."""
        provider = OpenAIModelProvider({"provider": "openai", "api_key": "test", "model_id": "gpt-4o"})
        
        # Create a mock tiktoken module
        mock_tiktoken = MagicMock()
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_tiktoken.encoding_for_model.return_value = mock_encoding
        
        # Patch the sys.modules to include our mock tiktoken
        with patch.dict(sys.modules, {'tiktoken': mock_tiktoken}):
            text = "This is a test message"
            token_count = await provider.count_tokens(text)
            
            assert token_count == 5
            mock_tiktoken.encoding_for_model.assert_called_once_with("gpt-4o")

    async def test_anthropic_count_tokens(self):
        """Test Anthropic token counting."""
        provider = AnthropicModelProvider({"provider": "anthropic", "api_key": "test", "model_id": "claude-3-7-sonnet-20250219"})
        
        # Create a mock anthropic module
        mock_anthropic = MagicMock()
        mock_client = MagicMock()
        mock_client.count_tokens.return_value = 5
        mock_anthropic.Anthropic.return_value = mock_client
        
        # Patch the sys.modules to include our mock anthropic
        with patch.dict(sys.modules, {'anthropic': mock_anthropic}):
            text = "This is a test message"
            token_count = await provider.count_tokens(text)
            
            assert token_count == 5
            mock_anthropic.Anthropic.assert_called_once_with(api_key="test")
            mock_client.count_tokens.assert_called_once_with(text)

    async def test_bedrock_count_tokens(self):
        """Test Bedrock token counting."""
        provider = BedrockModelProvider({
            "provider": "bedrock",
            "aws_region": "us-west-2",
            "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        })
        
        # Create a mock boto3 module
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_client.count_tokens.return_value = {"tokenCount": 5}
        mock_boto3.client.return_value = mock_client
        
        # Patch the sys.modules to include our mock boto3
        with patch.dict(sys.modules, {'boto3': mock_boto3}):
            text = "This is a test message"
            token_count = await provider.count_tokens(text)
            
            assert token_count == 5
            mock_boto3.client.assert_called_once_with("bedrock-runtime", region_name="us-west-2")
            mock_client.count_tokens.assert_called_once_with(
                modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                contentType="application/json",
                body='{"inputText": "This is a test message"}'
            )

    async def test_litellm_count_tokens(self):
        """Test LiteLLM token counting."""
        provider = LiteLLMModelProvider({
            "provider": "litellm",
            "api_key": "test",
            "model_id": "test-model",
            "base_url": "https://example.com"
        })
        
        # Create a mock litellm module
        mock_litellm = MagicMock()
        mock_litellm.token_counter.return_value = 5
        
        # Patch the sys.modules to include our mock litellm
        with patch.dict(sys.modules, {'litellm': mock_litellm}):
            text = "This is a test message"
            token_count = await provider.count_tokens(text)
            
            assert token_count == 5
            mock_litellm.token_counter.assert_called_once_with(text, "test-model")

    async def test_count_tokens_for_messages(self):
        """Test counting tokens for a list of messages."""
        provider = OpenAIModelProvider({"provider": "openai", "api_key": "test", "model_id": "gpt-4o"})
        
        # Create a mock tiktoken module
        mock_tiktoken = MagicMock()
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_tiktoken.encoding_for_model.return_value = mock_encoding
        
        # Patch the sys.modules to include our mock tiktoken
        with patch.dict(sys.modules, {'tiktoken': mock_tiktoken}):
            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
            
            token_count = await provider.count_tokens_for_messages(messages)
            
            # Each message should be counted separately
            assert mock_tiktoken.encoding_for_model.call_count == 3
            assert token_count == 15  # 5 tokens per message * 3 messages

    async def test_count_tokens_for_messages_with_tools(self):
        """Test counting tokens for messages with tools."""
        provider = OpenAIModelProvider({"provider": "openai", "api_key": "test", "model_id": "gpt-4o"})
        
        # Create a mock tiktoken module
        mock_tiktoken = MagicMock()
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_tiktoken.encoding_for_model.return_value = mock_encoding
        
        # Patch the sys.modules to include our mock tiktoken
        with patch.dict(sys.modules, {'tiktoken': mock_tiktoken}):
            messages = [{"role": "user", "content": "Hello"}]
            tools = [
                {"name": "tool1", "description": "A tool", "parameters": {}},
                {"name": "tool2", "description": "Another tool", "parameters": {}}
            ]
            
            token_count = await provider.count_tokens_for_messages(messages, tools)
            
            # Each message and tool should be counted
            assert mock_tiktoken.encoding_for_model.call_count == 3  # 1 message + 2 tools
            assert token_count == 15  # 5 tokens per item * 3 items

    async def test_count_tokens_empty_text(self):
        """Test counting tokens for empty text."""
        provider = OpenAIModelProvider({"provider": "openai", "api_key": "test", "model_id": "gpt-4o"})
        
        # Create a mock tiktoken module
        mock_tiktoken = MagicMock()
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = []  # 0 tokens
        mock_tiktoken.encoding_for_model.return_value = mock_encoding
        
        # Patch the sys.modules to include our mock tiktoken
        with patch.dict(sys.modules, {'tiktoken': mock_tiktoken}):
            token_count = await provider.count_tokens("")
            
            assert token_count == 0