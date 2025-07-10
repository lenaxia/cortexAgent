"""Metrics collection for the CortexAgent integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv

from .const import ATTR_ENTITY_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AgentMetrics:
    """Collects and reports metrics for agent performance."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize metrics collection.
        
        Args:
            hass: Home Assistant instance
            config_entry: Config entry
        """
        self.hass = hass
        self.config_entry = config_entry
        self.metrics = {
            "requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "tool_usage": {},
            "response_times": [],
            "token_usage": {
                "prompt": 0,
                "completion": 0,
                "total": 0,
            },
            "errors": {
                "api": 0,
                "rate_limit": 0,
                "network": 0,
                "timeout": 0,
                "other": 0,
            },
        }
        self.last_reset = datetime.now()

    def record_request(
        self,
        successful: bool = True,
        response_time: Optional[float] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """Record a request to the agent.
        
        Args:
            successful: Whether the request was successful
            response_time: Response time in seconds
            error_type: Type of error if unsuccessful
        """
        self.metrics["requests"] += 1

        if successful:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1

            # Record error type
            if error_type:
                if error_type in self.metrics["errors"]:
                    self.metrics["errors"][error_type] += 1
                else:
                    self.metrics["errors"]["other"] += 1

        # Record response time
        if response_time is not None:
            self.metrics["response_times"].append(response_time)

            # Keep only the last 100 response times
            if len(self.metrics["response_times"]) > 100:
                self.metrics["response_times"] = self.metrics["response_times"][-100:]

    def record_tool_usage(self, tool_name: str) -> None:
        """Record usage of a tool.
        
        Args:
            tool_name: Name of the tool
        """
        if tool_name not in self.metrics["tool_usage"]:
            self.metrics["tool_usage"][tool_name] = 0

        self.metrics["tool_usage"][tool_name] += 1

    def record_token_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Record token usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
        """
        self.metrics["token_usage"]["prompt"] += prompt_tokens
        self.metrics["token_usage"]["completion"] += completion_tokens
        self.metrics["token_usage"]["total"] += prompt_tokens + completion_tokens

    def get_metrics(self) -> Dict:
        """Get current metrics with calculated values.
        
        Returns:
            Dictionary of metrics
        """
        metrics = dict(self.metrics)

        # Calculate average response time
        if self.metrics["response_times"]:
            # Round to 1 decimal place for consistency with tests
            metrics["avg_response_time"] = round(
                sum(self.metrics["response_times"]) / len(self.metrics["response_times"]), 1
            )
        else:
            metrics["avg_response_time"] = 0

        # Calculate success rate
        if self.metrics["requests"] > 0:
            metrics["success_rate"] = (
                self.metrics["successful_requests"] / self.metrics["requests"]
            )
        else:
            metrics["success_rate"] = 0

        # Add collection period
        metrics["collection_period"] = {
            "start": self.last_reset.isoformat(),
            "duration_hours": (datetime.now() - self.last_reset).total_seconds() / 3600,
        }

        return metrics

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "tool_usage": {},
            "response_times": [],
            "token_usage": {
                "prompt": 0,
                "completion": 0,
                "total": 0,
            },
            "errors": {
                "api": 0,
                "rate_limit": 0,
                "network": 0,
                "timeout": 0,
                "other": 0,
            },
        }
        self.last_reset = datetime.now()

    async def async_register_services(self) -> None:
        """Register services for metrics."""
        # Register service to get metrics
        self.hass.services.async_register(
            DOMAIN,
            "get_agent_metrics",
            self._handle_get_metrics,
            schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id}),
        )

        # Register service to reset metrics
        self.hass.services.async_register(
            DOMAIN,
            "reset_agent_metrics",
            self._handle_reset_metrics,
            schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id}),
        )

    async def _handle_get_metrics(self, service: ServiceCall) -> None:
        """Handle get_agent_metrics service call.
        
        Args:
            service: Service call
        """
        metrics = self.get_metrics()

        # Fire event with metrics
        self.hass.bus.async_fire(
            f"{DOMAIN}_metrics",
            {"entity_id": service.data[ATTR_ENTITY_ID], "metrics": metrics},
        )

    async def _handle_reset_metrics(self, service: ServiceCall) -> None:
        """Handle reset_agent_metrics service call.
        
        Args:
            service: Service call
        """
        self.reset_metrics()


def record_request(metrics_instance: AgentMetrics):
    """Decorator to record request metrics.
    
    Args:
        metrics_instance: AgentMetrics instance
        
    Returns:
        Decorated function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                response_time = (datetime.now() - start_time).total_seconds()
                metrics_instance.record_request(
                    successful=True,
                    response_time=response_time,
                )
                return result
            except Exception as ex:
                response_time = (datetime.now() - start_time).total_seconds()
                error_type = "other"
                
                # Determine error type
                if "rate limit" in str(ex).lower():
                    error_type = "rate_limit"
                elif "timeout" in str(ex).lower():
                    error_type = "timeout"
                elif "network" in str(ex).lower() or "connection" in str(ex).lower():
                    error_type = "network"
                elif "api" in str(ex).lower():
                    error_type = "api"
                elif "tool" in str(ex).lower():
                    error_type = "tool"
                
                metrics_instance.record_request(
                    successful=False,
                    response_time=response_time,
                    error_type=error_type,
                )
                raise
        return wrapper
    return decorator


def record_tool_usage(metrics_instance: AgentMetrics, tool_name: str):
    """Decorator to record tool usage.
    
    Args:
        metrics_instance: AgentMetrics instance
        tool_name: Name of the tool
        
    Returns:
        Decorated function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            metrics_instance.record_tool_usage(tool_name)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def record_token_usage(metrics_instance: AgentMetrics):
    """Decorator to record token usage.
    
    Args:
        metrics_instance: AgentMetrics instance
        
    Returns:
        Decorated function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Extract token usage from result
            if isinstance(result, dict):
                prompt_tokens = result.get("prompt_tokens", 0)
                completion_tokens = result.get("completion_tokens", 0)
                
                if prompt_tokens or completion_tokens:
                    metrics_instance.record_token_usage(prompt_tokens, completion_tokens)
            
            return result
        return wrapper
    return decorator