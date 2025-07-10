"""Tests for the CortexAgent event_listener module."""
from unittest.mock import MagicMock, patch, AsyncMock, call

import pytest
from homeassistant.core import Event, HomeAssistant

from custom_components.cortex_agent.event_listener import (
    EventListener,
    async_setup_event_listener,
)
from custom_components.cortex_agent.const import DOMAIN


@pytest.fixture
def mock_hass():
    """Fixture to provide a mock hass instance."""
    hass = MagicMock(spec=HomeAssistant)
    return hass


@pytest.fixture
def mock_coordinator():
    """Fixture to provide a mock coordinator."""
    coordinator = MagicMock()
    coordinator.agent_id = "test_agent"
    coordinator.name = "Test Agent"
    return coordinator


def test_event_listener_init(mock_hass, mock_coordinator):
    """Test the initialization of EventListener."""
    # Create an event listener
    listener = EventListener(mock_hass, mock_coordinator)
    
    # Check the listener properties
    assert listener.hass == mock_hass
    assert listener.coordinator == mock_coordinator
    assert listener.agent_id == "test_agent"
    assert listener._listeners == []


async def test_event_listener_async_start(mock_hass, mock_coordinator):
    """Test the async_start method of EventListener."""
    # Create an event listener
    listener = EventListener(mock_hass, mock_coordinator)
    
    # Set up the mock hass.bus.async_listen
    mock_hass.bus.async_listen = AsyncMock(return_value=MagicMock())
    
    # Call async_start
    await listener.async_start()
    
    # Check that async_listen was called for each event type
    assert mock_hass.bus.async_listen.call_count == 3
    
    # Check that the listeners were added to the _listeners list
    assert len(listener._listeners) == 3


async def test_event_listener_async_stop(mock_hass, mock_coordinator):
    """Test the async_stop method of EventListener."""
    # Create an event listener
    listener = EventListener(mock_hass, mock_coordinator)
    
    # Set up mock listeners
    mock_listener1 = MagicMock()
    mock_listener2 = MagicMock()
    listener._listeners = [mock_listener1, mock_listener2]
    
    # Call async_stop
    await listener.async_stop()
    
    # Check that each listener was called
    mock_listener1.assert_called_once()
    mock_listener2.assert_called_once()
    
    # Check that the _listeners list was cleared
    assert listener._listeners == []


async def test_event_listener_handle_state_changed_event(mock_hass, mock_coordinator):
    """Test the _handle_state_changed_event method of EventListener."""
    # Create an event listener
    listener = EventListener(mock_hass, mock_coordinator)
    
    # Set up the mock coordinator.memory_handler
    mock_coordinator.memory_handler = MagicMock()
    mock_coordinator.memory_handler.store = MagicMock(return_value="memory_id_123")
    
    # Create a mock event
    mock_event = MagicMock(spec=Event)
    mock_event.data = {
        "entity_id": "light.living_room",
        "old_state": MagicMock(state="off"),
        "new_state": MagicMock(state="on"),
    }
    
    # Call _handle_state_changed_event
    await listener._handle_state_changed_event(mock_event)
    
    # Check that store was called on the memory handler
    mock_coordinator.memory_handler.store.assert_called_once()
    args, kwargs = mock_coordinator.memory_handler.store.call_args
    assert kwargs["agent_id"] == "test_agent"
    assert "light.living_room" in kwargs["content"]
    assert "off" in kwargs["content"]
    assert "on" in kwargs["content"]
    assert kwargs["metadata"]["type"] == "state_changed"
    assert kwargs["metadata"]["entity_id"] == "light.living_room"


async def test_event_listener_handle_state_changed_event_no_old_state(mock_hass, mock_coordinator):
    """Test the _handle_state_changed_event method with no old state."""
    # Create an event listener
    listener = EventListener(mock_hass, mock_coordinator)
    
    # Set up the mock coordinator.memory_handler
    mock_coordinator.memory_handler = MagicMock()
    mock_coordinator.memory_handler.store = MagicMock(return_value="memory_id_123")
    
    # Create a mock event with no old_state
    mock_event = MagicMock(spec=Event)
    mock_event.data = {
        "entity_id": "light.living_room",
        "old_state": None,
        "new_state": MagicMock(state="on"),
    }
    
    # Call _handle_state_changed_event
    await listener._handle_state_changed_event(mock_event)
    
    # Check that store was called on the memory handler
    mock_coordinator.memory_handler.store.assert_called_once()
    args, kwargs = mock_coordinator.memory_handler.store.call_args
    assert kwargs["agent_id"] == "test_agent"
    assert "light.living_room" in kwargs["content"]
    assert "on" in kwargs["content"]
    assert kwargs["metadata"]["type"] == "state_changed"
    assert kwargs["metadata"]["entity_id"] == "light.living_room"


