# Basic Example: Modular JSON Test Script

This document provides a complete, step-by-step example of a modular JSON test script for the FiberWise testing system. It covers all required fields, recommended patterns, and best practices for writing a robust, maintainable test.

---

## Example: User Registration and Login Test

```json
{
  "script_name": "basic_user_registration_and_login",
  "description": "Registers a new user and verifies login flow in a temp instance.",
  "version": "1.0",
  "settings": {
    "headless": true,
    "use_temp_instance": true,
    "video_recording": false,
    "take_screenshots": true,
    "auto_cleanup": false
  },
  "steps": [
    {
      "id": "setup",
      "type": "instance",
      "action": "create_temp_instance",
      "description": "Create and start a temporary FiberWise instance."
    },
    {
      "id": "register_user",
      "type": "browser",
      "action": "register_multiple_users",
      "description": "Register a new test user.",
      "config": {
        "users": [
          {
            "username": "testuser1",
            "email": "testuser1@example.com",
            "password": "TestPass123!"
          }
        ]
      }
    },
    {
      "id": "login_user",
      "type": "browser",
      "action": "test_login",
      "description": "Login with the new user and verify dashboard access.",
      "config": {
        "username": "testuser1",
        "password": "TestPass123!",
        "keep_page_open": true,
        "take_screenshot": true
      }
    },
    {
      "id": "verify_dashboard",
      "type": "browser",
      "action": "navigate_and_verify",
      "description": "Navigate to the dashboard and verify page loads.",
      "config": {
        "url": "/",
        "wait_for_selector": "body",
        "take_screenshot": true,
        "keep_page_open": true
      }
    },
    {
      "id": "analyze_logs",
      "type": "command",
      "action": "analyze_server_logs",
      "description": "Analyze server logs for errors and warnings.",
      "config": {
        "log_types": ["error", "warning"],
        "generate_summary": true
      }
    }
  ]
}
```

---

## Key Details & Best Practices

- **script_name**: Unique, descriptive name for the test (used for output directories).
- **description**: Clear summary of the test's purpose.
- **version**: Increment when making changes to the script.
- **settings**:
  - `headless`: Use `true` for fast, non-interactive runs; set `false` for debugging.
  - `use_temp_instance`: Always `true` for isolated, reproducible tests.
  - `video_recording`: Enable for debugging complex flows.
  - `take_screenshots`: Always `true` for visual validation and debugging.
  - `auto_cleanup`: Set `false` during development to preserve logs and artifacts.
- **steps**:
  - Always start with `create_temp_instance`.
  - Register users before login.
  - Use `keep_page_open: true` after login to maintain session.
  - Take screenshots after key actions.
  - Analyze logs at the end for errors and warnings.

## Output & Debugging

- Screenshots and logs are saved in `demo_sessions/<script_name>_<timestamp>/`.
- Temp instance files are in `temp-instances/<instance_id>/`.
- Use `auto_cleanup: false` to keep the environment for manual inspection.

## How to Run

```bash
python json_script_runner_modular.py scripts/basic_user_registration_and_login.json
```

---

This example can be copied and adapted for more complex scenarios. For more advanced patterns, see the other documentation files in the `docs/` folder.
