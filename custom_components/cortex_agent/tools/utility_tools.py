"""Utility tools for CortexAgent."""
from __future__ import annotations

import logging
import json
import re
import time
import datetime
import random
import string
from typing import Any, Dict, List, Optional
import uuid

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


def register_utility_tools(tool_registry) -> None:
    """Register utility tools with the tool registry."""
    tool_registry.register_tool(
        name="get_current_time",
        description="Get the current time in various formats",
        function=get_current_time,
        parameters={
            "format": {
                "type": "string",
                "description": "Optional format string for the time (default: ISO format)",
            },
            "timezone": {
                "type": "string",
                "description": "Optional timezone name (default: local timezone)",
            },
        },
        category="utility",
    )
    
    tool_registry.register_tool(
        name="parse_json",
        description="Parse a JSON string into an object",
        function=parse_json,
        parameters={
            "json_string": {
                "type": "string",
                "description": "The JSON string to parse",
            },
        },
        category="utility",
    )
    
    tool_registry.register_tool(
        name="format_json",
        description="Format a JSON object as a string",
        function=format_json,
        parameters={
            "json_object": {
                "type": "object",
                "description": "The JSON object to format",
            },
            "pretty": {
                "type": "boolean",
                "description": "Whether to pretty-print the JSON (default: true)",
            },
        },
        category="utility",
    )
    
    tool_registry.register_tool(
        name="generate_random",
        description="Generate random values",
        function=generate_random,
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
        },
        category="utility",
    )
    
    tool_registry.register_tool(
        name="regex_match",
        description="Match a string against a regular expression",
        function=regex_match,
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
        },
        category="utility",
    )
    
    tool_registry.register_tool(
        name="regex_replace",
        description="Replace text using a regular expression",
        function=regex_replace,
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
        },
        category="utility",
    )
    
    tool_registry.register_tool(
        name="string_operations",
        description="Perform various string operations",
        function=string_operations,
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
        },
        category="utility",
    )


async def get_current_time(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
    """Get the current time in various formats."""
    format_str = args.get("format")
    timezone = args.get("timezone")
    
    try:
        # Get current time
        if timezone:
            try:
                tz = dt_util.get_time_zone(timezone)
                if not tz:
                    return {"error": f"Invalid timezone: {timezone}"}
                now = dt_util.now(tz)
            except Exception as ex:
                return {"error": f"Error parsing timezone: {str(ex)}"}
        else:
            now = dt_util.now()
        
        # Format time
        if format_str:
            try:
                formatted = now.strftime(format_str)
            except Exception as ex:
                return {"error": f"Error formatting time: {str(ex)}"}
        else:
            formatted = now.isoformat()
        
        return {
            "iso": now.isoformat(),
            "timestamp": int(now.timestamp()),
            "formatted": formatted,
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "weekday": now.strftime("%A"),
            "timezone": str(now.tzinfo),
        }
    except Exception as ex:
        _LOGGER.error("Error getting current time: %s", ex)
        return {"error": f"Error getting current time: {str(ex)}"}


async def parse_json(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a JSON string into an object."""
    json_string = args.get("json_string")
    if not json_string:
        return {"error": "json_string is required"}
    
    try:
        parsed = json.loads(json_string)
        return {"result": parsed}
    except json.JSONDecodeError as ex:
        _LOGGER.error("Error parsing JSON: %s", ex)
        return {"error": f"Error parsing JSON: {str(ex)}"}


async def format_json(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
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
        
        return {"result": formatted}
    except Exception as ex:
        _LOGGER.error("Error formatting JSON: %s", ex)
        return {"error": f"Error formatting JSON: {str(ex)}"}


async def generate_random(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate random values."""
    value_type = args.get("type")
    if not value_type:
        return {"error": "type is required"}
    
    try:
        if value_type == "string":
            length = args.get("length", 10)
            chars = args.get("chars", string.ascii_letters + string.digits)
            result = ''.join(random.choice(chars) for _ in range(length))
            return {"result": result}
        elif value_type == "number":
            min_val = args.get("min", 0)
            max_val = args.get("max", 100)
            result = random.uniform(min_val, max_val)
            # Return as int if both min and max are integers
            if isinstance(min_val, int) and isinstance(max_val, int):
                result = int(result)
            return {"result": result}
        elif value_type == "uuid":
            result = str(uuid.uuid4())
            return {"result": result}
        else:
            return {"error": f"Invalid type: {value_type}"}
    except Exception as ex:
        _LOGGER.error("Error generating random value: %s", ex)
        return {"error": f"Error generating random value: {str(ex)}"}


async def regex_match(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
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
        return {"error": f"Regex error: {str(ex)}"}
    except Exception as ex:
        _LOGGER.error("Error matching regex: %s", ex)
        return {"error": f"Error matching regex: {str(ex)}"}


async def regex_replace(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # Perform replacement
        result = re.sub(pattern, replacement, text, flags=flags)
        
        return {
            "result": result,
            "original": text,
        }
    except re.error as ex:
        _LOGGER.error("Regex error: %s", ex)
        return {"error": f"Regex error: {str(ex)}"}
    except Exception as ex:
        _LOGGER.error("Error replacing text: %s", ex)
        return {"error": f"Error replacing text: {str(ex)}"}


async def string_operations(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
    """Perform various string operations."""
    operation = args.get("operation")
    text = args.get("text")
    
    if not operation:
        return {"error": "operation is required"}
    
    try:
        if operation == "split":
            if text is None:
                return {"error": "text is required for split operation"}
            
            delimiter = args.get("delimiter", " ")
            result = text.split(delimiter)
            return {"result": result}
        
        elif operation == "join":
            items = args.get("items")
            if not items:
                return {"error": "items is required for join operation"}
            
            delimiter = args.get("delimiter", " ")
            result = delimiter.join(str(item) for item in items)
            return {"result": result}
        
        elif operation == "upper":
            if text is None:
                return {"error": "text is required for upper operation"}
            
            result = text.upper()
            return {"result": result}
        
        elif operation == "lower":
            if text is None:
                return {"error": "text is required for lower operation"}
            
            result = text.lower()
            return {"result": result}
        
        elif operation == "title":
            if text is None:
                return {"error": "text is required for title operation"}
            
            result = text.title()
            return {"result": result}
        
        elif operation == "strip":
            if text is None:
                return {"error": "text is required for strip operation"}
            
            result = text.strip()
            return {"result": result}
        
        else:
            return {"error": f"Invalid operation: {operation}"}
    except Exception as ex:
        _LOGGER.error("Error performing string operation: %s", ex)
        return {"error": f"Error performing string operation: {str(ex)}"}