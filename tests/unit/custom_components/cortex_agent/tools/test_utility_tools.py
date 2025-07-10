"""Tests for the CortexAgent utility_tools module."""
from unittest.mock import MagicMock, patch
import json
import datetime

import pytest

from custom_components.cortex_agent.tools.utility_tools import (
    get_current_time,
    parse_json,
    format_text,
    generate_uuid,
    tool_registry,
)


def test_tool_registry():
    """Test that the tool registry is initialized."""
    assert tool_registry is not None


@patch("custom_components.cortex_agent.tools.utility_tools.datetime")
def test_get_current_time(mock_datetime):
    """Test the get_current_time function."""
    # Set up the mock datetime
    mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    mock_datetime.datetime.now.return_value = mock_now
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call get_current_time
    result = get_current_time(mock_hass)
    
    # Check that datetime.now was called
    mock_datetime.datetime.now.assert_called_once()
    
    # Check the result
    assert result["success"] is True
    assert result["timestamp"] == "2023-01-01T12:00:00+00:00"
    assert result["iso_format"] == "2023-01-01T12:00:00+00:00"
    assert result["year"] == 2023
    assert result["month"] == 1
    assert result["day"] == 1
    assert result["hour"] == 12
    assert result["minute"] == 0
    assert result["second"] == 0
    assert result["weekday"] == "Sunday"


@patch("custom_components.cortex_agent.tools.utility_tools.datetime")
def test_get_current_time_with_timezone(mock_datetime):
    """Test the get_current_time function with a timezone."""
    # Set up the mock datetime
    mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    mock_datetime.datetime.now.return_value = mock_now
    
    # Mock timezone conversion
    mock_tz = MagicMock()
    mock_tz.localize.return_value = datetime.datetime(2023, 1, 1, 4, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-8)))
    mock_datetime.timezone.return_value = mock_tz
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call get_current_time
    result = get_current_time(mock_hass, timezone="America/Los_Angeles")
    
    # Check that datetime.now was called
    mock_datetime.datetime.now.assert_called_once()
    
    # Check the result
    assert result["success"] is True
    assert "America/Los_Angeles" in result["timezone"]
    # Note: We can't check the exact timestamp because the timezone conversion is mocked


def test_parse_json_valid():
    """Test the parse_json function with valid JSON."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Call parse_json
    result = parse_json(
        mock_hass,
        json_string='{"name": "Test", "value": 123, "nested": {"key": "value"}}',
    )
    
    # Check the result
    assert result["success"] is True
    assert result["parsed"]["name"] == "Test"
    assert result["parsed"]["value"] == 123
    assert result["parsed"]["nested"]["key"] == "value"


def test_parse_json_invalid():
    """Test the parse_json function with invalid JSON."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Call parse_json
    result = parse_json(
        mock_hass,
        json_string='{"name": "Test", "value": 123,}',  # Invalid JSON (trailing comma)
    )
    
    # Check the result
    assert result["success"] is False
    assert "Invalid JSON" in result["error"]


def test_format_text():
    """Test the format_text function."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Call format_text
    result = format_text(
        mock_hass,
        text="Hello, {name}!",
        variables={"name": "World"},
        format_type="basic",
    )
    
    # Check the result
    assert result["success"] is True
    assert result["formatted_text"] == "Hello, World!"


def test_format_text_advanced():
    """Test the format_text function with advanced formatting."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Call format_text
    result = format_text(
        mock_hass,
        text="The {item} costs ${price:.2f}",
        variables={"item": "apple", "price": 1.5},
        format_type="advanced",
    )
    
    # Check the result
    assert result["success"] is True
    assert result["formatted_text"] == "The apple costs $1.50"


def test_format_text_error():
    """Test the format_text function with an error."""
    # Mock hass
    mock_hass = MagicMock()
    
    # Call format_text
    result = format_text(
        mock_hass,
        text="Hello, {name}!",
        variables={},  # Missing 'name' variable
        format_type="basic",
    )
    
    # Check the result
    assert result["success"] is False
    assert "KeyError" in result["error"]


@patch("custom_components.cortex_agent.tools.utility_tools.uuid")
def test_generate_uuid(mock_uuid):
    """Test the generate_uuid function."""
    # Set up the mock uuid
    mock_uuid.uuid4.return_value = "12345678-1234-5678-1234-567812345678"
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call generate_uuid
    result = generate_uuid(mock_hass)
    
    # Check that uuid.uuid4 was called
    mock_uuid.uuid4.assert_called_once()
    
    # Check the result
    assert result["success"] is True
    assert result["uuid"] == "12345678-1234-5678-1234-567812345678"


@patch("custom_components.cortex_agent.tools.utility_tools.uuid")
def test_generate_uuid_with_prefix(mock_uuid):
    """Test the generate_uuid function with a prefix."""
    # Set up the mock uuid
    mock_uuid.uuid4.return_value = "12345678-1234-5678-1234-567812345678"
    
    # Mock hass
    mock_hass = MagicMock()
    
    # Call generate_uuid
    result = generate_uuid(mock_hass, prefix="test")
    
    # Check that uuid.uuid4 was called
    mock_uuid.uuid4.assert_called_once()
    
    # Check the result
    assert result["success"] is True
    assert result["uuid"] == "test-12345678-1234-5678-1234-567812345678"