import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

class CortexMcpServersCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      entryId: { type: String },
      servers: { type: Array },
      loading: { type: Boolean },
      error: { type: String },
      showAddDialog: { type: Boolean },
      newServer: { type: Object },
      selectedServer: { type: Object },
      showServerTools: { type: Boolean },
    };
  }

  constructor() {
    super();
    this.servers = [];
    this.loading = false;
    this.error = null;
    this.showAddDialog = false;
    this.newServer = {
      name: "",
      url: "",
      server_type: "sse",
      auth_token: "",
    };
    this.selectedServer = null;
    this.showServerTools = false;
  }

  connectedCallback() {
    super.connectedCallback();
    this._fetchServers();
  }

  async _fetchServers() {
    if (!this.hass || !this.entryId) {
      return;
    }

    this.loading = true;
    this.error = null;

    try {
      const result = await this.hass.callWS({
        type: "cortex_agent/get_mcp_servers",
        entry_id: this.entryId,
      });

      this.servers = result.servers || [];
    } catch (err) {
      this.error = `Error loading MCP servers: ${err.message || err}`;
    } finally {
      this.loading = false;
    }
  }

  async _connectServer() {
    if (!this.newServer.name || !this.newServer.url) {
      this.error = "Name and URL are required";
      return;
    }

    this.loading = true;
    this.error = null;

    try {
      await this.hass.callService("cortex_agent", "connect_mcp_server", {
        entity_id: `cortex_agent.${this.entryId}`,
        name: this.newServer.name,
        url: this.newServer.url,
        server_type: this.newServer.server_type,
        auth_token: this.newServer.auth_token || undefined,
      });

      this.showAddDialog = false;
      this.newServer = {
        name: "",
        url: "",
        server_type: "sse",
        auth_token: "",
      };

      // Refresh the server list
      await this._fetchServers();
    } catch (err) {
      this.error = `Error connecting to MCP server: ${err.message || err}`;
    } finally {
      this.loading = false;
    }
  }

  async _disconnectServer(serverName) {
    this.loading = true;
    this.error = null;

    try {
      await this.hass.callService("cortex_agent", "disconnect_mcp_server", {
        entity_id: `cortex_agent.${this.entryId}`,
        name: serverName,
      });

      // Refresh the server list
      await this._fetchServers();
    } catch (err) {
      this.error = `Error disconnecting from MCP server: ${err.message || err}`;
    } finally {
      this.loading = false;
    }
  }

  _showServerTools(server) {
    this.selectedServer = server;
    this.showServerTools = true;
  }

  _hideServerTools() {
    this.showServerTools = false;
  }

  _renderAddDialog() {
    if (!this.showAddDialog) {
      return "";
    }

    return html`
      <div class="dialog-overlay">
        <div class="dialog">
          <div class="dialog-header">
            <h3>Add MCP Server</h3>
            <ha-icon-button
              icon="mdi:close"
              @click=${() => (this.showAddDialog = false)}
            ></ha-icon-button>
          </div>
          <div class="dialog-content">
            <div class="form-field">
              <label for="server-name">Name</label>
              <input
                id="server-name"
                type="text"
                .value=${this.newServer.name}
                @input=${(e) => (this.newServer.name = e.target.value)}
                placeholder="Server name"
              />
            </div>
            <div class="form-field">
              <label for="server-url">URL</label>
              <input
                id="server-url"
                type="text"
                .value=${this.newServer.url}
                @input=${(e) => (this.newServer.url = e.target.value)}
                placeholder="https://example.com/mcp"
              />
            </div>
            <div class="form-field">
              <label for="server-type">Server Type</label>
              <select
                id="server-type"
                .value=${this.newServer.server_type}
                @change=${(e) => (this.newServer.server_type = e.target.value)}
              >
                <option value="sse">SSE</option>
                <option value="streamable_http">Streamable HTTP</option>
              </select>
            </div>
            <div class="form-field">
              <label for="auth-token">Auth Token (optional)</label>
              <input
                id="auth-token"
                type="password"
                .value=${this.newServer.auth_token}
                @input=${(e) => (this.newServer.auth_token = e.target.value)}
                placeholder="Authentication token"
              />
            </div>
          </div>
          <div class="dialog-actions">
            <mwc-button
              @click=${() => (this.showAddDialog = false)}
              ?disabled=${this.loading}
            >
              Cancel
            </mwc-button>
            <mwc-button
              @click=${this._connectServer}
              ?disabled=${this.loading || !this.newServer.name || !this.newServer.url}
            >
              Connect
            </mwc-button>
          </div>
        </div>
      </div>
    `;
  }

  _renderServerTools() {
    if (!this.showServerTools || !this.selectedServer) {
      return "";
    }

    return html`
      <div class="dialog-overlay">
        <div class="dialog">
          <div class="dialog-header">
            <h3>${this.selectedServer.name} Tools</h3>
            <ha-icon-button
              icon="mdi:close"
              @click=${this._hideServerTools}
            ></ha-icon-button>
          </div>
          <div class="dialog-content">
            <div class="server-tools">
              ${this.selectedServer.tools.length === 0
                ? html`<div class="empty">No tools available</div>`
                : html`
                    <div class="tools-list">
                      ${this.selectedServer.tools.map(
                        (tool) => html`
                          <div class="tool">
                            <div class="tool-name">${tool.name}</div>
                            <div class="tool-description">
                              ${tool.description}
                            </div>
                            <details>
                              <summary>Parameters</summary>
                              <div class="parameters">
                                ${Object.entries(tool.parameters || {}).map(
                                  ([name, param]) => html`
                                    <div class="parameter">
                                      <div class="param-name">${name}</div>
                                      <div class="param-type">${param.type}</div>
                                      <div class="param-description">
                                        ${param.description}
                                      </div>
                                    </div>
                                  `
                                )}
                                ${Object.keys(tool.parameters || {}).length === 0
                                  ? html`<div class="no-parameters">No parameters</div>`
                                  : ""}
                              </div>
                            </details>
                          </div>
                        `
                      )}
                    </div>
                  `}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  render() {
    if (!this.hass) {
      return html`<div>Loading...</div>`;
    }

    return html`
      <ha-card>
        <div class="card-header">
          <div class="name">MCP Servers</div>
          <div class="actions">
            <ha-icon-button
              icon="mdi:refresh"
              @click=${this._fetchServers}
              ?disabled=${this.loading}
            ></ha-icon-button>
            <ha-icon-button
              icon="mdi:plus"
              @click=${() => (this.showAddDialog = true)}
              ?disabled=${this.loading}
            ></ha-icon-button>
          </div>
        </div>

        <div class="servers-container">
          ${this.error
            ? html`<div class="error">${this.error}</div>`
            : ""}
          ${this.loading && !this.servers.length
            ? html`<div class="loading">Loading servers...</div>`
            : ""}
          ${!this.loading && this.servers.length === 0
            ? html`<div class="empty">No MCP servers connected</div>`
            : ""}
          ${this.servers.map(
            (server) => html`
              <div class="server">
                <div class="server-header">
                  <div class="server-name">${server.name}</div>
                  <div class="server-actions">
                    <ha-icon-button
                      icon="mdi:tools"
                      @click=${() => this._showServerTools(server)}
                      title="View tools"
                    ></ha-icon-button>
                    <ha-icon-button
                      icon="mdi:lan-disconnect"
                      @click=${() => this._disconnectServer(server.name)}
                      title="Disconnect"
                      ?disabled=${this.loading}
                    ></ha-icon-button>
                  </div>
                </div>
                <div class="server-info">
                  <div class="tool-count">
                    ${server.tool_count} tool${server.tool_count !== 1 ? "s" : ""}
                  </div>
                </div>
              </div>
            `
          )}
        </div>

        ${this._renderAddDialog()}
        ${this._renderServerTools()}
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
      .actions {
        display: flex;
      }
      .servers-container {
        flex: 1;
        overflow-y: auto;
        padding: 0 16px 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .server {
        padding: 12px;
        border-radius: 8px;
        background-color: var(--secondary-background-color);
      }
      .server-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .server-name {
        font-weight: bold;
      }
      .server-actions {
        display: flex;
      }
      .server-info {
        margin-top: 8px;
        font-size: 0.9em;
        color: var(--secondary-text-color);
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
      .dialog-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .dialog {
        background-color: var(--card-background-color);
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        width: 90%;
        max-width: 500px;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
      }
      .dialog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid var(--divider-color);
      }
      .dialog-header h3 {
        margin: 0;
      }
      .dialog-content {
        padding: 16px;
        overflow-y: auto;
        flex: 1;
      }
      .dialog-actions {
        padding: 8px 16px 16px;
        display: flex;
        justify-content: flex-end;
        gap: 8px;
      }
      .form-field {
        margin-bottom: 16px;
      }
      .form-field label {
        display: block;
        margin-bottom: 4px;
        font-weight: 500;
      }
      .form-field input, .form-field select {
        width: 100%;
        padding: 8px;
        border-radius: 4px;
        border: 1px solid var(--divider-color);
        background-color: var(--card-background-color);
        color: var(--primary-text-color);
      }
      .server-tools {
        max-height: 60vh;
        overflow-y: auto;
      }
      .tools-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .tool {
        padding: 12px;
        border-radius: 4px;
        background-color: rgba(var(--rgb-primary-color), 0.1);
      }
      .tool-name {
        font-weight: bold;
        margin-bottom: 4px;
      }
      .tool-description {
        font-size: 0.9em;
        margin-bottom: 8px;
      }
      details {
        border-top: 1px solid var(--divider-color);
        padding-top: 8px;
      }
      summary {
        cursor: pointer;
        color: var(--secondary-text-color);
      }
      .parameters {
        margin-top: 8px;
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .parameter {
        padding: 8px;
        border-radius: 4px;
        background-color: rgba(var(--rgb-primary-color), 0.05);
      }
      .param-name {
        font-weight: bold;
      }
      .param-type {
        font-size: 0.8em;
        color: var(--secondary-text-color);
      }
      .param-description {
        font-size: 0.9em;
        margin-top: 4px;
      }
      .no-parameters {
        color: var(--secondary-text-color);
        font-style: italic;
        padding: 8px 0;
      }
    `;
  }
}

customElements.define("cortex-mcp-servers-card", CortexMcpServersCard);