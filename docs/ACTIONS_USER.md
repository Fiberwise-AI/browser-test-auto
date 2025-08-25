# UserActions Module Documentation

**File:** actions/user_actions.py

## Purpose
Manages user registration, login, and session validation steps.

## Key Features
- Registers multiple users in isolated browser contexts.
- Handles login flows and session persistence.
- Can verify user logins and manage user-specific test data.

## Usage
Invoked by BrowserActions for user-related steps.

## Main Actions
- `register_multiple_users`
- `test_login`
- `verify_user_logins`
