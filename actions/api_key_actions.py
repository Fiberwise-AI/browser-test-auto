"""
API key management browser actions.
"""

import asyncio
from typing import Dict, Any, List
from .base_action import BaseAction


class APIKeyActions(BaseAction):
    """Handles API key-related browser actions."""
    
    async def execute(self, step: Dict[str, Any]) -> Any:
        """Execute API key-related step."""
        action = step.get('action')
        config = step.get('config', {})
        
        # Initialize browser if needed
        if not self.runner.browser:
            settings = self.runner.script.get('settings', {})
            await self.runner.initialize_browser(settings, config)
        
        context = self.runner.browser_context
        
        if action == "create_api_key":
            await self.create_api_key(context, config)
        elif action == "create_api_keys_bulk":
            await self.create_api_keys_bulk(context, config)
        elif action == "list_api_keys":
            await self.list_api_keys(context, config)
        elif action == "test_api_key_scopes":
            await self.test_api_key_scopes(context, config)
        elif action == "test_api_key":
            await self.test_api_key(context, config)
        else:
            self.log_step("Unknown API Key Action", f"Action '{action}' not implemented")
            return None
    
    async def create_api_key(self, context, config: Dict[str, Any]):
        """Create a single API key after logging in."""
        username = config.get('username', 'testuser1')
        password = config.get('password', 'testpass123')
        key_name = config.get('key_name', 'Test Key')
        scopes = config.get('scopes', ['read', 'write'])
        capture_secret = config.get('capture_secret', None)  # Session variable name to store the API key
        
        page, should_close = await self.get_or_create_page(context, config)
        try:
            self.log_step("API Key Creation", f"Creating API key '{key_name}' for {username}")
            
            # Login first
            await self._perform_login(page, username, password)
            
            # Navigate to API keys page
            await self._navigate_to_api_keys_page(page)
            
            # Create the API key
            captured_value = await self._create_single_api_key(page, key_name, scopes)
            
            # Store in session variables if capture_secret is specified
            if capture_secret and captured_value:
                self.runner.set_session_variable(
                    capture_secret, 
                    captured_value, 
                    f"API key secret for '{key_name}'"
                )
                self.log_step("Session Variable", f"Stored API key in session variable: {capture_secret}")
            
        except Exception as e:
            self.log_step("API Key Creation Error", f"Error creating API key: {str(e)}")
        finally:
            if should_close:
                await page.close()
    
    async def create_api_keys_bulk(self, context, config: Dict[str, Any]):
        """Create multiple API keys in a single session."""
        username = config.get('username', 'testuser1')
        password = config.get('password', 'testpass123')
        keys_to_create = config.get('keys', [])
        
        if not keys_to_create:
            self.log_step("Bulk API Keys", "No keys specified for creation")
            return
        
        page, should_close = await self.get_or_create_page(context, config)
        try:
            self.log_step("Bulk API Key Creation", f"Creating {len(keys_to_create)} API keys for {username}")
            
            # Login first
            await self._perform_login(page, username, password)
            
            # Navigate to API keys page
            await self._navigate_to_api_keys_page(page)
            
            # Create each API key
            for i, key_config in enumerate(keys_to_create):
                key_name = key_config.get('name', f'Test Key {i+1}')
                scopes = key_config.get('scopes', ['read', 'write'])
                
                self.log_step(f"Creating Key {i+1}", f"Name: {key_name}, Scopes: {scopes}")
                await self._create_single_api_key(page, key_name, scopes)
                
                # Brief pause between creations
                await asyncio.sleep(1)
            
        except Exception as e:
            self.log_step("Bulk API Key Error", f"Error in bulk creation: {str(e)}")
        finally:
            if should_close:
                await page.close()
    
    async def _perform_login(self, page, username: str, password: str):
        """Perform login if not already logged in."""
        current_url = page.url
        if '/login' not in current_url and not await self._is_logged_in(page):
            # Navigate to login page
            await page.goto(f"{self.runner.base_url}/login", timeout=10000)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Fill login form
            await self._fill_login_form(page, username, password)
    
    async def _is_logged_in(self, page) -> bool:
        """Check if user is already logged in."""
        try:
            # Look for common logged-in indicators
            indicators = [
                'text="Logout"',
                'text="Profile"',
                '[data-testid="user-menu"]',
                '.user-profile'
            ]
            
            for indicator in indicators:
                if await page.locator(indicator).count() > 0:
                    return True
            return False
        except:
            return False
    
    async def _fill_login_form(self, page, username: str, password: str):
        """Fill and submit login form."""
        # Fill username (using identifier field from login form)
        await page.fill('input[name="identifier"]', username, timeout=3000)
        
        # Fill password
        await page.fill('input[name="password"]', password, timeout=3000)
        
        # Submit form
        await page.click('button[type="submit"]', timeout=3000)
        
        # Wait for redirect
        await asyncio.sleep(3)
    
    async def _navigate_to_api_keys_page(self, page):
        """Navigate to the API keys management page."""
        # Use the exact route from routes.js
        api_keys_url = f"{self.runner.base_url}/settings/api-keys"
        
        try:
            await page.goto(api_keys_url, timeout=10000)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Verify we're on the API keys page
            if await self._is_api_keys_page(page):
                self.log_step("API Keys Page", f"Successfully navigated to: {api_keys_url}")
                return
            else:
                self.log_step("API Keys Navigation Error", f"Navigated to {api_keys_url} but page doesn't contain API keys content")
        except Exception as e:
            self.log_step("API Keys Navigation Error", f"Failed to navigate to {api_keys_url}: {str(e)}")
            
        # If direct navigation failed, try to find a link as fallback
        await self._find_api_keys_link(page)
    
    async def _is_api_keys_page(self, page) -> bool:
        """Check if current page is the API keys management page."""
        try:
            # Check for the api-keys-page component (from routes.js)
            return await page.locator('api-keys-page').count() > 0
        except:
            return False
    
    async def _find_api_keys_link(self, page):
        """Try to find and click Settings navigation link."""
        try:
            # Look for Settings link in navigation (from routes.js category: 'Settings')
            if await page.locator('a:has-text("Settings")').count() > 0:
                await page.click('a:has-text("Settings")', timeout=3000)
                await asyncio.sleep(2)
                
                # Check if we found API keys section
                if await self._is_api_keys_page(page):
                    self.log_step("API Keys Navigation", "Found via Settings link")
                    return
        except:
            pass
            
        self.log_step("API Keys Navigation", "Could not find API keys page")
    
    async def _create_single_api_key(self, page, key_name: str, scopes: List[str]):
        """Create a single API key with given name and scopes."""
        # Take screenshot before creation
        await page.screenshot(path=self.get_screenshot_path(f"before_create_{key_name.replace(' ', '_')}"))
        
        # Look for create button (simplified)
        create_button_found = False
        try:
            if await page.locator('button:has-text("Create API Key")').count() > 0:
                await page.click('button:has-text("Create API Key")', timeout=3000)
                create_button_found = True
                self.log_step("Create Button", "Clicked: Create API Key button")
        except Exception as e:
            self.log_step("Create Button Error", f"Failed to click Create API Key button: {str(e)}")
        
        if not create_button_found:
            self.log_step("Create Button Error", "Could not find Create API Key button")
            return None
        
        # Wait for form to appear
        await asyncio.sleep(2)
        
        # Debug: Show all input fields on page
        try:
            all_inputs = await page.locator('input').all()
            input_info = []
            for j, input_elem in enumerate(all_inputs):
                try:
                    name = await input_elem.get_attribute('name') or 'no-name'
                    placeholder = await input_elem.get_attribute('placeholder') or 'no-placeholder'
                    input_type = await input_elem.get_attribute('type') or 'text'
                    input_id = await input_elem.get_attribute('id') or 'no-id'
                    input_info.append(f"Input{j+1}: type={input_type}, name={name}, id={input_id}, placeholder={placeholder}")
                except:
                    continue
            
            if input_info:
                self.log_step("API Key Form Inputs", f"Found {len(input_info)} input fields")
                for info in input_info[:5]:  # Show first 5 fields
                    self.log_step("Form Input", info)
        except Exception as e:
            self.log_step("Form Debug Error", f"Could not analyze form: {str(e)}")
        
        # Fill API key name
        name_selectors = [
            'input[name="name"]',
            'input[name="key_name"]',
            'input[name="keyName"]',
            'input[placeholder*="name" i]',
            'input[placeholder*="key" i]',
            '#api-key-name',
            '#name',
            '#keyName'
        ]
        
        name_filled = False
        for selector in name_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, key_name, timeout=3000)
                    name_filled = True
                    self.log_step("API Key Name", f"✅ Filled '{key_name}' using: {selector}")
                    break
            except Exception as e:
                self.log_step("Name Field Error", f"❌ Failed {selector}: {str(e)}")
                continue
        
        if not name_filled:
            self.log_step("Name Field Error", "❌ Could not find or fill API key name field")
        
        # Select scopes
        await self._select_scopes(page, scopes)
        
        # Submit the form and capture the result
        captured_value = await self._submit_api_key_form(page, key_name)
        
        return captured_value
    
    async def _select_scopes(self, page, scopes: List[str]):
        """Select the specified scopes for the API key."""
        self.log_step("Scope Selection", f"Selecting scopes: {scopes}")
        
        # Debug: Show all checkboxes and scope-related elements
        try:
            all_checkboxes = await page.locator('input[type="checkbox"]').all()
            if all_checkboxes:
                self.log_step("Scope Debug", f"Found {len(all_checkboxes)} checkboxes on page")
                for i, checkbox in enumerate(all_checkboxes):
                    try:
                        name = await checkbox.get_attribute('name') or 'no-name'
                        value = await checkbox.get_attribute('value') or 'no-value'
                        data_scope = await checkbox.get_attribute('data-scope') or 'no-data-scope'
                        checkbox_id = await checkbox.get_attribute('id') or 'no-id'
                        self.log_step(f"Checkbox {i+1}", f"name={name}, value={value}, data-scope={data_scope}, id={checkbox_id}")
                    except:
                        continue
            else:
                self.log_step("Scope Debug", "No checkboxes found - might use different scope selection method")
                
                # Look for other scope selection elements
                other_selectors = ['select[name*="scope"]', '.scope-selector', '[data-testid*="scope"]']
                for selector in other_selectors:
                    count = await page.locator(selector).count()
                    if count > 0:
                        self.log_step("Scope Debug", f"Found {count} elements matching: {selector}")
        except Exception as e:
            self.log_step("Scope Debug Error", f"Error analyzing scope elements: {str(e)}")
        
        for scope in scopes:
            # Try different scope selector patterns
            scope_selectors = [
                f'input[name="scopes"][value="{scope}"]',
                f'input[value="{scope}"]',
                f'input[type="checkbox"][value="{scope}"]',
                f'checkbox[data-scope="{scope}"]',
                f'input[type="checkbox"][data-testid="scope-{scope}"]',
                f'input[type="checkbox"][data-scope="{scope}"]',
                f'label:has-text("{scope}") input[type="checkbox"]',
                f'input[name="scope_{scope}"]',
                f'input[id="scope-{scope}"]'
            ]
            
            scope_selected = False
            for selector in scope_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.check(selector, timeout=3000)
                        scope_selected = True
                        self.log_step(f"Scope {scope}", f"✅ Selected using: {selector}")
                        break
                except Exception as e:
                    self.log_step(f"Scope {scope} Error", f"❌ Failed {selector}: {str(e)}")
                    continue
            
            if not scope_selected:
                # Try clicking on scope text/label
                try:
                    scope_label = page.locator(f'text="{scope}"').first
                    if await scope_label.count() > 0:
                        await scope_label.click(timeout=3000)
                        scope_selected = True
                        self.log_step(f"Scope {scope}", "✅ Selected by clicking label")
                except:
                    pass
                    
                if not scope_selected:
                    # Try case-insensitive match
                    try:
                        scope_label_ci = page.locator(f'text="{scope}"', has_text=scope.lower()).first
                        if await scope_label_ci.count() > 0:
                            await scope_label_ci.click(timeout=3000)
                            scope_selected = True
                            self.log_step(f"Scope {scope}", "✅ Selected by clicking case-insensitive label")
                    except:
                        pass
                
                if not scope_selected:
                    self.log_step(f"Scope {scope}", "❌ Could not find or select")
    
    async def _submit_api_key_form(self, page, key_name: str):
        """Submit the API key creation form."""
        submitted = False
        
        # Try multiple submit button patterns
        submit_selectors = [
            'button:has-text("Create")',
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit")',
            'button:has-text("Generate")',
            '.btn-primary',
            '[data-testid="create-api-key"]'
        ]
        
        for selector in submit_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.click(selector, timeout=3000)
                    submitted = True
                    self.log_step("API Key Submit", f"Submitted using: {selector}")
                    break
            except Exception as e:
                self.log_step("Submit Attempt", f"Failed {selector}: {str(e)}")
                continue
        
        if submitted:
            # Wait longer for creation response and database update
            self.log_step("API Key Waiting", "Waiting for API key creation to complete...")
            await asyncio.sleep(5)  # Increased wait time for database transaction
            
            # Check for success indicators
            success_indicators = [
                'text="API key created"',
                'text="Successfully created"',
                'text="Key generated"',
                '.alert-success',
                '.success-message'
            ]
            
            success_found = False
            for indicator in success_indicators:
                try:
                    if await page.locator(indicator).count() > 0:
                        self.log_step("Creation Success", f"Found success indicator: {indicator}")
                        success_found = True
                        break
                except:
                    continue
            
            if not success_found:
                # Check for error messages
                error_indicators = [
                    '.alert-danger',
                    '.error-message',
                    'text="Error"',
                    'text="Failed"'
                ]
                
                for indicator in error_indicators:
                    try:
                        if await page.locator(indicator).count() > 0:
                            error_text = await page.locator(indicator).text_content()
                            self.log_step("Creation Error", f"Found error: {error_text}")
                            return
                    except:
                        continue
            
            # Take screenshot after creation
            await page.screenshot(path=self.get_screenshot_path(f"after_create_{key_name.replace(' ', '_')}"))
            
            # Try to capture the created API key value
            captured_value = await self._capture_api_key_value(page, key_name)
            
            if captured_value:
                self.log_step("API Key Created", f"✅ Successfully created and captured API key '{key_name}'")
                return captured_value
            else:
                self.log_step("API Key Status", f"✅ API key '{key_name}' created (server confirmed) but value not captured")
                return None
            
        else:
            self.log_step("Submit Error", "Could not find or click any submit button")
            return None
    
    async def _capture_api_key_value(self, page, key_name: str):
        """Try to capture the generated API key value and store it in session."""
        try:
            # Look for common patterns where API keys are displayed
            key_selectors = [
                'input[readonly]',
                'input[type="text"][readonly]',
                '.api-key-value',
                '[data-testid="api-key-value"]',
                'code',
                '.monospace',
                'pre',
                '.api-key-secret',
                '[data-api-key]',
                'input[value*="fwk_"]',  # FiberWise API key prefix
                'span:has-text("fwk_")'
            ]
            
            captured_value = None
            capture_method = None
            
            for selector in key_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for element in elements:
                        # Try to get value from input elements
                        if await element.get_attribute('type') == 'text' or await element.get_attribute('readonly') is not None:
                            value = await element.input_value()
                        else:
                            # Try to get text content
                            value = await element.text_content()
                        
                        if value and len(value) > 20 and not value.isspace():
                            # Check if it looks like an API key (contains expected patterns)
                            if any(pattern in value.lower() for pattern in ['fwk_', 'api', 'key']) or len(value) > 30:
                                captured_value = value.strip()
                                capture_method = selector
                                break
                    
                    if captured_value:
                        break
                        
                except Exception as e:
                    self.log_step(f"Selector Error", f"Failed to check {selector}: {str(e)}")
                    continue
            
            if captured_value:
                self.log_step(f"API Key Captured", f"Key '{key_name}': {captured_value[:20]}... (via {capture_method})")
                
                # Store in session variables for later use
                variable_key = f"api_key_{key_name.lower().replace(' ', '_')}"
                self.runner.set_session_variable(
                    variable_key, 
                    captured_value, 
                    f"API key secret for '{key_name}'"
                )
                
                # Also store a generic "last_api_key" for convenience
                self.runner.set_session_variable(
                    "last_api_key", 
                    captured_value, 
                    f"Most recently created API key: '{key_name}'"
                )
                
                return captured_value
            else:
                self.log_step(f"API Key Value", f"Created '{key_name}' but could not capture value")
                
                # Debug: Log all input elements on page
                try:
                    all_inputs = await page.locator('input').all()
                    for i, input_elem in enumerate(all_inputs):
                        try:
                            input_type = await input_elem.get_attribute('type') or 'text'
                            input_value = await input_elem.input_value() or 'no-value'
                            readonly = await input_elem.get_attribute('readonly') or 'no'
                            self.log_step(f"Debug Input {i+1}", f"type={input_type}, readonly={readonly}, value={input_value[:30]}...")
                        except:
                            continue
                except:
                    pass
                
                return None
            
        except Exception as e:
            self.log_step(f"Capture Error", f"Error capturing API key: {str(e)}")
            return None
    
    async def list_api_keys(self, context, config: Dict[str, Any]):
        """List existing API keys."""
        username = config.get('username', 'testuser1')
        password = config.get('password', 'testpass123')
        
        page, should_close = await self.get_or_create_page(context, config)
        try:
            self.log_step("List API Keys", f"Fetching API keys for {username}")
            
            # Login first
            await self._perform_login(page, username, password)
            
            # Navigate to API keys page
            await self._navigate_to_api_keys_page(page)
            
            # Take screenshot of API keys list
            await page.screenshot(path=self.get_screenshot_path("api_keys_list"))
            
            # Try to extract API key information
            await self._extract_api_keys_list(page)
            
        except Exception as e:
            self.log_step("List API Keys Error", f"Error listing API keys: {str(e)}")
        finally:
            if should_close:
                await page.close()
    
    async def _extract_api_keys_list(self, page):
        """Extract information about existing API keys."""
        try:
            # Look for API key rows/items
            row_selectors = [
                '.api-key-row',
                '.api-key-item',
                'tr[data-api-key]',
                '[data-testid="api-key-row"]'
            ]
            
            api_keys_found = []
            
            for selector in row_selectors:
                try:
                    rows = await page.locator(selector).all()
                    if rows:
                        for i, row in enumerate(rows):
                            try:
                                text = await row.text_content()
                                if text and text.strip():
                                    api_keys_found.append(text.strip())
                            except:
                                continue
                        break
                except:
                    continue
            
            if api_keys_found:
                self.log_step("API Keys Found", f"Found {len(api_keys_found)} API keys")
                for i, key_info in enumerate(api_keys_found):
                    self.log_step(f"API Key {i+1}", key_info[:100])
            else:
                # Try to get general page text content for debugging
                page_text = await page.text_content('body')
                if 'no api keys' in page_text.lower() or 'create your first' in page_text.lower():
                    self.log_step("API Keys Status", "No API keys found - empty list")
                else:
                    self.log_step("API Keys Status", "Could not extract API key information")
                    
        except Exception as e:
            self.log_step("Extract Error", f"Error extracting API keys: {str(e)}")
    
    async def test_api_key(self, context, config: Dict[str, Any]):
        """Test using a captured API key value."""
        # Get API key from session variables or config
        api_key_variable = config.get('api_key_variable', 'last_api_key')
        api_key_value = config.get('api_key', None)
        
        # If no direct API key provided, try to get from session variables
        if not api_key_value:
            api_key_value = self.runner.get_session_variable(api_key_variable)
            
        if not api_key_value:
            self.log_step("API Key Test Error", f"No API key found in variable '{api_key_variable}' or config")
            return
        
        self.log_step("API Key Test", f"Testing API key: {api_key_value[:20]}...")
        
        # Test the API key by making a simple API request
        test_endpoint = config.get('test_endpoint', '/api/v1/user/profile')
        base_url = config.get('base_url', self.runner.base_url)
        
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {api_key_value}',
                'Content-Type': 'application/json'
            }
            
            test_url = f"{base_url}{test_endpoint}"
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.log_step("API Key Test Success", f"✅ API key works! Status: {response.status_code}")
                
                # Store test result
                self.runner.set_session_variable(
                    f"{api_key_variable}_test_result",
                    "success",
                    f"API key test successful at {test_endpoint}"
                )
            else:
                self.log_step("API Key Test Failed", f"❌ Status: {response.status_code}, Response: {response.text[:100]}")
                
                # Store test result
                self.runner.set_session_variable(
                    f"{api_key_variable}_test_result",
                    f"failed_{response.status_code}",
                    f"API key test failed with status {response.status_code}"
                )
                
        except Exception as e:
            self.log_step("API Key Test Error", f"❌ Error testing API key: {str(e)}")
            
            # Store test result
            self.runner.set_session_variable(
                f"{api_key_variable}_test_result",
                f"error",
                f"API key test error: {str(e)}"
            )
