

# FiberWise Modular Test System Documentation

## Overview


The FiberWise Modular Test System is a comprehensive browser automation and testing framework with a clean, modular architecture for different types of test operations.

## Architecture

### Core Components

#### 1. JSONScriptRunner (Main Orchestrator)
- **File**: `json_script_runner_modular.py`
- **Purpose**: Main execution engine for modular test scripts
- **Key Features**:
  - Random port assignment for temp instances
  - Bootstrap system for dependency management
  - Temporary instance creation and cleanup
  - Session management with screenshots and videos
  - Console log collection
  - Session variable storage for cross-step data sharing

#### 2. Modular Action Handlers


##### InstanceActions (`actions/instance_actions.py`)
**Purpose:** Manage the lifecycle of test environments (create, start, clean up, connect to existing).
**Main Actions:**
- `create_temp_instance` — Create isolated test instance
- `start_existing_instance` — Connect to a running instance
- `cleanup_instance` — Remove temp instance and resources
- `fiber_install_app` — Install app into instance


##### BrowserActions (`actions/browser_actions.py`)
**Purpose:** Automate browser-based test steps using Playwright (navigation, login, UI checks, screenshots, etc.).
**Main Actions:**
- `register_multiple_users` — Register users in browser
- `test_login` — Login and session validation
- `navigate_and_verify` — Navigate to page and verify
- `create_api_key` — Create API key via UI
- `configure_llm_provider` — LLM provider setup
- `test_websocket_isolation` — Chat/session isolation
- ...and more


##### UserActions (`actions/user_actions.py`)
**Purpose:** Manage user registration, login, and session validation.
**Main Actions:**
- `register_multiple_users` — Register users
- `test_login` — Login and validate session
- `verify_user_logins` — Check multiple user logins


##### APIKeyActions (`actions/api_key_actions.py`)
**Purpose:** Automate API key creation, listing, deletion, and testing.
**Main Actions:**
- `create_api_key` — Create API key (with scopes)
- `list_api_keys` — List and verify API keys
- `delete_api_key` — Remove API key
- `test_api_key` — Validate API key
**Features:**
- Capture API secrets as session variables
- Scope and permission validation


##### CommandActions (`actions/command_actions.py`)
**Purpose:** Execute CLI/system commands, analyze logs, and verify database state.
**Main Actions:**
- `run_command` — Run shell/CLI command
- `analyze_server_logs` — Analyze server logs
- `verify_database` — Run SQL queries and verify DB


##### TestActions (`actions/test_actions.py`)
**Purpose:** Specialized or meta-test actions (performance, API key scope validation, etc.).
**Main Actions:**
- `verify_api_keys` — Validate API keys
- `test_api_key_scopes` — Test API key scopes
- `performance_test` — Performance/benchmark tests

## Session Variable System

### Purpose
Enables sharing data between test steps, crucial for complex workflows where one step's output becomes another step's input.

### Implementation
```python
# Storage
self.session_variables = {}

# Setting variables
def set_session_variable(self, key: str, value: str, description: str = ""):
    timestamp = datetime.now().isoformat()
    self.session_variables[key] = {
        "value": value,
        "description": description,
        "timestamp": timestamp
    }

# Getting variables  
def get_session_variable(self, key: str) -> str:
    if key in self.session_variables:
        return self.session_variables[key]["value"]
    return None

# Template replacement
def replace_variables_in_string(self, text: str) -> str:
    # Replaces {{variable_name}} with actual values
```

### Usage Examples
```json
{
  "action": "create_api_key",
  "config": {
    "capture_secret": "my_api_secret"
  }
}
```

```json
{
  "action": "test_api_key",
  "config": {
    "api_key": "{{my_api_secret}}"
  }
}
```

## JSON Script Format

### Basic Structure
```json
{
  "script_name": "test_name",
  "description": "Test description",
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
      "id": "unique_step_id",
      "type": "action_category", 
      "action": "specific_action",
      "description": "Step description",
      "config": {
        // Action-specific configuration
      }
    }
  ]
}
```

### Step Types and Actions

#### Instance Steps (`type: "instance"`)
```json
{
  "type": "instance",
  "action": "create_temp_instance",
  "description": "Create isolated test environment"
}
```

