"""Tests for the CortexAgent http_tools module."""
from unittest.mock import MagicMock, patch

import pytest
import aiohttp
from aiohttp import ClientResponseError, ClientConnectorError

from custom_components.cortex_agent.tools.http_tools import (
    http_get,
    http_post,
    http_put,
    http_delete,
    tool_registry,
)


def test_tool_registry():
    """Test that the tool registry is initialized."""
    assert tool_registry is not None


@patch("custom_components.cortex_agent.tools.http_tools.aiohttp.ClientSession")
async def test_http_get_success(mock_client_session):
    """Test the http_get function with a successful response."""
    # Set up the mock client session
    mock_session = MagicMock()
    mock_client_session.return_value.__aenter__.return_value = mock_session
    
    # Set up the mock response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text.return_value = '{"key": "value"}'
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call http_get
    result = await http_get(
        mock_hass,
        url="https://example.com/api",
        headers={"Authorization": "Bearer token"},
        params={"param1": "value1"},
        timeout=10,
    )
    
    # Check that ClientSession was created
    mock_client_session.assert_called_once()
    
    # Check that get was called with the right arguments
    mock_session.get.assert_called_once_with(
        "https://example.com/api",
        headers={"Authorization": "Bearer token"},
        params={"param1": "value1"},
        timeout=10,
        ssl=None,
    )
    
    # Check the result
    assert result["success"] is True
    assert result["status"] == 200
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["text"] == '{"key": "value"}'


@patch("custom_components.cortex_agent.tools.http_tools.aiohttp.ClientSession")
async def test_http_get_error_response(mock_client_session):
    """Test the http_get function with an error response."""
    # Set up the mock client session
    mock_session = MagicMock()
    mock_client_session.return_value.__aenter__.return_value = mock_session
    
    # Set up the mock response
    mock_response = MagicMock()
    mock_response.status = 404
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text.return_value = '{"error": "Not found"}'
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call http_get
    result = await http_get(
        mock_hass,
        url="https://example.com/api/nonexistent",
        headers={},
        params={},
        timeout=10,
    )
    
    # Check that ClientSession was created
    mock_client_session.assert_called_once()
    
    # Check that get was called with the right arguments
    mock_session.get.assert_called_once_with(
        "https://example.com/api/nonexistent",
        headers={},
        params={},
        timeout=10,
        ssl=None,
    )
    
    # Check the result
    assert result["success"] is False
    assert result["status"] == 404
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["text"] == '{"error": "Not found"}'


@patch("custom_components.cortex_agent.tools.http_tools.aiohttp.ClientSession")
async def test_http_get_exception(mock_client_session):
    """Test the http_get function with an exception."""
    # Set up the mock client session
    mock_session = MagicMock()
    mock_client_session.return_value.__aenter__.return_value = mock_session
    
    # Set up the mock get to raise an exception
    mock_session.get.side_effect = ClientConnectorError(
        connection_key=None,
        os_error=OSError("Connection refused"),
    )
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call http_get
    result = await http_get(
        mock_hass,
        url="https://nonexistent.example.com",
        headers={},
        params={},
        timeout=10,
    )
    
    # Check that ClientSession was created
    mock_client_session.assert_called_once()
    
    # Check that get was called with the right arguments
    mock_session.get.assert_called_once_with(
        "https://nonexistent.example.com",
        headers={},
        params={},
        timeout=10,
        ssl=None,
    )
    
    # Check the result
    assert result["success"] is False
    assert "Connection refused" in result["error"]


