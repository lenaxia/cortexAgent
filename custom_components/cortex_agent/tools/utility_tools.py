"""Utility tools for CortexAgent."""
from __future__ import annotations

import json
import logging
import random
import re
import string
from typing import Any
import uuid

from custom_components.cortex_agent.models import ToolMetadata
from custom_components.cortex_agent.tool_registry import ToolRegistry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


def register_utility_tools(tool_registry: ToolRegistry) -> None:
    """Register utility tools with the tool registry."""
    tool_registry.register_tool(
        tool_id="get_current_time",
        tool_fn=get_current_time,
        metadata=ToolMetadata(
            name="get_current_time",
            description="Get the current time in various formats",
            category="utility",
            parameters={
                "format": {
                    "type": "string",
                    "description": "Optional format string for the time (default: ISO format)",
                },
                "timezone": {
                    "type": "string",
                    "description": "Optional timezone name (default: local timezone)",
                },
            }
        )
    )

    tool_registry.register_tool(
        tool_id="parse_json",
        tool_fn=parse_json,
        metadata=ToolMetadata(
            name="parse_json",
            description="Parse a JSON string into an object",
            category="utility",
            parameters={
                "json_string": {
                    "type": "string",
                    "description": "The JSON string to parse",
                },
            }
        )
    )

    tool_registry.register_tool(
        tool_id="format_json",
        tool_fn=format_json,
        metadata=ToolMetadata(
            name="format_json",
            description="Format a JSON object as a string",
            category="utility",
            parameters={
                "json_object": {
                    "type": "object",
                    "description": "The JSON object to format",
                },
                "pretty": {
                    "type": "boolean",
                    "description": "Whether to pretty-print the JSON (default: true)",
                },
            }
        )
    )

    tool_registry.register_tool(
        tool_id="generate_random",
        tool_fn=generate_random,
        metadata=ToolMetadata(
            name="generate_random",
            description="Generate random values",
            category="utility",
            parameters={
                "type": {
                    "type": "string",
                    "description": "Type of random value to generate (string, number, uuid)",
                },
                "length": {
                    "type": "integer",
                    "description": "Length of random string (for type=string)",
                },
                "min": {
                    "type": "number",
                    "description": "Minimum value (for type=number)",
                },
                "max": {
                    "type": "number",
                    "description": "Maximum value (for type=number)",
                },
                "chars": {
                    "type": "string",
                    "description": "Character set to use (for type=string)",
                },
            }
        )
    )

    tool_registry.register_tool(
        tool_id="regex_match",
        tool_fn=regex_match,
        metadata=ToolMetadata(
            name="regex_match",
            description="Match a string against a regular expression",
            category="utility",
            parameters={
                "pattern": {
                    "type": "string",
                    "description": "The regular expression pattern",
                },
                "text": {
                    "type": "string",
                    "description": "The text to match against",
                },
                "flags": {
                    "type": "string",
                    "description": "Optional regex flags (e.g., 'i' for case-insensitive)",
                },
            }
        )
    )

    tool_registry.register_tool(
        tool_id="regex_replace",
        tool_fn=regex_replace,
        metadata=ToolMetadata(
            name="regex_replace",
            description="Replace text using a regular expression",
            category="utility",
            parameters={
                "pattern": {
                    "type": "string",
                    "description": "The regular expression pattern",
                },
                "text": {
                    "type": "string",
                    "description": "The text to perform replacements on",
                },
                "replacement": {
                    "type": "string",
                    "description": "The replacement string",
                },
                "flags": {
                    "type": "string",
                    "description": "Optional regex flags (e.g., 'i' for case-insensitive)",
                },
            }
        )
    )

    tool_registry.register_tool(
        tool_id="string_operations",
        tool_fn=string_operations,
        metadata=ToolMetadata(
            name="string_operations",
            description="Perform various string operations",
            category="utility",
            parameters={
                "operation": {
                    "type": "string",
                    "description": "The operation to perform (split, join, upper, lower, title, strip)",
                },
                "text": {
                    "type": "string",
                    "description": "The text to operate on",
                },
                "delimiter": {
                    "type": "string",
                    "description": "Delimiter for split/join operations",
                },
                "items": {
                    "type": "array",
                    "description": "Items to join (for join operation)",
                },
            }
        )
    )


