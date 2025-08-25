
# FiberWise Modular Browser Testing Suite



## 🧩 Modular Testing System

- **Action-based**: Organize tests by browser, API, user, instance, and more.
- **Session variables**: Share data between steps.
- **Temp instances**: Isolated, auto-managed test environments.
- **Comprehensive logging**: Screenshots, videos, and console logs for every run.
- **Purpose-built for agent development**: Designed so agents (and humans) can create, run, and refine tests for FiberWise apps.
- **Agent-driven test authoring**: Agents can generate new tests, review logs, and present screenshots for human confirmation, enabling rapid iteration and improvement.
- **Human-in-the-loop workflows**: Screenshots and logs are surfaced for review, so humans can confirm results, provide feedback, and cycle improvements with the agent.

## 📂 Project Structure

```
fiberwise-browser-tests/
├── actions/               # Modular action handlers
├── scripts/               # JSON test scripts
├── utils/                 # Core utilities  
├── demo_sessions/         # Test output and logs
├── temp-instances/        # Temporary app instances (auto-created)
└── requirements.txt       # Python dependencies
```

## 🛠️ Running Tests

```bash
python json_script_runner_modular.py scripts/<script_name>.json
```

- All configuration is in your JSON script.
- See [MODULAR_SYSTEM_DOCUMENTATION.md](docs/MODULAR_SYSTEM_DOCUMENTATION.md) for all available actions and settings.


## 📦 Module & API Documentation

All core modules and action handlers are documented in the `docs/` folder:

- [ACTIONS_INSTANCE.md](docs/ACTIONS_INSTANCE.md): **InstanceActions** — Manage the lifecycle of test environments, including creation, startup, and cleanup of temp instances.
- [UTILS_TEMP_INSTANCE_MANAGER.md](docs/UTILS_TEMP_INSTANCE_MANAGER.md): **TempInstanceManager** — Handles creation, configuration, and teardown of isolated FiberWise instances.
- [ACTIONS_BROWSER.md](docs/ACTIONS_BROWSER.md): **BrowserActions** — Automates browser-based test steps (navigation, login, UI checks, screenshots, etc.).
- [ACTIONS_USER.md](docs/ACTIONS_USER.md): **UserActions** — Manages user registration, login, and session validation.
- [ACTIONS_API_KEY.md](docs/ACTIONS_API_KEY.md): **APIKeyActions** — Automates API key creation, listing, deletion, and testing.
- [ACTIONS_COMMAND.md](docs/ACTIONS_COMMAND.md): **CommandActions** — Executes CLI/system commands, analyzes logs, and verifies database state.
- [ACTIONS_TEST.md](docs/ACTIONS_TEST.md): **TestActions** — Handles specialized or meta-test actions (e.g., performance tests, API key scope validation).
- [ACTIONS_BASE.md](docs/ACTIONS_BASE.md): **BaseAction** — Shared utilities and logging for all action handlers.

See each file for detailed usage, main actions, and integration notes.
# FiberWise Modular Browser Testing Suite

## 🗂️ Output Artifacts & Folders

All test runs generate output artifacts for debugging, validation, and reporting:

- **Screenshots**: Captured at key steps and errors, saved in `demo_sessions/<script_name>_<timestamp>/screenshots/`.
- **Videos**: (If enabled) Full browser session recordings in `demo_sessions/<script_name>_<timestamp>/videos/`.
- **Logs**: Browser, console, and server logs for each run.
- **Temp Instance Data**: Isolated app instance, logs, and database in `temp-instances/<instance_id>/`.
- **Session Info**: Full step-by-step log and variable capture in `session_info.json`.

Artifacts are organized by test run and scenario for easy review. Use `auto_cleanup: false` to preserve all artifacts for manual inspection.

See [`docs/OUTPUT_ARTIFACTS.md`](docs/OUTPUT_ARTIFACTS.md) for a detailed guide to all output folders and files, including best practices for reviewing and managing artifacts.

## 📚 Documentation

All general documentation is in the `docs/` folder:

- [docs/MODULAR_SYSTEM_DOCUMENTATION.md](docs/MODULAR_SYSTEM_DOCUMENTATION.md) — Full system reference: actions, settings, advanced usage
- [docs/MODULAR_TEST_GUIDE.md](docs/MODULAR_TEST_GUIDE.md) — Step-by-step modular test writing guide and best practices
- [docs/CREATING_NEW_TESTS.md](docs/CREATING_NEW_TESTS.md) — Complete guide for creating new JSON test scripts

## 📝 Example JSON Test

```json
{
  "script_name": "auth_test",
  "description": "Test authentication flow with temp instance",
  "settings": {
    "headless": false,
    "use_temp_instance": true,
    "auto_cleanup": false,
    "take_screenshots": true
  },
  "steps": [
    {
      "id": "setup",
      "type": "instance", 
      "action": "create_temp_instance",
      "description": "Create isolated test instance"
    },
    {
      "id": "register",
      "type": "browser",
      "action": "register_multiple_users",
      "config": {
        "users": [{"username": "testuser", "email": "test@example.com", "password": "testpass123"}]
      }
    },
    {
      "id": "login", 
      "type": "browser",
      "action": "test_login",
      "config": {
        "username": "testuser",
        "password": "testpass123"
      }
    }
  ]
}
```


