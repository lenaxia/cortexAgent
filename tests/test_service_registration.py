"""Test service registration for CortexAgent."""
from unittest.mock import patch, MagicMock

import pytest
from homeassistant.core import HomeAssistant
import voluptuous as vol

from custom_components.cortex_agent import async_register_services

async def test_async_register_services(hass: HomeAssistant):
    """Test service registration."""
    with patch(
        "homeassistant.core.ServiceRegistry.async_register"
    ) as mock_register:
        await async_register_services(hass)
        
        # Should register 6 services
        assert mock_register.call_count == 6
        
        # Verify reload service registration
        assert mock_register.call_args_list[0][0][1] == "reload"
        
        # Verify connect_mcp_server service schema
        connect_schema = mock_register.call_args_list[1][0][3]
        assert isinstance(connect_schema, vol.Schema)
        assert "name" in connect_schema.schema
        assert "url" in connect_schema.schema
        
        # Verify other service registrations
        assert mock_register.call_args_list[2][0][1] == "disconnect_mcp_server"
        assert mock_register.call_args_list[3][0][1] == "add_tool"
        assert mock_register.call_args_list[4][0][1] == "remove_tool"
        assert mock_register.call_args_list[5][0][1] == "clear_conversation"