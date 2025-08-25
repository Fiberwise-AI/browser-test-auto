# InstanceActions Module Documentation

**File:** actions/instance_actions.py

## Purpose
Manages the lifecycle of test environments for modular testing.

## Key Features
- Create, start, and clean up temporary FiberWise instances for each test.
- Supports connecting to existing instances and auto-discovers settings.
- Exposes instance URLs, ports, and paths as session variables for use in test steps.
- Can auto-discover existing users in the test database for reuse.

## Usage
Invoked automatically by the modular test runner when a JSON step has `"type": "instance"`.

## Main Actions
- `create_temp_instance`
- `start_existing_instance`
- `cleanup_instance`
- `fiber_install_app`

## Integration
Works closely with TempInstanceManager for full environment isolation and reproducibility.
