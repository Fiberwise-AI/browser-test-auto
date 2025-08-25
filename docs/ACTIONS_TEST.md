# TestActions Module Documentation

**File:** actions/test_actions.py

## Purpose
Handles specialized or meta-test actions, such as performance tests or API key scope validation.

## Key Features
- Provides advanced test logic and validation steps.
- Can be extended for custom test requirements.

## Usage
Invoked by the modular test runner for steps with `"type": "test"`.

## Main Actions
- `verify_api_keys`
- `test_api_key_scopes`
- `performance_test`
