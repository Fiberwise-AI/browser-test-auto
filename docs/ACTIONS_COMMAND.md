# CommandActions Module Documentation

**File:** actions/command_actions.py

## Purpose
Executes CLI/system commands, analyzes logs, and verifies database state.

## Key Features
- Runs shell commands and fiber CLI operations.
- Analyzes server logs for errors, warnings, and performance issues.
- Executes SQL queries for database verification and data capture.

## Usage
Invoked by the modular test runner for steps with `"type": "command"`.

## Main Actions
- `run_command`
- `analyze_server_logs`
- `verify_database`
