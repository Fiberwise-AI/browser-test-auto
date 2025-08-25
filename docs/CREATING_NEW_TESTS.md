# Creating New JSON Test Scripts - Complete Guide

This guide provides detailed instructions for creating new JSON-based test scripts based on the proven working pattern from `debug_login_with_logs.json`.

## 🎯 Overview

The JSON script testing system allows you to create comprehensive automated tests using a declarative JSON configuration. Each test script follows a predictable pattern that ensures reliability and maintainability.

## � Troubleshooting

### Browser Visibility

**Behavior**: Browser headless mode is set at initialization and cannot be changed per-step.

**Solutions**:
- **Screenshots**: Use `"take_screenshot": true` for visual validation ✅ **WORKS PERFECTLY**
- **Manual inspection**: Add `show_browser` action to open browser window at any point
- **Server logs**: Use `analyze_server_logs` action for error detection

### Show Browser Action

**Add this step anywhere to open browser window:**

```json
{
  "id": "show_browser",
  "type": "browser", 
  "action": "show_browser",
  "description": "Open browser window for inspection",
  "config": {
    "keep_open": true,
    "show_devtools": false
  }
}
```

### Available Routes (Updated 2025-08-06)

**Based on successful test execution with routes.js:**

✅ **CONFIRMED Working Routes:**
- `/` - Dashboard/Home page ✅ **TESTED**
- `/settings/api-keys` - API keys settings page ✅ **TESTED**
- `/manage/apps` - Apps management page ✅ **TESTED** 
- `/manage/workers` - Workers management page ✅ **TESTED**
- `/agents` - Agent list page (from routes.js)
- `/pipelines` - Pipeline list page (from routes.js)
- `/functions` - Function list page (from routes.js)
- `/workflows` - Workflow list page (from routes.js)
- `/settings/llm-providers` - LLM provider settings (from routes.js)
- `/settings/oauth-providers` - OAuth settings (from routes.js)

❌ **Routes NOT Available:**
- `/api-keys` - **NOT IMPLEMENTED** (use `/settings/api-keys` instead)
- `/workers` - **NOT IMPLEMENTED** (use `/manage/workers` instead) 
- `/apps` - **NOT IMPLEMENTED** (use `/manage/apps` instead)

**Important**: All routes tested maintained session authentication correctly with server logs showing "Authentication successful via cookie"!

### Session Persistence Issues

**Problem**: Getting redirected to login page despite successful login.

**Solution**: Ensure every step after login uses `"keep_page_open": true`:

```json
{
  "id": "login_step",
  "config": { "keep_page_open": true }  // ✅ REQUIRED
},
{
  "id": "any_navigation",
  "config": { "keep_page_open": true }  // ✅ REQUIRED
}
```

**Validation**: Check server logs for "Authentication successful via cookie" messages.

## 📋 Templates

Every test script must follow this exact structure to work properly:

### 1. Script Header (Required)

```json
{
  "script_name": "your_test_name",
  "description": "Clear description of what this test does",
  "version": "1.0",
  "settings": {
    "headless": true,
    "use_temp_instance": true,
    "video_recording": false,
    "take_screenshots": true,
    "auto_cleanup": false
  },
  "steps": [
    // Your test steps go here
  ]
}
```

#### Critical Settings Explained:

- **`script_name`**: Must be unique and descriptive (used for session directories)
- **`description`**: Appears in logs and helps with debugging
- **`version`**: Track script changes (increment when making modifications)
- **`headless: true`**: RECOMMENDED for automated tests - runs faster, use screenshots for validation
- **`use_temp_instance: true`**: REQUIRED - creates isolated test environment
- **`video_recording: false`**: RECOMMENDED false - videos may not capture properly in headless mode
- **`take_screenshots: true`**: CRITICAL - provides visual validation for headless tests
- **`auto_cleanup: false`**: RECOMMENDED - keeps instance running for manual verification

### 2. Mandatory First Step: Instance Creation

**EVERY script must start with this exact step:**

```json
{
  "id": "setup",
  "type": "instance",
  "action": "create_temp_instance",
  "description": "Create and start temp FiberWise instance with enhanced logging"
}
```

This step:
- Creates isolated FiberWise instance with dynamic ports (6000+)
- Bootstraps complete environment (copies source, installs dependencies)
- Starts both frontend (Vite) and backend (uvicorn) servers
- Enables comprehensive server logging
- Provides clean database and storage

