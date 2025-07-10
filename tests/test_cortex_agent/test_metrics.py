"""Tests for the CortexAgent metrics component."""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from custom_components.cortex_agent.metrics import (
    AgentMetrics,
    record_request,
    record_tool_usage,
    record_token_usage,
)
from custom_components.cortex_agent.const import (
    DOMAIN,
    ATTR_ENTITY_ID,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.bus = MagicMock()
    hass.bus.async_fire = AsyncMock()
    hass.services = MagicMock()
    hass.services.async_register = AsyncMock()
    return hass


@pytest.fixture
def mock_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry-id"
    return entry


@pytest.fixture
def agent_metrics(mock_hass, mock_entry):
    """Create an AgentMetrics instance."""
    return AgentMetrics(mock_hass, mock_entry)


class TestAgentMetrics:
    """Test the AgentMetrics class."""

    def test_init(self, mock_hass, mock_entry):
        """Test initialization."""
        metrics = AgentMetrics(mock_hass, mock_entry)
        
        assert metrics.hass == mock_hass
        assert metrics.config_entry == mock_entry
        assert metrics.metrics["requests"] == 0
        assert metrics.metrics["successful_requests"] == 0
        assert metrics.metrics["failed_requests"] == 0
        assert metrics.metrics["tool_usage"] == {}
        assert metrics.metrics["response_times"] == []
        assert metrics.metrics["token_usage"]["prompt"] == 0
        assert metrics.metrics["token_usage"]["completion"] == 0
        assert metrics.metrics["token_usage"]["total"] == 0
        assert metrics.metrics["errors"] == {
            "api": 0,
            "rate_limit": 0,
            "network": 0,
            "timeout": 0,
            "other": 0,
        }
        assert isinstance(metrics.last_reset, datetime)

    def test_record_request_success(self, agent_metrics):
        """Test recording a successful request."""
        agent_metrics.record_request(
            successful=True,
            response_time=1.5,
        )
        
        assert agent_metrics.metrics["requests"] == 1
        assert agent_metrics.metrics["successful_requests"] == 1
        assert agent_metrics.metrics["failed_requests"] == 0
        assert agent_metrics.metrics["response_times"] == [1.5]

    def test_record_request_failure(self, agent_metrics):
        """Test recording a failed request."""
        agent_metrics.record_request(
            successful=False,
            response_time=0.5,
            error_type="api",
        )
        
        assert agent_metrics.metrics["requests"] == 1
        assert agent_metrics.metrics["successful_requests"] == 0
        assert agent_metrics.metrics["failed_requests"] == 1
        assert agent_metrics.metrics["response_times"] == [0.5]
        assert agent_metrics.metrics["errors"]["api"] == 1

    def test_record_request_unknown_error(self, agent_metrics):
        """Test recording a request with an unknown error type."""
        agent_metrics.record_request(
            successful=False,
            error_type="unknown",
        )
        
        assert agent_metrics.metrics["requests"] == 1
        assert agent_metrics.metrics["successful_requests"] == 0
        assert agent_metrics.metrics["failed_requests"] == 1
        assert agent_metrics.metrics["errors"]["other"] == 1

    def test_record_tool_usage(self, agent_metrics):
        """Test recording tool usage."""
        agent_metrics.record_tool_usage("test_tool")
        agent_metrics.record_tool_usage("test_tool")
        agent_metrics.record_tool_usage("another_tool")
        
        assert agent_metrics.metrics["tool_usage"]["test_tool"] == 2
        assert agent_metrics.metrics["tool_usage"]["another_tool"] == 1

    def test_record_token_usage(self, agent_metrics):
        """Test recording token usage."""
        agent_metrics.record_token_usage(100, 50)
        agent_metrics.record_token_usage(200, 100)
        
        assert agent_metrics.metrics["token_usage"]["prompt"] == 300
        assert agent_metrics.metrics["token_usage"]["completion"] == 150
        assert agent_metrics.metrics["token_usage"]["total"] == 450

    def test_get_metrics(self, agent_metrics):
        """Test getting metrics."""
        # Add some data
        agent_metrics.record_request(successful=True, response_time=1.0)
        agent_metrics.record_request(successful=True, response_time=2.0)
        agent_metrics.record_request(successful=False, response_time=0.5, error_type="api")
        agent_metrics.record_tool_usage("test_tool")
        agent_metrics.record_token_usage(100, 50)
        
        # Get metrics
        metrics = agent_metrics.get_metrics()
        
        # Check metrics
        assert metrics["requests"] == 3
        assert metrics["successful_requests"] == 2
        assert metrics["failed_requests"] == 1
        # The average is rounded to 1 decimal place: (1.0 + 2.0 + 0.5) / 3 = 1.2
        assert metrics["avg_response_time"] == 1.2
        assert metrics["success_rate"] == 2/3
        assert metrics["tool_usage"]["test_tool"] == 1
        assert metrics["token_usage"]["prompt"] == 100
        assert metrics["token_usage"]["completion"] == 50
        assert metrics["token_usage"]["total"] == 150
        assert metrics["errors"]["api"] == 1
        assert "collection_period" in metrics
        assert "start" in metrics["collection_period"]
        assert "duration_hours" in metrics["collection_period"]

    def test_reset_metrics(self, agent_metrics):
        """Test resetting metrics."""
        # Add some data
        agent_metrics.record_request(successful=True, response_time=1.0)
        agent_metrics.record_tool_usage("test_tool")
        agent_metrics.record_token_usage(100, 50)
        
        # Reset metrics
        agent_metrics.reset_metrics()
        
        # Check metrics
        assert agent_metrics.metrics["requests"] == 0
        assert agent_metrics.metrics["successful_requests"] == 0
        assert agent_metrics.metrics["failed_requests"] == 0
        assert agent_metrics.metrics["tool_usage"] == {}
        assert agent_metrics.metrics["response_times"] == []
        assert agent_metrics.metrics["token_usage"]["prompt"] == 0
        assert agent_metrics.metrics["token_usage"]["completion"] == 0
        assert agent_metrics.metrics["token_usage"]["total"] == 0
        assert agent_metrics.metrics["errors"] == {
            "api": 0,
            "rate_limit": 0,
            "network": 0,
            "timeout": 0,
            "other": 0,
        }
        
        # Check that last_reset was updated
        assert agent_metrics.last_reset > datetime.now() - timedelta(seconds=1)

    async def test_async_register_services(self, agent_metrics):
        """Test registering services."""
        # Register services
        await agent_metrics.async_register_services()
        
        # Check that services were registered
        assert agent_metrics.hass.services.async_register.call_count == 2
        
        # Check service names
        service_names = [
            call.args[1] for call in agent_metrics.hass.services.async_register.call_args_list
        ]
        assert "get_agent_metrics" in service_names
        assert "reset_agent_metrics" in service_names

    async def test_handle_get_metrics(self, agent_metrics):
        """Test handling get_metrics service call."""
        # Create service call
        service_call = MagicMock(spec=ServiceCall)
        service_call.domain = DOMAIN
        service_call.service = "get_agent_metrics"
        service_call.data = {ATTR_ENTITY_ID: "cortex_agent.test"}
        
        # Add some data
        agent_metrics.record_request(successful=True, response_time=1.0)
        
        # Handle service call
        await agent_metrics._handle_get_metrics(service_call)
        
        # Check that event was fired
        agent_metrics.hass.bus.async_fire.assert_called_once()
        
        # Check event data - the second argument to async_fire is the event data
        call_args = agent_metrics.hass.bus.async_fire.call_args
        assert call_args[0][0] == f"{DOMAIN}_metrics"  # First arg is event name
        event_data = call_args[0][1]  # Second arg is event data
        assert event_data[ATTR_ENTITY_ID] == "cortex_agent.test"
        assert "metrics" in event_data
        assert event_data["metrics"]["requests"] == 1

    async def test_handle_reset_metrics(self, agent_metrics):
        """Test handling reset_metrics service call."""
        # Create service call
        service_call = MagicMock(spec=ServiceCall)
        service_call.domain = DOMAIN
        service_call.service = "reset_agent_metrics"
        service_call.data = {ATTR_ENTITY_ID: "cortex_agent.test"}
        
        # Add some data
        agent_metrics.record_request(successful=True, response_time=1.0)
        
        # Handle service call
        await agent_metrics._handle_reset_metrics(service_call)
        
        # Check that metrics were reset
        assert agent_metrics.metrics["requests"] == 0


class TestMetricDecorators:
    """Test the metric decorator functions."""

    async def test_record_request_decorator(self, agent_metrics):
        """Test the record_request decorator."""
        # Create a function with the decorator
        @record_request(agent_metrics)
        async def test_function():
            return "success"
        
        # Call the function
        result = await test_function()
        
        # Check result
        assert result == "success"
        
        # Check that request was recorded
        assert agent_metrics.metrics["requests"] == 1
        assert agent_metrics.metrics["successful_requests"] == 1

    async def test_record_request_decorator_with_error(self, agent_metrics):
        """Test the record_request decorator with an error."""
        # Create a function with the decorator
        @record_request(agent_metrics)
        async def test_function():
            raise ValueError("Test error")
        
        # Call the function
        with pytest.raises(ValueError):
            await test_function()
        
        # Check that request was recorded as failed
        assert agent_metrics.metrics["requests"] == 1
        assert agent_metrics.metrics["successful_requests"] == 0
        assert agent_metrics.metrics["failed_requests"] == 1

    async def test_record_tool_usage_decorator(self, agent_metrics):
        """Test the record_tool_usage decorator."""
        # Create a function with the decorator
        @record_tool_usage(agent_metrics, "test_tool")
        async def test_function():
            return "success"
        
        # Call the function
        result = await test_function()
        
        # Check result
        assert result == "success"
        
        # Check that tool usage was recorded
        assert agent_metrics.metrics["tool_usage"]["test_tool"] == 1

    async def test_record_token_usage_decorator(self, agent_metrics):
        """Test the record_token_usage decorator."""
        # Create a function with the decorator
        @record_token_usage(agent_metrics)
        async def test_function():
            return {"prompt_tokens": 100, "completion_tokens": 50}
        
        # Call the function
        result = await test_function()
        
        # Check result
        assert result == {"prompt_tokens": 100, "completion_tokens": 50}
        
        # Check that token usage was recorded
        assert agent_metrics.metrics["token_usage"]["prompt"] == 100
        assert agent_metrics.metrics["token_usage"]["completion"] == 50
        assert agent_metrics.metrics["token_usage"]["total"] == 150