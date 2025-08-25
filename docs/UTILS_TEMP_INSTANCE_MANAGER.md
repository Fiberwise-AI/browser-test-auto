# TempInstanceManager Documentation

**File:** utils/temp_instance_manager.py

## Purpose
Handles the creation, configuration, startup, and cleanup of isolated FiberWise instances for testing.

## Key Features
- Generates unique, isolated environments with dedicated ports and storage.
- Bootstraps or copies the application, sets up all config and .env files.
- Starts both frontend (Vite) and backend (uvicorn) servers as subprocesses.
- Waits for services to be ready and provides health checks.
- Cleans up all processes and files after tests, with full log capture.
- Can be used as a context manager for auto-cleanup.

## Usage
Used by InstanceActions and can be used directly for advanced scenarios.

## Example
```
from utils.temp_instance_manager import create_temp_instance
with create_temp_instance() as instance:
    # Use instance.base_url, instance.api_url, etc.
    ...
# Instance is cleaned up automatically
```