### 3. User Registration Pattern

**ALWAYS register users before any browser interactions:**

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
        "username": "testuser1",
        "email": "test1@example.com",
        "password": "testpass123"
      },
      {
        "username": "testuser2", 
        "email": "test2@example.com",
        "password": "testpass123"
      }
    ]
  }
}
```

**Important Notes:**
- Use `"headless": true` for registration (faster, less visual noise)
- Always use unique usernames and emails
- Password must be at least 8 characters
- Multiple users can be registered in a single step

### 4. Login Testing Pattern

**Standard login step:**

```json
{
  "id": "test_login",
  "type": "browser", 
  "action": "test_login",
  "description": "Test user authentication",
  "config": {
    "username": "testuser1",
    "password": "testpass123",
    "keep_page_open": true
  }
}
```

**Critical Configuration:**
- Use exact username from registration
- `keep_page_open: true` maintains browser context for subsequent steps
- Only use `keep_browser_open: true` on the FINAL step for manual user testing

## 🌐 Available Routes (Based on routes.js)

### ✅ Verified Working Routes:

**Dashboard:**
- `/` - Dashboard page (dashboard-page component)

**App Management:**
- `/manage/apps` - Apps list page (apps-list-page component)
- `/manage/apps/:id` - App details page
- `/manage/apps/:appId/data` - App data explorer
- `/apps/:id` - App view page

**Worker Management:**
- `/manage/workers` - Worker list page (worker-list-page component)
- `/manage/workers/:id` - Worker details page

**AI Tools:**
- `/agents` - Agent list page (agent-list-page component)
- `/agents/new` - Create agent
- `/agents/:id` - Agent details
- `/agent-types` - Agent types list
- `/pipelines` - Pipeline list page (pipeline-list-page component)
- `/pipelines/new` - Create pipeline
- `/pipelines/:id` - Pipeline details
- `/workflows` - Workflow list page
- `/functions` - Function list page (function-list-page component)
- `/functions/new` - Create function
- `/functions/:id` - Function details

**Settings:**
- `/settings/api-keys` - API keys page (api-keys-page component)
- `/settings/llm-providers` - LLM providers page (llm-providers-page component)
- `/settings/oauth-providers` - OAuth providers page

**Other:**
- `*` - 404 Not Found page

### ❌ Routes That Don't Exist:
- `/api-keys` - Use `/settings/api-keys` instead
- `/workers` - Use `/manage/workers` instead
- `/apps` - Use `/manage/apps` instead

## 🧪 Common Test Patterns

### Navigation and Verification

```json
{
  "id": "verify_page",
  "type": "browser",
  "action": "navigate_and_verify", 
  "description": "Verify specific page loads correctly",
  "config": {
    "url": "/apps",
    "wait_for_selector": "body",
    "take_screenshot": true,
    "verify_elements": ["title", "h1", ".main-content"],
    "keep_page_open": true
  }
}
```

### Working Route Examples (Based on routes.js)

**Dashboard and Main Pages:**
```json
{
  "id": "navigate_to_dashboard",
  "type": "browser",
  "action": "navigate_and_verify",
  "description": "Navigate to main dashboard",
  "config": {
    "url": "/",
    "wait_for_selector": "body",
    "take_screenshot": true,
    "keep_page_open": true
  }
}
```

**Management Pages:**
```json
{
  "id": "navigate_to_apps",
  "type": "browser",
  "action": "navigate_and_verify",
  "description": "Navigate to apps management page",
  "config": {
    "url": "/manage/apps",
    "wait_for_selector": "body",
    "take_screenshot": true,
    "keep_page_open": true
  }
},
{
  "id": "navigate_to_workers",
  "type": "browser",
  "action": "navigate_and_verify",
  "description": "Navigate to workers management page",
  "config": {
    "url": "/manage/workers",
    "wait_for_selector": "body",
    "take_screenshot": true,
    "keep_page_open": true
  }
}
```

**AI Tools Pages:**
```json
{
  "id": "navigate_to_agents",
  "type": "browser",
  "action": "navigate_and_verify",
  "description": "Navigate to agents page",
  "config": {
    "url": "/agents",
    "wait_for_selector": "body",
    "take_screenshot": true,
    "keep_page_open": true
  }
},
{
  "id": "navigate_to_pipelines",
  "type": "browser",
  "action": "navigate_and_verify",
  "description": "Navigate to pipelines page",
  "config": {
    "url": "/pipelines",
    "wait_for_selector": "body",
    "take_screenshot": true,
    "keep_page_open": true
  }
},
{
  "id": "navigate_to_functions",
  "type": "browser",
  "action": "navigate_and_verify",
  "description": "Navigate to functions page",
  "config": {
    "url": "/functions",
    "wait_for_selector": "body",
    "take_screenshot": true,
    "keep_page_open": true
  }
}
```

**Settings Pages:**
```json
{
  "id": "navigate_to_api_keys",
  "type": "browser",
  "action": "navigate_and_verify",
  "description": "Navigate to API keys settings",
  "config": {
    "url": "/settings/api-keys",
    "wait_for_selector": "body",
    "take_screenshot": true,
    "keep_page_open": true
  }
},
{
  "id": "navigate_to_llm_providers",
  "type": "browser",
  "action": "navigate_and_verify",
  "description": "Navigate to LLM providers settings",
  "config": {
    "url": "/settings/llm-providers",
    "wait_for_selector": "body",
    "take_screenshot": true,
    "keep_page_open": true
  }
}
```

### ❌ Deprecated: API Key Creation

```json
{
  "id": "create_api_key",
  "type": "browser",
  "action": "create_api_key_demo",
  "description": "⚠️ DEPRECATED: API key functionality not implemented in current router",
  "config": {
    "key_name": "Test API Key",
    "take_screenshot": true,
    "keep_browser_open": true
  }
}
```

### Command Execution

```json
{
  "id": "run_command",
  "type": "command",
  "action": "check_git_repo",
  "description": "Verify git repository structure", 
  "config": {
    "repo_path": "../fiber-apps",
    "required_directories": ["dev", "examples"]
  }
}
```

## 🔧 Available Actions by Type

### Instance Actions (`type: "instance"`)

- **`create_temp_instance`**: Creates isolated FiberWise instance
  - Always required as first step
  - No configuration needed
- **`cleanup_instance`**: Manually cleanup temp instance
  - Usually automatic with `auto_cleanup: true`

### Browser Actions (`type: "browser"`)

- **`register_multiple_users`**: Register one or more test users
  - Required before any login attempts
- **`test_login`**: Authenticate a user
  - Requires pre-registered user
- **`navigate_and_verify`**: Navigate to URL and verify page elements
  - Supports HTML analysis and element verification
- **`show_browser`**: Open browser window for manual inspection
  - Can be added at any point to make browser visible
  - Keeps browser open until manually closed
- **`verify_app_installation`**: Check if app is properly installed
- **`test_app_access`**: Test app functionality
- **`verify_user_logins`**: Verify multiple user login scenarios
- **`navigate_to_home`**: Navigate to home page
- **`explore_ui`**: General UI exploration
- **`demo_interactions`**: Demo user interactions
- **`final_documentation`**: Generate final documentation
- **`final_review`**: Perform final review
- **`verify_database`**: Verify database operations

#### ⚠️ Deprecated Actions:
- **`create_api_key_demo`**: ❌ **DEPRECATED** - API key functionality not implemented in current system
- **`configure_llm_provider`**: ❌ **DEPRECATED** - Use navigation to settings pages instead

### Command Actions (`type: "command"`)

- **`check_git_repo`**: Verify git repository structure
- **`list_apps`**: List available apps in repository  
- **`fiber_install`**: Install app using fiber CLI
- **`fiber_install_app`**: Install specific fiber app
- **`analyze_server_logs`**: Analyze server logs for errors and warnings
  - Post-run analysis of temp instance logs
  - Identifies errors, warnings, and performance issues

## 🎨 Configuration Patterns

### Browser Step Configuration

```json
"config": {
  "headless": false,           // Show browser (true for background)
  "take_screenshot": true,     // Capture screenshot
  "keep_page_open": true,      // Keep page open for next browser step
  "wait_for_selector": "body", // Wait for element before proceeding
  "timeout": 30000             // Timeout in milliseconds
}
```

### 🚨 Critical: Browser Session Persistence

**The browser session and cookie authentication work correctly, but there are important considerations:**

#### ✅ What Works:
- Session cookies persist across browser steps when properly configured
- Authentication state is maintained between steps
- Server logs confirm "Authentication successful via cookie"

#### ⚠️ Current Issues:
- Browser visibility may not respect individual step `headless` settings
- Creating new pages can break session continuity
- Only `keep_browser_open: true` reliably shows the browser window

#### 🔧 Session Persistence Rules:

**For Authentication Flow:**
```json
{
  "id": "login_step",
  "config": { 
    "keep_page_open": true,      // ✅ REQUIRED: Maintains session
    "take_screenshot": true      // ✅ RECOMMENDED: Visual validation
  }
},
{
  "id": "authenticated_step",
  "config": { 
    "keep_page_open": true,      // ✅ REQUIRED: Reuses authenticated session
    "take_screenshot": true      // ✅ RECOMMENDED: Visual validation
  }
},
{
  "id": "show_browser_step",
  "type": "browser",
  "action": "show_browser",
  "description": "Open browser for manual inspection",
  "config": { 
    "keep_open": true           // ✅ Opens browser window
  }
}
```

**Session Continuity Patterns:**
- ✅ `keep_page_open: true` - Reuses the same page and cookies
- ❌ `keep_page_open: false` - Creates new page, loses session
- ✅ `keep_browser_open: true` - Final step only, for manual testing

### ⚠️ Important: `keep_browser_open` vs `keep_page_open`

#### Session Persistence Behavior (Updated 2025-08-06):

- **`keep_page_open: true`**: 
  - ✅ **CRITICAL for authentication flows** - Reuses the same page object
  - ✅ **Maintains cookies and session state** across steps
  - ✅ **Prevents login redirects** on subsequent pages
  - ⚠️ **Must be used consistently** after login for session continuity

- **`keep_browser_open: true`**: 
  - ✅ **Only use on FINAL step** for manual user testing
  - ✅ **Shows browser window reliably** (other headless settings may not work)
  - ❌ **Never use in middle of automated tests** - breaks automation flow

- **No keep settings**:
  - ❌ **Creates new page each step** - loses cookies and session
  - ❌ **Forces re-authentication** on every navigation
  - ❌ **Results in 302 redirects to /login**

#### Authentication Flow Pattern:
```json
{
  "id": "register_step",
  "config": { "headless": true }                    // ✅ Fast registration
},
{
  "id": "login_step", 
  "config": { "keep_page_open": true }              // ✅ REQUIRED: Store session
},
{
  "id": "navigate_step1",
  "config": { "keep_page_open": true }              // ✅ REQUIRED: Reuse session
},
{
  "id": "navigate_step2", 
  "config": { "keep_page_open": true }              // ✅ REQUIRED: Maintain session
},
{
  "id": "final_manual_test",
  "config": { "keep_browser_open": true }           // ✅ For manual inspection
}
```

#### ❌ Common Session-Breaking Mistakes:
```json
{
  "id": "login_step",
  "config": { "keep_page_open": true }              // ✅ Session stored
},
{
  "id": "broken_step",
  "config": { "take_screenshot": true }             // ❌ NO keep_page_open = new page = lost session!
}
```

### Command Step Configuration

```json
"config": {
  "timeout": 120,              // Command timeout in seconds
  "capture_output": true,      // Capture command output
  "working_directory": ".",    // Working directory for command
  "environment_vars": {}       // Additional environment variables
}
```

## 📊 Post-Run Analysis

### Server Log Analysis

**Add this as the final step to analyze server logs for errors:**

```json
{
  "id": "analyze_logs",
  "type": "command",
  "action": "analyze_server_logs",
  "description": "Analyze server logs for errors and warnings",
  "config": {
    "log_types": ["error", "warning", "critical"],
    "include_performance": true,
    "generate_summary": true
  }
}
```

**This step will:**
- ✅ Parse server.log and server_error.log files
- ✅ Identify error patterns and HTTP status codes
- ✅ Check for authentication failures
- ✅ Report on performance issues (slow queries, timeouts)
- ✅ Generate summary report with actionable insights

### Error Pattern Detection

**Common errors to watch for:**
- **500 Internal Server Error**: Backend crashes or unhandled exceptions
- **404 Not Found**: Incorrect routes or missing static files
- **403 Forbidden**: Permission or authentication issues
- **Database errors**: Connection failures, constraint violations
- **JavaScript errors**: Frontend runtime errors visible in console
- **Performance warnings**: Slow API responses, memory issues

### Manual Log Review

**After test completion, manually check:**
```
temp-instances/script_TESTNAME_TIMESTAMP/logs/
├── server.log          # Complete server output
├── server_error.log    # Error messages only
└── frontend.log        # Vite/frontend logs
```

**Key log patterns:**
```
✅ "Authentication successful via cookie" - Session working
❌ "500 Internal Server Error" - Backend issues
❌ "Failed to connect to database" - Database problems
❌ "Uncaught exception" - Unhandled errors
⚠️ "Slow query" - Performance issues
```

## 📝 Complete Example Script

Here's a complete example that demonstrates all essential patterns:

```json
{
  "script_name": "complete_example_test",
  "description": "Complete example showing all essential test patterns",
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
      "description": "Create and start temp FiberWise instance with enhanced logging"
    },
    {
      "id": "register_users",
      "type": "browser",
      "action": "register_multiple_users",
      "description": "Register test users",
      "config": {
        "headless": true,
        "users": [
          {
            "username": "testuser1",
            "email": "test1@example.com", 
            "password": "testpass123"
          }
        ]
      }
    },
    {
      "id": "test_login",
      "type": "browser",
      "action": "test_login",
      "description": "Test user authentication",
      "config": {
        "username": "testuser1",
        "password": "testpass123",
        "keep_page_open": true
      }
    },
    {
      "id": "verify_dashboard",
      "type": "browser",
      "action": "navigate_and_verify",
      "description": "Verify dashboard loads correctly",
      "config": {
        "url": "/",
        "wait_for_selector": "body",
        "take_screenshot": true,
        "verify_elements": ["title", "body"],
        "keep_page_open": true
      }
    },
    {
      "id": "navigate_to_api_keys",
      "type": "browser",
      "action": "navigate_and_verify",
      "description": "Navigate to API keys settings page",
      "config": {
        "url": "/settings/api-keys",
        "wait_for_selector": "body",
        "take_screenshot": true,
        "verify_elements": ["title", "body"],
        "keep_page_open": true
      }
    },
    {
      "id": "verify_apps_page",
      "type": "browser",
      "action": "navigate_and_verify",
      "description": "Verify apps management page loads",
      "config": {
        "url": "/manage/apps",
        "wait_for_selector": "body",
        "take_screenshot": true,
        "keep_page_open": true
      }
    },
    {
      "id": "analyze_server_logs",
      "type": "command",
      "action": "analyze_server_logs",
      "description": "Analyze server logs for errors and warnings",
      "config": {
        "log_types": ["error", "warning", "critical"],
        "include_performance": true,
        "generate_summary": true
      }
    }
  ]
}
```

## 🚀 Running Your Test

1. **Save your script** in the `scripts/` directory:
   ```
   scripts/your_test_name.json
   ```

2. **Run the test**:
   ```bash
   cd fiberwise-browser-tests
   python json_script_runner.py scripts/your_test_name.json
   ```

3. **Monitor execution**:
   - Watch console output for step-by-step progress
   - Check screenshots in `demo_sessions/your_test_name_TIMESTAMP/screenshots/`
   - Review server logs in temp instance directory

## 🔍 Debugging Tips

### Essential Debugging Settings

**Always use these settings for debugging:**

```json
"settings": {
  "headless": false,           // REQUIRED: Shows browser
  "auto_cleanup": false,       // REQUIRED: Keeps instance running
  "take_screenshots": true,    // REQUIRED: Visual debugging
  "video_recording": true      // RECOMMENDED: Full session recording
}
```

### Browser Step Debugging

**Add to any browser step:**

```json
"config": {
  "keep_browser_open": true,   // Don't close browser
  "take_screenshot": true,     // Capture visual state
  "wait_time": 5              // Pause to observe
}
```

### Instance Information

**After running, find your instance at:**
```
temp-instances/script_your_test_name_TIMESTAMP/
```

**Key files:**
- `logs/server.log` - Complete server output
- `logs/server_error.log` - Error messages  
- `instance_info.json` - Instance configuration
- `local_data/fiberwise.db` - Test database

### Manual Testing

**With `auto_cleanup: false`, you can:**
1. Keep browser open for manual testing
2. Access running instance at the logged URL (e.g., `http://localhost:6919`)
3. Login with registered test credentials
4. Manually verify app functionality

