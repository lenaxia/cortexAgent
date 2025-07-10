import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

class CortexToolsCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      entryId: { type: String },
      tools: { type: Array },
      filteredTools: { type: Array },
      selectedCategory: { type: String },
      categories: { type: Array },
      loading: { type: Boolean },
      error: { type: String },
      searchQuery: { type: String },
    };
  }

  constructor() {
    super();
    this.tools = [];
    this.filteredTools = [];
    this.categories = [];
    this.selectedCategory = "all";
    this.loading = false;
    this.error = null;
    this.searchQuery = "";
  }

  connectedCallback() {
    super.connectedCallback();
    this._fetchTools();
  }

  async _fetchTools() {
    if (!this.hass || !this.entryId) {
      return;
    }

    this.loading = true;
    this.error = null;

    try {
      const result = await this.hass.callWS({
        type: "cortex_agent/get_tools",
        entry_id: this.entryId,
      });

      this.tools = result.tools || [];
      
      // Extract unique categories
      const categorySet = new Set(this.tools.map(tool => tool.category || "uncategorized"));
      this.categories = ["all", ...Array.from(categorySet).sort()];
      
      this._filterTools();
    } catch (err) {
      this.error = `Error loading tools: ${err.message || err}`;
    } finally {
      this.loading = false;
    }
  }

  _filterTools() {
    let filtered = [...this.tools];
    
    // Filter by category
    if (this.selectedCategory && this.selectedCategory !== "all") {
      filtered = filtered.filter(tool => tool.category === this.selectedCategory);
    }
    
    // Filter by search query
    if (this.searchQuery) {
      const query = this.searchQuery.toLowerCase();
      filtered = filtered.filter(tool => 
        tool.name.toLowerCase().includes(query) || 
        tool.description.toLowerCase().includes(query)
      );
    }
    
    // Sort by name
    filtered.sort((a, b) => a.name.localeCompare(b.name));
    
    this.filteredTools = filtered;
  }

  _handleCategoryChange(e) {
    this.selectedCategory = e.target.value;
    this._filterTools();
  }

  _handleSearchInput(e) {
    this.searchQuery = e.target.value;
    this._filterTools();
  }

  _renderToolParameters(parameters) {
    if (!parameters || Object.keys(parameters).length === 0) {
      return html`<div class="no-parameters">No parameters</div>`;
    }

    return html`
      <div class="parameters">
        ${Object.entries(parameters).map(
          ([name, param]) => html`
            <div class="parameter">
              <div class="param-name">${name}</div>
              <div class="param-type">${param.type}</div>
              <div class="param-description">${param.description}</div>
            </div>
          `
        )}
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
          <div class="name">Cortex Agent Tools</div>
          <ha-icon-button
            icon="mdi:refresh"
            @click=${this._fetchTools}
            ?disabled=${this.loading}
          ></ha-icon-button>
        </div>

        <div class="filters">
          <div class="search">
            <ha-icon icon="mdi:magnify"></ha-icon>
            <input
              type="text"
              placeholder="Search tools..."
              .value=${this.searchQuery}
              @input=${this._handleSearchInput}
            />
          </div>
          
          <div class="category-filter">
            <select @change=${this._handleCategoryChange}>
              ${this.categories.map(
                category => html`
                  <option value=${category} ?selected=${this.selectedCategory === category}>
                    ${category.charAt(0).toUpperCase() + category.slice(1)}
                  </option>
                `
              )}
            </select>
          </div>
        </div>

        <div class="tools-container">
          ${this.error
            ? html`<div class="error">${this.error}</div>`
            : ""}
          ${this.loading
            ? html`<div class="loading">Loading tools...</div>`
            : ""}
          ${!this.loading && this.filteredTools.length === 0
            ? html`<div class="empty">No tools found</div>`
            : ""}
          ${this.filteredTools.map(
            tool => html`
              <div class="tool">
                <div class="tool-header">
                  <div class="tool-name">${tool.name}</div>
                  <div class="tool-category">${tool.category || "uncategorized"}</div>
                </div>
                <div class="tool-description">${tool.description}</div>
                <details>
                  <summary>Parameters</summary>
                  ${this._renderToolParameters(tool.parameters)}
                </details>
              </div>
            `
          )}
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
      .filters {
        display: flex;
        padding: 0 16px 16px;
        gap: 8px;
      }
      .search {
        flex: 1;
        display: flex;
        align-items: center;
        background-color: var(--secondary-background-color);
        border-radius: 4px;
        padding: 0 8px;
      }
      .search input {
        flex: 1;
        border: none;
        background: none;
        padding: 8px;
        color: var(--primary-text-color);
      }
      .search input:focus {
        outline: none;
      }
      .category-filter select {
        padding: 8px;
        border-radius: 4px;
        border: 1px solid var(--divider-color);
        background-color: var(--card-background-color);
        color: var(--primary-text-color);
      }
      .tools-container {
        flex: 1;
        overflow-y: auto;
        padding: 0 16px 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .tool {
        padding: 12px;
        border-radius: 8px;
        background-color: var(--secondary-background-color);
      }
      .tool-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      .tool-name {
        font-weight: bold;
      }
      .tool-category {
        font-size: 0.8em;
        padding: 2px 6px;
        border-radius: 4px;
        background-color: var(--primary-color);
        color: var(--text-primary-color);
      }
      .tool-description {
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
        background-color: rgba(var(--rgb-primary-color), 0.1);
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
    `;
  }
}

customElements.define("cortex-tools-card", CortexToolsCard);