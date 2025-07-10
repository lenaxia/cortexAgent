"""Pytest configuration for CortexAgent tests."""
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

# Add the project root directory to the path so we can import both custom_components and homeassistant
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Mock only external dependencies that might not be installed
MOCK_MODULES = [
    "strands",
    "strands.models",
    "strands.types",
    "strands.types.tools",
    "strands.tools",
    "strands.tools.mcp",
    "strands.tools.mcp.mcp_client",
    "strands_tools",
    "mcp",
    "mcp.client",
    "mcp.client.sse",
    "mcp.client.streamable_http",
    "mcp.client.stdio",
    "mcp.server",
    "boto3",
]

# Create module mocks with proper function behavior
for mod_name in MOCK_MODULES:
    # Create a class that will act as our module
    class MockModule:
        def __getattr__(self, name):
            # Return a function that accepts any arguments
            return lambda *args, **kwargs: MagicMock()
    
    # Create an instance of the class and assign it to sys.modules
    sys.modules[mod_name] = MockModule()


@pytest.fixture
def hass():
    """Fixture to provide a Home Assistant instance."""
    # For the config_flow tests, we need to mock HomeAssistant instead of creating a real one
    # because it requires an event loop
    from homeassistant.core import HomeAssistant
    
    mock_hass = MagicMock(spec=HomeAssistant)
    mock_hass.data = {}
    mock_hass.config_entries = MagicMock()
    mock_hass.config_entries.flow = MagicMock()
    mock_hass.config_entries.flow.async_init = AsyncMock()
    mock_hass.config_entries.flow.async_configure = AsyncMock()
    mock_hass.config_entries.options = MagicMock()
    mock_hass.config_entries.options.async_init = AsyncMock()
    mock_hass.config_entries.options.async_configure = AsyncMock()
    mock_hass.config_entries._entries = []
    
    return mock_hass

@pytest.fixture
def config_entry():
    """Fixture to provide a config entry."""
    from homeassistant.config_entries import ConfigEntry
    return ConfigEntry(
        version=1,
        domain="cortex_agent",
        title="Cortex Agent",
        data={},
        source="user",
        options={},
        entry_id="test_entry_id",
    )

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(monkeypatch):
    """Enable custom integrations defined in the test dir."""
    # Instead of mocking a non-existent function, let's patch the Integration.resolve_from_root method
    from homeassistant.loader import Integration
    
    original_resolve = Integration.resolve_from_root
    
    @classmethod
    def mock_resolve_from_root(cls, hass, root_module, domain):
        """Mock resolve_from_root to always return a valid integration."""
        integration = original_resolve(cls, hass, root_module, domain)
        if integration is not None:
            return integration
            
        # If the integration wasn't found, create a mock integration
        import pathlib
        
        manifest = {
            "domain": domain,
            "name": domain,
            "version": "1.0.0",
            "documentation": "https://www.home-assistant.io/",
            "dependencies": [],
            "codeowners": [],
            "requirements": [],
        }
        
        return cls(
            hass,
            f"{root_module.__name__}.{domain}",
            pathlib.Path(f"/mock/path/{domain}"),
            manifest,
            set(),
        )
    
    monkeypatch.setattr(Integration, "resolve_from_root", mock_resolve_from_root)

@pytest.fixture
def hass_storage():
    """Fixture to mock storage."""
    with patch("homeassistant.helpers.storage.Store") as mock_store:
        yield mock_store