## ⚠️ Critical Requirements

### What You MUST Include

1. **Instance creation as first step** - Always required
2. **User registration before login** - Users don't persist between runs
3. **Unique script names** - Avoids session directory conflicts
4. **Proper step IDs** - Must be unique within script
5. **Descriptive descriptions** - Helps with debugging

### What You MUST NOT Do

1. **Don't skip instance creation** - Nothing will work
2. **Don't reuse usernames** - Each script run needs fresh users  
3. **Don't use `auto_cleanup: true` during development** - Removes debugging ability
4. **Don't use `headless: true` globally during development** - Hides visual feedback
5. **Don't change working script patterns** - Stick to proven templates

## 📂 File Organization

### Script Structure
```
scripts/
├── debug_login_with_logs.json     # ✅ WORKING REFERENCE
├── your_new_test.json             # Your new test
└── experimental_test.json         # Experimental features
```

### Generated Files
```
demo_sessions/
└── your_test_name_TIMESTAMP/
    ├── screenshots/               # Auto-captured screenshots
    ├── videos/                   # Session recordings  
    └── session_info.json         # Complete session data

temp-instances/
└── script_your_test_name_TIMESTAMP/
    ├── logs/                     # Server logs
    ├── local_data/              # Database and storage
    └── fiberwise_core/          # Application files
```