#### Browser Steps (`type: "browser"`)
```json
{
  "type": "browser", 
  "action": "navigate_and_verify",
  "config": {
    "url": "/settings/api-keys",
    "take_screenshot": true,
    "keep_page_open": true
  }
}
```

#### User Steps (`type: "browser"` with user actions)
```json
{
  "type": "browser",
  "action": "register_multiple_users",
  "config": {
    "users": [
      {
        "username": "testuser",
        "email": "test@example.com", 
        "password": "TestPass123!"
      }
    ]
  }
}
```

#### API Key Steps (`type: "api_key"`)
```json
{
  "type": "api_key",
  "action": "create_api_key",
  "config": {
    "key_name": "Test API Key",
    "scopes": ["read:all", "write:all"],
    "capture_secret": "my_api_key"
  }
}
```

#### Database Steps with External Database (`type: "command"`)
```json
{
  "type": "command",
  "action": "verify_database", 
  "config": {
    "queries": [
      "SELECT COUNT(*) FROM users;",
      "SELECT * FROM api_keys ORDER BY created_at DESC LIMIT 5;"
    ],
    "database_url": "postgresql://user:pass@localhost:5432/fiberwise",
    "database_path": "{{instance_dir}}/local_data/fiberwise.db"
  }
}
```

#### Existing Instance Testing
```json
{
  "type": "browser",
  "action": "test_login",
  "config": {
    "username": "existing_user@company.com",
    "password": "existing_password",
    "keep_page_open": true
  }
}
```

## Working Test Scripts

### 1. simple_api_key_test.json
- **Purpose**: Basic API key page verification
- **Features**: User registration, login, navigation to API keys page
- **Status**: ✅ Working
- **Use Case**: Quick smoke test for API key functionality

### 2. create_api_key_working_user.json  
- **Purpose**: Complete API key creation workflow
- **Features**: User registration, login, API key creation, database verification
- **Status**: ✅ Working (with minor capture issue)
- **Use Case**: End-to-end API key testing

### 3. simple_database_test.json
- **Purpose**: Database connectivity and structure validation
- **Features**: User creation, database queries, table structure verification
- **Status**: ✅ Ready
- **Use Case**: Database integrity verification

### 4. existing_instance_with_db_test.json
- **Purpose**: Test against existing FiberWise instance with real data
- **Features**: Existing user login, API key creation, database verification with external DB
- **Status**: ✅ Ready for customization
- **Use Case**: Production-like testing with existing users and data

### 5. simple_existing_instance_test.json
- **Purpose**: Basic test against local running FiberWise instance
- **Features**: User registration, login, API key creation on existing instance
- **Status**: ✅ Working
- **Use Case**: Quick test against running instance without database queries

### 6. login_test.json
- **Purpose**: Basic user registration and login testing
- **Features**: User registration, database verification, login validation, dashboard access
- **Status**: ✅ Ready
- **Use Case**: Authentication workflow testing

### 7. multi_user_registration.json
- **Purpose**: Bulk user registration and verification
- **Features**: Register 3 users, database verification, login testing for multiple users
- **Status**: ✅ Ready
- **Use Case**: Multi-user environment testing

### 8. app_install_test.json
- **Purpose**: Complete workflow for API key creation and app installation
- **Features**: User registration, API key creation with capture, fiber CLI simulation, database verification
- **Status**: ✅ Ready
- **Use Case**: End-to-end app installation workflow testing

## Key Features

### Random Port Assignment
- Prevents port conflicts during parallel testing
- Automatic port detection and assignment

### Bootstrap System
- Automated dependency installation
- File copying and environment setup
- One-time setup for temp instances

### Temporary Instance Management
- Isolated test environments
- Complete FiberWise stack (frontend + backend)
- Independent databases and storage

### Comprehensive Logging
- Step-by-step execution logging
- Server log collection and analysis
- Console error tracking
- Screenshot and video capture

### Session Persistence
- Browser session maintained across steps
- Cookie-based authentication preservation
- Shared page state for complex workflows

## Configuration Options

### Global Settings
```json
"settings": {
  "headless": false,           // Show browser UI
  "use_temp_instance": true,   // Create isolated instance
  "use_existing_instance": false, // Use existing FiberWise instance
  "existing_instance_url": "http://localhost:8000", // URL of existing instance
  "video_recording": true,     // Record video
  "take_screenshots": true,    // Capture screenshots
  "auto_cleanup": false,       // Keep resources after test
  "database_config": {         // External database configuration
    "database_url": "postgresql://user:pass@localhost:5432/fiberwise",
    "database_path": "/path/to/database.db"
  }
}
```