async def test_event_listener_handle_state_changed_event_no_new_state(mock_hass, mock_coordinator):
    """Test the _handle_state_changed_event method with no new state."""
    # Create an event listener
    listener = EventListener(mock_hass, mock_coordinator)
    
    # Set up the mock coordinator.memory_handler
    mock_coordinator.memory_handler = MagicMock()
    mock_coordinator.memory_handler.store = MagicMock(return_value="memory_id_123")
    
    # Create a mock event with no new_state
    mock_event = MagicMock(spec=Event)
    mock_event.data = {
        "entity_id": "light.living_room",
        "old_state": MagicMock(state="off"),
        "new_state": None,
    }
    
    # Call _handle_state_changed_event
    await listener._handle_state_changed_event(mock_event)
    
    # Check that store was called on the memory handler
    mock_coordinator.memory_handler.store.assert_called_once()
    args, kwargs = mock_coordinator.memory_handler.store.call_args
    assert kwargs["agent_id"] == "test_agent"
    assert "light.living_room" in kwargs["content"]
    assert "off" in kwargs["content"]
    assert kwargs["metadata"]["type"] == "state_changed"
    assert kwargs["metadata"]["entity_id"] == "light.living_room"


async def test_event_listener_handle_service_call_event(mock_hass, mock_coordinator):
    """Test the _handle_service_call_event method of EventListener."""
    # Create an event listener
    listener = EventListener(mock_hass, mock_coordinator)
    
    # Set up the mock coordinator.memory_handler
    mock_coordinator.memory_handler = MagicMock()
    mock_coordinator.memory_handler.store = MagicMock(return_value="memory_id_123")
    
    # Create a mock event
    mock_event = MagicMock(spec=Event)
    mock_event.data = {
        "domain": "light",
        "service": "turn_on",
        "service_data": {"brightness": 255},
        "target": {"entity_id": "light.living_room"},
    }
    
    # Call _handle_service_call_event
    await listener._handle_service_call_event(mock_event)
    
    # Check that store was called on the memory handler
    mock_coordinator.memory_handler.store.assert_called_once()
    args, kwargs = mock_coordinator.memory_handler.store.call_args
    assert kwargs["agent_id"] == "test_agent"
    assert "light" in kwargs["content"]
    assert "turn_on" in kwargs["content"]
    assert "light.living_room" in kwargs["content"]
    assert kwargs["metadata"]["type"] == "service_call"
    assert kwargs["metadata"]["domain"] == "light"
    assert kwargs["metadata"]["service"] == "turn_on"


async def test_event_listener_handle_automation_triggered_event(mock_hass, mock_coordinator):
    """Test the _handle_automation_triggered_event method of EventListener."""
    # Create an event listener
    listener = EventListener(mock_hass, mock_coordinator)
    
    # Set up the mock coordinator.memory_handler
    mock_coordinator.memory_handler = MagicMock()
    mock_coordinator.memory_handler.store = MagicMock(return_value="memory_id_123")
    
    # Create a mock event
    mock_event = MagicMock(spec=Event)
    mock_event.data = {
        "name": "Test Automation",
        "entity_id": "automation.test_automation",
    }
    
    # Call _handle_automation_triggered_event
    await listener._handle_automation_triggered_event(mock_event)
    
    # Check that store was called on the memory handler
    mock_coordinator.memory_handler.store.assert_called_once()
    args, kwargs = mock_coordinator.memory_handler.store.call_args
    assert kwargs["agent_id"] == "test_agent"
    assert "Test Automation" in kwargs["content"]
    assert "automation.test_automation" in kwargs["content"]
    assert kwargs["metadata"]["type"] == "automation_triggered"
    assert kwargs["metadata"]["entity_id"] == "automation.test_automation"


@patch("custom_components.cortex_agent.event_listener.EventListener")
async def test_async_setup_event_listener(mock_event_listener_class, mock_hass, mock_coordinator):
    """Test the async_setup_event_listener function."""
    # Set up the mock EventListener
    mock_event_listener = MagicMock()
    mock_event_listener.async_start = AsyncMock()
    mock_event_listener_class.return_value = mock_event_listener
    
    # Call async_setup_event_listener
    listener = await async_setup_event_listener(mock_hass, mock_coordinator)
    
    # Check that EventListener was created with the right arguments
    mock_event_listener_class.assert_called_once_with(mock_hass, mock_coordinator)
    
    # Check that async_start was called
    mock_event_listener.async_start.assert_called_once()
    
    # Check that the listener was returned
    assert listener == mock_event_listener