## 🎯 Best Practices

### Script Development Workflow

1. **Start with proven template** - Copy `debug_login_with_logs.json`
2. **Change only necessary parts** - Modify step-by-step
3. **Test frequently** - Run after each major change
4. **Use descriptive names** - Clear script and step names
5. **Keep detailed descriptions** - Help future debugging

### Testing Strategy

1. **Test basic flow first** - Registration → Login → Dashboard
2. **Add features incrementally** - One new step at a time
3. **Verify each step works** - Check screenshots and logs
4. **Use manual testing** - Leverage `auto_cleanup: false`
5. **Document new patterns** - Update this guide with discoveries

### Performance Considerations

1. **Use `headless: true` for registration** - Faster execution
2. **Minimize wait times** - Only wait when necessary
3. **Clean up resources** - Set `auto_cleanup: true` for production runs
4. **Batch related operations** - Group similar steps together

## 🛠️ Advanced Patterns

### Conditional Steps

Use step dependencies and error handling:

```json
{
  "id": "optional_step",
  "type": "browser",
  "action": "navigate_and_verify",
  "description": "Optional verification step",
  "config": {
    "url": "/optional-page", 
    "continue_on_error": true,
    "take_screenshot": true
  }
}
```

### Dynamic Configuration

Use template variables:

```json
{
  "id": "dynamic_step",
  "type": "command",
  "action": "fiber_install",
  "config": {
    "base_url": "{{instance_url}}",
    "app_path": "../fiber-apps/dev/activation-chat"
  }
}
```

### Multi-User Scenarios

Test concurrent users:

```json
{
  "id": "register_multiple",
  "type": "browser",
  "action": "register_multiple_users",
  "config": {
    "users": [
      {"username": "admin", "email": "admin@test.com", "password": "admin123"},
      {"username": "user", "email": "user@test.com", "password": "user123"}
    ]
  }
}
```

## 📞 Support and Troubleshooting

### Common Issues

1. **Script won't start**: Check JSON syntax and required fields
2. **Instance creation fails**: Ensure no conflicting ports
3. **Registration fails**: Check user data format and uniqueness
4. **Login fails**: Verify user was registered successfully
5. **Browser crashes**: Check for missing `keep_browser_open: true`

### Getting Help

1. **Check existing working scripts** - Use as reference
2. **Review console output** - Contains detailed error information
3. **Examine server logs** - Found in temp instance directory
4. **Use manual testing** - Keep instance running with `auto_cleanup: false`
5. **Compare with working patterns** - Stick to proven templates

### Debug Checklist

- [ ] Script follows exact structure from working example
- [ ] Instance creation is first step
- [ ] User registration precedes login
- [ ] Unique script name and step IDs
- [ ] Debugging settings enabled (`headless: false`, `auto_cleanup: false`)
- [ ] Valid JSON syntax
- [ ] Descriptive step descriptions

