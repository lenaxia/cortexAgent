"""Home Assistant tools for CortexAgent."""
from __future__ import annotations

import logging
from typing import Any, TypeVar

from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceNotFound, TemplateError
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


def register_ha_tools(tool_registry: Any) -> None:
    """Register Home Assistant tools with the tool registry."""
    # Entity tools
    tool_registry.register_tool(
        name="get_entity_state",
        description="Get the current state of a Home Assistant entity",
        function=get_entity_state,
        parameters={
            "entity_id": {
                "type": "string",
                "description": "The entity ID to get the state for",
            },
        },
        category="home_assistant",
    )

    tool_registry.register_tool(
        name="call_service",
        description="Call a Home Assistant service",
        function=call_service,
        parameters={
            "domain": {
                "type": "string",
                "description": "The domain of the service to call",
            },
            "service": {
                "type": "string",
                "description": "The service to call",
            },
            "service_data": {
                "type": "object",
                "description": "The data to pass to the service",
            },
            "target": {
                "type": "object",
                "description": "The target for the service call (entity_id, device_id, or area_id)",
            },
        },
        category="home_assistant",
    )

    tool_registry.register_tool(
        name="get_entities",
        description="Get a list of entities matching a filter",
        function=get_entities,
        parameters={
            "domain": {
                "type": "string",
                "description": "Filter entities by domain (e.g., light, switch)",
            },
            "area": {
                "type": "string",
                "description": "Filter entities by area name",
            },
            "device": {
                "type": "string",
                "description": "Filter entities by device name",
            },
        },
        category="home_assistant",
    )

    tool_registry.register_tool(
        name="render_template",
        description="Render a Home Assistant template",
        function=render_template,
        parameters={
            "template": {
                "type": "string",
                "description": "The template to render",
            },
        },
        category="home_assistant",
    )

    # Domain-specific tools
    tool_registry.register_tool(
        name="turn_on_light",
        description="Turn on a light with specific attributes",
        function=turn_on_light,
        parameters={
            "entity_id": {
                "type": "string",
                "description": "The light entity ID",
            },
            "brightness": {
                "type": "integer",
                "description": "Brightness level (0-255)",
            },
            "color_name": {
                "type": "string",
                "description": "Color name (e.g., red, green, blue)",
            },
            "rgb_color": {
                "type": "array",
                "description": "RGB color as [r, g, b] with values 0-255",
            },
            "color_temp": {
                "type": "integer",
                "description": "Color temperature in mireds",
            },
        },
        category="home_assistant",
    )

    tool_registry.register_tool(
        name="set_climate",
        description="Set climate device parameters",
        function=set_climate,
        parameters={
            "entity_id": {
                "type": "string",
                "description": "The climate entity ID",
            },
            "temperature": {
                "type": "number",
                "description": "Target temperature",
            },
            "hvac_mode": {
                "type": "string",
                "description": "HVAC mode (e.g., heat, cool, auto, off)",
            },
            "preset_mode": {
                "type": "string",
                "description": "Preset mode (e.g., home, away, eco)",
            },
        },
        category="home_assistant",
    )


