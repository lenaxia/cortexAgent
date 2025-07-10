/**
 * @jest-environment jsdom
 */

// Mock the Home Assistant frontend
window.customCards = [];
window.loadCardHelpers = jest.fn().mockResolvedValue({});
window.customElements = {
  get: jest.fn().mockReturnValue(undefined),
  define: jest.fn(),
};

// Mock the document
document.querySelector = jest.fn().mockReturnValue({
  hass: {},
});
document.body = {
  appendChild: jest.fn(),
  removeChild: jest.fn(),
};

// Import the components
import '../cortex-conversation-card.js';
import '../cortex-tools-card.js';
import '../cortex-mcp-servers-card.js';
import '../index.js';

describe('Cortex Agent Frontend Components', () => {
  beforeEach(() => {
    // Clear mocks
    jest.clearAllMocks();
    window.customCards = [];
  });

  test('cortex-conversation-card is defined', () => {
    // Check that the component is defined
    expect(customElements.define).toHaveBeenCalledWith(
      'cortex-conversation-card',
      expect.any(Function)
    );
  });

  test('cortex-tools-card is defined', () => {
    // Check that the component is defined
    expect(customElements.define).toHaveBeenCalledWith(
      'cortex-tools-card',
      expect.any(Function)
    );
  });

  test('cortex-mcp-servers-card is defined', () => {
    // Check that the component is defined
    expect(customElements.define).toHaveBeenCalledWith(
      'cortex-mcp-servers-card',
      expect.any(Function)
    );
  });

  test('custom cards are registered', () => {
    // Import the index file to register the cards
    require('../index.js');

    // Check that the cards are registered
    expect(window.customCards.length).toBeGreaterThanOrEqual(3);
    expect(window.customCards).toContainEqual(
      expect.objectContaining({
        type: 'cortex-conversation-card',
        name: 'Cortex Agent Conversation',
      })
    );
    expect(window.customCards).toContainEqual(
      expect.objectContaining({
        type: 'cortex-tools-card',
        name: 'Cortex Agent Tools',
      })
    );
    expect(window.customCards).toContainEqual(
      expect.objectContaining({
        type: 'cortex-mcp-servers-card',
        name: 'Cortex Agent MCP Servers',
      })
    );
  });

  test('loadCardHelpers is called', () => {
    // Import the index file to register the cards
    require('../index.js');

    // Check that loadCardHelpers is called
    expect(window.loadCardHelpers).toHaveBeenCalled();
  });
});

describe('CortexConversationCard', () => {
  let card;

  beforeEach(() => {
    // Create a new card instance
    card = document.createElement('cortex-conversation-card');
    card.hass = {
      callWS: jest.fn().mockResolvedValue({
        messages: [
          {
            role: 'user',
            content: 'Hello',
            timestamp: '2023-01-01T00:00:00',
          },
          {
            role: 'assistant',
            content: 'Hi there',
            timestamp: '2023-01-01T00:00:01',
          },
        ],
      }),
    };
    card.entryId = 'test_entry_id';
    card.conversationId = 'test_conversation_id';
  });

  test('initializes with default values', () => {
    expect(card.messages).toEqual([]);
    expect(card.loading).toBe(false);
    expect(card.error).toBe(null);
    expect(card.inputText).toBe('');
  });

  test('fetches conversation on connected callback', async () => {
    // Mock the _fetchConversation method
    card._fetchConversation = jest.fn();

    // Call connectedCallback
    await card.connectedCallback();

    // Check that _fetchConversation was called
    expect(card._fetchConversation).toHaveBeenCalled();
  });
});

describe('CortexToolsCard', () => {
  let card;

  beforeEach(() => {
    // Create a new card instance
    card = document.createElement('cortex-tools-card');
    card.hass = {
      callWS: jest.fn().mockResolvedValue({
        tools: [
          {
            name: 'tool1',
            description: 'Tool 1',
            parameters: {
              param1: {
                type: 'string',
                description: 'Parameter 1',
              },
            },
            category: 'category1',
          },
          {
            name: 'tool2',
            description: 'Tool 2',
            parameters: {
              param2: {
                type: 'number',
                description: 'Parameter 2',
              },
            },
            category: 'category2',
          },
        ],
      }),
    };
    card.entryId = 'test_entry_id';
  });

  test('initializes with default values', () => {
    expect(card.tools).toEqual([]);
    expect(card.filteredTools).toEqual([]);
    expect(card.categories).toEqual([]);
    expect(card.selectedCategory).toBe('all');
    expect(card.loading).toBe(false);
    expect(card.error).toBe(null);
    expect(card.searchQuery).toBe('');
  });

  test('fetches tools on connected callback', async () => {
    // Mock the _fetchTools method
    card._fetchTools = jest.fn();

    // Call connectedCallback
    await card.connectedCallback();

    // Check that _fetchTools was called
    expect(card._fetchTools).toHaveBeenCalled();
  });
});

describe('CortexMcpServersCard', () => {
  let card;

  beforeEach(() => {
    // Create a new card instance
    card = document.createElement('cortex-mcp-servers-card');
    card.hass = {
      callWS: jest.fn().mockResolvedValue({
        servers: [
          {
            name: 'server1',
            tools: [
              {
                name: 'tool1',
                description: 'Tool 1',
                parameters: {
                  param1: {
                    type: 'string',
                    description: 'Parameter 1',
                  },
                },
              },
            ],
            tool_count: 1,
          },
          {
            name: 'server2',
            tools: [
              {
                name: 'tool2',
                description: 'Tool 2',
                parameters: {
                  param2: {
                    type: 'number',
                    description: 'Parameter 2',
                  },
                },
              },
            ],
            tool_count: 1,
          },
        ],
      }),
      callService: jest.fn().mockResolvedValue({}),
    };
    card.entryId = 'test_entry_id';
  });

  test('initializes with default values', () => {
    expect(card.servers).toEqual([]);
    expect(card.loading).toBe(false);
    expect(card.error).toBe(null);
    expect(card.showAddDialog).toBe(false);
    expect(card.newServer).toEqual({
      name: '',
      url: '',
      server_type: 'sse',
      auth_token: '',
    });
    expect(card.selectedServer).toBe(null);
    expect(card.showServerTools).toBe(false);
  });

  test('fetches servers on connected callback', async () => {
    // Mock the _fetchServers method
    card._fetchServers = jest.fn();

    // Call connectedCallback
    await card.connectedCallback();

    // Check that _fetchServers was called
    expect(card._fetchServers).toHaveBeenCalled();
  });
});