# CortexAgent Tests

This directory contains tests for the CortexAgent Home Assistant integration.

## Test Structure

The tests are organized as follows:

- `conftest.py`: Contains pytest fixtures and configuration
- `test_cortex_agent/`: Contains tests for the CortexAgent integration
  - `test_init.py`: Tests for the integration setup
  - `test_conversation.py`: Tests for the conversation component
  - `test_conversation_manager.py`: Tests for the conversation manager
  - `test_memory_handler.py`: Tests for the memory handler
  - `test_mcp_connector.py`: Tests for the MCP connector
  - `test_model_provider.py`: Tests for the model provider
  - `test_tool_registry.py`: Tests for the tool registry
  - `test_tools.py`: Tests for the built-in tools

## Running Tests

To run the tests, you need to have pytest installed:

```bash
pip install pytest pytest-asyncio pytest-cov
```

### Running All Tests

```bash
pytest tests/
```

### Running Specific Test Files

```bash
pytest tests/test_cortex_agent/test_model_provider.py
```

### Running Tests with Coverage

```bash
pytest tests/ --cov=custom_components.cortex_agent
```

### Running Tests with Verbose Output

```bash
pytest tests/ -v
```

## Test Driven Development

These tests follow the test-driven development (TDD) approach:

1. Write a test for a feature
2. Run the test to verify it fails
3. Implement the feature
4. Run the test to verify it passes
5. Refactor the code if needed

## Mocking External Dependencies

The tests use mocking to isolate the code being tested from external dependencies:

- Home Assistant components are mocked
- External libraries like `strands` and `mcp` are mocked
- Storage is mocked to avoid file system operations

This allows the tests to run quickly and reliably without requiring a full Home Assistant instance or external services.