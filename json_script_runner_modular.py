#!/usr/bin/env python3
"""
Modular JSON-based script runner for FiberWise demos.
This is the ORIGINAL json_script_runner.py with modular action delegation.
Preserves ALL original functionality: random ports, bootstrap, temp locations, etc.
"""

import asyncio
import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from playwright.async_api import async_playwright

# Add utils directory to path
sys.path.insert(0, str(Path(__file__).parent / "utils"))
# TempInstanceManager is used indirectly via InstanceActions; direct import not required here

# Import modular actions
from actions.instance_actions import InstanceActions
from actions.command_actions import CommandActions
from actions.browser_actions import BrowserActions
from actions.user_actions import UserActions
from actions.api_key_actions import APIKeyActions
from actions.test_actions import TestActions


class JSONScriptRunner:
    """Runs JSON-defined demo scripts with flexible browser and instance management."""
    
    def __init__(self, script_path: str):
        self.script_path = Path(script_path)
        self.script = self.load_script()
        
        # Create clean session ID without spaces or special characters
        script_name_clean = self.script['script_name'].lower().replace(' ', '_').replace('-', '_')
        script_name_clean = ''.join(c for c in script_name_clean if c.isalnum() or c == '_')
        self.session_id = f"{script_name_clean}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create session directory
        self.base_dir = Path(__file__).parent / "demo_sessions" / self.session_id
        self.screenshots_dir = self.base_dir / "screenshots"
        self.videos_dir = self.base_dir / "videos"
        
        # Shared browser state for session persistence
        self.shared_page = None
        self.browser_context = None
        self.browser = None
        self.playwright = None
        self.logs_dir = self.base_dir / "logs"
        
        # Console log collection
        self.console_logs = []
        self.console_errors = []
        
        # Create directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.videos_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Runtime state
        self.temp_instance = None
        self.base_url = "http://localhost:6701"
        self.step_count = 0
        self.session_log = []
        self.session_api_key = None  # Store API key for fiber CLI usage
        
        # Session variables for storing captured values between steps
        self.session_variables = {}
        
        # Initialize modular action handlers - pass self to maintain compatibility
        self.instance_actions = InstanceActions(self)
        self.command_actions = CommandActions(self)
        self.browser_actions = BrowserActions(self)
        self.user_actions = UserActions(self)
        self.api_key_actions = APIKeyActions(self)
        self.test_actions = TestActions(self)
        
        print(f"[SCRIPT] Loaded: {self.script['script_name']}")
        print(f"[SCRIPT] Description: {self.script['description']}")
        print(f"[SCRIPT] Session: {self.session_id}")
    
    def load_script(self) -> dict:
        """Load JSON script from disk."""
        if not self.script_path.exists():
            raise FileNotFoundError(f"Script file not found: {self.script_path}")
        with open(self.script_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def log_step(self, step_name: str, details: str = ""):
        """Log a step in the script execution."""
        self.step_count += 1
        timestamp = datetime.now().isoformat()
        
        # Clean Unicode characters to avoid encoding issues
        clean_step_name = self._clean_unicode_text(step_name)
        clean_details = self._clean_unicode_text(details)
        
        entry = {"step": self.step_count, "timestamp": timestamp, "name": clean_step_name, "details": clean_details}
        self.session_log.append(entry)
        if clean_details:
            print(f"[STEP {self.step_count}] {clean_step_name}\n    {clean_details}")
        else:
            print(f"[STEP {self.step_count}] {clean_step_name}")

    async def run_script(self):
        """Run all steps in the loaded script."""
        self.log_step("Script Start", f"Running {self.script.get('script_name')}")
        try:
            for step in self.script.get('steps', []):
                await self.execute_step(step)
        finally:
            await self.cleanup()
            self.save_session_info()
            self.log_step("Script Complete", "All steps finished")
    
    async def execute_step(self, step: dict):
        """Execute a single script step with modular delegation."""
        step_id = step.get('id', 'unknown')
        step_type = step.get('type', 'unknown')
        action = step.get('action', 'unknown')
        description = step.get('description', '')
        
        # Perform variable substitution for config values (deep)
        config = step.get('config')
        if isinstance(config, dict):
            step['config'] = self._replace_variables_in_dict(config)

        self.log_step(f"Executing {step_id}", description or f"{step_type}:{action}")
        
        # Delegate to appropriate modular action handler
        if step_type == "instance":
            await self.instance_actions.execute(step)
        elif step_type == "browser":
            await self.browser_actions.execute(step)
        elif step_type == "command":
            await self.command_actions.execute(step)
        elif step_type == "user":
            await self.user_actions.execute(step)
        elif step_type == "api_key":
            await self.api_key_actions.execute(step)
        elif step_type == "test":
            await self.test_actions.execute(step)
        else:
            self.log_step("Unknown Step Type", f"Step type '{step_type}' not supported")
    
    # PRESERVE ALL ORIGINAL BROWSER MANAGEMENT METHODS
    async def initialize_browser(self, settings, config):
        """Initialize browser and context for session persistence."""
        # Determine browser settings for this step
        headless = config.get('headless', settings.get('headless', False))
        slow_mo = settings.get('slow_motion', 400) if not headless else 0
        
        # Check if we need to reinitialize browser due to headless mode change
        current_headless = getattr(self, '_current_headless', None)
        
        if self.playwright and current_headless is not None and current_headless != headless:
            await self.cleanup_browser()
        
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
            self._current_headless = headless
            
            # Create context with video recording if enabled
            context_options = {}
            if settings.get('video_recording', False):
                context_options['record_video_dir'] = str(self.videos_dir)
                context_options['record_video_size'] = {"width": 1280, "height": 720}
            
            self.browser_context = await self.browser.new_context(**context_options)
            self.log_step("Browser Initialized", f"Headless: {headless}, Slow motion: {slow_mo}ms")
    
    async def cleanup_browser(self):
        """Clean up browser resources without closing playwright."""
        if self.shared_page:
            await self.shared_page.close()
            self.shared_page = None
        
        if self.browser_context:
            await self.browser_context.close()
            self.browser_context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
    
    async def get_or_create_page(self, context, config):
        """Get shared page or create new one based on keep_page_open setting."""
        keep_page_open = config.get('keep_page_open', False)
        
        if keep_page_open and self.shared_page:
            return self.shared_page, False
        else:
            page = await context.new_page()
            await self.setup_console_monitoring(page)
            if keep_page_open:
                self.shared_page = page
            return page, not keep_page_open
    
    async def setup_console_monitoring(self, page):
        """Set up console log monitoring for a page."""
        def handle_console_message(msg):
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "type": msg.type,
                "text": msg.text,
                "location": msg.location
            }
            
            self.console_logs.append(log_entry)
            
            if msg.type in ['error', 'warning']:
                self.console_errors.append(log_entry)
        
        # Attach console listener
        page.on("console", handle_console_message)
        
        # Also listen for page errors (uncaught exceptions)
        def handle_page_error(error):
            timestamp = datetime.now().isoformat()
            error_entry = {
                "timestamp": timestamp,
                "type": "page_error",
                "text": str(error),
                "location": None
            }
            self.console_errors.append(error_entry)
        
        page.on("pageerror", handle_page_error)
    
    def analyze_console_logs(self):
        """Analyze collected console logs and return summary."""
        if not self.console_errors:
            return "Console: No JavaScript errors or warnings detected"
        
        # Group by type
        error_count = len([e for e in self.console_errors if e['type'] == 'error'])
        warning_count = len([e for e in self.console_errors if e['type'] == 'warning'])
        page_error_count = len([e for e in self.console_errors if e['type'] == 'page_error'])
        
        console_summary = f"Console: {error_count} JS errors, {warning_count} JS warnings, {page_error_count} page errors"
        
        # Log recent console issues
        if self.console_errors:
            self.log_step("Console Issues Found", f"Total console issues: {len(self.console_errors)}")
            for i, error in enumerate(self.console_errors[-5:], 1):
                clean_text = error['text'].encode('ascii', 'ignore').decode('ascii')[:100]
                self.log_step(f"Console Error {i}", f"{error['type']}: {clean_text}")
        
        return console_summary
    
    def get_screenshot_path(self, name: str) -> str:
        """Get path for screenshot with step number."""
        return str(self.screenshots_dir / f"{self.step_count:02d}_{name}.png")
    
    async def cleanup(self):
        """Clean up resources."""
        # Clean up browser resources
        await self.cleanup_browser()
                
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        
        # Clean up temp instance (only if auto_cleanup is enabled)
        if self.temp_instance:
            auto_cleanup = self.script.get('settings', {}).get('auto_cleanup', True)
            if auto_cleanup:
                self.temp_instance.cleanup_instance()
            else:
                print(f"[INFO] Stopping processes but preserving instance - auto_cleanup set to {auto_cleanup}")
                # Stop running processes but keep the instance directory
                self.temp_instance.stop_instance()
                print(f"[INFO] Instance {self.temp_instance.instance_id} stopped but preserved for further testing")
            self.temp_instance = None
    
    def set_session_variable(self, key: str, value: str, description: str = ""):
        """Store a value in session variables for use in later steps."""
        self.session_variables[key] = {
            "value": value,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "step": self.step_count
        }
        self.log_step("Variable Stored", f"'{key}' = '{value[:20]}{'...' if len(value) > 20 else ''}' ({description})")
    
    def get_session_variable(self, key: str, default: str = None) -> str:
        """Retrieve a value from session variables."""
        if key in self.session_variables:
            value = self.session_variables[key]["value"]
            self.log_step("Variable Retrieved", f"'{key}' = '{value[:20]}{'...' if len(value) > 20 else ''}'")
            return value
        elif default is not None:
            self.log_step("Variable Default", f"'{key}' not found, using default: '{default}'")
            return default
        else:
            self.log_step("Variable Missing", f"'{key}' not found and no default provided")
            return ""
    
    def substitute_template_variables(self, text: str) -> str:
        """Replace template variables like {{key}} with session variable values."""
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            return self.get_session_variable(var_name, f"{{{{ {var_name} }}}}")
        
        return re.sub(r'\{\{(\w+)\}\}', replace_var, text)
    
    def _replace_variables_in_dict(self, obj):
        """Recursively replace variables in dictionary/list structures."""
        if isinstance(obj, dict):
            return {k: self._replace_variables_in_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_variables_in_dict(item) for item in obj]
        elif isinstance(obj, str):
            return self.replace_variables_in_string(obj)
        else:
            return obj
    
    def replace_variables_in_string(self, text: str) -> str:
        """Replace {{variable_name}} and {{ENV:VARNAME}} placeholders with session variable or environment variable values."""
        import re
        import os

        def replace_var(match):
            var_name = match.group(1)
            # Support environment variable substitution: {{ENV:VARNAME}}
            if var_name.startswith('ENV:'):
                env_var = var_name[4:]
                return os.environ.get(env_var, match.group(0))
            # Otherwise, use session variable
            val = self.get_session_variable(var_name, None)
            return val if val is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace_var, text)
    
    def _clean_unicode_text(self, text: str) -> str:
        """Clean Unicode characters that cause encoding issues."""
        if not text:
            return text
        
        import re
        
        # Replace common emoji characters that cause encoding issues
        emoji_replacements = {
            '📱': '[phone]',
            '✅': '[check]',
            '❌': '[x]',
            '⚠️': '[warning]',
            '🔧': '[wrench]',
            '🎉': '[party]',
            '💡': '[bulb]',
            '🔍': '[search]',
            '📊': '[chart]',
            '🚀': '[rocket]',
            '⏰': '[clock]',
            '🔒': '[lock]',
            '🔓': '[unlock]',
            '📝': '[memo]',
            '💻': '[computer]',
            '🌐': '[globe]',
            '⭐': '[star]',
            '🎯': '[target]',
        }
        
        cleaned_text = text
        for emoji, replacement in emoji_replacements.items():
            cleaned_text = cleaned_text.replace(emoji, replacement)
        
        # Remove any remaining emoji characters (broader cleanup)
        # This regex matches most emoji characters
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251" 
            "]+",
            flags=re.UNICODE
        )
        
        cleaned_text = emoji_pattern.sub('[emoji]', cleaned_text)
        
        return cleaned_text
    
    def save_session_info(self):
        """Save session information."""
        session_info = {
            "script_name": self.script['script_name'],
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "total_steps": self.step_count,
            "script_config": self.script,
            "logs": self.session_log,
            "console_logs": self.console_logs,
            "console_errors": self.console_errors,
            "session_variables": self.session_variables  # Include captured variables
        }
        
        info_file = self.base_dir / "session_info.json"
        with open(info_file, 'w') as f:
            json.dump(session_info, f, indent=2)
        
        self.log_step("Session Saved", f"Session info saved to {info_file}")


