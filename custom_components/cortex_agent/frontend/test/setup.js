// Mock the window object
window.customCards = [];
window.loadCardHelpers = jest.fn().mockResolvedValue({});
window.customElements = {
  get: jest.fn().mockReturnValue(undefined),
  define: jest.fn(),
};

// Mock the document object
document.querySelector = jest.fn().mockReturnValue({
  hass: {},
});
document.body = {
  appendChild: jest.fn(),
  removeChild: jest.fn(),
};

// Mock the lit-element module
jest.mock('https://unpkg.com/lit-element@2.4.0/lit-element.js?module', () => ({
  LitElement: class {
    static get properties() {
      return {};
    }
    constructor() {}
    connectedCallback() {}
    disconnectedCallback() {}
    render() {}
  },
  html: (strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''),
  css: (strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''),
}), { virtual: true });

// Mock the Home Assistant components
jest.mock('ha-card', () => ({
  __esModule: true,
  default: class {
    constructor() {}
  },
}), { virtual: true });

jest.mock('ha-icon-button', () => ({
  __esModule: true,
  default: class {
    constructor() {}
  },
}), { virtual: true });

// Mock the event dispatcher
global.fireEvent = jest.fn();

// Console error and warning mocks
console.error = jest.fn();
console.warn = jest.fn();