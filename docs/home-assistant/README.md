# Home Assistant Integration Development Documentation

This directory contains comprehensive documentation for developing integrations for Home Assistant. Each document covers specific aspects of the integration development process, from basic file structure to advanced features like event handling and data fetching.

## Document Overview

### dev_101_services.md - Integration Service Actions

**Description:** This document provides a foundational introduction to creating custom service actions in Home Assistant integrations. It covers how to register services, handle service calls, and properly document them for users.

**When to use:** Reference this document when you need to add custom functionality to your integration that users can call as services. It's particularly useful when your integration needs to expose actions that aren't covered by Home Assistant's built-in services. The document includes a complete "hello world" example showing how to register a service, handle service calls, and create the necessary configuration files.

**Key topics:**
- Creating and registering custom services
- Handling service calls with parameters
- Documenting services with `services.yaml`
- Adding icons to services
- Creating entity-specific services
- Implementing service response data for advanced automations

### integration_00_file_structure.md - Integration File Structure

**Description:** This document outlines the basic file structure of a Home Assistant integration, explaining the purpose of each file and how they work together.

**When to use:** Consult this document when starting a new integration or trying to understand the organization of an existing one. It provides the foundation for understanding where different components of your integration should be placed and how Home Assistant locates and loads integrations.

**Key topics:**
- Basic file structure requirements (`manifest.json` and `__init__.py`)
- Platform files for device integration (`light.py`, `switch.py`, etc.)
- Service description files (`services.yaml`)
- Data update coordinator implementation (`coordinator.py`)
- Integration discovery and loading process
- Custom component locations and overriding built-in integrations

### integration_01_tests_file_structure.md - Integration File Structure (Duplicate)

**Description:** This appears to be a duplicate of the file structure document with the same content as `integration_00_file_structure.md`.

**When to use:** Same as `integration_00_file_structure.md`.

### integration_02_manifest.md - Integration Manifest

**Description:** This document provides detailed information about the `manifest.json` file, which is required for all integrations and contains metadata about the integration.

**When to use:** Reference this document when creating or updating your integration's manifest file. The manifest defines critical information about your integration, including dependencies, discovery mechanisms, and quality indicators.

**Key topics:**
- Required and optional manifest fields
- Integration types and their appropriate use cases
- Dependency management between integrations
- Device discovery mechanisms (Bluetooth, SSDP, Zeroconf, etc.)
- Integration quality scale requirements
- IoT class definitions
- Virtual integrations for product support

### integration_03_config_flow_handler.md - Config Flow

**Description:** This document explains how to implement a configuration flow for your integration, allowing users to set up your integration through the Home Assistant UI.

**When to use:** Consult this document when implementing user-facing configuration for your integration. Config flows provide a standardized way for users to configure your integration, handle authentication, and manage discovery of devices or services.

**Key topics:**
- Creating a config flow handler
- Defining configuration steps
- Managing unique IDs to prevent duplicate setups
- Handling device discovery
- Implementing OAuth2 authentication
- Translating configuration UI elements
- Handling configuration migration
- Implementing reauthentication flows
- Creating subentry flows for complex configurations

### integration_04_options_flow_handler.md - Options Flow

**Description:** This document covers how to implement an options flow, which allows users to modify the behavior of an already configured integration.

**When to use:** Reference this document when you need to provide users with the ability to change settings after the initial setup. Options flows are ideal for configuration that might change over time, such as which devices to include or specific behavior preferences.

**Key topics:**
- Creating an options flow handler
- Implementing the options UI
- Handling option updates
- Registering update listeners to react to option changes

### integration_05_diagnostics.md - Integration Diagnostics

**Description:** This document explains how to implement diagnostics capabilities for your integration, helping users gather troubleshooting data.

**When to use:** Implement diagnostics when you want to provide users with an easy way to collect relevant data for troubleshooting issues with your integration. This is particularly valuable for complex integrations or those that interact with external APIs or devices.

**Key topics:**
- Implementing config entry diagnostics
- Implementing device-specific diagnostics
- Safely redacting sensitive information
- Providing useful diagnostic data for troubleshooting

### integration_06_system_health.md - Integration System Health

**Description:** This document covers how to implement system health information for your integration, providing users with insights into the operational status of your integration.

**When to use:** Add system health support when you want to expose information about the current state of your integration, such as API connectivity, quota usage, or other operational metrics. This helps users understand if the integration is functioning correctly.

**Key topics:**
- Registering system health callbacks
- Providing both synchronous and asynchronous health information
- Translating system health information
- Testing connectivity to external services

### integration_07_fetching_data.md - Fetching Data

**Description:** This document explains different approaches to fetching data from APIs and devices, including push and poll methods, and how to implement them efficiently.

**When to use:** Reference this document when designing how your integration will retrieve data from external sources. It provides patterns for efficient data retrieval that minimize resource usage and maximize responsiveness.

**Key topics:**
- Push vs. poll data retrieval methods
- Using the DataUpdateCoordinator for efficient polling
- Handling API authentication errors
- Coordinating updates across multiple entities
- Controlling polling intervals
- Managing request parallelism

### integration_08_listen_events.md - Listening for Events

**Description:** This document details how to listen for events within Home Assistant and react to them in your integration.

**When to use:** Consult this document when your integration needs to respond to events occurring within Home Assistant, such as state changes, time-based events, or system events.

**Key topics:**
- Available event helpers for different use cases
- Tracking entity state changes
- Tracking template changes
- Tracking entity registry changes
- Tracking time changes and sun events
- Listening directly to the event bus
- Common events and their appropriate use

### integration_09_firing_events.md - Firing Events

**Description:** This document explains how to fire events from your integration to notify Home Assistant about external events.

**When to use:** Reference this document when your integration needs to inform Home Assistant about events occurring in external devices or services, such as motion detection or button presses.

**Key topics:**
- Properly formatting and firing events
- Attributing events to specific devices
- Making events accessible to users through device triggers
- Best practices for event handling

## Getting Started

If you're new to Home Assistant integration development, we recommend starting with the following documents in order:

1. `integration_00_file_structure.md` - Understand the basic structure
2. `integration_02_manifest.md` - Learn how to define your integration
3. `integration_03_config_flow_handler.md` - Implement user configuration
4. `integration_07_fetching_data.md` - Learn how to retrieve data efficiently

For more advanced features, consult the other documents as needed for your specific integration requirements.