### Instance Configuration Modes

#### 1. **Temporary Instance Mode** (Default)
```json
"settings": {
  "use_temp_instance": true,
  "use_existing_instance": false
}
```
- Creates isolated test environment
- Random port assignment
- Independent SQLite database
- Automatic cleanup after tests

#### 2. **Existing Instance Mode**
```json
"settings": {
  "use_temp_instance": false,
  "use_existing_instance": true,
  "existing_instance_url": "http://localhost:8000"
}
```
- Tests against running FiberWise instance
- Uses existing users and data
- No instance management or cleanup
- Perfect for production-like testing

#### 3. **No Instance Mode**
```json
"settings": {
  "use_temp_instance": false,
  "use_existing_instance": false
}
```
- Browser-only testing
- Manual instance management
- Custom setup workflows

## Instance Persistence and Keep-Alive

### Overview
The FiberWise testing framework provides powerful instance persistence capabilities, allowing test instances to remain running and be reused across multiple test sessions. This is essential for complex workflows like app installation, agent activation, and multi-session testing.

### How Instance Keep-Alive Works

#### 1. Process Management
When `auto_cleanup: false` is set, the framework starts background processes that continue running:
- **Vite Dev Server**: Frontend development server (typically port 6620+)
- **Python Backend**: FastAPI/uvicorn server (typically port 6621+)
- **Database**: SQLite database with all app data, users, and configurations

#### 2. Instance Directory Structure
```
temp-instances/
├── test_20250807_130424_da0bcca5/
│   ├── instance_info.json          # Instance configuration and connection details
│   ├── local_data/
│   │   └── fiberwise.db            # Persistent SQLite database
│   ├── logs/
│   │   ├── server.log              # Backend server logs
│   │   └── server_error.log        # Error logs
│   ├── start_instance.py           # Script to restart the instance
│   └── main.py                     # Backend application entry point
```

#### 3. Reconnection Configuration
To reconnect to an existing instance, use these settings:
```json
"settings": {
  "auto_cleanup": false,
  "use_existing_instance": true,
  "existing_instance_url": "http://localhost:6620"
}
```

#### 4. Variable Preservation
Use `set_session_variables` action to restore instance state:
```json
{
  "id": "restore_instance_state",
  "type": "test",
  "action": "set_session_variables",
  "config": {
    "variables": {
      "base_url": "http://localhost:6620",
      "instance_dir": "C:\\...\\temp-instances\\test_20250807_130424_da0bcca5",
      "app_id": "82d3c606-bbfc-4bbd-b78d-50a7d5ef3f50",
      "agent_id": "ee0edf12-ded7-46fe-9093-09f1451f346c"
    }
  }
}
```

### Persistence Benefits

#### 1. **App Installation Continuity**
- Installed FiberWise apps remain available across sessions
- App configurations, agents, and metadata persist
- No need to reinstall apps for subsequent tests

#### 2. **User Session Preservation**
- User accounts and authentication data remain valid
- API keys and access tokens continue working
- Browser sessions can be restored with login

#### 3. **Agent Activation State**
- Activated agents maintain their configuration
- Chat history and interaction data preserved
- Agent-specific settings and customizations retained

#### 4. **Database Continuity**
- Full relational data integrity maintained
- Complex data relationships preserved
- Historical test data available for analysis

### Practical Usage Examples

#### Example 1: App Installation and Chat Testing
```json
// First run: Install app with auto_cleanup: false
"settings": { "auto_cleanup": false }
// Instance keeps running with installed app

// Second run: Reconnect and test chat
"settings": {
  "use_existing_instance": true,
  "existing_instance_url": "http://localhost:6620"
}
```

#### Example 2: Multi-Session Development Workflow
```json
// Development session: Create apps, users, test data
"settings": { "auto_cleanup": false }
// Instance remains active for development

// Testing session: Run tests against preserved state
"settings": { "use_existing_instance": true }
// Access all previously created data
```

