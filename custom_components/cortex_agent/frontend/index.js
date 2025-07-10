import "./cortex-conversation-card.js";
import "./cortex-tools-card.js";
import "./cortex-mcp-servers-card.js";

// Register the custom cards with the frontend
window.customCards = window.customCards || [];
window.customCards.push({
  type: "cortex-conversation-card",
  name: "Cortex Agent Conversation",
  description: "A card for interacting with Cortex Agent conversations",
});
window.customCards.push({
  type: "cortex-tools-card",
  name: "Cortex Agent Tools",
  description: "A card for managing Cortex Agent tools",
});
window.customCards.push({
  type: "cortex-mcp-servers-card",
  name: "Cortex Agent MCP Servers",
  description: "A card for managing Cortex Agent MCP servers",
});

// Register the custom cards with the Lovelace editor
const fireEvent = (node, type, detail = {}, options = {}) => {
  const event = new Event(type, {
    bubbles: options.bubbles === undefined ? true : options.bubbles,
    cancelable: Boolean(options.cancelable),
    composed: options.composed === undefined ? true : options.composed,
  });
  event.detail = detail;
  node.dispatchEvent(event);
  return event;
};

if (window.loadCardHelpers) {
  window.loadCardHelpers().then((helpers) => {
    const updateCardEditor = async (type) => {
      const cardHelpers = await window.loadCardHelpers();
      const tag = type.replace("cortex-", "hui-cortex-") + "-editor";
      if (customElements.get(tag)) return;

      const configurator = document.createElement(tag);
      configurator.hass = document.querySelector("home-assistant").hass;
      configurator.setConfig({});
      document.body.appendChild(configurator);
      document.body.removeChild(configurator);
    };

    const cortexConversationConfigSpec = {
      type: "object",
      properties: {
        type: { type: "string", enum: ["cortex-conversation-card"] },
        entry_id: { type: "string", description: "Config entry ID for the Cortex Agent" },
        conversation_id: { type: "string", description: "Optional conversation ID to load" },
      },
      required: ["type", "entry_id"],
    };

    const cortexToolsConfigSpec = {
      type: "object",
      properties: {
        type: { type: "string", enum: ["cortex-tools-card"] },
        entry_id: { type: "string", description: "Config entry ID for the Cortex Agent" },
      },
      required: ["type", "entry_id"],
    };

    const cortexMcpServersConfigSpec = {
      type: "object",
      properties: {
        type: { type: "string", enum: ["cortex-mcp-servers-card"] },
        entry_id: { type: "string", description: "Config entry ID for the Cortex Agent" },
      },
      required: ["type", "entry_id"],
    };

    // Register card editor for conversation card
    window.customCards.push({
      type: "cortex-conversation-card",
      name: "Cortex Agent Conversation",
      preview: false,
      description: "A card for interacting with Cortex Agent conversations",
      configSchema: cortexConversationConfigSpec,
    });

    // Register card editor for tools card
    window.customCards.push({
      type: "cortex-tools-card",
      name: "Cortex Agent Tools",
      preview: false,
      description: "A card for managing Cortex Agent tools",
      configSchema: cortexToolsConfigSpec,
    });

    // Register card editor for MCP servers card
    window.customCards.push({
      type: "cortex-mcp-servers-card",
      name: "Cortex Agent MCP Servers",
      preview: false,
      description: "A card for managing Cortex Agent MCP servers",
      configSchema: cortexMcpServersConfigSpec,
    });

    updateCardEditor("cortex-conversation-card");
    updateCardEditor("cortex-tools-card");
    updateCardEditor("cortex-mcp-servers-card");

    // Dispatch event to notify the frontend that the cards are available
    fireEvent(window, "cortex-agent-cards-loaded");
  });
}