"""Frontend resources for CortexAgent integration."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

FRONTEND_SCRIPT_URL: Final = f"/frontend_es5/{DOMAIN}/index.js"
ICON: Final = "mdi:robot"


@callback
def async_register_frontend(hass: HomeAssistant) -> None:
    """Register the frontend resources."""
    # Register the built-in panel
    async_register_built_in_panel(
        hass,
        component_name=DOMAIN,
        sidebar_title="Cortex Agent",
        sidebar_icon=ICON,
        frontend_url_path=DOMAIN,
        require_admin=False,
        config={},
    )

    # Register the frontend resources
    hass.http.register_static_path(
        FRONTEND_SCRIPT_URL,
        str(Path(__file__).parent / "frontend/index.js"),
        True,
    )

    # Register the frontend components
    for component in ("cortex-conversation-card", "cortex-tools-card", "cortex-mcp-servers-card"):
        filename = f"{component}.js"
        url = f"/frontend_es5/{DOMAIN}/{filename}"
        filepath = Path(__file__).parent / f"frontend/{filename}"

        if filepath.exists():
            hass.http.register_static_path(url, str(filepath), True)
        else:
            _LOGGER.error("Frontend component file not found: %s", filepath)

    # Add the frontend script to the frontend resources
    hass.components.frontend.async_add_extra_js_url(hass, FRONTEND_SCRIPT_URL)


class CortexAgentFrontendView(HomeAssistantView):
    """View to serve CortexAgent frontend."""

    requires_auth = True
    url = "/cortex_agent/frontend"
    name = "cortex_agent:frontend"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass

    async def get(self, _request):
        """Handle GET requests."""
        return self.json({
            "panels": [
                {
                    "name": "conversation",
                    "title": "Conversation",
                    "icon": "mdi:chat",
                    "card_type": "cortex-conversation-card",
                },
                {
                    "name": "tools",
                    "title": "Tools",
                    "icon": "mdi:tools",
                    "card_type": "cortex-tools-card",
                },
                {
                    "name": "mcp_servers",
                    "title": "MCP Servers",
                    "icon": "mdi:server-network",
                    "card_type": "cortex-mcp-servers-card",
                },
            ]
        })
