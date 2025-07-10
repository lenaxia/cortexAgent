"""Tests for the CortexAgent entity module."""
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.cortex_agent.entity import (
    CortexAgentEntity,
    CortexAgentStatusEntity,
    CortexAgentModelEntity,
    CortexAgentMemoryEntity,
    CortexAgentConversationEntity,
    CortexAgentToolsEntity,
)
from custom_components.cortex_agent.coordinator import (
    CortexAgentCoordinator,
    CortexAgentData,
)


@pytest.fixture
def mock_hass():
    """Fixture to provide a mock hass instance."""
    return MagicMock()


@pytest.fixture
def mock_coordinator(mock_hass):
    """Fixture to provide a mock coordinator."""
    coordinator = MagicMock(spec=CortexAgentCoordinator)
    coordinator.hass = mock_hass
    coordinator.agent_id = "test_agent"
    coordinator.name = "Test Agent"
    
    # Set up the coordinator data
    coordinator.data = CortexAgentData(
        model_provider_connected=True,
        model_provider_name="OpenAI",
        model_provider_model="gpt-4",
        mcp_servers=[
            {
                "server_id": "server_123",
                "name": "Test Server",
                "server_type": "remote",
                "connected": True,
            },
        ],
        memory_count=10,
        conversation_history_length=5,
        available_tools=["tool1", "tool2"],
    )
    
    return coordinator


def test_cortex_agent_entity_init(mock_coordinator):
    """Test the initialization of CortexAgentEntity."""
    # Create an entity
    entity = CortexAgentEntity(mock_coordinator)
    
    # Check the entity properties
    assert entity.coordinator == mock_coordinator
    assert entity._attr_unique_id == "test_agent"
    assert entity._attr_name == "Test Agent"
    assert entity._attr_should_poll is False
    assert entity._attr_has_entity_name is True


def test_cortex_agent_entity_available(mock_coordinator):
    """Test the available property of CortexAgentEntity."""
    # Create an entity
    entity = CortexAgentEntity(mock_coordinator)
    
    # Check the available property
    assert entity.available is True
    
    # Set the coordinator data to None
    mock_coordinator.data = None
    
    # Check the available property again
    assert entity.available is False


def test_cortex_agent_status_entity_init(mock_coordinator):
    """Test the initialization of CortexAgentStatusEntity."""
    # Create an entity
    entity = CortexAgentStatusEntity(mock_coordinator)
    
    # Check the entity properties
    assert entity.coordinator == mock_coordinator
    assert entity._attr_unique_id == "test_agent_status"
    assert entity._attr_name == "Status"
    assert entity._attr_icon == "mdi:robot"


def test_cortex_agent_status_entity_native_value(mock_coordinator):
    """Test the native_value property of CortexAgentStatusEntity."""
    # Create an entity
    entity = CortexAgentStatusEntity(mock_coordinator)
    
    # Check the native_value property
    assert entity.native_value == "Connected"
    
    # Set the model provider to disconnected
    mock_coordinator.data.model_provider_connected = False
    
    # Check the native_value property again
    assert entity.native_value == "Disconnected"


def test_cortex_agent_status_entity_extra_state_attributes(mock_coordinator):
    """Test the extra_state_attributes property of CortexAgentStatusEntity."""
    # Create an entity
    entity = CortexAgentStatusEntity(mock_coordinator)
    
    # Check the extra_state_attributes property
    assert entity.extra_state_attributes == {
        "model_provider_name": "OpenAI",
        "model_provider_model": "gpt-4",
        "mcp_servers": [
            {
                "server_id": "server_123",
                "name": "Test Server",
                "server_type": "remote",
                "connected": True,
            },
        ],
    }


