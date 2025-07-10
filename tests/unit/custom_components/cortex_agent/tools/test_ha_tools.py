"""Tests for the CortexAgent ha_tools module."""
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import State

from custom_components.cortex_agent.tools.ha_tools import (
    call_service,
    get_areas,
    get_devices,
    get_state,
    render_template,
    set_state,
    tool_registry,
)


def test_tool_registry():
    """Test that the tool registry is initialized."""
    assert tool_registry is not None


def test_get_state_specific_entity(mock_hass):
    """Test the get_state function with a specific entity."""
    # Create a mock state
    mock_state = MagicMock(spec=State)
    mock_state.state = "on"
    mock_state.attributes = {"brightness": 255}
    mock_state.last_updated.isoformat.return_value = "2023-01-01T00:00:00+00:00"
    
    # Set up the mock hass.states.get to return the mock state
    mock_hass.states.get.return_value = mock_state
    
    # Call get_state
    result = get_state(mock_hass, entity_id="light.living_room")
    
    # Check that hass.states.get was called with the right entity_id
    mock_hass.states.get.assert_called_once_with("light.living_room")
    
    # Check the result
    assert "light.living_room" in result
    assert result["light.living_room"]["state"] == "on"
    assert result["light.living_room"]["attributes"] == {"brightness": 255}
    assert result["light.living_room"]["last_updated"] == "2023-01-01T00:00:00+00:00"


def test_get_state_domain(mock_hass):
    """Test the get_state function with a domain."""
    # Create mock states
    mock_state1 = MagicMock(spec=State)
    mock_state1.entity_id = "light.living_room"
    mock_state1.state = "on"
    mock_state1.attributes = {"brightness": 255}
    mock_state1.last_updated.isoformat.return_value = "2023-01-01T00:00:00+00:00"
    
    mock_state2 = MagicMock(spec=State)
    mock_state2.entity_id = "light.bedroom"
    mock_state2.state = "off"
    mock_state2.attributes = {}
    mock_state2.last_updated.isoformat.return_value = "2023-01-01T00:00:00+00:00"
    
    # Set up the mock hass.states.async_all to return the mock states
    mock_hass.states.async_all.return_value = [mock_state1, mock_state2]
    
    # Call get_state
    result = get_state(mock_hass, domain="light")
    
    # Check that hass.states.async_all was called with the right domain
    mock_hass.states.async_all.assert_called_once_with("light")
    
    # Check the result
    assert "light.living_room" in result
    assert result["light.living_room"]["state"] == "on"
    assert result["light.living_room"]["attributes"] == {"brightness": 255}
    assert result["light.living_room"]["last_updated"] == "2023-01-01T00:00:00+00:00"
    
    assert "light.bedroom" in result
    assert result["light.bedroom"]["state"] == "off"
    assert result["light.bedroom"]["attributes"] == {}
    assert result["light.bedroom"]["last_updated"] == "2023-01-01T00:00:00+00:00"


def test_get_state_all(mock_hass):
    """Test the get_state function with no entity_id or domain."""
    # Create mock states
    mock_state1 = MagicMock(spec=State)
    mock_state1.entity_id = "light.living_room"
    mock_state1.state = "on"
    mock_state1.attributes = {"brightness": 255}
    mock_state1.last_updated.isoformat.return_value = "2023-01-01T00:00:00+00:00"
    
    mock_state2 = MagicMock(spec=State)
    mock_state2.entity_id = "switch.kitchen"
    mock_state2.state = "off"
    mock_state2.attributes = {}
    mock_state2.last_updated.isoformat.return_value = "2023-01-01T00:00:00+00:00"
    
    # Set up the mock hass.states.async_all to return the mock states
    mock_hass.states.async_all.return_value = [mock_state1, mock_state2]
    
    # Call get_state
    result = get_state(mock_hass)
    
    # Check that hass.states.async_all was called with no arguments
    mock_hass.states.async_all.assert_called_once_with()
    
    # Check the result
    assert "light.living_room" in result
    assert result["light.living_room"]["state"] == "on"
    assert result["light.living_room"]["attributes"] == {"brightness": 255}
    assert result["light.living_room"]["last_updated"] == "2023-01-01T00:00:00+00:00"
    
    assert "switch.kitchen" in result
    assert result["switch.kitchen"]["state"] == "off"
    assert result["switch.kitchen"]["attributes"] == {}
    assert result["switch.kitchen"]["last_updated"] == "2023-01-01T00:00:00+00:00"


def test_set_state(mock_hass):
    """Test the set_state function."""
    # Set up the mock hass.states.get to return a mock state
    mock_hass.states.get.return_value = MagicMock(spec=State)
    
    # Call set_state
    result = set_state(mock_hass, entity_id="light.living_room", state="on", attributes={"brightness": 255})
    
    # Check that hass.states.get was called with the right entity_id
    mock_hass.states.get.assert_called_once_with("light.living_room")
    
    # Check that hass.states.async_set was called with the right arguments
    mock_hass.states.async_set.assert_called_once_with("light.living_room", "on", {"brightness": 255})
    
    # Check the result
    assert result["success"] is True
    assert result["entity_id"] == "light.living_room"
    assert result["state"] == "on"


