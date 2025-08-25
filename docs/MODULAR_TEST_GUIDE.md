

# FiberWise Modular Test Guide

> **NOTE:** All tests are defined in JSON and executed via `json_script_runner_modular.py`.

## Best Practices

- Use descriptive step IDs and script names for clarity.
- Keep each test focused on a single workflow or feature.
- Use session variables to share data between steps.
- Set `auto_cleanup: false` for debugging and artifact preservation.
- Always check selectors and wait conditions for browser actions.
- Use fallback app paths and robust queries for resilience.


## Troubleshooting Common Mistakes

- **Test not running:** Ensure your JSON script is valid and referenced correctly.
- **Selector or element errors:** Double-check selectors and add waits as needed.

This guide explains how to create and run modular tests using the `json_script_runner_modular.py` system.

> **⚠️ IMPORTANT**: For proven working patterns and correct action names, see **[SMART_TEST_WRITING_GUIDE.md](./SMART_TEST_WRITING_GUIDE.md)** - it contains tested examples and common mistakes to avoid.

## Overview

The modular test system allows you to create comprehensive tests using JSON configuration files that combine different types of actions:
- **Instance actions**: Create and manage temporary FiberWise instances
- **Browser actions**: Automate web browser interactions
- **Command actions**: Execute CLI commands and system operations
- **Database actions**: Query and verify database state

## Test Script Structure

### Basic JSON Structure

```json
{
  "script_name": "your_test_name",
  "description": "Description of what your test does",
  "version": "1.0",
  "settings": {
    "headless": false,
    "use_temp_instance": true,
    "video_recording": true,
    "take_screenshots": true,
    "auto_cleanup": false
  },
  "steps": [
    // Your test steps go here
  ]
}
```

### Settings Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `headless` | boolean | false | Run browser tests without UI |
| `use_temp_instance` | boolean | true | Create temporary instance for testing |
| `video_recording` | boolean | true | Record video of browser interactions |
| `take_screenshots` | boolean | true | Take screenshots during test |
| `auto_cleanup` | boolean | false | Automatically clean up resources after test |

## Step Types and Actions

### 1. Instance Actions (`type: "instance"`)

Create and manage temporary FiberWise instances.

#### `create_temp_instance`
Creates a new temporary instance with isolated database and configuration.

```json
{
  "id": "setup",
  "type": "instance",
  "action": "create_temp_instance",
  "description": "Create and start temp FiberWise instance"
}
```

### 2. Browser Actions (`type: "browser"`)

Automate web browser interactions using Playwright.

#### `register_multiple_users`
Register one or more test users.

```json
{
  "id": "register_user",
  "type": "browser",
  "action": "register_multiple_users",
  "description": "Register test users",
  "config": {
    "headless": true,
    "users": [
      {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
      }
    ]
  }
}
```

#### `test_login`
Login with user credentials.

```json
{
  "id": "login",
  "type": "browser",
  "action": "test_login",
  "description": "Login with test user",
  "config": {
    "username": "testuser",
    "password": "TestPassword123!",
    "keep_page_open": true,
    "take_screenshot": true
  }
}
```

#### `navigate_and_verify`
Navigate to a specific page and verify it loads.

```json
{
  "id": "navigate_page",
  "type": "browser",
  "action": "navigate_and_verify",
  "description": "Navigate to target page",
  "config": {
    "url": "/agents",
    "take_screenshot": true,
    "keep_page_open": true,
    "wait_for_selector": ".agents-grid"
  }
}
```

#### `create_api_key`
Create an API key through the browser interface.

```json
{
  "id": "create_api_key",
  "type": "browser",
  "action": "create_api_key",
  "description": "Create API key",
  "config": {
    "key_name": "Test API Key",
    "scopes": ["read:all", "write:all"],
    "take_screenshot": true,
    "keep_page_open": true
  }
}
```

### 3. Command Actions (`type: "command"`)

Execute CLI commands and system operations.

#### `run_cli_command`
Execute a CLI command.

```json
{
  "id": "cli_command",
  "type": "command",
  "action": "run_cli_command",
  "description": "Execute CLI command",
  "config": {
    "command": "fiber account list-providers",
    "working_directory": "/path/to/instance",
    "timeout": 30,
    "capture_output": true
  }
}
```

#### `analyze_server_logs`
Analyze server logs for issues.

```json
{
  "id": "check_logs",
  "type": "command",
  "action": "analyze_server_logs",
  "description": "Check server logs",
  "config": {
    "log_types": ["error", "warning"],
    "check_auth_patterns": true,
    "include_performance": true,
    "generate_summary": true
  }
}
```

### 4. Database Actions (`type: "database"`)

Query and verify database state.

```json
{
  "id": "verify_db",
  "type": "database",
  "action": "verify_records",
  "description": "Verify database records",
  "config": {
    "queries": [
      {
        "name": "check_providers",
        "sql": "SELECT COUNT(*) as count FROM llm_providers WHERE name LIKE '%Test%'",
        "expected_count": 1
      }
    ]
  }
}
```

## Common Test Patterns

### 1. Basic Web Page Test