async def get_entity_state(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Get the state of a Home Assistant entity."""
    if not (entity_id := args.get("entity_id")):
        return {"error": "entity_id is required"}

    if not (state := hass.states.get(entity_id)):
        return {"error": f"Entity {entity_id} not found"}

    return {
        "entity_id": entity_id,
        "state": state.state,
        "attributes": dict(state.attributes),
        "last_updated": state.last_updated.isoformat(),
        "last_changed": state.last_changed.isoformat(),
    }


async def call_service(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Call a Home Assistant service."""
    domain = args.get("domain")
    service = args.get("service")
    service_data = args.get("service_data", {})
    target = args.get("target", {})

    if not domain:
        return {"error": "domain is required"}

    if not service:
        return {"error": "service is required"}

    try:
        await hass.services.async_call(
            domain=domain,
            service=service,
            service_data=service_data,
            target=target,
            blocking=True,
            context=Context(),
        )
    except ServiceNotFound as ex:
        _LOGGER.error("Service %s.%s not found: %s", domain, service, ex)
        return {
            "error": f"Service {domain}.{service} not found: {ex!s}",
        }
    except HomeAssistantError as ex:
        _LOGGER.error("Error calling service %s.%s: %s", domain, service, ex)
        return {
            "error": f"Error calling service {domain}.{service}: {ex!s}",
        }

    return {
        "success": True,
        "domain": domain,
        "service": service,
        "service_data": service_data,
        "target": target,
    }


async def get_entities(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Get a list of entities matching a filter."""
    domain = args.get("domain")
    area_name = args.get("area")
    device_name = args.get("device")

    # Get registries
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    area_registry = ar.async_get(hass)

    # Filter by area if specified
    area_id = None
    if area_name:
        for area in area_registry.areas.values():
            if area.name.lower() == area_name.lower():
                area_id = area.id
                break

        if not area_id:
            return {"error": f"Area '{area_name}' not found"}

    # Filter by device if specified
    device_id = None
    if device_name:
        for device in device_registry.devices.values():
            if device.name and device.name.lower() == device_name.lower():
                device_id = device.id
                break

        if not device_id:
            return {"error": f"Device '{device_name}' not found"}

    # Filter entities
    entities = []
    for entity_entry in entity_registry.entities.values():
        # Skip disabled entities
        if entity_entry.disabled:
            continue

        # Filter by domain
        if domain and not entity_entry.entity_id.startswith(f"{domain}."):
            continue

        # Filter by device
        if device_id and entity_entry.device_id != device_id:
            continue

        # Filter by area
        if area_id:
            entity_area_id = entity_entry.area_id
            if not entity_area_id and entity_entry.device_id:
                device: DeviceEntry | None = device_registry.async_get(entity_entry.device_id)
                if device is not None:
                    entity_area_id = device.area_id

            if entity_area_id != area_id:
                continue

        # Get state
        if not (state := hass.states.get(entity_entry.entity_id)):
            continue

        # Add entity to results
        entities.append({
            "entity_id": entity_entry.entity_id,
            "name": entity_entry.name or state.name,
            "state": state.state,
            "domain": entity_entry.domain,
            "device_id": entity_entry.device_id,
            "area_id": entity_entry.area_id,
        })

    return {
        "entities": entities,
        "count": len(entities),
    }


async def render_template(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Render a Home Assistant template."""
    if not (template_str := args.get("template")):
        return {"error": "template is required"}

    try:
        template = Template(template_str, hass)
        result = template.async_render()
    except TemplateError as ex:
        _LOGGER.error("Error rendering template: %s", ex)
        return {
            "error": f"Error rendering template: {ex!s}",
        }

    return {
        "result": result,
    }


async def turn_on_light(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Turn on a light with specific attributes."""
    if not (entity_id := args.get("entity_id")):
        return {"error": "entity_id is required"}

    # Check if entity exists and is a light
    if not hass.states.get(entity_id):
        return {"error": f"Entity {entity_id} not found"}

    if not entity_id.startswith("light."):
        return {"error": f"Entity {entity_id} is not a light"}

    # Prepare service data
    service_data = {"entity_id": entity_id}

    # Add optional parameters
    if "brightness" in args:
        service_data["brightness"] = args["brightness"]

    if "color_name" in args:
        service_data["color_name"] = args["color_name"]

    if "rgb_color" in args:
        service_data["rgb_color"] = args["rgb_color"]

    if "color_temp" in args:
        service_data["color_temp"] = args["color_temp"]

    try:
        await hass.services.async_call(
            domain="light",
            service="turn_on",
            service_data=service_data,
            blocking=True,
            context=Context(),
        )

        # Get updated state
        if not (updated_state := hass.states.get(entity_id)):
            return {
                "error": f"Failed to get updated state for {entity_id}",
            }
    except ServiceNotFound as ex:
        _LOGGER.error("Light service not found: %s", ex)
        return {
            "error": f"Light service not found: {ex!s}",
        }
    except HomeAssistantError as ex:
        _LOGGER.error("Error turning on light %s: %s", entity_id, ex)
        return {
            "error": f"Error turning on light {entity_id}: {ex!s}",
        }

    return {
        "success": True,
        "entity_id": entity_id,
        "state": updated_state.state,
        "attributes": dict(updated_state.attributes),
    }


async def set_climate(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Set climate device parameters."""
    if not (entity_id := args.get("entity_id")):
        return {"error": "entity_id is required"}

    # Check if entity exists and is a climate device
    if not hass.states.get(entity_id):
        return {"error": f"Entity {entity_id} not found"}

    if not entity_id.startswith("climate."):
        return {"error": f"Entity {entity_id} is not a climate device"}

    # Handle different parameters with separate service calls
    try:
        # Set HVAC mode if specified
        if "hvac_mode" in args:
            await hass.services.async_call(
                domain="climate",
                service="set_hvac_mode",
                service_data={
                    "entity_id": entity_id,
                    "hvac_mode": args["hvac_mode"],
                },
                blocking=True,
                context=Context(),
            )

        # Set temperature if specified
        if "temperature" in args:
            await hass.services.async_call(
                domain="climate",
                service="set_temperature",
                service_data={
                    "entity_id": entity_id,
                    "temperature": args["temperature"],
                },
                blocking=True,
                context=Context(),
            )

        # Set preset mode if specified
        if "preset_mode" in args:
            await hass.services.async_call(
                domain="climate",
                service="set_preset_mode",
                service_data={
                    "entity_id": entity_id,
                    "preset_mode": args["preset_mode"],
                },
                blocking=True,
                context=Context(),
            )

        # Get updated state
        if not (updated_state := hass.states.get(entity_id)):
            return {
                "error": f"Failed to get updated state for {entity_id}",
            }
    except ServiceNotFound as ex:
        _LOGGER.error("Climate service not found: %s", ex)
        return {
            "error": f"Climate service not found: {ex!s}",
        }
    except HomeAssistantError as ex:
        _LOGGER.error("Error setting climate parameters for %s: %s", entity_id, ex)
        return {
            "error": f"Error setting climate parameters for {entity_id}: {ex!s}",
        }
    return {
        "success": True,
        "entity_id": entity_id,
        "state": updated_state.state,
        "attributes": dict(updated_state.attributes),
    }