---

## 🔐 Session Authentication Template (Updated 2025-08-06)

**Working Pattern**: Use this for tests requiring login persistence across multiple steps.

**File**: `test_session_auth.json`

```json
{
  "test_id": "session_authentication_flow",
  "description": "Template for maintaining session across multiple steps",
  "expected_outcomes": ["Login successful", "Session maintained", "Authentication via cookies"],
  "temp_instance": {
    "use_temp": true,
    "cleanup_on_completion": true
  },
  "steps": [
    {
      "id": "register_user",
      "step_type": "register_user",
      "description": "Create test user account",
      "config": {
        "headless": true
      },
      "params": {
        "email": "session@example.com",
        "password": "TestPassword123",
        "confirm_password": "TestPassword123"
      }
    },
    {
      "id": "login_user",
      "step_type": "test_login",
      "description": "Login and establish session",
      "config": {
        "keep_page_open": true,
        "headless": false
      },
      "params": {
        "email": "session@example.com",
        "password": "TestPassword123"
      }
    },
    {
      "id": "navigate_dashboard",
      "step_type": "navigate_and_verify",
      "description": "Navigate while maintaining session",
      "config": {
        "keep_page_open": true
      },
      "params": {
        "url": "/dashboard",
        "expected_content": "Dashboard"
      }
    },
    {
      "id": "navigate_profile",
      "step_type": "navigate_and_verify", 
      "description": "Test session persistence",
      "config": {
        "keep_page_open": true
      },
      "params": {
        "url": "/profile",
        "expected_content": "Profile"
      }
    },
    {
      "id": "final_inspection",
      "step_type": "navigate_and_verify",
      "description": "Keep browser open for manual testing",
      "config": {
        "keep_browser_open": true
      },
      "params": {
        "url": "/dashboard",
        "expected_content": "Dashboard"
      }
    }
  ]
}
```

