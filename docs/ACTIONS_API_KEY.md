# APIKeyActions Module Documentation

**File:** actions/api_key_actions.py

## Purpose
Manages API key creation, listing, deletion, and testing.

## Key Features
- Automates UI flows for API key management.
- Supports capturing API secrets as session variables for later use.
- Can validate API key scopes and permissions.

## Usage
Invoked by the modular test runner for steps with `"type": "api_key"`.

## Main Actions
- `create_api_key`
- `list_api_keys`
- `delete_api_key`
- `test_api_key`
