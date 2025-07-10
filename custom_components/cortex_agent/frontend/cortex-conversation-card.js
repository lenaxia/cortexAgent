import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

class CortexConversationCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      entryId: { type: String },
      conversationId: { type: String },
      messages: { type: Array },
      loading: { type: Boolean },
      error: { type: String },
      inputText: { type: String },
    };
  }

  constructor() {
    super();
    this.messages = [];
    this.loading = false;
    this.error = null;
    this.inputText = "";
  }

  connectedCallback() {
    super.connectedCallback();
    this._fetchConversation();
  }

  async _fetchConversation() {
    if (!this.hass || !this.entryId || !this.conversationId) {
      return;
    }

    this.loading = true;
    this.error = null;

    try {
      const result = await this.hass.callWS({
        type: "cortex_agent/get_conversation_history",
        entry_id: this.entryId,
        conversation_id: this.conversationId,
      });

      this.messages = result.messages;
    } catch (err) {
      this.error = `Error loading conversation: ${err.message || err}`;
    } finally {
      this.loading = false;
    }
  }

  async _sendMessage() {
    if (!this.inputText.trim()) {
      return;
    }

    const text = this.inputText.trim();
    this.inputText = "";

    // Add user message to UI immediately
    this.messages = [
      ...this.messages,
      {
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      },
    ];

    this.loading = true;

    try {
      // Send message to conversation agent
      const result = await this.hass.callWS({
        type: "conversation/process",
        text,
        conversation_id: this.conversationId,
        agent_id: this.entryId,
      });

      // Add assistant response to UI
      this.messages = [
        ...this.messages,
        {
          role: "assistant",
          content: result.response.speech.plain.speech,
          timestamp: new Date().toISOString(),
        },
      ];

      // Update conversation ID if it was created
      if (result.conversation_id && !this.conversationId) {
        this.conversationId = result.conversation_id;
      }
    } catch (err) {
      this.error = `Error sending message: ${err.message || err}`;
    } finally {
      this.loading = false;
    }
  }

  async _clearConversation() {
    if (!this.conversationId) {
      return;
    }

    try {
      await this.hass.callWS({
        type: "cortex_agent/clear_conversation",
        entry_id: this.entryId,
        conversation_id: this.conversationId,
      });

      this.messages = [];
    } catch (err) {
      this.error = `Error clearing conversation: ${err.message || err}`;
    }
  }

  _handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      this._sendMessage();
    }
  }

  render() {
    if (!this.hass) {
      return html`<div>Loading...</div>`;
    }

    return html`
      <ha-card>
        <div class="card-header">
          <div class="name">Cortex Agent Conversation</div>
          <ha-icon-button
            icon="mdi:delete"
            @click=${this._clearConversation}
            ?disabled=${!this.conversationId || this.loading}
          ></ha-icon-button>
        </div>

        <div class="conversation">
          ${this.error
            ? html`<div class="error">${this.error}</div>`
            : ""}
          ${this.loading && !this.messages.length
            ? html`<div class="loading">Loading conversation...</div>`
            : ""}
          ${this.messages.length === 0 && !this.loading
            ? html`<div class="empty">No messages yet. Start a conversation!</div>`
            : ""}
          ${this.messages.map(
            (msg) => html`
              <div class="message ${msg.role}">
                <div class="content">${msg.content}</div>
                <div class="timestamp">
                  ${msg.timestamp
                    ? new Date(msg.timestamp).toLocaleTimeString()
                    : ""}
                </div>
              </div>
            `
          )}
          ${this.loading && this.messages.length
            ? html`<div class="message assistant loading">
                <div class="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>`
            : ""}
        </div>

        <div class="input-container">
          <textarea
            placeholder="Type a message..."
            .value=${this.inputText}
            @input=${(e) => (this.inputText = e.target.value)}
            @keydown=${this._handleKeyDown}
            ?disabled=${this.loading}
          ></textarea>
          <ha-icon-button
            icon="mdi:send"
            @click=${this._sendMessage}
            ?disabled=${!this.inputText.trim() || this.loading}
          ></ha-icon-button>
        </div>
      </ha-card>
    `;
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      ha-card {
        display: flex;
        flex-direction: column;
        height: 100%;
        overflow: hidden;
      }
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
      }
      .name {
        font-weight: bold;
      }
      .conversation {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .message {
        padding: 12px;
        border-radius: 8px;
        max-width: 80%;
      }
      .message.user {
        align-self: flex-end;
        background-color: var(--primary-color);
        color: var(--text-primary-color);
      }
      .message.assistant {
        align-self: flex-start;
        background-color: var(--secondary-background-color);
        color: var(--primary-text-color);
      }
      .message.loading {
        background-color: var(--secondary-background-color);
        min-height: 24px;
        min-width: 60px;
      }
      .content {
        white-space: pre-wrap;
      }
      .timestamp {
        font-size: 0.8em;
        opacity: 0.7;
        margin-top: 4px;
        text-align: right;
      }
      .input-container {
        display: flex;
        padding: 16px;
        border-top: 1px solid var(--divider-color);
      }
      textarea {
        flex: 1;
        border: none;
        border-radius: 4px;
        padding: 8px;
        min-height: 40px;
        resize: none;
        background-color: var(--secondary-background-color);
        color: var(--primary-text-color);
      }
      textarea:focus {
        outline: none;
        box-shadow: 0 0 0 2px var(--primary-color);
      }
      .error {
        color: var(--error-color);
        padding: 8px;
        margin-bottom: 8px;
        border-radius: 4px;
        background-color: rgba(var(--rgb-error-color), 0.1);
      }
      .empty, .loading {
        text-align: center;
        padding: 24px;
        color: var(--secondary-text-color);
      }
      .typing-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
      }
      .typing-indicator span {
        width: 8px;
        height: 8px;
        background-color: var(--secondary-text-color);
        border-radius: 50%;
        animation: bounce 1.5s infinite ease-in-out;
      }
      .typing-indicator span:nth-child(1) {
        animation-delay: 0s;
      }
      .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
      }
      .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
      }
      @keyframes bounce {
        0%, 60%, 100% {
          transform: translateY(0);
        }
        30% {
          transform: translateY(-4px);
        }
      }
    `;
  }
}

customElements.define("cortex-conversation-card", CortexConversationCard);