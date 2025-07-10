"""HTTP tools for CortexAgent."""
from __future__ import annotations

import logging
import json
import aiohttp
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


def register_http_tools(tool_registry) -> None:
    """Register HTTP tools with the tool registry."""
    tool_registry.register_tool(
        name="http_get",
        description="Make an HTTP GET request to a URL",
        function=http_get,
        parameters={
            "url": {
                "type": "string",
                "description": "The URL to make the request to",
            },
            "headers": {
                "type": "object",
                "description": "Optional headers to include in the request",
            },
            "params": {
                "type": "object",
                "description": "Optional query parameters to include in the request",
            },
            "timeout": {
                "type": "number",
                "description": "Optional timeout in seconds (default: 10)",
            },
        },
        category="http",
    )
    
    tool_registry.register_tool(
        name="http_post",
        description="Make an HTTP POST request to a URL",
        function=http_post,
        parameters={
            "url": {
                "type": "string",
                "description": "The URL to make the request to",
            },
            "data": {
                "type": "object",
                "description": "The data to send in the request body",
            },
            "headers": {
                "type": "object",
                "description": "Optional headers to include in the request",
            },
            "json": {
                "type": "boolean",
                "description": "Whether to send the data as JSON (default: true)",
            },
            "timeout": {
                "type": "number",
                "description": "Optional timeout in seconds (default: 10)",
            },
        },
        category="http",
    )
    
    tool_registry.register_tool(
        name="http_put",
        description="Make an HTTP PUT request to a URL",
        function=http_put,
        parameters={
            "url": {
                "type": "string",
                "description": "The URL to make the request to",
            },
            "data": {
                "type": "object",
                "description": "The data to send in the request body",
            },
            "headers": {
                "type": "object",
                "description": "Optional headers to include in the request",
            },
            "json": {
                "type": "boolean",
                "description": "Whether to send the data as JSON (default: true)",
            },
            "timeout": {
                "type": "number",
                "description": "Optional timeout in seconds (default: 10)",
            },
        },
        category="http",
    )
    
    tool_registry.register_tool(
        name="http_delete",
        description="Make an HTTP DELETE request to a URL",
        function=http_delete,
        parameters={
            "url": {
                "type": "string",
                "description": "The URL to make the request to",
            },
            "headers": {
                "type": "object",
                "description": "Optional headers to include in the request",
            },
            "timeout": {
                "type": "number",
                "description": "Optional timeout in seconds (default: 10)",
            },
        },
        category="http",
    )


def _validate_url(url: str) -> bool:
    """Validate that a URL is safe to access."""
    parsed = urlparse(url)
    
    # Check for valid scheme
    if parsed.scheme not in ("http", "https"):
        return False
    
    # Check for localhost or private IP addresses
    hostname = parsed.netloc.split(":")[0].lower()
    if hostname in ("localhost", "127.0.0.1", "::1"):
        return False
    
    # Check for private IP ranges
    if hostname.startswith(("10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.",
                           "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
                           "172.26.", "172.27.", "172.28.", "172.29.", "172.30.",
                           "172.31.", "192.168.")):
        return False
    
    return True


async def _process_response(response: aiohttp.ClientResponse) -> Dict[str, Any]:
    """Process an HTTP response."""
    try:
        # Try to parse as JSON first
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            data = await response.json()
        else:
            # Otherwise, get as text
            data = await response.text()
            
            # Try to parse as JSON anyway if it looks like JSON
            if data.strip().startswith(("{", "[")):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    pass
        
        return {
            "status": response.status,
            "headers": dict(response.headers),
            "data": data,
        }
    except Exception as ex:
        _LOGGER.error("Error processing HTTP response: %s", ex)
        return {
            "status": response.status,
            "headers": dict(response.headers),
            "error": f"Error processing response: {str(ex)}",
        }


async def http_get(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
    """Make an HTTP GET request."""
    url = args.get("url")
    headers = args.get("headers", {})
    params = args.get("params", {})
    timeout = args.get("timeout", 10)
    
    if not url:
        return {"error": "url is required"}
    
    # Validate URL
    if not _validate_url(url):
        return {"error": f"Invalid or unsafe URL: {url}"}
    
    try:
        session = async_get_clientsession(hass)
        async with session.get(
            url=url,
            headers=headers,
            params=params,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            return await _process_response(response)
    except aiohttp.ClientError as ex:
        _LOGGER.error("HTTP GET request failed: %s", ex)
        return {"error": f"HTTP GET request failed: {str(ex)}"}
    except Exception as ex:
        _LOGGER.error("Error making HTTP GET request: %s", ex)
        return {"error": f"Error making HTTP GET request: {str(ex)}"}


async def http_post(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
    """Make an HTTP POST request."""
    url = args.get("url")
    data = args.get("data", {})
    headers = args.get("headers", {})
    use_json = args.get("json", True)
    timeout = args.get("timeout", 10)
    
    if not url:
        return {"error": "url is required"}
    
    # Validate URL
    if not _validate_url(url):
        return {"error": f"Invalid or unsafe URL: {url}"}
    
    try:
        session = async_get_clientsession(hass)
        
        # Determine how to send the data
        kwargs = {}
        if use_json:
            kwargs["json"] = data
        else:
            kwargs["data"] = data
        
        async with session.post(
            url=url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout),
            **kwargs,
        ) as response:
            return await _process_response(response)
    except aiohttp.ClientError as ex:
        _LOGGER.error("HTTP POST request failed: %s", ex)
        return {"error": f"HTTP POST request failed: {str(ex)}"}
    except Exception as ex:
        _LOGGER.error("Error making HTTP POST request: %s", ex)
        return {"error": f"Error making HTTP POST request: {str(ex)}"}


async def http_put(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
    """Make an HTTP PUT request."""
    url = args.get("url")
    data = args.get("data", {})
    headers = args.get("headers", {})
    use_json = args.get("json", True)
    timeout = args.get("timeout", 10)
    
    if not url:
        return {"error": "url is required"}
    
    # Validate URL
    if not _validate_url(url):
        return {"error": f"Invalid or unsafe URL: {url}"}
    
    try:
        session = async_get_clientsession(hass)
        
        # Determine how to send the data
        kwargs = {}
        if use_json:
            kwargs["json"] = data
        else:
            kwargs["data"] = data
        
        async with session.put(
            url=url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout),
            **kwargs,
        ) as response:
            return await _process_response(response)
    except aiohttp.ClientError as ex:
        _LOGGER.error("HTTP PUT request failed: %s", ex)
        return {"error": f"HTTP PUT request failed: {str(ex)}"}
    except Exception as ex:
        _LOGGER.error("Error making HTTP PUT request: %s", ex)
        return {"error": f"Error making HTTP PUT request: {str(ex)}"}


async def http_delete(hass: HomeAssistant, args: Dict[str, Any]) -> Dict[str, Any]:
    """Make an HTTP DELETE request."""
    url = args.get("url")
    headers = args.get("headers", {})
    timeout = args.get("timeout", 10)
    
    if not url:
        return {"error": "url is required"}
    
    # Validate URL
    if not _validate_url(url):
        return {"error": f"Invalid or unsafe URL: {url}"}
    
    try:
        session = async_get_clientsession(hass)
        async with session.delete(
            url=url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            return await _process_response(response)
    except aiohttp.ClientError as ex:
        _LOGGER.error("HTTP DELETE request failed: %s", ex)
        return {"error": f"HTTP DELETE request failed: {str(ex)}"}
    except Exception as ex:
        _LOGGER.error("Error making HTTP DELETE request: %s", ex)
        return {"error": f"Error making HTTP DELETE request: {str(ex)}"}