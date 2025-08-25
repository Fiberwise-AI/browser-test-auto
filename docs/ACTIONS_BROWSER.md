# BrowserActions Module Documentation

**File:** actions/browser_actions.py

## Purpose
Automates browser-based test steps using Playwright.

## Key Features
- Handles navigation, login, registration, UI verification, and screenshots.
- Supports robust selectors and error handling for dynamic UIs.
- Can create API keys, configure LLM providers, and test chat/websocket isolation.
- Integrates with session variables for data sharing between steps.
- Provides advanced debugging: screenshots, network monitoring, and console log capture.

## Usage
Invoked automatically by the modular test runner when a JSON step has `"type": "browser"`.

## Main Actions
- `register_multiple_users`
- `test_login`
- `navigate_and_verify`
- `create_api_key`
- `configure_llm_provider`
- `test_websocket_isolation`
- ...and more