def test_set_state_entity_not_found(mock_hass):
    """Test the set_state function with an entity that doesn't exist."""
    # Set up the mock hass.states.get to return None
    mock_hass.states.get.return_value = None
    
    # Call set_state
    result = set_state(mock_hass, entity_id="light.non_existent", state="on")
    
    # Check that hass.states.get was called with the right entity_id
    mock_hass.states.get.assert_called_once_with("light.non_existent")
    
    # Check that hass.states.async_set was not called
    mock_hass.states.async_set.assert_not_called()
    
    # Check the result
    assert result["success"] is False
    assert "not found" in result["error"]


def test_call_service(mock_hass):
    """Test the call_service function."""
    # Call call_service
    result = call_service(
        mock_hass,
        domain="light",
        service="turn_on",
        service_data={"brightness": 255},
        target={"entity_id": "light.living_room"},
    )
    
    # Check that hass.services.call was called with the right arguments
    mock_hass.services.call.assert_called_once_with(
        domain="light",
        service="turn_on",
        service_data={"brightness": 255},
        target={"entity_id": "light.living_room"},
        blocking=True,
    )
    
    # Check the result
    assert result["success"] is True
    assert result["domain"] == "light"
    assert result["service"] == "turn_on"
    assert result["service_data"] == {"brightness": 255}
    assert result["target"] == {"entity_id": "light.living_room"}


def test_render_template(mock_hass):
    """Test the render_template function."""
    # Set up the mock Template to return a value
    with patch("custom_components.cortex_agent.tools.ha_tools.Template") as mock_template:
        mock_template_instance = MagicMock()
        mock_template_instance.async_render.return_value = "Rendered template"
        mock_template.return_value = mock_template_instance
        
        # Call render_template
        result = render_template(mock_hass, template="{{ states('sensor.temperature') }}")
        
        # Check that Template was called with the right arguments
        mock_template.assert_called_once_with("{{ states('sensor.temperature') }}", mock_hass)
        
        # Check that async_render was called
        mock_template_instance.async_render.assert_called_once()
        
        # Check the result
        assert result["success"] is True
        assert result["result"] == "Rendered template"


def test_render_template_error(mock_hass):
    """Test the render_template function with an error."""
    # Set up the mock Template to raise an exception
    with patch("custom_components.cortex_agent.tools.ha_tools.Template") as mock_template:
        mock_template_instance = MagicMock()
        mock_template_instance.async_render.side_effect = Exception("Template error")
        mock_template.return_value = mock_template_instance
        
        # Call render_template
        result = render_template(mock_hass, template="{{ invalid template }}")
        
        # Check that Template was called with the right arguments
        mock_template.assert_called_once_with("{{ invalid template }}", mock_hass)
        
        # Check that async_render was called
        mock_template_instance.async_render.assert_called_once()
        
        # Check the result
        assert result["success"] is False
        assert "Template error" in result["error"]


@patch("custom_components.cortex_agent.tools.ha_tools.area_registry")
@patch("custom_components.cortex_agent.tools.ha_tools.entity_registry")
def test_get_areas(mock_entity_registry, mock_area_registry, mock_hass):
    """Test the get_areas function."""
    # Set up mock area registry
    mock_area_reg = MagicMock()
    mock_area_registry.async_get.return_value = mock_area_reg
    
    # Set up mock areas
    mock_area1 = MagicMock()
    mock_area1.id = "area1"
    mock_area1.name = "Living Room"
    
    mock_area2 = MagicMock()
    mock_area2.id = "area2"
    mock_area2.name = "Kitchen"
    
    mock_area_reg.areas = {
        "area1": mock_area1,
        "area2": mock_area2,
    }
    
    # Set up mock entity registry
    mock_entity_reg = MagicMock()
    mock_entity_registry.async_get.return_value = mock_entity_reg
    
    # Set up mock entity entries
    mock_entity1 = MagicMock()
    mock_entity1.entity_id = "light.living_room"
    mock_entity1.area_id = "area1"
    mock_entity1.name = "Living Room Light"
    
    mock_entity2 = MagicMock()
    mock_entity2.entity_id = "switch.kitchen"
    mock_entity2.area_id = "area2"
    mock_entity2.name = "Kitchen Switch"
    
    mock_entity_reg.entities = {
        "light.living_room": mock_entity1,
        "switch.kitchen": mock_entity2,
    }
    
    # Set up mock states
    mock_state1 = MagicMock(spec=State)
    mock_state1.name = "Living Room Light"
    mock_state1.state = "on"
    
    mock_state2 = MagicMock(spec=State)
    mock_state2.name = "Kitchen Switch"
    mock_state2.state = "off"
    
    # Set up the mock hass.states.get to return the mock states
    mock_hass.states.get.side_effect = lambda entity_id: {
        "light.living_room": mock_state1,
        "switch.kitchen": mock_state2,
    }.get(entity_id)
    
    # Call get_areas
    result = get_areas(mock_hass)
    
    # Check that area_registry.async_get was called
    mock_area_registry.async_get.assert_called_once_with(mock_hass)
    
    # Check that entity_registry.async_get was called
    mock_entity_registry.async_get.assert_called_once_with(mock_hass)
    
    # Check the result
    assert "area1" in result
    assert result["area1"]["name"] == "Living Room"
    assert len(result["area1"]["entities"]) == 1
    assert result["area1"]["entities"][0]["entity_id"] == "light.living_room"
    assert result["area1"]["entities"][0]["name"] == "Living Room Light"
    assert result["area1"]["entities"][0]["state"] == "on"
    
    assert "area2" in result
    assert result["area2"]["name"] == "Kitchen"
    assert len(result["area2"]["entities"]) == 1
    assert result["area2"]["entities"][0]["entity_id"] == "switch.kitchen"
    assert result["area2"]["entities"][0]["name"] == "Kitchen Switch"
    assert result["area2"]["entities"][0]["state"] == "off"


