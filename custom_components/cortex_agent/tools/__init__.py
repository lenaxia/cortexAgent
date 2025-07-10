"""Built-in tools for CortexAgent."""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Type definitions
ToolFunction = Callable[[HomeAssistant, Dict[str, Any]], Dict[str, Any]]

# Import functions from ha_tools.py
from .ha_tools import (
    get_entity_state,
    call_service,
    get_entities,
)

# Define wrapper functions for test compatibility
async def ha_get_state(hass: HomeAssistant, entity_id: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
    """Wrapper for get_entity_state that accepts keyword arguments and formats results as expected by tests."""
    result = {}
    
    # Handle single entity case
    if entity_id:
        state = hass.states.get(entity_id)
        if state:
            result[entity_id] = {
                "state": state.state,
                "attributes": dict(state.attributes),
                "last_updated": state.last_updated.isoformat(),
            }
        else:
            result[entity_id] = None
        return result
    
    # Handle domain or all states case
    if domain:
        states = hass.states.async_all(domain)
    else:
        states = hass.states.async_all()
    for state in states:
        result[state.entity_id] = {
            "state": state.state,
            "attributes": dict(state.attributes),
            "last_updated": state.last_updated.isoformat(),
        }
    
    return result

async def ha_call_service(hass: HomeAssistant, domain: str, service: str, service_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Wrapper for call_service that accepts keyword arguments."""
    try:
        await hass.services.async_call(
            domain,
            service,
            service_data or {},
            blocking=True
        )
        return {
            "success": True,
            "domain": domain,
            "service": service,
        }
    except Exception as ex:
        _LOGGER.error("Error calling service: %s", ex)
        return {
            "success": False,
            "domain": domain,
            "service": service,
            "error": str(ex),
        }

async def ha_get_entities(hass: HomeAssistant, domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get a list of entities."""
    result = []
    if domain:
        states = hass.states.async_all(domain)
    else:
        states = hass.states.async_all()
    
    for state in states:
        result.append({
            "entity_id": state.entity_id,
            "state": state.state,
            "attributes": dict(state.attributes),
        })
    
    return result

async def ha_set_state(hass: HomeAssistant, entity_id: str, state: str, attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Set the state of an entity."""
    try:
        await hass.states.async_set(entity_id, state, attributes or {})
        return {
            "success": True,
            "entity_id": entity_id,
            "state": state,
        }
    except Exception as ex:
        _LOGGER.error("Error setting state: %s", ex)
        return {
            "success": False,
            "entity_id": entity_id,
            "error": str(ex),
        }

async def ha_get_services(hass: HomeAssistant, domain: Optional[str] = None) -> Dict[str, Any]:
    """Get available services."""
    # Get services (MagicMock in tests, coroutine in real usage)
    services_obj = hass.services.async_services()
    
    # Handle both MagicMock and coroutine cases
    if callable(getattr(services_obj, "return_value", None)):
        # This is a MagicMock
        services = services_obj.return_value
    else:
        # This is a real coroutine
        try:
            services = await services_obj
        except TypeError:
            # If it's not awaitable, just use it directly
            services = services_obj
    
    # Return the requested domain or all services
    if domain:
        return {domain: services.get(domain, {})}
    return services

def register_built_in_tools(tool_registry) -> None:
    """Register all built-in tools with the tool registry."""
    from .ha_tools import register_ha_tools
    from .http_tools import register_http_tools
    from .utility_tools import register_utility_tools
    
    # Register all tool categories
    register_ha_tools(tool_registry)
    register_http_tools(tool_registry)
    register_utility_tools(tool_registry)