#### Example 3: Debugging and Iteration
```json
// Failed test run: Keep instance running for investigation
"settings": { "auto_cleanup": false }
// Manually inspect database, logs, UI state

// Retry test: Continue from where you left off
"settings": { "use_existing_instance": true }
// Skip setup steps, focus on specific issues
```

### Instance Restart and Recovery

#### Automatic Restart
If an instance process crashes, use the generated restart script:
```bash
cd temp-instances/test_20250807_130424_da0bcca5
python start_instance.py
```

#### Manual Process Check
Verify instance processes are running:
```bash
# Check if Vite server is running
curl -s -o /dev/null -w "%{http_code}" http://localhost:6620

# Check backend API
curl -s -o /dev/null -w "%{http_code}" http://localhost:6621/api/v1/health
```

#### Database Connection Test
Verify database accessibility:
```json
{
  "type": "command",
  "action": "verify_database",
  "config": {
    "queries": ["SELECT COUNT(*) as user_count FROM users;"],
    "database_path": "{{instance_dir}}/local_data/fiberwise.db"
  }
}
```

### Step-Level Configuration
Each action type supports specific configuration options:

- **Browser actions**: `take_screenshot`, `keep_page_open`, `timeout`
- **User actions**: `headless`, `slow_motion`, `wait_time`
- **API key actions**: `scopes`, `capture_secret`, `expires_in_days`
- **Command actions**: `timeout`, `working_directory`, `environment`

## Error Handling

### Graceful Failures
- Detailed error logging with context
- Screenshot capture on failures
- Server log dumping for debugging
- Resource cleanup on exceptions

### Debugging Features
- Real-time server log monitoring
- Console error collection
- Page state capture at each step
- Session variable inspection

## Best Practices

### 1. **Script Organization**
- Use descriptive step IDs
- Include detailed descriptions
- Group related actions logically

### 2. **Resource Management**
- Set `auto_cleanup: false` for debugging
- Use session variables for data sharing
- Take screenshots at critical points

### 3. **Error Prevention**
- Include database verification steps
- Use exact routes from routes.js
- Validate user creation before proceeding

### 4. **Performance Optimization**
- Use headless mode for speed
- Minimize unnecessary screenshots
- Combine related operations in single steps

## Running Tests

### Command Line Usage
```bash
# Navigate to test directory
cd C:\Users\david\fiberwise\fiberwise-browser-tests

# Run specific test
python json_script_runner_modular.py scripts\simple_api_key_test.json

# Run with different Python version
python3 json_script_runner_modular.py scripts\create_api_key_working_user.json
```

### Output Locations
- **Session Data**: `demo_sessions/{script_name}_{timestamp}/`
- **Screenshots**: `demo_sessions/{session}/screenshots/`
- **Videos**: `demo_sessions/{session}/videos/`
- **Logs**: `demo_sessions/{session}/logs/`
- **Temp Instances**: `temp-instances/{instance_name}/`

## Troubleshooting

### Common Issues

#### 1. **Port Conflicts**
- **Symptom**: Instance startup failures
- **Solution**: Random port assignment handles this automatically

#### 2. **Authentication Failures**
- **Symptom**: Login redirects or 401 errors
- **Solution**: Check user registration success, verify password requirements

#### 3. **Element Not Found**
- **Symptom**: Browser action failures
- **Solution**: Use exact selectors from frontend code, add wait strategies

#### 4. **Database Connection Issues**
- **Symptom**: SQLite errors in database verification
- **Solution**: Verify instance startup completed, check database path variables

### Debug Mode
Set `auto_cleanup: false` to:
- Keep temp instances running for manual inspection
- Preserve browser state for debugging
- Access server logs and database directly



## Future Enhancements

### Planned Features
- **Parallel test execution**: Run multiple tests simultaneously
- **Test data management**: External test data files
- **Advanced reporting**: HTML test reports with screenshots
- **CI/CD integration**: GitHub Actions compatibility
- **Mock services**: External service mocking for testing

### Extension Points
- **Custom actions**: Add new action categories
- **Plugins**: Extend functionality with plugins
- **Custom assertions**: Domain-specific validation
- **Data providers**: External data sources for tests

## Conclusion

The modular test system provides a robust, maintainable foundation for FiberWise testing. The clean separation of concerns makes it easy to extend functionality while maintaining reliability.
