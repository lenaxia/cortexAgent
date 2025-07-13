"""Built-in tools for CortexAgent."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


def register_built_in_tools(tool_registry: Any) -> None:
    """Register built-in tools with the tool registry."""
    tool_registry.register_tool(
        name="ha_get_state",
        description="Get the state of one or more entities",
        function=ha_get_state,
        parameters={
            "entity_id": {
                "type": "string",
                "description": "Entity ID to get state for (optional)",
            },
            "domain": {
                "type": "string",
                "description": "Domain to get states for (optional)",
            },
        },
        category="home_assistant",
    )

    tool_registry.register_tool(
        name="ha_set_state",
        description="Set the state of an entity",
        function=ha_set_state,
        parameters={
            "entity_id": {
                "type": "string",
                "description": "Entity ID to set state for",
                "required": True,
            },
            "state": {
                "type": "string",
                "description": "State to set",
                "required": True,
            },
            "attributes": {
                "type": "object",
                "description": "Attributes to set (optional)",
            },
        },
        category="home_assistant",
    )

    tool_registry.register_tool(
        name="ha_call_service",
        description="Call a Home Assistant service",
        function=ha_call_service,
        parameters={
            "domain": {
                "type": "string",
                "description": "Domain of the service",
                "required": True,
            },
            "service": {
                "type": "string",
                "description": "Service to call",
                "required": True,
            },
            "service_data": {
                "type": "object",
                "description": "Service data (optional)",
            },
        },
        category="home_assistant",
    )

    tool_registry.register_tool(
        name="ha_get_entities",
        description="Get a list of entities",
        function=ha_get_entities,
        parameters={
            "domain": {
                "type": "string",
                "description": "Domain to filter entities by (optional)",
            },
        },
        category="home_assistant",
    )

    tool_registry.register_tool(
        name="ha_get_services",
        description="Get available services",
        function=ha_get_services,
        parameters={
            "domain": {
                "type": "string",
                "description": "Domain to filter services by (optional)",
            },
        },
        category="home_assistant",
    )


async def ha_get_state(
    hass: HomeAssistant,
    entity_id: str | None = None,
    domain: str | None = None
) -> dict[str, Any]:
    """Get the state of one or more entities.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to get state for (optional)
        domain: Domain to get states for (optional)

    Returns:
        Dictionary of entity states
    """
    result = {}

    # Get state for a specific entity
    if entity_id:
        state = hass.states.get(entity_id)
        if state:
            result[entity_id] = {
                "state": state.state,
                "attributes": dict(state.attributes),
                "last_updated": state.last_updated.isoformat(),
            }
        else:
            result[entity_id] = {}
        return result

    # Get states for a domain or all states
    states = hass.states.async_all(domain)
    for state in states:
        result[state.entity_id] = {
            "state": state.state,
            "attributes": dict(state.attributes),
            "last_updated": state.last_updated.isoformat(),
        }

    return result


async def ha_set_state(
    hass: HomeAssistant,
    entity_id: str,
    state: str,
    attributes: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Set the state of an entity.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to set state for
        state: State to set
        attributes: Attributes to set (optional)

    Returns:
        Dictionary with result information
    """
    # Set state and handle exceptions
    try:
        # Call async_set without awaiting the result
        hass.states.async_set(entity_id, state, attributes or {})
    except (ValueError, TypeError, KeyError) as ex:
        # Error case
        _LOGGER.error("Error setting state: %s", ex)
        return {
            "success": False,
            "entity_id": entity_id,
            "error": str(ex),
        }

    # Success case
    return {
        "success": True,
        "entity_id": entity_id,
        "state": state,
    }


async def ha_call_service(
    hass: HomeAssistant,
    domain: str,
    service: str,
    service_data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Call a Home Assistant service.

    Args:
        hass: Home Assistant instance
        domain: Domain of the service
        service: Service to call
        service_data: Service data (optional)

    Returns:
        Dictionary with result information
    """
    try:
        await hass.services.async_call(
            domain,
            service,
            service_data or {},
            blocking=True
        )
    except (ValueError, TypeError, KeyError, HomeAssistantError) as ex:
        _LOGGER.error("Error calling service: %s", ex)
        return {
            "success": False,
            "domain": domain,
            "service": service,
            "error": str(ex),
        }

    return {
        "success": True,
        "domain": domain,
        "service": service,
    }


async def ha_get_entities(
    hass: HomeAssistant,
    domain: str | None = None
) -> list[dict[str, Any]]:
    """Get a list of entities.

    Args:
        hass: Home Assistant instance
        domain: Domain to filter entities by (optional)

    Returns:
        List of entities
    """
    states = hass.states.async_all(domain)
    return [
        {
            "entity_id": state.entity_id,
            "state": state.state,
            "attributes": dict(state.attributes),
        }
        for state in states
    ]


async def ha_get_services(
    hass: HomeAssistant,
    domain: str | None = None
) -> dict[str, Any]:
    """Get available services.

    Args:
        hass: Home Assistant instance
        domain: Domain to filter services by (optional)

    Returns:
        Dictionary of services
    """
    # Get services and handle the case where it might return a dict directly
    services_result = hass.services.async_services()
    if hasattr(services_result, "__await__"):
        services = await services_result
    else:
        services = services_result

    result: dict[str, Any] = {}
    if domain:
        result = {domain: services.get(domain, {})}
    else:
        result = services

    return result