async def get_current_time(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Get the current time in various formats."""
    format_str = args.get("format")
    timezone = args.get("timezone")

    try:
        # Get current time
        now = dt_util.now()

        # Apply timezone if specified
        if timezone:
            try:
                now = now.astimezone(dt_util.get_time_zone(timezone))
            except ValueError:
                _LOGGER.warning("Invalid timezone: %s", timezone)

        # Format time if specified
        formatted = None
        if format_str:
            try:
                formatted = now.strftime(format_str)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid format string: %s", format_str)
                formatted = str(now)
        else:
            formatted = now.isoformat()

        # Return time information
        return {
            "formatted": formatted,
            "iso": now.isoformat(),
            "timestamp": now.timestamp(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "weekday": now.strftime("%A"),
            "timezone": str(now.tzinfo),
        }
    except (ValueError, TypeError, AttributeError) as ex:
        _LOGGER.error("Error getting current time: %s", ex)
        return {"error": f"Error getting current time: {ex!s}"}


async def parse_json(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Parse a JSON string into an object."""
    json_string = args.get("json_string")
    if not json_string:
        return {"error": "json_string is required"}

    try:
        parsed = json.loads(json_string)
    except json.JSONDecodeError as ex:
        _LOGGER.error("Error parsing JSON: %s", ex)
        return {"error": f"Error parsing JSON: {ex!s}"}
    else:
        return {"result": parsed}


async def format_json(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Format a JSON object as a string."""
    json_object = args.get("json_object")
    pretty = args.get("pretty", True)

    if json_object is None:
        return {"error": "json_object is required"}

    try:
        if pretty:
            formatted = json.dumps(json_object, indent=2, sort_keys=True)
        else:
            formatted = json.dumps(json_object)
    except (TypeError, ValueError, OverflowError) as ex:
        _LOGGER.error("Error formatting JSON: %s", ex)
        return {"error": f"Error formatting JSON: {ex!s}"}
    else:
        return {"result": formatted}


async def generate_random(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Generate random values."""
    value_type = args.get("type")
    if not value_type:
        return {"error": "type is required"}

    try:
        if value_type == "string":
            length = args.get("length", 10)
            chars = args.get("chars", string.ascii_letters + string.digits)
            result_str: str = ''.join(random.choice(chars) for _ in range(length))
            return {"result": result_str}
        if value_type == "number":
            min_val = args.get("min", 0)
            max_val = args.get("max", 100)
            result_num: float = random.uniform(min_val, max_val)
            # Return as int if both min and max are integers
            if isinstance(min_val, int) and isinstance(max_val, int):
                result_num = int(result_num)
            return {"result": result_num}
        if value_type == "uuid":
            result_uuid: str = str(uuid.uuid4())
            return {"result": result_uuid}
    except (ValueError, TypeError, OverflowError) as ex:
        _LOGGER.error("Error generating random value: %s", ex)
        return {"error": f"Error generating random value: {ex!s}"}
    else:
        return {"error": f"Invalid type: {value_type}"}


async def regex_match(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Match a string against a regular expression."""
    pattern = args.get("pattern")
    text = args.get("text")
    flags_str = args.get("flags", "")

    if not pattern:
        return {"error": "pattern is required"}

    if text is None:
        return {"error": "text is required"}

    try:
        # Parse flags
        flags = 0
        if "i" in flags_str:
            flags |= re.IGNORECASE
        if "m" in flags_str:
            flags |= re.MULTILINE
        if "s" in flags_str:
            flags |= re.DOTALL

        # Compile regex
        regex = re.compile(pattern, flags)

        # Find all matches
        matches = []
        for match in regex.finditer(text):
            match_data = {
                "start": match.start(),
                "end": match.end(),
                "match": match.group(0),
                "groups": match.groups(),
                "named_groups": match.groupdict(),
            }
            matches.append(match_data)

        return {
            "matches": matches,
            "count": len(matches),
            "match_found": len(matches) > 0,
        }
    except re.error as ex:
        _LOGGER.error("Regex error: %s", ex)
        return {"error": f"Regex error: {ex!s}"}
    except (TypeError, AttributeError, IndexError) as ex:
        _LOGGER.error("Error matching regex: %s", ex)
        return {"error": f"Error matching regex: {ex!s}"}


async def regex_replace(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Replace text using a regular expression."""
    pattern = args.get("pattern")
    text = args.get("text")
    replacement = args.get("replacement")
    flags_str = args.get("flags", "")

    if not pattern:
        return {"error": "pattern is required"}

    if text is None:
        return {"error": "text is required"}

    if replacement is None:
        return {"error": "replacement is required"}

    try:
        # Parse flags
        flags = 0
        if "i" in flags_str:
            flags |= re.IGNORECASE
        if "m" in flags_str:
            flags |= re.MULTILINE
        if "s" in flags_str:
            flags |= re.DOTALL

        # Compile regex and perform replacement
        regex = re.compile(pattern, flags)
        result = regex.sub(replacement, text)

        # Count replacements
        original_matches = regex.findall(text)
        count = len(original_matches)
    except re.error as ex:
        _LOGGER.error("Regex error: %s", ex)
        return {"error": f"Regex error: {ex!s}"}
    except (TypeError, AttributeError, IndexError) as ex:
        _LOGGER.error("Error replacing text: %s", ex)
        return {"error": f"Error replacing text: {ex!s}"}
    else:
        return {
            "result": result,
            "count": count,
            "replacements_made": count > 0,
        }


async def string_operations(hass: HomeAssistant, args: dict[str, Any]) -> dict[str, Any]:
    """Perform various string operations."""
    operation = args.get("operation")
    text = args.get("text")
    delimiter = args.get("delimiter", " ")
    items = args.get("items", [])

    if not operation:
        return {"error": "operation is required"}

    try:
        if operation == "split":
            if text is None:
                return {"error": "text is required for split operation"}
            result = text.split(delimiter)
            return {"result": result}

        if operation == "join":
            if not items:
                return {"error": "items is required for join operation"}
            result = delimiter.join(str(item) for item in items)
            return {"result": result}

        if operation == "upper":
            if text is None:
                return {"error": "text is required for upper operation"}
            result = text.upper()
            return {"result": result}

        if operation == "lower":
            if text is None:
                return {"error": "text is required for lower operation"}
            result = text.lower()
            return {"result": result}

        if operation == "title":
            if text is None:
                return {"error": "text is required for title operation"}
            result = text.title()
            return {"result": result}

        if operation == "strip":
            if text is None:
                return {"error": "text is required for strip operation"}
            result = text.strip()
            return {"result": result}
    except (TypeError, AttributeError) as ex:
        _LOGGER.error("Error performing string operation: %s", ex)
        return {"error": f"Error performing string operation: {ex!s}"}
    else:
        return {"error": f"Invalid operation: {operation}"}
