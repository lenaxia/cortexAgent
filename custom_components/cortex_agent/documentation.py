"""Documentation generation for the CortexAgent integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import ATTR_ENTITY_ID, ATTR_FORMAT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ToolDocumentation:
    """Generates documentation for available tools."""

    def __init__(self, hass: HomeAssistant, tool_registry: Any):
        """Initialize the documentation generator.
        
        Args:
            hass: Home Assistant instance
            tool_registry: Tool registry instance
        """
        self.hass = hass
        self.tool_registry = tool_registry

    def generate_markdown(self) -> str:
        """Generate markdown documentation for all tools.
        
        Returns:
            Markdown documentation
        """
        categories = self.tool_registry.get_categories()

        lines = ["# Available Agent Tools", ""]
        lines.append("This document lists all tools available to your CortexAgent.")
        lines.append("")

        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        for category in sorted(categories):
            category_name = category.replace("_", " ").title()
            lines.append(f"- [{category_name}](#{category.lower().replace(' ', '-')})")
        lines.append("")

        # Generate documentation for each category
        for category in sorted(categories):
            category_name = category.replace("_", " ").title()
            lines.append(f"## {category_name}")
            lines.append("")

            # Get tools in this category
            tool_ids = self.tool_registry._categories.get(category, [])

            for tool_id in sorted(tool_ids):
                tool_data = self.tool_registry._tools.get(tool_id)
                if not tool_data:
                    continue

                metadata = tool_data["metadata"]

                # Tool name and description
                lines.append(f"### {metadata.get('name', tool_id)}")
                lines.append("")
                lines.append(metadata.get("description", "No description available."))
                lines.append("")

                # Parameters
                if "parameters" in metadata:
                    lines.append("#### Parameters")
                    lines.append("")
                    lines.append("| Name | Type | Description | Required |")
                    lines.append("|------|------|-------------|----------|")

                    for param_name, param_data in metadata["parameters"].items():
                        param_type = param_data.get("type", "any")
                        param_desc = param_data.get("description", "No description")
                        param_required = "Yes" if param_data.get("required", False) else "No"

                        lines.append(
                            f"| `{param_name}` | `{param_type}` | {param_desc} | {param_required} |"
                        )

                    lines.append("")

                # Examples
                if "examples" in metadata and metadata["examples"]:
                    lines.append("#### Examples")
                    lines.append("")
                    for example in metadata["examples"]:
                        lines.append(f"- {example}")
                    lines.append("")

                # Permissions
                if "permissions" in metadata and metadata["permissions"]:
                    lines.append("#### Required Permissions")
                    lines.append("")
                    for permission in metadata["permissions"]:
                        lines.append(f"- {permission}")
                    lines.append("")

        return "\n".join(lines)

    def generate_html(self) -> str:
        """Generate HTML documentation for all tools.
        
        Returns:
            HTML documentation
        """
        # Convert markdown to HTML
        markdown = self.generate_markdown()
        try:
            import markdown as md

            html = md.markdown(markdown, extensions=["tables"])

            # Add some basic styling
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>CortexAgent Tools Documentation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #2c3e50; }}
                    h2 {{ color: #3498db; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                    h3 {{ color: #2980b9; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; }}
                    th {{ background-color: #f2f2f2; text-align: left; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    code {{ background-color: #f8f8f8; padding: 2px 4px; border-radius: 4px; }}
                </style>
            </head>
            <body>
                {html}
            </body>
            </html>
            """
            return styled_html
        except ImportError:
            return f"<pre>{markdown}</pre>"

    async def async_register_services(self) -> None:
        """Register services for documentation."""
        # Register service to generate documentation
        self.hass.services.async_register(
            DOMAIN,
            "generate_tool_documentation",
            self._handle_generate_documentation,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_ENTITY_ID): cv.entity_id,
                    vol.Optional(ATTR_FORMAT, default="markdown"): vol.In(
                        ["markdown", "html"]
                    ),
                }
            ),
        )

    async def _handle_generate_documentation(self, service: ServiceCall) -> None:
        """Handle generate_tool_documentation service call.
        
        Args:
            service: Service call
        """
        format_type = service.data.get(ATTR_FORMAT, "markdown")

        if format_type == "html":
            content = self.generate_html()
        else:
            content = self.generate_markdown()

        # Fire event with documentation
        self.hass.bus.async_fire(
            f"{DOMAIN}_documentation_generated",
            {
                "entity_id": service.data[ATTR_ENTITY_ID],
                "content": content,
                "format": format_type,
            },
        )