async def run_json_script(script_path: str):
    """Run a JSON script."""
    runner = None
    try:
        runner = JSONScriptRunner(script_path)
        await runner.run_script()
        
        print("\n" + "=" * 60)
        print("SCRIPT EXECUTION COMPLETE!")
        print(f"Session: {runner.session_id}")
        print(f"Directory: {runner.base_dir}")
        print(f"Screenshots: {runner.screenshots_dir}")
        print(f"Videos: {runner.videos_dir}")
        print("=" * 60)
        
        # Check if script requests forced exit
        settings = runner.script.get('settings', {})
        if settings.get('force_exit_on_complete', False):
            print("[INFO] Script completed - forcing clean exit...")
            await asyncio.sleep(1)  # Brief pause for any pending operations
            
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Script execution interrupted by user")
        if runner:
            try:
                await runner.cleanup()
            except Exception:
                pass
        
    except Exception as e:
        print(f"[ERROR] Script execution failed: {e}")
        traceback.print_exc()
        if runner:
            try:
                await runner.cleanup()
            except Exception:
                pass
    
    finally:
        # Ensure all async operations are completed
        try:
            # Cancel any remaining tasks, excluding the current task
            current_task = asyncio.current_task()
            tasks = [task for task in asyncio.all_tasks() if not task.done() and task is not current_task]
            if tasks:
                print(f"[CLEANUP] Cancelling {len(tasks)} remaining tasks...")
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            pass


async def main():
    """Main entry point with timeout protection."""
    parser = argparse.ArgumentParser(description="JSON Script Runner for FiberWise")
    parser.add_argument("script", help="Path to JSON script file")
    parser.add_argument("--timeout", type=int, default=600, help="Script timeout in seconds (default: 600)")
    
    args = parser.parse_args()
    
    try:
        # Run with timeout to prevent hanging
        await asyncio.wait_for(run_json_script(args.script), timeout=args.timeout)
        print("[INFO] Script completed successfully")
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] Script exceeded {args.timeout} seconds - forcing exit")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
    finally:
        print("[EXIT] Test runner exiting...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[CTRL+C] Force exit requested")
    except Exception as e:
        print(f"[FATAL] {e}")
    finally:
        import sys
        sys.exit(0)