@patch("custom_components.cortex_agent.tools.http_tools.aiohttp.ClientSession")
async def test_http_post_success(mock_client_session):
    """Test the http_post function with a successful response."""
    # Set up the mock client session
    mock_session = MagicMock()
    mock_client_session.return_value.__aenter__.return_value = mock_session
    
    # Set up the mock response
    mock_response = MagicMock()
    mock_response.status = 201
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text.return_value = '{"id": "123"}'
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call http_post
    result = await http_post(
        mock_hass,
        url="https://example.com/api/resource",
        headers={"Content-Type": "application/json"},
        data='{"name": "Test"}',
        timeout=10,
    )
    
    # Check that ClientSession was created
    mock_client_session.assert_called_once()
    
    # Check that post was called with the right arguments
    mock_session.post.assert_called_once_with(
        "https://example.com/api/resource",
        headers={"Content-Type": "application/json"},
        data='{"name": "Test"}',
        timeout=10,
        ssl=None,
    )
    
    # Check the result
    assert result["success"] is True
    assert result["status"] == 201
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["text"] == '{"id": "123"}'


@patch("custom_components.cortex_agent.tools.http_tools.aiohttp.ClientSession")
async def test_http_post_error_response(mock_client_session):
    """Test the http_post function with an error response."""
    # Set up the mock client session
    mock_session = MagicMock()
    mock_client_session.return_value.__aenter__.return_value = mock_session
    
    # Set up the mock response
    mock_response = MagicMock()
    mock_response.status = 400
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text.return_value = '{"error": "Bad request"}'
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call http_post
    result = await http_post(
        mock_hass,
        url="https://example.com/api/resource",
        headers={"Content-Type": "application/json"},
        data='{"invalid": "data"}',
        timeout=10,
    )
    
    # Check that ClientSession was created
    mock_client_session.assert_called_once()
    
    # Check that post was called with the right arguments
    mock_session.post.assert_called_once_with(
        "https://example.com/api/resource",
        headers={"Content-Type": "application/json"},
        data='{"invalid": "data"}',
        timeout=10,
        ssl=None,
    )
    
    # Check the result
    assert result["success"] is False
    assert result["status"] == 400
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["text"] == '{"error": "Bad request"}'


@patch("custom_components.cortex_agent.tools.http_tools.aiohttp.ClientSession")
async def test_http_put_success(mock_client_session):
    """Test the http_put function with a successful response."""
    # Set up the mock client session
    mock_session = MagicMock()
    mock_client_session.return_value.__aenter__.return_value = mock_session
    
    # Set up the mock response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text.return_value = '{"updated": true}'
    mock_session.put.return_value.__aenter__.return_value = mock_response
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call http_put
    result = await http_put(
        mock_hass,
        url="https://example.com/api/resource/123",
        headers={"Content-Type": "application/json"},
        data='{"name": "Updated Test"}',
        timeout=10,
    )
    
    # Check that ClientSession was created
    mock_client_session.assert_called_once()
    
    # Check that put was called with the right arguments
    mock_session.put.assert_called_once_with(
        "https://example.com/api/resource/123",
        headers={"Content-Type": "application/json"},
        data='{"name": "Updated Test"}',
        timeout=10,
        ssl=None,
    )
    
    # Check the result
    assert result["success"] is True
    assert result["status"] == 200
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["text"] == '{"updated": true}'


@patch("custom_components.cortex_agent.tools.http_tools.aiohttp.ClientSession")
async def test_http_delete_success(mock_client_session):
    """Test the http_delete function with a successful response."""
    # Set up the mock client session
    mock_session = MagicMock()
    mock_client_session.return_value.__aenter__.return_value = mock_session
    
    # Set up the mock response
    mock_response = MagicMock()
    mock_response.status = 204
    mock_response.headers = {}
    mock_response.text.return_value = ""
    mock_session.delete.return_value.__aenter__.return_value = mock_response
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call http_delete
    result = await http_delete(
        mock_hass,
        url="https://example.com/api/resource/123",
        headers={"Authorization": "Bearer token"},
        timeout=10,
    )
    
    # Check that ClientSession was created
    mock_client_session.assert_called_once()
    
    # Check that delete was called with the right arguments
    mock_session.delete.assert_called_once_with(
        "https://example.com/api/resource/123",
        headers={"Authorization": "Bearer token"},
        timeout=10,
        ssl=None,
    )
    
    # Check the result
    assert result["success"] is True
    assert result["status"] == 204
    assert result["headers"] == {}
    assert result["text"] == ""