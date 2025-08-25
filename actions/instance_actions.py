"""
Instance management actions for JSON Script Runner.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any

from .base_action import BaseAction


class InstanceActions(BaseAction):
    """Handles instance-related actions like creating and managing temp instances."""
    
    async def execute(self, step: Dict[str, Any]) -> Any:
        """Execute instance-related step."""
        action = step.get('action')
        
        if action == "create_temp_instance":
            return await self.create_temp_instance(step)
        elif action == "start_existing_instance":
            return await self.start_existing_instance(step)
        elif action == "cleanup_instance":
            return await self.cleanup_instance(step)
        elif action == "fiber_install_app":
            return await self.fiber_install_app(step.get('config', {}))
        else:
            self.log_step("Unknown Instance Action", f"Action '{action}' not implemented")
            return None
    
    async def start_existing_instance(self, step: Dict[str, Any]) -> Any:
        """Start an existing instance by ID and auto-discover settings."""
        config = step.get('config', {})
        instance_id = config.get('instance_id')
        
        if not instance_id:
            self.log_step("Missing Instance ID", "instance_id required for start_existing_instance")
            return None
        
        # Import here to avoid circular imports
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
        from temp_instance_manager import TempInstanceManager
        
        self.log_step("Starting Existing Instance", f"Instance ID: {instance_id}")
        
        # Create manager for existing instance
        self.runner.temp_instance = TempInstanceManager(instance_id=instance_id)
        
        # Check if instance directory exists
        if not self.runner.temp_instance.instance_dir.exists():
            self.log_step("Instance Not Found", f"Instance directory does not exist: {self.runner.temp_instance.instance_dir}")
            return None
        
        # Auto-discover database path
        db_path = self.runner.temp_instance.instance_dir / "local_data" / "fiberwise.db"
        
        # Start the instance
        if self.runner.temp_instance.start_instance():
            self.runner.base_url = self.runner.temp_instance.base_url
            
            # Set auto-discovered variables for template substitution
            self.runner.set_session_variable("base_url", self.runner.base_url, "Auto-discovered instance URL")
            self.runner.set_session_variable("existing_instance_url", self.runner.base_url, "Auto-discovered instance URL")
            self.runner.set_session_variable("instance_dir", str(self.runner.temp_instance.instance_dir), "Auto-discovered instance directory")
            self.runner.set_session_variable("existing_db_path", str(db_path), "Auto-discovered database path")
            self.runner.set_session_variable("instance_id", instance_id, "Instance ID")
            
            # Check if there are existing users we can import
            await self._discover_existing_users(db_path)
            
            self.log_step("Existing Instance Ready", f"Available at {self.runner.base_url}")
            self.log_step("Auto-discovered Settings", f"DB: {db_path}")
            return self.runner.base_url
        else:
            self.log_step("Instance Start Failed", "Could not start existing instance")
            return None
    
    async def _discover_existing_users(self, db_path: Path) -> None:
        """Discover existing users in the database for potential reuse."""
        try:
            if not db_path.exists():
                self.log_step("No Database Found", "Database file does not exist yet")
                return
            
            import sqlite3
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get existing users
            cursor.execute("SELECT id, username, email, is_active FROM users WHERE is_active = 1 LIMIT 5")
            users = cursor.fetchall()
            
            if users:
                self.log_step("Existing Users Found", f"Found {len(users)} active users")
                for user_id, username, email, is_active in users:
                    self.log_step("Available User", f"ID={user_id}, Username='{username}', Email='{email}'")
                    # Set session variables for the first user (can be used in tests)
                    if user_id == users[0][0]:  # First user
                        self.runner.set_session_variable("existing_user_id", user_id, "First existing user ID")
                        self.runner.set_session_variable("existing_username", username, "First existing username")
                        self.runner.set_session_variable("existing_email", email, "First existing user email")
            else:
                self.log_step("No Existing Users", "No active users found in database")
            
            conn.close()
            
        except Exception as e:
            self.log_step("User Discovery Error", f"Could not query users: {e}")

    async def create_temp_instance(self, step: Dict[str, Any]) -> Any:
        """Create and start a temporary FiberWise instance."""
        use_existing = self.runner.script.get('settings', {}).get('use_existing_instance', False)
        existing_url = self.runner.script.get('settings', {}).get('existing_instance_url', 'http://localhost:6701')
        
        if use_existing:
            self.log_step("Using Existing Instance", f"Connecting to {existing_url}")
            self.runner.base_url = existing_url
            return existing_url
        elif self.runner.script.get('settings', {}).get('use_temp_instance', True):
            return await self._create_new_temp_instance()
        else:
            self.log_step("No Instance Setup", "Neither temp nor existing instance configured")
            return None
    
    async def _create_new_temp_instance(self):
        """Create a new temporary instance."""
        # Import here to avoid circular imports
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
        from temp_instance_manager import TempInstanceManager
        
        self.log_step("Creating Instance", "Setting up temp instance...")
        # Let TempInstanceManager generate its own timestamp-based instance_id
        self.runner.temp_instance = TempInstanceManager()
        
        # Create and start the instance
        if self.runner.temp_instance.create_instance():
            self.log_step("Starting Instance", "Starting FiberWise services...")
            if self.runner.temp_instance.start_instance():
                self.runner.base_url = self.runner.temp_instance.base_url
                
                # Set instance info as session variables for template substitution
                self.runner.set_session_variable("base_url", self.runner.base_url, "Instance base URL")
                self.runner.set_session_variable("port", str(self.runner.temp_instance.api_port), "API port for connections")
                self.runner.set_session_variable("instance_dir", str(self.runner.temp_instance.instance_dir), "Instance directory path")
                self.runner.set_session_variable("instance_id", self.runner.temp_instance.instance_id, "Instance ID")
                
                self.log_step("Instance Ready", f"Available at {self.runner.base_url}")
                return self.runner.base_url
            else:
                self.log_step("Instance Start Failed", "Could not start services")
                return None
        else:
            self.log_step("Instance Creation Failed", "Could not create temp instance")
            return None
    
    async def cleanup_instance(self, step: Dict[str, Any]) -> Any:
        """Clean up temporary instance."""
        if self.runner.temp_instance:
            self.log_step("Cleaning Up Instance", "Stopping services and cleaning up...")
            self.runner.temp_instance.cleanup()
            self.runner.temp_instance = None
            self.log_step("Instance Cleaned Up", "Temporary instance removed")
        else:
            self.log_step("No Instance to Clean", "No temporary instance found")
        return True
    
    async def start_temp_instance(self, config: Dict[str, Any]):
        """Start a temporary FiberWise instance - wrapper for create_temp_instance."""
        return await self.create_temp_instance({'config': config})
        """Install FiberWise app using fiber CLI."""
        app_path = config.get('app_path', '')
        install_command = config.get('install_command', 'fiber install app . --verbose')
        
        self.log_step("Fiber Install", f"Installing app from {app_path}")
        
        # Change to app directory and run fiber install
        if app_path and Path(app_path).exists():
            try:
                result = subprocess.run(
                    install_command.split(),
                    cwd=app_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    self.log_step("Install Success", f"App installed successfully")
                    return True
                else:
                    self.log_step("Install Failed", f"Error: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.log_step("Install Timeout", "Installation timed out")
                return False
            except Exception as e:
                self.log_step("Install Error", f"Exception: {str(e)}")
                return False
        else:
            self.log_step("Invalid App Path", f"App path {app_path} does not exist")
            return False