**Key Session Persistence Rules**:
- ✅ **Login step MUST have `keep_page_open: true`** to store session cookies
- ✅ **All navigation steps MUST have `keep_page_open: true`** to maintain session
- ✅ **Server logs show "Authentication successful via cookie"** for working sessions
- ❌ **Missing `keep_page_open` = new page = lost session = 302 redirect to login**

---

## 🎉 Quick Start Template

Copy this template for new tests:

```json
{
  "script_name": "my_new_test", 
  "description": "Description of what this test does",
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
      "description": "Create and start temp FiberWise instance with enhanced logging"
    },
    {
      "id": "register_user",
      "type": "browser",
      "action": "register_multiple_users",
      "description": "Register test user",
      "config": {
        "headless": true,
        "users": [
          {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
          }
        ]
      }
    },
    {
      "id": "test_login",
      "type": "browser",
      "action": "test_login",
      "description": "Test user login",
      "config": {
        "username": "testuser",
        "password": "testpass123",
        "keep_page_open": true
      }
    },
    {
      "id": "verify_dashboard",
      "type": "browser", 
      "action": "navigate_and_verify",
      "description": "Verify dashboard loads",
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
      "description": "Check server logs for errors",
      "config": {
        "log_types": ["error", "warning"],
        "generate_summary": true
      }
    }
  ]
}
```

**Remember**: Start with this template, test it works, then add your specific steps incrementally!

---

## 🎉 **Updated Framework Features (August 2025)**

### ✅ **Major Improvements Implemented**

1. **🚀 Headless-First Approach**: 
   - Tests run fast in headless mode by default
   - Screenshots provide perfect visual validation
   - `show_browser` action opens visible browser when needed

2. **🔧 Flexible Browser Control**:
   - `show_browser` action can be added at any point
   - Switches from headless to visible mode seamlessly
   - Preserves session state during browser mode switch

3. **📊 Enhanced Log Analysis**:
   - `analyze_server_logs` command action detects errors and warnings
   - Authentication pattern analysis
   - Performance issue detection
   - Clean summary reports

4. **📹 Smart Video Recording**:
   - Disabled by default for better performance
   - Can be enabled when needed for debugging
   - Works in both headless and visible modes

5. **🔐 Robust Session Management**:
   - Cookie-based authentication works perfectly
   - Session persistence across all browser actions
   - Server logs confirm authentication success

### 🛠️ **Clean Documentation**

- Removed redundant headless issue mentions
- Streamlined troubleshooting section
- Added practical browser control patterns
- Updated all templates with best practices

**Result**: A clean, fast, reliable browser testing framework with excellent debugging capabilities!