## 📖 Basic Example

See [`docs/EXAMPLE_BASIC_TEST.md`](docs/EXAMPLE_BASIC_TEST.md) for a complete, step-by-step example of a modular JSON test script, including all required fields, best practices, and output details. This is the best starting point for new users.


## 🔑 Dynamic Variables & String Replacement

Test scripts support powerful string replacement and variable capture features, making your tests flexible and dynamic. You can:

- Reference environment variables using `{{ENV:VARNAME}}` (e.g., secrets, API keys)
- Capture values from previous steps and reuse them in later actions (e.g., `{{last_response.id}}`)
- Use built-in variables for timestamps, random values, and more
- Chain and nest variables for advanced templating

For example:

```json
{
  "api_key": "{{ENV:FW_API_KEY}}",
  "instance_id": "{{last_response.instance_id}}",
  "run_id": "{{RANDOM_HEX}}-{{TIMESTAMP}}"
}
```

All variables are resolved at runtime, and you can use them in any string field in your test JSON. This enables dynamic test flows, data-driven testing, and secure secret management.

See the "Dynamic Variables & String Replacement" section in [`docs/MODULAR_SYSTEM_DOCUMENTATION.md`](docs/MODULAR_SYSTEM_DOCUMENTATION.md) for a full list of supported variables, advanced templating, and best practices.

One of the coolest features of this framework is its ability to automatically capture screenshots (and optionally videos) during test runs. Screenshots are saved for every major browser action, errors, and checkpoints, making debugging and documentation much easier. Output folders are organized by test run and scenario for easy navigation.

Screenshot and video capture is enabled by default, but can be configured in your test JSON or via environment variables (see the docs for details). You can control when screenshots are taken, where they are saved, and whether to keep or clean up artifacts after tests.

### 🖥️ Headless & Headful Modes

Tests can run in either headless (no visible browser window) or headful (with browser UI) mode. Headless mode is ideal for CI/CD and fast automation, while headful mode is great for debugging and demos. You can control this behavior:

- By setting the `headless` property in your test JSON script (per test or globally)
- By using the `FW_BROWSER_HEADLESS` environment variable (`true` or `false`)
- By command-line flags if supported (see docs)

See [`docs/OUTPUT_ARTIFACTS.md`](docs/OUTPUT_ARTIFACTS.md) for a detailed guide to all output folders and files generated by the framework, including screenshots, videos, logs, temp instance data, and demo session artifacts. Learn where to find and how to use all test results and debugging information.

## 🛠️ Tech Stack

- **Python 3.10+** — Core language for the test runner and utilities
- **Playwright (Python)** — Browser automation and UI testing
- **JSON** — Declarative test script format
- **FiberWise** — Target application under test (core services)

# FiberWise Browser Testing Suite

Comprehensive browser testing framework for FiberWise using Python and Playwright with modular test execution.


# FiberWise Modular Browser Testing Suite

A comprehensive, modular browser testing framework for FiberWise, powered by Python and Playwright. All tests are defined in JSON and executed via a single runner script—no pytest or Python test files required.

## 🚀 Quick Start

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **Run a test script:**
   ```bash
   python json_script_runner_modular.py scripts/simple_modular_test.json
   ```

## 🗄️ Example: Database Verification Action

You can verify database state and run SQL queries as part of your test flow using the `verify_database` action. For example:

```json
{
  "type": "command",
  "action": "verify_database",
  "config": {
    "queries": [
      "SELECT COUNT(*) FROM users;",
      "SELECT * FROM api_keys ORDER BY created_at DESC LIMIT 5;"
    ],
    "database_path": "{{instance_dir}}/local_data/fiberwise.db"
  }
}
```

This step will connect to the specified SQLite database, run the queries, and capture results for use in later steps or assertions.

---

For more advanced and comprehensive test examples—including API health checks, user isolation, app install flows, LLM provider tests, and more—see the `scripts/` directory. Each JSON file there demonstrates different features and action types supported by the framework.

## 🐛 Troubleshooting

- **Port conflicts**: Use temp instances (default).
- **Element not found**: Check selectors and add waits.
- **Database issues**: Verify instance startup completed.

Enable debug mode by setting `"auto_cleanup": false` to preserve test artifacts.


## ❌ What is NOT Supported

- No Python test files or pytest integration.
- No test discovery outside JSON scripts.
- All test logic must be in JSON and run via `json_script_runner_modular.py`.

## 📞 Support

For questions or issues:
1. Check existing test examples in `scripts/`
2. Review console output for errors
3. Use debug mode for troubleshooting
4. Create an issue with reproduction steps