def test_cortex_agent_model_entity_init(mock_coordinator):
    """Test the initialization of CortexAgentModelEntity."""
    # Create an entity
    entity = CortexAgentModelEntity(mock_coordinator)
    
    # Check the entity properties
    assert entity.coordinator == mock_coordinator
    assert entity._attr_unique_id == "test_agent_model"
    assert entity._attr_name == "Model"
    assert entity._attr_icon == "mdi:brain"


def test_cortex_agent_model_entity_native_value(mock_coordinator):
    """Test the native_value property of CortexAgentModelEntity."""
    # Create an entity
    entity = CortexAgentModelEntity(mock_coordinator)
    
    # Check the native_value property
    assert entity.native_value == "OpenAI gpt-4"
    
    # Set the model provider to a different model
    mock_coordinator.data.model_provider_name = "Anthropic"
    mock_coordinator.data.model_provider_model = "claude-3"
    
    # Check the native_value property again
    assert entity.native_value == "Anthropic claude-3"


def test_cortex_agent_memory_entity_init(mock_coordinator):
    """Test the initialization of CortexAgentMemoryEntity."""
    # Create an entity
    entity = CortexAgentMemoryEntity(mock_coordinator)
    
    # Check the entity properties
    assert entity.coordinator == mock_coordinator
    assert entity._attr_unique_id == "test_agent_memory"
    assert entity._attr_name == "Memory"
    assert entity._attr_icon == "mdi:memory"


def test_cortex_agent_memory_entity_native_value(mock_coordinator):
    """Test the native_value property of CortexAgentMemoryEntity."""
    # Create an entity
    entity = CortexAgentMemoryEntity(mock_coordinator)
    
    # Check the native_value property
    assert entity.native_value == 10
    
    # Set the memory count to a different value
    mock_coordinator.data.memory_count = 20
    
    # Check the native_value property again
    assert entity.native_value == 20


def test_cortex_agent_conversation_entity_init(mock_coordinator):
    """Test the initialization of CortexAgentConversationEntity."""
    # Create an entity
    entity = CortexAgentConversationEntity(mock_coordinator)
    
    # Check the entity properties
    assert entity.coordinator == mock_coordinator
    assert entity._attr_unique_id == "test_agent_conversation"
    assert entity._attr_name == "Conversation"
    assert entity._attr_icon == "mdi:chat"


def test_cortex_agent_conversation_entity_native_value(mock_coordinator):
    """Test the native_value property of CortexAgentConversationEntity."""
    # Create an entity
    entity = CortexAgentConversationEntity(mock_coordinator)
    
    # Check the native_value property
    assert entity.native_value == 5
    
    # Set the conversation history length to a different value
    mock_coordinator.data.conversation_history_length = 15
    
    # Check the native_value property again
    assert entity.native_value == 15


def test_cortex_agent_tools_entity_init(mock_coordinator):
    """Test the initialization of CortexAgentToolsEntity."""
    # Create an entity
    entity = CortexAgentToolsEntity(mock_coordinator)
    
    # Check the entity properties
    assert entity.coordinator == mock_coordinator
    assert entity._attr_unique_id == "test_agent_tools"
    assert entity._attr_name == "Tools"
    assert entity._attr_icon == "mdi:tools"


def test_cortex_agent_tools_entity_native_value(mock_coordinator):
    """Test the native_value property of CortexAgentToolsEntity."""
    # Create an entity
    entity = CortexAgentToolsEntity(mock_coordinator)
    
    # Check the native_value property
    assert entity.native_value == 2
    
    # Set the available tools to a different value
    mock_coordinator.data.available_tools = ["tool1", "tool2", "tool3"]
    
    # Check the native_value property again
    assert entity.native_value == 3


def test_cortex_agent_tools_entity_extra_state_attributes(mock_coordinator):
    """Test the extra_state_attributes property of CortexAgentToolsEntity."""
    # Create an entity
    entity = CortexAgentToolsEntity(mock_coordinator)
    
    # Check the extra_state_attributes property
    assert entity.extra_state_attributes == {
        "tools": ["tool1", "tool2"],
    }