```json
{
  "script_name": "basic_page_test",
  "description": "Test basic page navigation and functionality",
  "settings": {
    "headless": false,
    "use_temp_instance": true,
    "take_screenshots": true
  },
  "steps": [
    {
      "id": "setup",
      "type": "instance",
      "action": "create_temp_instance",
      "description": "Create temp instance"
    },
    {
      "id": "register",
      "type": "browser",
      "action": "register_multiple_users",
      "description": "Register test user",
      "config": {
        "users": [{"username": "tester", "email": "test@example.com", "password": "Test123!"}]
      }
    },
    {
      "id": "login",
      "type": "browser",
      "action": "test_login",
      "description": "Login",
      "config": {"username": "tester", "password": "Test123!"}
    },
    {
      "id": "navigate",
      "type": "browser",
      "action": "navigate_and_verify",
      "description": "Navigate to target page",
      "config": {"url": "/your-page", "take_screenshot": true}
    }
  ]
}
```

### 2. CLI Integration Test

```json
{
  "script_name": "cli_integration_test",
  "description": "Test CLI commands with web verification",
  "steps": [
    {
      "id": "setup",
      "type": "instance",
      "action": "create_temp_instance",
      "description": "Create temp instance"
    },
    {
      "id": "register",
      "type": "browser",
      "action": "register_multiple_users",
      "description": "Register user",
      "config": {
        "users": [{"username": "cli_user", "email": "cli@example.com", "password": "Cli123!"}]
      }
    },
    {
      "id": "create_api_key",
      "type": "browser",
      "action": "create_api_key",
      "description": "Create API key for CLI",
      "config": {"key_name": "CLI Key", "scopes": ["read:all", "write:all"]}
    },
    {
      "id": "cli_command",
      "type": "command",
      "action": "run_cli_command",
      "description": "Execute CLI command",
      "config": {"command": "fiber account list-providers"}
    },
    {
      "id": "verify_web",
      "type": "browser",
      "action": "navigate_and_verify",
      "description": "Verify results in web UI",
      "config": {"url": "/settings/providers"}
    }
  ]
}
```

## Running Tests

### Command Line Usage

```bash
# Run a specific test
python json_script_runner_modular.py scripts/your_test.json

# Run with custom settings
python json_script_runner_modular.py scripts/your_test.json --headless --no-video

# Run all tests in a directory
python json_script_runner_modular.py scripts/*.json
```

### Directory Structure

```
fiberwise-browser-tests/
├── json_script_runner_modular.py     # Main test runner
├── scripts/                          # Test scripts
│   ├── test_agents_page.json
│   ├── test_api_keys.json
│   └── your_test.json
├── actions/                          # Action implementations
│   ├── browser_actions.py
│   ├── command_actions.py
│   ├── database_actions.py
│   └── instance_actions.py
├── temp-instances/                   # Temporary test instances
├── demo_sessions/                    # Test output and recordings
└── logs/                            # Test logs
```

## Best Practices

### 1. Test Design
- **Single Responsibility**: Each test should focus on one feature or workflow
- **Descriptive Names**: Use clear, descriptive names for tests and steps
- **Error Handling**: Include verification steps to catch failures early
- **Clean State**: Always start with a clean temporary instance

### 2. Configuration Management
- Use meaningful step IDs for easier debugging
- Include screenshots for visual verification
- Set appropriate timeouts for slow operations
- Use `keep_page_open: true` for debugging

### 3. Data Management
- Use realistic but non-sensitive test data
- Create unique usernames/emails to avoid conflicts
- Clean up resources when `auto_cleanup: true`

### 4. Debugging
- Set `headless: false` to see browser interactions
- Enable `video_recording` for complex scenarios
- Check server logs with `analyze_server_logs` action
- Use database queries to verify state changes

## Advanced Features

### Custom Actions
You can extend the system by adding custom actions to the action modules:

```python
# In browser_actions.py
async def custom_page_action(page, config, context):
    """Custom action implementation"""
    # Your custom logic here
    return {"success": True, "data": "result"}
```

### Context Sharing
Actions can share data through the context object:

```json
{
  "id": "save_data",
  "type": "browser",
  "action": "extract_data",
  "config": {"save_to_context": "user_data"}
}
```

### Conditional Steps
Use context data to make steps conditional:

```json
{
  "id": "conditional_step",
  "type": "browser", 
  "action": "navigate_and_verify",
  "condition": "context.user_data.is_admin",
  "config": {"url": "/admin"}
}
```

## Troubleshooting

### Common Issues

1. **Instance Creation Fails**
   - Check if ports are available
   - Verify FiberWise installation
   - Check disk space for temp instances

2. **Browser Actions Timeout**
   - Increase timeout values
   - Check element selectors
   - Verify page loads completely

3. **CLI Commands Fail**
   - Verify working directory
   - Check command syntax
   - Ensure proper permissions

4. **Database Queries Fail**
   - Verify database schema
   - Check connection strings
   - Ensure migrations are applied

### Debug Mode

Enable debug mode for verbose logging:

```bash
python json_script_runner_modular.py scripts/your_test.json --debug
```

This will provide detailed logs of each step execution and help identify issues.