@patch("custom_components.cortex_agent.tools.ha_tools.device_registry")
@patch("custom_components.cortex_agent.tools.ha_tools.entity_registry")
def test_get_devices(mock_entity_registry, mock_device_registry, mock_hass):
    """Test the get_devices function."""
    # Set up mock device registry
    mock_device_reg = MagicMock()
    mock_device_registry.async_get.return_value = mock_device_reg
    
    # Set up mock devices
    mock_device1 = MagicMock()
    mock_device1.id = "device1"
    mock_device1.name = "Living Room Light"
    mock_device1.manufacturer = "Philips"
    mock_device1.model = "Hue"
    mock_device1.sw_version = "1.0"
    
    mock_device2 = MagicMock()
    mock_device2.id = "device2"
    mock_device2.name = "Kitchen Switch"
    mock_device2.manufacturer = "GE"
    mock_device2.model = "Z-Wave"
    mock_device2.sw_version = "2.0"
    
    mock_device_reg.devices = {
        "device1": mock_device1,
        "device2": mock_device2,
    }
    
    # Set up mock entity registry
    mock_entity_reg = MagicMock()
    mock_entity_registry.async_get.return_value = mock_entity_reg
    
    # Set up mock entity entries
    mock_entity1 = MagicMock()
    mock_entity1.entity_id = "light.living_room"
    mock_entity1.device_id = "device1"
    mock_entity1.name = "Living Room Light"
    
    mock_entity2 = MagicMock()
    mock_entity2.entity_id = "switch.kitchen"
    mock_entity2.device_id = "device2"
    mock_entity2.name = "Kitchen Switch"
    
    mock_entity_reg.entities = {
        "light.living_room": mock_entity1,
        "switch.kitchen": mock_entity2,
    }
    
    # Set up mock states
    mock_state1 = MagicMock(spec=State)
    mock_state1.name = "Living Room Light"
    mock_state1.state = "on"
    
    mock_state2 = MagicMock(spec=State)
    mock_state2.name = "Kitchen Switch"
    mock_state2.state = "off"
    
    # Set up the mock hass.states.get to return the mock states
    mock_hass.states.get.side_effect = lambda entity_id: {
        "light.living_room": mock_state1,
        "switch.kitchen": mock_state2,
    }.get(entity_id)
    
    # Call get_devices
    result = get_devices(mock_hass)
    
    # Check that device_registry.async_get was called
    mock_device_registry.async_get.assert_called_once_with(mock_hass)
    
    # Check that entity_registry.async_get was called
    mock_entity_registry.async_get.assert_called_once_with(mock_hass)
    
    # Check the result
    assert "device1" in result
    assert result["device1"]["name"] == "Living Room Light"
    assert result["device1"]["manufacturer"] == "Philips"
    assert result["device1"]["model"] == "Hue"
    assert result["device1"]["sw_version"] == "1.0"
    assert len(result["device1"]["entities"]) == 1
    assert result["device1"]["entities"][0]["entity_id"] == "light.living_room"
    assert result["device1"]["entities"][0]["name"] == "Living Room Light"
    assert result["device1"]["entities"][0]["state"] == "on"
    
    assert "device2" in result
    assert result["device2"]["name"] == "Kitchen Switch"
    assert result["device2"]["manufacturer"] == "GE"
    assert result["device2"]["model"] == "Z-Wave"
    assert result["device2"]["sw_version"] == "2.0"
    assert len(result["device2"]["entities"]) == 1
    assert result["device2"]["entities"][0]["entity_id"] == "switch.kitchen"
    assert result["device2"]["entities"][0]["name"] == "Kitchen Switch"
    assert result["device2"]["entities"][0]["state"] == "off"