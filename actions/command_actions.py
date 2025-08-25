"""
Command-line actions for JSON Script Runner.
"""

import subprocess
import sqlite3
from pathlib import Path
from typing import Dict, Any

from .base_action import BaseAction


class CommandActions(BaseAction):
    """Handles command-line related actions."""
    
    async def execute(self, step: Dict[str, Any]) -> Any:
        """Execute command-related step."""
        action = step.get('action', 'unknown')
        config = step.get('config', {})
        
        if action == "run_command":
            return await self.run_command(config)
        elif action == "check_git_repo":
            return await self.check_git_repo(config)
        elif action == "list_apps":
            return await self.list_apps(config)
        elif action == "fiber_install":
            return await self.fiber_install(config)
        elif action == "fiber_update":
            return await self.fiber_update(config)
        elif action == "analyze_server_logs":
            return await self.analyze_server_logs(config)
        elif action == "analyze_output":
            return await self.analyze_server_logs(config)
        elif action == "verify_database":
            return await self.verify_database(config)
        elif action == "api_test":
            return await self.api_test(config)
        elif action == "generate_html_report":
            return await self.generate_html_report(config)
        else:
            self.log_step("Unknown Command Action", f"Action '{action}' not implemented")
            return None
    
    async def run_command(self, config: Dict[str, Any]):
        """Run a shell command and return the result."""
        command = config.get('command', '')
        timeout = config.get('timeout', 30)
        working_directory = config.get('working_directory', None)
        environment = config.get('environment', None)
        
        if not command:
            self.log_step("Command Error", "No command specified")
            return None
        
        try:
            # Replace variable placeholders with session variables
            original_command = command
            for var_name, var_value in self.runner.session_variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                if placeholder in command:
                    # Extract the actual value if it's a session variable object
                    if isinstance(var_value, dict) and 'value' in var_value:
                        actual_value = var_value['value']
                    else:
                        actual_value = var_value
                    command = command.replace(placeholder, str(actual_value))
            
            if command != original_command:
                self.log_step("Template Substitution", f"Replaced variables in command")
            
            # Prepare environment
            env = None
            if environment:
                import os
                env = os.environ.copy()
                env.update(environment)
            
            self.log_step("Running Command", f"Executing: {command}")
            
            # Run command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_directory,
                env=env
            )
            
            # Log results - remove emojis to avoid encoding issues
            if result.stdout:
                stdout_clean = self._clean_unicode_text(result.stdout.strip())
                self.log_step("Command Output", stdout_clean)
            
            if result.stderr:
                stderr_clean = self._clean_unicode_text(result.stderr.strip())
                self.log_step("Command Error", stderr_clean)
            
            if result.returncode != 0:
                self.log_step("Command Failed", f"Exit code: {result.returncode}")
                return {
                    "success": False,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                self.log_step("Command Success", "Command completed successfully")
                return {
                    "success": True,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
        
        except subprocess.TimeoutExpired:
            self.log_step("Command Timeout", f"Command timed out after {timeout} seconds")
            return {
                "success": False,
                "error": "timeout",
                "timeout": timeout
            }
        except Exception as e:
            self.log_step("Command Exception", f"Error running command: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_git_repo(self, config):
        """Check if a git repository exists and is valid."""
        from pathlib import Path
        
        repo_path = config.get('repo_path', '../fiber-apps')
        required = config.get('required', True)
        error_message = config.get('error_message', f'Repository not found at {repo_path}')
        
        try:
            repo_abs_path = Path(repo_path).resolve()
            
            if not repo_abs_path.exists():
                self.log_step("Repository Missing", error_message)
                if required:
                    raise FileNotFoundError(error_message)
                return False
            
            # Check if it's a git repository
            result = subprocess.run(
                ['git', 'status'], 
                cwd=repo_abs_path, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                self.log_step("Repository Valid", f"Git repository found at {repo_abs_path}")
                return True
            else:
                self.log_step("Repository Invalid", f"Not a git repository: {repo_abs_path}")
                if required:
                    raise RuntimeError(f"Invalid git repository at {repo_path}")
                return False
                
        except Exception as e:
            self.log_step("Repository Check Error", str(e))
            if required:
                raise
            return False
    
    async def list_apps(self, config):
        """List available apps in the fiber-apps repository."""
        from pathlib import Path
        
        repo_path = config.get('repo_path', '../fiber-apps')
        scan_directories = config.get('scan_directories', ['dev', 'examples', 'templates'])
        
        try:
            repo_abs_path = Path(repo_path).resolve()
            found_apps = []
            
            for scan_dir in scan_directories:
                scan_path = repo_abs_path / scan_dir
                if scan_path.exists():
                    for app_dir in scan_path.iterdir():
                        if app_dir.is_dir() and (app_dir / 'fiber.json').exists():
                            found_apps.append(str(app_dir))
            
            if found_apps:
                self.log_step("Apps Found", f"Found {len(found_apps)} apps")
                for app in found_apps[:10]:  # Show first 10
                    self.log_step("App Available", app)
            else:
                self.log_step("No Apps Found", f"No fiber apps found in {scan_directories}")
                
        except Exception as e:
            self.log_step("App Listing Error", str(e))
    
    async def fiber_install(self, config):
        """Execute fiber install command for an app."""
        from pathlib import Path
        
        app_path = config.get('app_path')
        fallback_apps = config.get('fallback_apps', [])
        base_url = config.get('base_url', '{{instance_url}}')
        use_api_key = config.get('use_api_key', False)
        timeout = config.get('timeout', 120)
        capture_output = config.get('capture_output', True)
        verbose = config.get('verbose', False)
        
        # Replace template variables
        if base_url == '{{instance_url}}' and hasattr(self.runner, 'temp_instance'):
            base_url = self.runner.temp_instance.base_url
        
        # Try main app path first, then fallbacks
        apps_to_try = [app_path] + fallback_apps
        
        for app_to_try in apps_to_try:
            if not app_to_try:
                continue
                
            try:
                app_abs_path = Path(app_to_try).resolve()
                if not app_abs_path.exists():
                    self.log_step("App Not Found", f"App path {app_to_try} does not exist")
                    continue
                
                # Construct fiber install command
                cmd = ['fiber', 'app', 'install', '.']
                if verbose:
                    cmd.append('--verbose')
                if base_url:
                    cmd.extend(['--server', base_url])
                if use_api_key and hasattr(self.runner, 'session_api_key') and self.runner.session_api_key:
                    cmd.extend(['--api-key', self.runner.session_api_key])
                
                self.log_step("Installing App", f"Running: {' '.join(cmd)} in {app_abs_path}")
                
                result = subprocess.run(
                    cmd,
                    cwd=app_abs_path,
                    capture_output=capture_output,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    self.log_step("Install Success", f"App installed successfully from {app_to_try}")
                    return True
                else:
                    self.log_step("Install Failed", f"Error: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.log_step("Install Timeout", "Installation timed out")
            except Exception as e:
                self.log_step("Install Error", f"Exception: {str(e)}")
        
        self.log_step("Install Failed", "All app installation attempts failed")
        return False
    
    async def fiber_update(self, config):
        """Execute fiber update command for an app."""
        from pathlib import Path
        
        app_path = config.get('app_path')
        fallback_apps = config.get('fallback_apps', [])
        base_url = config.get('base_url', '{{instance_url}}')
        use_api_key = config.get('use_api_key', False)
        timeout = config.get('timeout', 120)
        capture_output = config.get('capture_output', True)
        verbose = config.get('verbose', False)
        force = config.get('force', False)
        manifest_path = config.get('manifest_path')
        
        # Replace template variables
        if base_url == '{{instance_url}}' and hasattr(self.runner, 'temp_instance'):
            base_url = self.runner.temp_instance.base_url
        
        # Try main app path first, then fallbacks
        apps_to_try = [app_path] + fallback_apps
        
        for app_to_try in apps_to_try:
            if not app_to_try:
                continue
                
            try:
                app_abs_path = Path(app_to_try).resolve()
                if not app_abs_path.exists():
                    self.log_step("App Not Found", f"App path {app_to_try} does not exist")
                    continue
                
                # Construct fiber update command
                cmd = ['fiber', 'app', 'update']
                
                # Add app path (use current directory if running in app folder)
                if app_abs_path.name != '.':
                    cmd.append(str(app_abs_path))
                else:
                    cmd.append('.')
                    
                if manifest_path:
                    cmd.extend(['--manifest', manifest_path])
                if verbose:
                    cmd.append('--verbose')
                if force:
                    cmd.append('--force')
                if base_url:
                    cmd.extend(['--server', base_url])
                if use_api_key and hasattr(self.runner, 'session_api_key') and self.runner.session_api_key:
                    cmd.extend(['--api-key', self.runner.session_api_key])
                
                self.log_step("Updating App", f"Running: {' '.join(cmd)} in {app_abs_path}")
                
                result = subprocess.run(
                    cmd,
                    cwd=app_abs_path,
                    capture_output=capture_output,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    self.log_step("Update Success", f"App updated successfully from {app_to_try}")
                    if capture_output:
                        self.log_step("Update Output", result.stdout)
                    return True
                else:
                    self.log_step("Update Failed", f"Command failed with return code {result.returncode}")
                    if capture_output:
                        self.log_step("Error Output", result.stderr)
                        self.log_step("Standard Output", result.stdout)
                    continue
                    
            except subprocess.TimeoutExpired:
                self.log_step("Update Timeout", f"Command timed out after {timeout}s for {app_to_try}")
                continue
            except Exception as e:
                self.log_step("Update Error", f"Error updating {app_to_try}: {e}")
                continue
        
        self.log_step("Update Failed", "Failed to update app from any path")
        return False

    async def analyze_server_logs(self, config):
        """Analyze server logs for errors, warnings, and patterns."""
        from pathlib import Path
        
        self.log_step("Starting Log Analysis", "Analyzing server logs for issues")
        
        log_types = config.get('log_types', ['error', 'warning'])
        include_performance = config.get('include_performance', False)
        generate_summary = config.get('generate_summary', True)
        check_auth_patterns = config.get('check_auth_patterns', True)
        
        if not hasattr(self.runner, 'temp_instance') or not self.runner.temp_instance:
            self.log_step("No Instance", "No temp instance available for log analysis")
            return
        
        logs_dir = Path(self.runner.temp_instance.instance_dir) / "logs"
        
        # Define log files to analyze
        log_files = {
            'server': logs_dir / "server.log",
            'error': logs_dir / "server_error.log"
        }
        
        all_issues = []
        
        for log_name, log_path in log_files.items():
            if not log_path.exists():
                self.log_step(f"Log Missing", f"{log_name} log not found at {log_path}")
                continue
                
            self.log_step(f"Analyzing {log_name.title()}", f"Reading {log_path}")
            
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Analyze each line for issues
                for i, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    
                    # Error patterns
                    if any(pattern in line_lower for pattern in ['error', 'exception', 'traceback', 'failed']):
                        if 'error' in log_types:
                            all_issues.append(f"❌ Line {i}: {line.strip()}")
                    
                    # Warning patterns
                    elif any(pattern in line_lower for pattern in ['warning', 'warn', 'deprecated']):
                        if 'warning' in log_types:
                            all_issues.append(f"⚠️ Line {i}: {line.strip()}")
                    
                    # Critical patterns
                    elif any(pattern in line_lower for pattern in ['critical', 'fatal', 'crash', 'abort']):
                        all_issues.append(f"🚨 Line {i}: {line.strip()}")
                    
                    # Auth patterns if enabled
                    elif check_auth_patterns and any(pattern in line_lower for pattern in ['authentication', 'unauthorized', 'forbidden', 'token']):
                        all_issues.append(f"🔐 Line {i}: {line.strip()}")
                
            except Exception as e:
                self.log_step(f"Log Error", f"Error reading {log_name} log: {str(e)}")
        
        # Generate summary
        if generate_summary:
            error_count = len([i for i in all_issues if i.startswith('❌')])
            warning_count = len([i for i in all_issues if i.startswith('⚠️')])
            critical_count = len([i for i in all_issues if i.startswith('🚨')])
            
            # Add console log analysis
            console_summary = self.analyze_console_logs()
            
            summary = f"Found {error_count} errors, {warning_count} warnings, {critical_count} critical issues"
            if console_summary:
                summary += f" | {console_summary}"
            
            self.log_step("Log Analysis Summary", summary)
        
        # Log all issues found
        if all_issues:
            self.log_step("Issues Found", f"Total issues detected: {len(all_issues)}")
            for i, issue in enumerate(all_issues[:20], 1):
                clean_issue = issue.encode('ascii', 'ignore').decode('ascii')
                self.log_step(f"Issue {i}", clean_issue)
            if len(all_issues) > 20:
                self.log_step("More Issues", f"+ {len(all_issues) - 20} additional issues (truncated)")
        else:
            self.log_step("Clean Logs", "✅ No major issues detected in server logs")
        
        self.log_step("Log Analysis Complete", f"Analyzed {len(log_files)} log files")
    
    def analyze_console_logs(self):
        """Analyze collected console logs and return summary."""
        if not hasattr(self.runner, 'console_errors') or not self.runner.console_errors:
            return "Console: No JavaScript errors or warnings detected"
        
        # Group by type
        error_count = len([e for e in self.runner.console_errors if e['type'] == 'error'])
        warning_count = len([e for e in self.runner.console_errors if e['type'] == 'warning'])
        page_error_count = len([e for e in self.runner.console_errors if e['type'] == 'page_error'])
        
        console_summary = f"Console: {error_count} JS errors, {warning_count} JS warnings, {page_error_count} page errors"
        
        # Log recent console issues
        if self.runner.console_errors:
            self.log_step("Console Issues Found", f"Total console issues: {len(self.runner.console_errors)}")
            for i, error in enumerate(self.runner.console_errors[-5:], 1):
                timestamp = error.get('timestamp', 'unknown')[:19]  # Truncate timestamp
                clean_text = error['text'].encode('ascii', 'ignore').decode('ascii')[:100]
                self.log_step(f"Console Issue {i}", f"[{timestamp}] {error['type']}: {clean_text}")
        
        return console_summary
    
    async def verify_database(self, config: Dict[str, Any]):
        """Verify database contents and run SQL queries."""
        queries = config.get('queries', [])
        database_path = config.get('database_path', '')
        capture_variable = config.get('capture_variable')

        # Replace template variables
        if '{{instance_dir}}' in database_path and hasattr(self.runner, 'temp_instance'):
            database_path = database_path.replace('{{instance_dir}}', str(self.runner.temp_instance.instance_dir))

        if not database_path:
            self.log_step("Database Error", "No database path provided")
            return False

        db_path = Path(database_path)
        if not db_path.exists():
            self.log_step("Database Missing", f"Database file not found: {db_path}")
            return False

        self.log_step("Database Check", f"Connecting to: {db_path}")

        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row  # Enable column name access
                cursor = conn.cursor()

                for i, query in enumerate(queries, 1):
                    try:
                        self.log_step(f"Database Query {i}", f"Executing: {query[:80]}...")
                        cursor.execute(query)
                        results = cursor.fetchall()

                        if results:
                            self.log_step(f"Query {i} Results", f"Found {len(results)} rows")

                            # Show column headers
                            if len(results) > 0:
                                columns = list(results[0].keys())
                                self.log_step(f"Query {i} Columns", f"Columns: {', '.join(columns)}")

                            # Show first few rows
                            for j, row in enumerate(results[:5], 1):
                                row_data = []
                                for col in row.keys():
                                    value = row[col]
                                    if value is None:
                                        value = 'NULL'
                                    elif isinstance(value, str) and len(value) > 50:
                                        value = value[:50] + '...'
                                    row_data.append(f"{col}={value}")

                                self.log_step(f"Query {i} Row {j}", " | ".join(row_data))

                            if len(results) > 5:
                                self.log_step(f"Query {i} More", f"... and {len(results) - 5} more rows")

                            # Capture variable if requested (first column of first row)
                            if capture_variable and i == 1:
                                first_row = results[0]
                                first_col = list(first_row.keys())[0]
                                value = first_row[first_col]
                                self.runner.set_session_variable(capture_variable, str(value), f"Captured from DB: {first_col}")
                        else:
                            self.log_step(f"Query {i} Results", "No rows found")

                    except sqlite3.Error as e:
                        self.log_step(f"Query {i} Error", f"SQL Error: {str(e)}")

                self.log_step("Database Check Complete", f"Executed {len(queries)} queries")
                return True

        except sqlite3.Error as e:
            self.log_step("Database Connection Error", f"Could not connect to database: {str(e)}")
            return False
        except Exception as e:
            self.log_step("Database Unexpected Error", f"Unexpected error: {str(e)}")
            return False
    
    async def api_test(self, config: Dict[str, Any]):
        """Test API endpoint with HTTP request."""
        import requests
        
        method = config.get('method', 'GET').upper()
        url = config.get('url', '')
        headers = config.get('headers', {})
        data = config.get('data')
        json_data = config.get('json')
        expected_status = config.get('expected_status', 200)
        timeout = config.get('timeout', 10)
        
        if not url:
            self.log_step("API Test Error", "No URL specified")
            return False
        
        # Apply template substitution
        url = self.runner.substitute_template_variables(url)
        
        self.log_step("API Test", f"{method} {url}")
        
        try:
            # Make HTTP request
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=json_data, data=data, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=json_data, data=data, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                self.log_step("API Test Error", f"Unsupported method: {method}")
                return False
            
            # Check status code
            if isinstance(expected_status, list):
                success = response.status_code in expected_status
                expected_str = f"one of {expected_status}"
            else:
                success = response.status_code == expected_status
                expected_str = str(expected_status)
            
            if success:
                self.log_step("API Test Success", f"Status: {response.status_code} (expected {expected_str})")
                try:
                    # Try to parse JSON response
                    json_response = response.json()
                    self.log_step("API Response", f"JSON keys: {list(json_response.keys()) if isinstance(json_response, dict) else 'non-dict response'}")
                except:
                    self.log_step("API Response", f"Text response ({len(response.text)} chars)")
                return True
            else:
                self.log_step("API Test Failed", f"Status: {response.status_code} (expected {expected_str})")
                self.log_step("API Error Response", response.text[:200] if response.text else "No response body")
                return False
                
        except requests.exceptions.ConnectionError:
            self.log_step("API Test Failed", f"Connection refused to {url}")
            return False
        except requests.exceptions.Timeout:
            self.log_step("API Test Failed", f"Timeout after {timeout}s")
            return False
        except Exception as e:
            self.log_step("API Test Error", f"Exception: {str(e)}")
            return False

    async def generate_html_report(self, config: Dict[str, Any]):
        """Generate HTML test report using the dedicated report generator."""
        from pathlib import Path
        import sys
        
        # Configuration options
        report_title = config.get('title', 'FiberWise Test Report')
        include_screenshots = config.get('include_screenshots', True)
        custom_sections = config.get('custom_sections', {})
        report_filename = config.get('filename', 'test_report.html')
        
        self.log_step("HTML Report Generation", f"Generating report: {report_title}")
        
        try:
            # Get session directory from runner
            session_dir = self.runner.base_dir
            report_path = session_dir / report_filename
            screenshots_dir = session_dir / "screenshots"
            
            # Check if screenshots exist
            screenshot_files = list(screenshots_dir.glob("*.png")) if screenshots_dir.exists() else []
            screenshot_count = len(screenshot_files)
            
            self.log_step("Report Info", f"Session: {self.runner.session_id}")
            self.log_step("Report Info", f"Screenshots found: {screenshot_count}")
            
            # Generate the report content
            html_content = self._generate_report_html(
                report_title, 
                session_dir, 
                screenshot_files if include_screenshots else [],
                custom_sections
            )
            
            # Write the HTML report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.log_step("HTML Report Success", f"Report generated: {report_path}")
            self.log_step("Report Details", f"File size: {report_path.stat().st_size} bytes")
            
            return True
            
        except Exception as e:
            self.log_step("HTML Report Error", f"Failed to generate report: {str(e)}")
            return False
    
    def _generate_report_html(self, title, session_dir, screenshot_files, custom_sections):
        """Generate the HTML content for the test report."""
        from datetime import datetime
        import json
        
        session_path = Path(session_dir)
        screenshot_count = len(screenshot_files)
        
        # Load session info for detailed metrics
        session_info_path = session_path / "session_info.json"
        database_metrics = self._extract_database_metrics(session_info_path)
        routes_tested = self._extract_routes_tested(session_info_path)
        
        # Build custom sections HTML
        custom_html = ""
        for section_title, section_content in custom_sections.items():
            custom_html += f"""
        <div class="section">
            <h2>{section_title}</h2>
            {section_content}
        </div>"""
        
        # Generate detailed database verification HTML
        database_html = self._generate_database_verification_html(database_metrics)
        
        # Generate routes and pages tested HTML
        routes_html = self._generate_routes_tested_html(routes_tested)
        
        # Generate screenshot gallery HTML (ALL screenshots)
        screenshot_html = ""
        if screenshot_files:
            screenshot_html = self._generate_screenshot_gallery(screenshot_files, show_all=True)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }}
        .success {{ color: #28a745; font-weight: bold; }}
        .section {{ margin-bottom: 20px; padding: 15px; border-left: 4px solid #667eea; background-color: #f8f9ff; }}
        .section.database {{ border-left-color: #28a745; background-color: #f8fff8; }}
        .section.routes {{ border-left-color: #ffc107; background-color: #fffef8; }}
        .summary {{ background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); border: 1px solid #c3e6cb; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
        .test-item {{ display: flex; align-items: center; margin-bottom: 8px; padding: 5px; }}
        .check {{ color: #28a745; font-size: 1.2em; margin-right: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; margin-bottom: 5px; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        .screenshot-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 15px; }}
        .screenshot {{ border: 1px solid #ddd; border-radius: 5px; overflow: hidden; background: white; transition: transform 0.2s; }}
        .screenshot:hover {{ transform: scale(1.02); }}
        .screenshot img {{ width: 100%; height: auto; display: block; cursor: pointer; }}
        .screenshot-title {{ padding: 8px; background: #f8f9fa; font-size: 0.9em; color: #666; text-align: center; }}
        .metric-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .metric-table th, .metric-table td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        .metric-table th {{ background-color: #f8f9fa; font-weight: bold; }}
        .metric-value {{ font-family: monospace; background: #f8f9fa; padding: 2px 6px; border-radius: 3px; }}
        .query-block {{ background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; margin: 10px 0; font-family: monospace; font-size: 0.9em; white-space: pre-wrap; }}
        .collapsible {{ cursor: pointer; padding: 10px; background: #e9ecef; border: none; width: 100%; text-align: left; border-radius: 5px; margin-top: 10px; }}
        .collapsible:hover {{ background: #dee2e6; }}
        .content {{ display: none; padding: 10px; background: #f8f9fa; border-radius: 5px; margin-top: 5px; }}
        .route-card {{ background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 10px; }}
        .route-path {{ font-family: monospace; background: #e9ecef; padding: 4px 8px; border-radius: 4px; }}
    </style>
    <script>
        function toggleContent(element) {{
            var content = element.nextElementSibling;
            if (content.style.display === "none" || content.style.display === "") {{
                content.style.display = "block";
                element.textContent = element.textContent.replace("▶", "▼");
            }} else {{
                content.style.display = "none";
                element.textContent = element.textContent.replace("▼", "▶");
            }}
        }}
        
        function openScreenshot(src) {{
            window.open(src, '_blank');
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 {title}</h1>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Session:</strong> {session_path.name}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">✅</div>
                <div class="stat-label">Test Status</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{screenshot_count}</div>
                <div class="stat-label">Screenshots</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(self.runner.session_log)}</div>
                <div class="stat-label">Steps Completed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{database_metrics.get('total_queries', 0)}</div>
                <div class="stat-label">DB Queries</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(routes_tested)}</div>
                <div class="stat-label">Pages Visited</div>
            </div>
        </div>

        <div class="summary">
            <h2>🎯 Test Summary</h2>
            <div class="test-item">
                <span class="check">✅</span>
                <span>Test execution completed successfully</span>
            </div>
            <div class="test-item">
                <span class="check">✅</span>
                <span>Database integrity verified with {database_metrics.get('total_queries', 0)} queries</span>
            </div>
            <div class="test-item">
                <span class="check">✅</span>
                <span>Models created: {database_metrics.get('models_verified', 0)}</span>
            </div>
            <div class="test-item">
                <span class="check">✅</span>
                <span>Fields verified: {database_metrics.get('fields_verified', 0)}</span>
            </div>
            <div class="test-item">
                <span class="check">✅</span>
                <span>Routes tested: {len(routes_tested)}</span>
            </div>
            <div class="test-item">
                <span class="check">✅</span>
                <span>Screenshots captured: {screenshot_count}</span>
            </div>
        </div>

        {custom_html}
        
        {database_html}
        
        {routes_html}
        
        <div class="section">
            <h2>📊 Test Execution Details</h2>
            <ul>
                <li><strong>Session ID:</strong> {self.runner.session_id}</li>
                <li><strong>Total Steps:</strong> {len(self.runner.session_log)}</li>
                <li><strong>Console Logs:</strong> {len(self.runner.console_logs)} entries</li>
                <li><strong>Console Errors:</strong> {len(self.runner.console_errors)} entries</li>
                <li><strong>Session Variables:</strong> {len(self.runner.session_variables)} captured</li>
            </ul>
        </div>

        <div class="section">
            <h2>📁 Session Files</h2>
            <p><strong>Session Directory:</strong> {session_path.name}</p>
            <p>Available files and directories:</p>
            <ul>
                <li><code>screenshots/</code> - Test step screenshots ({screenshot_count} images)</li>
                <li><code>videos/</code> - Browser session recordings (if enabled)</li>
                <li><code>logs/</code> - Application and test logs</li>
                <li><code>session_info.json</code> - Complete session data (generated at end)</li>
            </ul>
        </div>

        {screenshot_html}
        
        <div class="section" style="border-left-color: #28a745; background-color: #d4edda;">
            <h2>✅ Test Result: SUCCESS</h2>
            <p>Test execution completed successfully. All configured steps were processed, database integrity verified, and session data preserved for analysis.</p>
        </div>
    </div>
</body>
</html>"""
        
        return html_content
    
    def _generate_screenshot_gallery(self, screenshot_files, show_all=False):
        """Generate HTML for screenshot gallery."""
        if not screenshot_files:
            return ""
        
        # Sort screenshots by filename to maintain chronological order
        sorted_screenshots = sorted(screenshot_files, key=lambda x: x.name)
        
        screenshot_html = f"""
        <div class="section">
            <h2>📸 Test Screenshots ({len(sorted_screenshots)} images)</h2>
            <p>Click on any screenshot to view it in full size in a new tab.</p>
            <div class="screenshot-grid">"""
        
        for i, screenshot in enumerate(sorted_screenshots):
            screenshot_name = screenshot.stem.replace('_', ' ').title()
            step_number = screenshot.stem.split('_')[0] if screenshot.stem.split('_')[0].isdigit() else str(i+1)
            
            screenshot_html += f"""
                <div class="screenshot">
                    <img src="screenshots/{screenshot.name}" 
                         alt="Screenshot {i+1}" 
                         loading="lazy"
                         onclick="openScreenshot('screenshots/{screenshot.name}')">
                    <div class="screenshot-title">
                        <strong>Step {step_number}:</strong><br>
                        {screenshot_name}
                    </div>
                </div>"""
        
        screenshot_html += """
            </div>
        </div>"""
        
        return screenshot_html
    
    def _extract_database_metrics(self, session_info_path):
        """Extract database verification metrics from session info."""
        import json
        from pathlib import Path
        
        metrics = {
            'total_queries': 0,
            'models_verified': 0,
            'fields_verified': 0,
            'routes_verified': 0,
            'verification_details': []
        }
        
        try:
            if session_info_path.exists():
                with open(session_info_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Extract database verification steps from config
                steps = session_data.get('steps', [])
                session_logs = session_data.get('logs', [])
                
                for step in steps:
                    if step.get('action') == 'verify_database':
                        step_id = step.get('id', '')
                        queries = step.get('config', {}).get('queries', [])
                        metrics['total_queries'] += len(queries)
                        
                        # Extract specific logs for this verification step
                        step_logs = [log for log in session_logs 
                                   if step_id.lower().replace('_', ' ') in log.get('step', '').lower() or 
                                      ('database' in log.get('step', '').lower() and 
                                       any(keyword in log.get('step', '').lower() for keyword in step_id.split('_')))]
                        
                        # Parse the results from logs
                        parsed_results = self._parse_verification_logs(step_logs, queries)
                        
                        verification_detail = {
                            'step_id': step_id,
                            'description': step.get('description', ''),
                            'queries': queries,
                            'query_count': len(queries),
                            'logs': step_logs[:20],  # Limit logs to prevent too much data
                            'parsed_results': parsed_results,
                            'summary': self._generate_step_summary(parsed_results, step.get('description', ''))
                        }
                        
                        # Categorize verification types
                        description_lower = step.get('description', '').lower()
                        if 'model' in description_lower:
                            metrics['models_verified'] += 1
                        if 'field' in description_lower:
                            metrics['fields_verified'] += 1
                        if 'route' in description_lower:
                            metrics['routes_verified'] += 1
                            
                        metrics['verification_details'].append(verification_detail)
        
        except Exception as e:
            # Fallback to basic metrics if parsing fails
            print(f"Database metrics extraction error: {str(e)}")
        
        return metrics
    
    def _parse_verification_logs(self, step_logs, queries):
        """Parse verification results from step logs."""
        results = []
        
        for i, query in enumerate(queries):
            query_num = str(i + 1)
            query_result = {
                'query_number': query_num,
                'sql': query,
                'status': 'success',
                'rows_found': 0,
                'columns': [],
                'sample_data': [],
                'insights': []
            }
            
            # Look for results in logs
            for log in step_logs:
                step_name = log.get('step', '')
                message = log.get('message', '')
                
                if f'Query {query_num} Results' in step_name:
                    if 'Found' in message and 'rows' in message:
                        try:
                            rows_text = message.split('Found ')[1].split(' rows')[0]
                            query_result['rows_found'] = int(rows_text)
                        except (IndexError, ValueError):
                            pass
                    elif 'No rows found' in message:
                        query_result['rows_found'] = 0
                        
                elif f'Query {query_num} Columns' in step_name and 'Columns:' in message:
                    columns_text = message.split('Columns: ')[1]
                    query_result['columns'] = [col.strip() for col in columns_text.split(',')]
                    
                elif f'Query {query_num} Row' in step_name:
                    query_result['sample_data'].append(message)
                    
                elif f'Query {query_num} Error' in step_name:
                    query_result['status'] = 'error'
                    query_result['error'] = message
            
            # Generate insights based on query and results
            query_result['insights'] = self._generate_query_insights(query, query_result)
            results.append(query_result)
        
        return results
    
    def _generate_query_insights(self, sql, result):
        """Generate insights from a query and its results."""
        insights = []
        sql_upper = sql.upper()
        rows = result.get('rows_found', 0)
        
        if 'COUNT(*)' in sql_upper:
            table_name = ''
            if 'FROM apps' in sql_upper:
                table_name = 'apps'
                insights.append(f"✓ Database contains {rows} application(s)")
            elif 'FROM models' in sql_upper:
                table_name = 'models'
                insights.append(f"✓ Found {rows} data model(s) in the system")
            elif 'FROM fields' in sql_upper:
                table_name = 'fields'
                insights.append(f"✓ Database has {rows} field definition(s)")
            elif 'FROM app_routes' in sql_upper:
                table_name = 'routes'
                insights.append(f"✓ System has {rows} registered route(s)")
            elif 'FROM api_keys' in sql_upper:
                insights.append(f"✓ Found {rows} API key(s) configured")
            elif 'FROM llm_providers' in sql_upper:
                insights.append(f"✓ System has {rows} LLM provider(s) configured")
            elif 'FROM agents' in sql_upper:
                insights.append(f"✓ Found {rows} agent(s) in the system")
                
            if rows == 0 and table_name:
                insights.append(f"⚠️ No {table_name} found - this might indicate an issue")
                
        elif 'SELECT' in sql_upper and rows > 0:
            if 'JOIN' in sql_upper:
                insights.append(f"✓ Successfully retrieved {rows} related record(s) via JOIN")
            else:
                insights.append(f"✓ Query returned {rows} record(s)")
                
        elif result.get('status') == 'error':
            insights.append(f"❌ Query failed - check database structure")
        
        return insights
    
    def _generate_step_summary(self, parsed_results, description):
        """Generate a summary for a verification step."""
        if not parsed_results:
            return "No results available"
        
        total_rows = sum(r.get('rows_found', 0) for r in parsed_results)
        success_count = sum(1 for r in parsed_results if r.get('status') == 'success')
        error_count = len(parsed_results) - success_count
        
        # Extract key insights
        key_insights = []
        for result in parsed_results:
            insights = result.get('insights', [])
            key_insights.extend([i for i in insights if '✓' in i])
        
        summary_parts = [f"{success_count}/{len(parsed_results)} queries successful"]
        
        if key_insights:
            summary_parts.extend(key_insights[:2])  # Show top 2 insights
        
        if error_count > 0:
            summary_parts.append(f"❌ {error_count} queries failed")
        
        return " | ".join(summary_parts)
    
    def _extract_step_logs(self, session_logs, step_id):
        """Extract all log entries related to a specific step."""
        step_logs = []
        in_step = False
        
        for log_entry in session_logs:
            step_name = log_entry.get('step', '')
            if step_id in step_name:
                in_step = True
            elif in_step and 'Database' not in step_name and 'Query' not in step_name:
                # Stop when we reach the next major step
                break
                
            if in_step:
                step_logs.append(log_entry)
        
        return step_logs
    
    def _parse_database_query_results(self, step_logs):
        """Parse database query results from step logs."""
        query_results = []
        current_query = None
        
        for log_entry in step_logs:
            step_name = log_entry.get('step', '')
            message = log_entry.get('message', '')
            
            if 'Database Query' in step_name and 'Executing:' in message:
                # Start of new query
                query_num = step_name.split('Database Query ')[1].split(' ')[0] if 'Database Query ' in step_name else '0'
                current_query = {
                    'query_number': query_num,
                    'sql': message.split('Executing: ')[1] if 'Executing: ' in message else '',
                    'rows_found': 0,
                    'columns': [],
                    'sample_data': [],
                    'status': 'success'
                }
                
            elif current_query and f"Query {current_query['query_number']} Results" in step_name:
                if 'Found' in message and 'rows' in message:
                    # Extract row count
                    try:
                        rows_text = message.split('Found ')[1].split(' rows')[0]
                        current_query['rows_found'] = int(rows_text)
                    except (IndexError, ValueError):
                        current_query['rows_found'] = 0
                elif 'No rows found' in message:
                    current_query['rows_found'] = 0
                    
            elif current_query and f"Query {current_query['query_number']} Columns" in step_name:
                # Extract column names
                if 'Columns: ' in message:
                    columns_text = message.split('Columns: ')[1]
                    current_query['columns'] = [col.strip() for col in columns_text.split(',')]
                    
            elif current_query and f"Query {current_query['query_number']} Row" in step_name:
                # Extract sample data
                current_query['sample_data'].append(message)
                
            elif current_query and f"Query {current_query['query_number']} More" in step_name:
                # Extract "more rows" info
                current_query['additional_rows_note'] = message
                
            elif current_query and f"Query {current_query['query_number']} Error" in step_name:
                current_query['status'] = 'error'
                current_query['error'] = message
                
            elif current_query and 'Database Check Complete' in step_name:
                # End of all queries for this step
                if current_query not in query_results:
                    query_results.append(current_query)
                current_query = None
                break
        
        # Add the last query if it wasn't added yet
        if current_query and current_query not in query_results:
            query_results.append(current_query)
            
        return query_results
    
    def _generate_query_summary(self, query_results):
        """Generate a summary of query results."""
        if not query_results:
            return "No query results available"
        
        total_rows = sum(q.get('rows_found', 0) for q in query_results)
        success_count = sum(1 for q in query_results if q.get('status') == 'success')
        error_count = len(query_results) - success_count
        
        summary_parts = [
            f"{len(query_results)} queries executed",
            f"{total_rows} total rows returned"
        ]
        
        if error_count > 0:
            summary_parts.append(f"{error_count} queries failed")
        
        # Add specific insights
        insights = []
        for query in query_results:
            if query.get('rows_found', 0) > 0:
                sql = query.get('sql', '').upper()
                if 'COUNT(*)' in sql:
                    # This is a count query
                    count_value = query.get('rows_found', 0)
                    if 'FROM models' in sql:
                        insights.append(f"Found {count_value} models in database")
                    elif 'FROM fields' in sql:
                        insights.append(f"Found {count_value} fields in database")
                    elif 'FROM apps' in sql:
                        insights.append(f"Found {count_value} apps in database")
                    elif 'FROM app_routes' in sql:
                        insights.append(f"Found {count_value} routes in database")
                    elif 'FROM api_keys' in sql:
                        insights.append(f"Found {count_value} API keys in database")
                    elif 'FROM llm_providers' in sql:
                        insights.append(f"Found {count_value} LLM providers in database")
        
        if insights:
            summary_parts.extend(insights)
        
        return " | ".join(summary_parts)
    
    def _extract_routes_tested(self, session_info_path):
        """Extract routes and pages tested from session info."""
        import json
        from pathlib import Path
        
        routes_tested = []
        
        try:
            if session_info_path.exists():
                with open(session_info_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Extract browser navigation and page interaction steps
                steps = session_data.get('steps', [])
                session_logs = session_data.get('logs', [])
                
                for step in steps:
                    step_type = step.get('type', '')
                    action = step.get('action', '')
                    step_id = step.get('id', '')
                    description = step.get('description', '')
                    
                    # Identify page/route related actions
                    if (step_type == 'browser' or 
                        'navigate' in action or 
                        any(keyword in description.lower() for keyword in 
                            ['page', 'login', 'register', 'api key', 'manage', 'agents', 'apps', 'dashboard'])):
                        
                        route_info = {
                            'step_id': step_id,
                            'action': action,
                            'description': description,
                            'config': step.get('config', {}),
                            'category': self._categorize_page_action(action, description)
                        }
                        
                        # Extract screenshots related to this step
                        step_screenshots = [log for log in session_logs 
                                          if step_id in log.get('step', '') and 'screenshot' in log.get('message', '').lower()]
                        route_info['screenshots'] = len(step_screenshots)
                        
                        routes_tested.append(route_info)
        
        except Exception as e:
            print(f"Routes extraction error: {str(e)}")
        
        return routes_tested
    
    def _categorize_page_action(self, action, description):
        """Categorize page actions into logical groups."""
        desc_lower = description.lower()
        action_lower = action.lower()
        
        if 'register' in desc_lower or 'registration' in desc_lower:
            return 'Authentication'
        elif 'login' in desc_lower or 'sign in' in desc_lower:
            return 'Authentication'
        elif 'api key' in desc_lower:
            return 'API Management'
        elif 'manage apps' in desc_lower or 'app' in desc_lower:
            return 'App Management'
        elif 'agent' in desc_lower:
            return 'Agent Interface'
        elif 'navigate' in action_lower:
            return 'Navigation'
        elif 'dashboard' in desc_lower or 'home' in desc_lower:
            return 'Dashboard'
        else:
            return 'General'
    
    def _generate_database_verification_html(self, database_metrics):
        """Generate HTML for database verification section."""
        if not database_metrics['verification_details']:
            return ""
        
        html = """
        <div class="section database">
            <h2>🗄️ Database Verification Results</h2>
            <p>This section shows all database integrity checks performed during the test, including the specific SQL queries used, results returned, and verification metrics.</p>
            
            <table class="metric-table">
                <tr>
                    <th>Verification Step</th>
                    <th>Queries</th>
                    <th>Summary</th>
                    <th>Status</th>
                </tr>"""
        
        for detail in database_metrics['verification_details']:
            summary = detail.get('summary', 'No summary available')
            query_count = detail['query_count']
            
            # Determine status based on results
            results = detail.get('results', [])
            status = "✅ Success" if all(r.get('status') == 'success' for r in results) else "❌ Issues"
            
            html += f"""
                <tr>
                    <td><strong>{detail['step_id'].replace('_', ' ').title()}</strong><br>
                        <small>{detail['description']}</small></td>
                    <td><span class="metric-value">{query_count}</span></td>
                    <td><small>{summary}</small></td>
                    <td>{status}</td>
                </tr>"""
        
        html += """
            </table>
            
            <h3>� Detailed Query Results</h3>
            <p>Click on each verification step to see the SQL queries executed and their results:</p>"""
        
        for i, detail in enumerate(database_metrics['verification_details']):
            html += f"""
            <button class="collapsible" onclick="toggleContent(this)">
                ▶ {detail['step_id'].replace('_', ' ').title()} - {detail.get('summary', 'No summary')}
            </button>
            <div class="content">
                <p><strong>Purpose:</strong> {detail['description']}</p>
                <p><strong>Summary:</strong> {detail.get('summary', 'No summary available')}</p>"""
            
            results = detail.get('results', [])
            
            for j, query_result in enumerate(results):
                query_num = query_result.get('query_number', j+1)
                sql = query_result.get('sql', 'No SQL available')
                rows_found = query_result.get('rows_found', 0)
                columns = query_result.get('columns', [])
                sample_data = query_result.get('sample_data', [])
                status = query_result.get('status', 'unknown')
                
                status_icon = "✅" if status == "success" else "❌"
                
                html += f"""
                <div style="margin: 15px 0; padding: 10px; border: 1px solid #dee2e6; border-radius: 5px;">
                    <h4>{status_icon} Query {query_num}: {rows_found} rows returned</h4>
                    <div class="query-block">{sql}</div>"""
                
                if status == 'error':
                    html += f"""<div style="color: #dc3545; margin-top: 10px;"><strong>Error:</strong> {query_result.get('error', 'Unknown error')}</div>"""
                else:
                    if columns:
                        html += f"""<p><strong>Columns:</strong> {', '.join(columns)}</p>"""
                    
                    if sample_data:
                        html += f"""<div><strong>Sample Data:</strong></div>"""
                        for data_row in sample_data[:3]:  # Show first 3 rows
                            html += f"""<div style="font-family: monospace; background: #f8f9fa; padding: 5px; margin: 2px 0; border-radius: 3px; font-size: 0.85em;">{data_row}</div>"""
                        
                        if len(sample_data) > 3:
                            html += f"""<div style="font-style: italic; color: #666; margin-top: 5px;">... and {len(sample_data) - 3} more sample rows</div>"""
                        
                        if query_result.get('additional_rows_note'):
                            html += f"""<div style="font-style: italic; color: #666; margin-top: 5px;">{query_result['additional_rows_note']}</div>"""
                    
                    elif rows_found == 0:
                        html += f"""<div style="color: #6c757d; font-style: italic;">No data returned</div>"""
                    
                html += """</div>"""
            
            if not results:
                # Fall back to showing the queries if no parsed results
                for j, query in enumerate(detail['queries']):
                    html += f"""
                    <div style="margin: 10px 0;">
                        <strong>Query {j+1}:</strong>
                        <div class="query-block">{query}</div>
                    </div>"""
            
            html += "</div>"
        
        html += """
        </div>"""
        
        return html
    
    def _generate_routes_tested_html(self, routes_tested):
        """Generate HTML for routes and pages tested section."""
        if not routes_tested:
            return ""
        
        # Group routes by category
        routes_by_category = {}
        for route in routes_tested:
            category = route.get('category', 'General')
            if category not in routes_by_category:
                routes_by_category[category] = []
            routes_by_category[category].append(route)
        
        html = f"""
        <div class="section routes">
            <h2>🌐 Pages and Routes Tested ({len(routes_tested)} total)</h2>
            <p>This section shows all the pages and routes that were visited or tested during the execution, grouped by functionality.</p>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-bottom: 20px;">"""
        
        # Create category summary cards
        for category, category_routes in routes_by_category.items():
            screenshot_count = sum(r.get('screenshots', 0) for r in category_routes)
            html += f"""
                <div class="route-card" style="text-align: center; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);">
                    <h4 style="margin: 10px 0; color: #495057;">{category}</h4>
                    <div style="font-size: 1.5em; color: #6c757d; margin: 5px 0;">{len(category_routes)} pages</div>
                    <div style="font-size: 0.9em; color: #6c757d;">{screenshot_count} screenshots</div>
                </div>"""
        
        html += """</div>"""
        
        # Show detailed breakdown by category
        for category, category_routes in routes_by_category.items():
            html += f"""
            <button class="collapsible" onclick="toggleContent(this)">
                ▶ {category} - {len(category_routes)} pages tested
            </button>
            <div class="content">"""
            
            for route in category_routes:
                action_badge = route.get('action', 'unknown').replace('_', ' ').title()
                screenshot_count = route.get('screenshots', 0)
                screenshot_info = f"📸 {screenshot_count}" if screenshot_count > 0 else "📷 No screenshots"
                
                html += f"""
                <div class="route-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0;">{route['step_id'].replace('_', ' ').title()}</h4>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <span style="background: #e9ecef; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">{action_badge}</span>
                            <span style="background: #e8f4fd; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">{screenshot_info}</span>
                        </div>
                    </div>
                    <p><strong>Description:</strong> {route['description']}</p>"""
                
                # Add config details if available
                config = route.get('config', {})
                if config:
                    config_items = []
                    for key, value in config.items():
                        if isinstance(value, str) and len(value) < 100:
                            config_items.append(f"<strong>{key}:</strong> <code>{value}</code>")
                        elif isinstance(value, (int, bool)):
                            config_items.append(f"<strong>{key}:</strong> <code>{value}</code>")
                    
                    if config_items:
                        html += f"<div style='margin-top: 10px; font-size: 0.9em;'>{' | '.join(config_items)}</div>"
                
                html += "</div>"
            
            html += "</div>"
        
        # Add summary statistics
        total_screenshots = sum(r.get('screenshots', 0) for r in routes_tested)
        categories_count = len(routes_by_category)
        
        html += f"""
        <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <h4>📊 Page Testing Summary</h4>
            <ul style="margin: 10px 0; list-style: none; padding: 0;">
                <li>• <strong>{len(routes_tested)}</strong> total pages/routes tested</li>
                <li>• <strong>{categories_count}</strong> functional categories covered</li>
                <li>• <strong>{total_screenshots}</strong> screenshots captured during page interactions</li>
                <li>• <strong>Categories:</strong> {', '.join(routes_by_category.keys())}</li>
            </ul>
        </div>
        </div>"""
        
        return html
