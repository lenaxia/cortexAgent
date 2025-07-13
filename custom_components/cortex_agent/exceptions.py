"""Exceptions for the CortexAgent integration."""
from __future__ import annotations


class CortexAgentError(Exception):
    """Base exception for Cortex Agent."""


class ModelProviderError(CortexAgentError):
    """Model provider error."""


class APIRateLimitError(ModelProviderError):
    """API rate limit exceeded."""

    def __init__(self, provider: str, retry_after: int | None = None):
        """Initialize the exception.

        Args:
            provider: The provider name
            retry_after: Seconds to wait before retrying
        """
        self.provider = provider
        self.retry_after = retry_after
        super().__init__(
            f"{provider} rate limit exceeded. Retry after {retry_after or 'unknown'} seconds."
        )


class AuthenticationError(ModelProviderError):
    """Authentication failed."""


class NetworkError(CortexAgentError):
    """Network communication error."""

    def __init__(self, message: str, is_temporary: bool = True):
        """Initialize the exception.

        Args:
            message: Error message
            is_temporary: Whether the error is temporary
        """
        self.is_temporary = is_temporary
        super().__init__(message)


class ToolExecutionError(CortexAgentError):
    """Tool execution error."""

    def __init__(self, tool_name: str, message: str):
        """Initialize the exception.

        Args:
            tool_name: Name of the tool
            message: Error message
        """
        self.tool_name = tool_name
        super().__init__(f"Error executing tool '{tool_name}': {message}")


class MemoryOperationError(CortexAgentError):
    """Memory operation error."""


# Alias for backward compatibility
CortexMemoryError = MemoryOperationError


class ConfigurationError(CortexAgentError):
    """Configuration error."""
