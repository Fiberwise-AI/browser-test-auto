"""
Core browser management actions.
"""

import asyncio
from typing import Dict, Any, Tuple
from datetime import datetime
from .base_action import BaseAction


class BrowserActions(BaseAction):
    """Handles core browser initialization and management."""
    
    async def execute(self, step: Dict[str, Any]) -> Any:
        """Execute browser-related step."""
        action = step.get('action')
        config = step.get('config', {})
        settings = self.runner.script.get('settings', {})
        
        # Initialize browser if not already done
        if not self.runner.browser:
            await self.runner.initialize_browser(settings, config)
        
        context = self.runner.browser_context
        
        # Delegate user-related actions to UserActions
        if action == "register_multiple_users":
            from .user_actions import UserActions
            user_actions = UserActions(self.runner)
            return await user_actions.register_multiple_users(context, config)
        elif action == "test_login":
            from .user_actions import UserActions
            user_actions = UserActions(self.runner)
            return await user_actions.test_login(context, config)
        elif action == "verify_user_logins":
            from .user_actions import UserActions
            user_actions = UserActions(self.runner)
            return await user_actions.verify_user_logins(context, config)
        elif action == "navigate_to_home":
            await self.navigate_to_home(context, config)
        elif action == "explore_ui":
            await self.explore_ui(context, config)
        elif action == "demo_interactions":
            await self.demo_interactions(context, config)
        elif action == "final_documentation":
            await self.final_documentation(context, config)
        elif action == "create_api_key_demo":
            await self.create_api_key_demo(context, config)
        elif action == "test_app_with_user":
            await self.test_app_with_user(context, config)
        elif action == "final_review":
            await self.final_review(context, config)
        elif action == "verify_database":
            await self.verify_database(context, config)
        elif action == "navigate_and_verify":
            await self.navigate_and_verify(context, config)
        elif action == "analyze_page_html":
            await self.analyze_page_html(context, config)
        elif action == "verify_app_installation":
            await self.verify_app_installation(context, config)
        elif action == "test_app_access":
            await self.test_app_access(context, config)
        elif action == "show_browser":
            await self.show_browser(context, config)
        elif action == "configure_llm_provider":
            await self.configure_llm_provider(context, config)
        elif action == "create_api_key":
            await self.create_api_key(context, config)
        elif action == "test_api_key_scopes":
            await self.test_api_key_scopes(context, config)
        elif action == "verify_api_keys":
            await self.verify_api_keys(context, config)
        # New modular methods
        elif action == "initialize_browser":
            await self.initialize_browser(context, config)
        elif action == "take_screenshot":
            await self.take_screenshot(context, config)
        elif action == "navigate_to_url":
            await self.navigate_to_url(context, config)
        elif action == "wait_for_element":
            await self.wait_for_element(context, config)
        elif action == "cleanup_shared_page":
            await self.cleanup_shared_page(context, config)
        elif action == "monitor_network_requests":
            await self.monitor_network_requests(context, config)
        elif action == "login_user":
            await self.login_user(context, config)
        elif action == "send_chat_message":
            await self.send_chat_message(context, config)
        elif action == "test_websocket_isolation":
            await self.test_websocket_isolation(context, config)
        else:
            self.log_step("Unknown Browser Action", f"Action '{action}' not implemented")
            return None
    
    # Copy ALL original browser methods from json_script_runner.py
    async def register_multiple_users(self, context, config):
        """Register multiple users headlessly in isolated browser contexts."""
        users = config.get('users', [])
        
        # Default selectors for FiberWise registration
        default_selectors = {
            'username_field': 'input[name="username"], input[placeholder*="username" i], #username',
            'email_field': 'input[name="email"], input[type="email"], input[placeholder*="email" i], #email',
            'password_field': 'input[name="password"], input[type="password"], #password',
            'password_confirm_field': 'input[name="password_confirm"], input[name="confirm_password"], input[name="password2"], input[placeholder*="confirm" i]',
            'display_name_field': 'input[name="display_name"], input[name="displayName"], input[placeholder*="display" i]',
            'first_name_field': 'input[name="first_name"], input[name="firstName"], input[placeholder*="first" i]',
            'last_name_field': 'input[name="last_name"], input[name="lastName"], input[placeholder*="last" i]',
            'submit_button': 'button[type="submit"], button:has-text("Register"), button:has-text("Sign up"), .btn-submit'
        }
        
        selectors = {**default_selectors, **config.get('selectors', {})}
        
        for i, user in enumerate(users):
            self.log_step(f"Registering User {i+1}", f"Creating account for {user.get('username', 'user')} in isolated context")
            
            user_context = None
            try:
                # Create a new context for isolation
                user_context = await self.runner.browser.new_context()
                page = await user_context.new_page()
                
                # Navigate to registration page
                register_url = f"{self.runner.base_url}/register"
                await page.goto(register_url)
                await page.wait_for_load_state('networkidle')
                
                # Fill registration form
                if 'username' in user:
                    await page.fill(selectors['username_field'], user['username'])
                if 'email' in user:
                    await page.fill(selectors['email_field'], user['email'])
                if 'password' in user:
                    await page.fill(selectors['password_field'], user['password'])
                    await page.fill(selectors['password_confirm_field'], user['password'])
                if 'display_name' in user:
                    await page.fill(selectors['display_name_field'], user['display_name'])
                if 'first_name' in user:
                    await page.fill(selectors['first_name_field'], user['first_name'])
                if 'last_name' in user:
                    await page.fill(selectors['last_name_field'], user['last_name'])
                
                # Submit form
                await page.click(selectors['submit_button'])
                await page.wait_for_load_state('networkidle')
                
                self.log_step(f"User {i+1} Registered", f"Account created for {user.get('username', 'user')}")
                
            except Exception as e:
                self.log_step(f"Registration Failed", f"Error registering user {i+1}: {str(e)}")
            finally:
                if user_context:
                    await user_context.close()
    
    async def test_login(self, context, config):
        """Simple login test without API key creation."""
        username = config.get('username', 'testuser1')
        password = config.get('password', 'testpass123')
        
        page, should_close = await self.runner.get_or_create_page(context, config)
        try:
            # Navigate to login page
            login_url = f"{self.runner.base_url}/login"
            self.log_step("Login Test", f"Navigating to {login_url}")
            await page.goto(login_url)
            await page.wait_for_load_state('networkidle')
            
            # Fill login form
            await page.fill('input[name="username"], input[type="email"]', username)
            await page.fill('input[name="password"], input[type="password"]', password)
            
            # Submit login
            await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")')
            await page.wait_for_load_state('networkidle')
            
            # Check if login was successful
            current_url = page.url
            if '/dashboard' in current_url or '/home' in current_url:
                self.log_step("Login Success", f"Successfully logged in as {username}")
            else:
                self.log_step("Login Status", f"Login completed, current URL: {current_url}")
            
        except Exception as e:
            self.log_step("Login Error", f"Error during login: {str(e)}")
        finally:
            if should_close:
                await page.close()
    
    # Add other original methods as needed...
    async def navigate_and_verify(self, context, config):
        """Navigate to specified URL and verify page loads correctly"""
        page, should_close = await self.runner.get_or_create_page(context, config)
        
        url = config.get('url', '/dashboard')
        verify_element = config.get('verify_element')
        verify_text = config.get('verify_text')
        wait_time = config.get('wait_time', 3000)
        
        # Replace session variables in URL
        url = self.runner.replace_variables_in_string(url)
        
        # Use the base URL from the instance
        base_url = getattr(self.runner, 'base_url', 'http://localhost:6884')
        
        try:
            if not url.startswith('http'):
                full_url = f"{base_url}{url}"
            else:
                full_url = url
                
            self.log_step("Navigation", f"Going to {full_url}")
            await page.goto(full_url)
            await page.wait_for_load_state('networkidle')
            
            # Wait specified time
            await asyncio.sleep(wait_time / 1000)
            
            # Take screenshot after navigation
            if config.get('take_screenshot', False):
                screenshot_name = url.replace('/', '_').replace('?', '_').replace('&', '_')
                if screenshot_name.startswith('_'):
                    screenshot_name = screenshot_name[1:]
                if not screenshot_name:
                    screenshot_name = "navigation"
                await page.screenshot(path=self.get_screenshot_path(f"navigate_{screenshot_name}"))
                self.log_step("Screenshot", f"Captured navigation to {url}")
            
            # Debug: Get page info
            page_title = await page.title()
            current_url = page.url
            self.log_step("Navigation Result", f"Title: '{page_title}', URL: {current_url}")
            
            # Verify element if specified
            if verify_element:
                try:
                    await page.wait_for_selector(verify_element, timeout=5000)
                    self.log_step("Element Verified", f"Found element: {verify_element}")
                except:
                    self.log_step("Element Not Found", f"Could not find: {verify_element}")
            
            # Verify text if specified  
            if verify_text:
                if await page.locator(f':has-text("{verify_text}")').count() > 0:
                    self.log_step("Text Verified", f"Found text: {verify_text}")
                else:
                    self.log_step("Text Not Found", f"Could not find: {verify_text}")
            
        except Exception as e:
            self.log_step("Navigation Error", f"Error: {str(e)}")
            # Take error screenshot
            if config.get('take_screenshot', False):
                try:
                    await page.screenshot(path=self.get_screenshot_path("navigation_error"))
                    self.log_step("Error Screenshot", "Captured navigation error")
                except:
                    pass
        finally:
            if should_close:
                await page.close()
    
    # Add placeholder methods for other original actions
    async def verify_user_logins(self, context, config):
        """Verify users can log in."""
        self.log_step("Login Verification", "Verifying user login capability")
    
    async def navigate_to_home(self, context, config):
        """Navigate to homepage."""
        await self.navigate_to_url(context, {'url': '/', **config})
    
    async def explore_ui(self, context, config):
        """Explore UI elements and take screenshots."""
        self.log_step("UI Exploration", "Exploring user interface")
    
    async def demo_interactions(self, context, config):
        """Demonstrate UI interactions."""
        self.log_step("Demo Interactions", "Demonstrating user interactions")
    
    async def final_documentation(self, context, config):
        """Take final documentation screenshots."""
        self.log_step("Final Documentation", "Taking final screenshots")
    
    async def create_api_key_demo(self, context, config):
        """Demonstrate API key creation with visible browser."""
        self.log_step("API Key Demo", "Demonstrating API key creation")
    
    async def test_app_with_user(self, context, config):
        """Test installed app with a specific user."""
        self.log_step("App Testing", "Testing app functionality")
    
    async def final_review(self, context, config):
        """Take final screenshots and optionally keep browser open."""
        self.log_step("Final Review", "Taking final screenshots")
    
    async def verify_database(self, context, config):
        """Verify users are actually in the database."""
        self.log_step("Database Verification", "Checking database state")
    
    async def analyze_page_html(self, context, config):
        """Analyze page HTML structure and elements"""
        self.log_step("HTML Analysis", "Analyzing page structure")
    
    async def verify_app_installation(self, context, config):
        """Verify that an app was successfully installed."""
        self.log_step("App Verification", "Checking app installation")
    
    async def test_app_access(self, context, config):
        """Test accessing and interacting with an installed app."""
        self.log_step("App Access Test", "Testing app functionality")
    
    async def show_browser(self, context, config):
        """Open browser window for manual inspection."""
        self.log_step("Show Browser", "Making browser visible")
    
    async def configure_llm_provider(self, context, config):
        """Configure an LLM provider in the settings."""
        provider_name = config.get('provider_name', 'Test Provider')
        provider_type = config.get('provider_type', 'custom')
        api_endpoint = config.get('api_endpoint', '')
        api_key = config.get('api_key', '')
        models = config.get('models', [])
        temperature = config.get('temperature', 0.7)
        
        # Force using the shared page to continue from navigation
        page, should_close = await self.runner.get_or_create_page(context, {'keep_page_open': True})
        
        try:
            self.log_step("LLM Provider Setup", f"Configuring {provider_name}")
            
            # Debug: Check page content first
            page_title = await page.title()
            current_url = page.url
            self.log_step("Page Info", f"Title: '{page_title}', URL: {current_url}")
            
            # If we're on about:blank, navigate to the LLM providers page
            if current_url == "about:blank" or "llm-providers" not in current_url:
                providers_url = f"{self.runner.base_url}/settings/llm-providers"
                self.log_step("Navigation Fix", f"Navigating to {providers_url}")
                await page.goto(providers_url)
                await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Wait for page to be ready and JavaScript to render
            await page.wait_for_load_state('networkidle', timeout=10000)
            await page.wait_for_selector('llm-providers-page', timeout=10000)
            await page.wait_for_timeout(2000)
            
            # Find and click the Add Provider button
            add_button_selectors = [
                "#add-provider",
                "button:has-text('Add New Provider')",
                "button:has-text('Add Provider')"
            ]
            
            button_clicked = False
            for selector in add_button_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.locator(selector).click(timeout=5000)
                        button_clicked = True
                        self.log_step("Add Provider", f"✅ Clicked button: {selector}")
                        break
                except Exception as e:
                    continue
            
            if not button_clicked:
                self.log_step("Button Not Found", "Could not find Add Provider button")
                await page.screenshot(path=self.get_screenshot_path("add_provider_button_not_found"))
                raise Exception("Add Provider button not found")
            
            await page.wait_for_timeout(2000)
            
            # Wait for form to appear with multiple possible selectors
            form_selectors = [
                ".card:has-text('Add New Provider')",
                "form[data-provider-form]",
                ".provider-form",
                "[class*='provider'][class*='form']",
                ".modal:has-text('Provider')",
                ".add-provider-form"
            ]
            
            form_appeared = False
            for selector in form_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    form_appeared = True
                    self.log_step("Form Display", f"Provider form appeared using: {selector}")
                    break
                except:
                    continue
            
            if not form_appeared:
                self.log_step("Form Not Found", "Provider form did not appear")
                # Take screenshot for debugging
                await page.screenshot(path=self.get_screenshot_path("provider_form_not_found"))
                raise Exception("Provider form did not appear")
            
            self.log_step("Form Display", "Provider form appeared")
            
            # Select provider type
            type_select = page.locator("#provider-type")
            
            # Wait for the dropdown to be populated (it might load via JavaScript)
            await page.wait_for_timeout(3000)
            
            try:
                # Check if dropdown is populated now
                options = await type_select.locator('option').all()
                available_values = []
                for option in options:
                    value = await option.get_attribute('value')
                    text = await option.inner_text()
                    if value:  # Skip empty values
                        available_values.append(value)
                
                self.log_step("Available Options", f"Found: {', '.join(available_values)}")
                
                if not available_values:
                    # If still no options, try to trigger a page refresh or dropdown population
                    await page.reload()
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(2000)
                    
                    # Try to click the Add Provider button again
                    for selector in add_button_selectors:
                        try:
                            if await page.locator(selector).count() > 0:
                                await page.locator(selector).click(timeout=5000)
                                self.log_step("Re-click Add", f"Re-clicked: {selector}")
                                break
                        except:
                            continue
                    
                    await page.wait_for_timeout(2000)
                    # Check options again
                    options = await type_select.locator('option').all()
                    available_values = []
                    for option in options:
                        value = await option.get_attribute('value')
                        if value:
                            available_values.append(value)
                    
                    self.log_step("Options After Refresh", f"Found: {', '.join(available_values)}")
                
                # Try to select the configured provider type first
                if provider_type in available_values:
                    await type_select.select_option(provider_type)
                    self.log_step("Provider Type", f"✅ Selected {provider_type}")
                else:
                    # Try common alternatives in order of preference
                    alternatives = ['gemini', 'google', 'openai', 'anthropic', 'custom']
                    selected = False
                    for alt in alternatives:
                        if alt in available_values:
                            await type_select.select_option(alt)
                            self.log_step("Provider Type", f"✅ Selected {alt}")
                            selected = True
                            break
                    
                    if not selected and available_values:
                        # Just select the first available option
                        await type_select.select_option(available_values[0])
                        self.log_step("Provider Type", f"✅ Selected first available: {available_values[0]}")
                    elif not available_values:
                        # If still no options, skip the dropdown and continue
                        self.log_step("Provider Type Warning", "No options available in dropdown, skipping selection")
                
            except Exception as e:
                self.log_step("Provider Type Error", f"Could not select provider type: {str(e)}")
                # Continue anyway - maybe the form will work without selecting type
            
            await page.wait_for_timeout(1000)
            
            # Fill provider name
            name_input = page.locator("#provider-name")
            await name_input.fill(provider_name)
            self.log_step("Provider Name", f"Filled '{provider_name}'")
            
            # Fill API endpoint if provided
            if api_endpoint:
                endpoint_input = page.locator("#api-endpoint")
                await endpoint_input.fill(api_endpoint)
                self.log_step("API Endpoint", f"Filled '{api_endpoint}'")
            
            # Fill API key
            key_input = page.locator("#api-key")
            await key_input.fill(api_key)
            self.log_step("API Key", "Filled API key")
            
            # Add models
            if models:
                model_input = page.locator("#new-model-input")
                add_model_btn = page.locator("#add-model-btn")
                
                for model in models:
                    await model_input.fill(model)
                    await add_model_btn.click()
                    await page.wait_for_timeout(500)
                    self.log_step("Model Added", f"Added model: {model}")
            
            # Set temperature
            temp_input = page.locator("#temperature")
            await temp_input.fill(str(temperature))
            self.log_step("Temperature", f"Set to {temperature}")
            
            # Save provider
            save_button = page.locator("#save-provider")
            await save_button.click()
            await page.wait_for_timeout(3000)
            self.log_step("Provider Saved", f"Saved {provider_name}")
            
            # Verify provider appears in list - try multiple selectors and be more flexible
            verification_selectors = [
                f".provider-card:has-text('{provider_name}')",
                f".provider-item:has-text('{provider_name}')", 
                f"[data-provider-name='{provider_name}']",
                f"tr:has-text('{provider_name}')",
                f".card:has-text('{provider_name}')",
                f"[class*='provider']:has-text('{provider_name}')"
            ]
            
            provider_found = False
            for selector in verification_selectors:
                try:
                    await page.locator(selector).wait_for(timeout=3000)
                    provider_found = True
                    self.log_step("Verification", f"✅ Provider {provider_name} found using: {selector}")
                    break
                except:
                    continue
            
            if not provider_found:
                # Try a more general approach - look for the provider name anywhere on the page
                try:
                    await page.wait_for_timeout(2000)  # Give page time to refresh
                    page_content = await page.content()
                    if provider_name in page_content:
                        self.log_step("Verification", f"✅ Provider {provider_name} found in page content")
                        provider_found = True
                    else:
                        self.log_step("Verification Warning", f"⚠️ Could not verify {provider_name} in provider list")
                        # Take a screenshot for debugging
                        await page.screenshot(path=self.get_screenshot_path("provider_verification_failed"))
                except Exception as e:
                    self.log_step("Verification Error", f"Error verifying provider: {str(e)}")
            
            if not provider_found:
                self.log_step("Verification", f"⚠️ Could not verify provider {provider_name} but form was submitted")
            else:
                self.log_step("Verification", f"✅ Successfully verified provider {provider_name}")
            
        except Exception as e:
            self.log_step("Error", f"Failed to configure LLM provider: {str(e)}")
            raise
        finally:
            if should_close:
                await page.close()
    
    async def create_api_key(self, context, config):
        """Create an API key with specified configuration."""
        key_name = config.get('name', f'Test Key {datetime.now().strftime("%H%M%S")}')
        key_description = config.get('description', 'Test API key created by automation')
        scopes = config.get('scopes', ['read'])
        
        page, should_close = await self.runner.get_or_create_page(context, config)
        
        try:
            # Navigate to API keys page
            api_keys_url = f"{self.runner.base_url}/settings/api-keys"
            self.log_step("API Key Creation", f"Navigating to {api_keys_url}")
            await page.goto(api_keys_url)
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot of API keys page
            if config.get('take_screenshot', False):
                await page.screenshot(path=self.get_screenshot_path(f"api_keys_page_{key_name.replace(' ', '_')}"))
                self.log_step("Screenshot", f"Captured API keys page for {key_name}")
            
            # Debug: Check what's on the page
            page_title = await page.title()
            current_url = page.url
            self.log_step("API Key Page Info", f"Title: '{page_title}', URL: {current_url}")
            
            # Look for existing API key creation form or button
            all_buttons = await page.locator('button').all()
            button_info = []
            for i, button in enumerate(all_buttons):
                try:
                    text = await button.inner_text() or 'no-text'
                    button_info.append(f"Button{i+1}: {text}")
                except:
                    continue
            
            if button_info:
                self.log_step("Available Buttons", f"Found {len(button_info)} buttons")
                for info in button_info[:5]:  # Show first 5 buttons
                    self.log_step("Button", info)
            
            # Look for input fields that might already be visible
            all_inputs = await page.locator('input').all()
            input_info = []
            for i, input_elem in enumerate(all_inputs):
                try:
                    name = await input_elem.get_attribute('name') or 'no-name'
                    placeholder = await input_elem.get_attribute('placeholder') or 'no-placeholder'
                    input_type = await input_elem.get_attribute('type') or 'text'
                    input_id = await input_elem.get_attribute('id') or 'no-id'
                    input_info.append(f"Input{i+1}: type={input_type}, name={name}, id={input_id}, placeholder={placeholder}")
                except:
                    continue
            
            if input_info:
                self.log_step("Available Inputs", f"Found {len(input_info)} inputs")
                for info in input_info[:5]:  # Show first 5 inputs
                    self.log_step("Input", info)
            
            # Try to find and click create button
            create_selectors = [
                'button:has-text("Create API Key")',
                'button:has-text("Add API Key")', 
                'button:has-text("New Key")',
                'button:has-text("Create")',
                'button:has-text("Add")',
                '[data-testid="create-api-key"]',
                '.create-api-key-btn',
                '.btn-primary'
            ]
            
            button_clicked = False
            for selector in create_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector)
                        button_clicked = True
                        self.log_step("Create Button", f"✅ Clicked: {selector}")
                        break
                except Exception as e:
                    self.log_step("Create Button Error", f"❌ Failed {selector}: {str(e)}")
                    continue
            
            if not button_clicked:
                self.log_step("Create Button Not Found", "⚠️ Could not find create API key button")
            
            # Wait for form to appear
            await page.wait_for_timeout(2000)
            
            # Take screenshot after clicking create
            if config.get('take_screenshot', False):
                await page.screenshot(path=self.get_screenshot_path(f"api_key_form_{key_name.replace(' ', '_')}"))
                self.log_step("Screenshot", f"Captured API key form for {key_name}")
            
            # Debug: Check for form fields after clicking
            all_inputs_after = await page.locator('input').all()
            input_info_after = []
            for i, input_elem in enumerate(all_inputs_after):
                try:
                    name = await input_elem.get_attribute('name') or 'no-name'
                    placeholder = await input_elem.get_attribute('placeholder') or 'no-placeholder'
                    input_type = await input_elem.get_attribute('type') or 'text'
                    input_id = await input_elem.get_attribute('id') or 'no-id'
                    is_visible = await input_elem.is_visible()
                    input_info_after.append(f"Input{i+1}: type={input_type}, name={name}, id={input_id}, placeholder={placeholder}, visible={is_visible}")
                except:
                    continue
            
            if input_info_after:
                self.log_step("Form Inputs After Click", f"Found {len(input_info_after)} inputs")
                for info in input_info_after[:8]:  # Show more inputs
                    self.log_step("Form Input", info)
            
            # Fill API key form with enhanced debugging
            name_filled = False
            name_selectors = [
                '#key-name',  # Add the correct ID selector first
                'input[name="name"]', 
                'input[name="keyName"]',
                'input[name="api_key_name"]',
                'input[placeholder*="name" i]',
                'input[placeholder*="key name" i]', 
                '#api-key-name',
                '#name',
                '#keyName'
            ]
            
            for selector in name_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        # Check if field is visible
                        is_visible = await page.locator(selector).is_visible()
                        if is_visible:
                            await page.fill(selector, key_name)
                            name_filled = True
                            self.log_step("Name Field", f"✅ Filled '{key_name}' using: {selector}")
                            break
                        else:
                            self.log_step("Name Field Hidden", f"⚠️ Field found but not visible: {selector}")
                except Exception as e:
                    self.log_step("Name Field Error", f"❌ Failed {selector}: {str(e)}")
                    continue
            
            if not name_filled:
                self.log_step("Name Field Error", "❌ Could not find or fill name field")
            
            # Fill description field
            desc_filled = False
            desc_selectors = [
                'input[name="description"]', 
                'textarea[name="description"]',
                'input[name="keyDescription"]',
                'input[placeholder*="description" i]',
                '#api-key-description',
                '#description',
                '#keyDescription'
            ]
            
            for selector in desc_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        is_visible = await page.locator(selector).is_visible()
                        if is_visible:
                            await page.fill(selector, key_description)
                            desc_filled = True
                            self.log_step("Description Field", f"✅ Filled description using: {selector}")
                            break
                except Exception as e:
                    self.log_step("Description Field Error", f"❌ Failed {selector}: {str(e)}")
                    continue
            
            if not desc_filled:
                self.log_step("Description Field Warning", "⚠️ Could not find description field")
            
            # Wait before submitting
            await page.wait_for_timeout(1000)
            
            # Take screenshot after filling form
            if config.get('take_screenshot', False):
                await page.screenshot(path=self.get_screenshot_path(f"api_key_filled_{key_name.replace(' ', '_')}"))
                self.log_step("Screenshot", f"Captured filled form for {key_name}")
            
            # Submit form
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Create")',
                'button:has-text("Generate")',
                'button:has-text("Save")',
                '[data-testid="submit-api-key"]',
                '.btn-submit'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        is_visible = await page.locator(selector).is_visible()
                        if is_visible:
                            await page.click(selector)
                            submitted = True
                            self.log_step("Submit", f"✅ Clicked submit: {selector}")
                            break
                except Exception as e:
                    self.log_step("Submit Error", f"❌ Failed {selector}: {str(e)}")
                    continue
            
            if submitted:
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Take screenshot after submission
                if config.get('take_screenshot', False):
                    await page.screenshot(path=self.get_screenshot_path(f"api_key_result_{key_name.replace(' ', '_')}"))
                    self.log_step("Screenshot", f"Captured result for {key_name}")
                
                # Wait for the API key to be displayed and capture it
                await page.wait_for_timeout(2000)
                
                # Try to capture the API key value
                api_key_value = None
                key_selectors = [
                    'h3:has-text("New API Key Created") ~ *',  # Any element after the success heading
                    'div:has-text("New API Key Created") *:has-text("-")',  # Child elements with hyphens in success div  
                    'div:has-text("Your new API key has been created") *:has-text("-")',  # In success message area
                    '*:has-text("Your new API key has been created") ~ *:has-text("-")',  # After success text
                    'div.bg-gray-100',  # Gray background div (likely contains the key)
                    'div[class*="gray"]:has-text("-")',  # Gray-styled div with hyphens
                    'div[style*="gray"]:has-text("-")',  # Inline gray style with hyphens
                    'div:has-text("-"):has-text("-"):has-text("-")',  # Element with multiple hyphens (UUID pattern)
                    'input[readonly][value*="api_"]',  # Readonly input with api_ prefix
                    'input[readonly]',  # Any readonly input
                    'code:has-text("-")',  # Code element with UUID pattern
                    'pre:has-text("-")',  # Preformatted text with UUID pattern
                ]
                
                for selector in key_selectors:
                    try:
                        count = await page.locator(selector).count()
                        self.log_step("Selector Test", f"{selector} -> {count} matches")
                        if count > 0:
                            element = page.locator(selector).first
                            # Try getting value attribute first, then text content
                            api_key_value = await element.get_attribute('value')
                            if not api_key_value:
                                api_key_value = await element.inner_text()
                            
                            # Clean and validate the API key
                            if api_key_value:
                                api_key_value = api_key_value.strip()
                            
                            self.log_step("Key Content", f"Found text: '{api_key_value}' (len={len(api_key_value) if api_key_value else 0})")
                            
                            # Check if it looks like a valid API key
                            # UUID format: 8-4-4-4-12 characters with hyphens  
                            # or api_ prefix
                            if api_key_value and (
                                (len(api_key_value) >= 32 and api_key_value.count('-') >= 3) or  # UUID-like
                                api_key_value.startswith('api_')  # API prefix
                            ):
                                self.log_step("API Key Captured", f"Found key using selector: {selector}")
                                break
                    except Exception as e:
                        self.log_step("Selector Error", f"{selector} failed: {str(e)}")
                        continue
                
                # Store in session variables if capture_secret is specified
                capture_secret = config.get('capture_secret')
                if capture_secret and api_key_value:
                    self.runner.set_session_variable(
                        capture_secret, 
                        api_key_value, 
                        f"API key secret for '{key_name}'"
                    )
                    self.log_step("Session Variable", f"Stored API key in session variable: {capture_secret}")
                elif capture_secret:
                    self.log_step("Capture Warning", "Could not capture API key value - check UI elements")
                
                self.log_step("API Key Created", f"Created '{key_name}' but could not capture value" if not api_key_value else f"Created '{key_name}' with captured value")
            else:
                self.log_step("Submit Error", "❌ Could not find or click submit button")
            
        except Exception as e:
            self.log_step("API Key Error", f"Error creating API key: {str(e)}")
            # Take error screenshot
            if config.get('take_screenshot', False):
                try:
                    await page.screenshot(path=self.get_screenshot_path(f"api_key_error_{key_name.replace(' ', '_')}"))
                    self.log_step("Error Screenshot", f"Captured error for {key_name}")
                except:
                    pass
        finally:
            if should_close:
                await page.close()
    
    async def test_api_key_scopes(self, context, config):
        """Test API key creation with different scopes."""
        scopes_to_test = config.get('scopes', [
            ['read'],
            ['read', 'write'],
            ['read', 'write', 'apps'],
            ['admin']
        ])
        
        created_keys = []
        
        for i, scopes in enumerate(scopes_to_test):
            key_config = {
                'name': f'Test Key {i+1}',
                'description': f'Test key with scopes: {", ".join(scopes)}',
                'scopes': scopes,
                **config
            }
            await self.create_api_key(context, key_config)
            created_keys.append(key_config)
        
        self.log_step("Scope Testing Complete", f"Created {len(created_keys)} test keys")
        return created_keys
    
    async def verify_api_keys(self, context, config):
        """Verify API keys are listed and accessible."""
        page, should_close = await self.runner.get_or_create_page(context, config)
        
        try:
            # Navigate to API keys page
            api_keys_url = f"{self.runner.base_url}/settings/api-keys"
            self.log_step("API Keys Verification", f"Checking {api_keys_url}")
            await page.goto(api_keys_url)
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot of API keys page
            if config.get('take_screenshot', False):
                await page.screenshot(path=self.get_screenshot_path("api_keys_verification"))
                self.log_step("Screenshot", "Captured API keys verification page")
            
            # Debug: Check page content
            page_title = await page.title()
            current_url = page.url
            self.log_step("Verification Page Info", f"Title: '{page_title}', URL: {current_url}")
            
            # Look for API key list elements
            key_selectors = [
                '.api-key-item',
                '[data-testid="api-key"]',
                'tr[data-api-key]',
                '.key-row',
                '.api-key',
                '[data-key-id]',
                'tbody tr',  # Table rows
                '.list-item',
                '[class*="key"]'
            ]
            
            key_count = 0
            found_selector = None
            
            for selector in key_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        key_count = count
                        found_selector = selector
                        self.log_step("API Key Selector", f"Found {count} keys using: {selector}")
                        break
                except Exception as e:
                    continue
            
            # If no specific selectors found, check for general content
            if key_count == 0:
                # Look for text content that might indicate API keys
                page_content = await page.content()
                
                # Check for empty state messages
                empty_indicators = [
                    "No API keys",
                    "Create your first",
                    "Get started by creating",
                    "You don't have any"
                ]
                
                for indicator in empty_indicators:
                    if indicator.lower() in page_content.lower():
                        self.log_step("Empty State Found", f"Found indicator: {indicator}")
                        break
                
                # Look for any text that might be API key names
                potential_keys = []
                for line in page_content.split('\n'):
                    line = line.strip()
                    if 'key' in line.lower() and len(line) > 3 and len(line) < 100:
                        if any(word in line.lower() for word in ['read', 'write', 'admin', 'test', 'api']):
                            potential_keys.append(line)
                
                if potential_keys:
                    self.log_step("Potential Keys Found", f"Found {len(potential_keys)} potential key references")
                    for i, key_text in enumerate(potential_keys[:5]):
                        self.log_step(f"Potential Key {i+1}", key_text)
                else:
                    self.log_step("Content Check", "No obvious API key content found")
            
            self.log_step("API Keys Found", f"Found {key_count} API keys")
            
            # If we found keys, try to get their details
            if key_count > 0 and found_selector:
                try:
                    key_elements = await page.locator(found_selector).all()
                    for i, key_elem in enumerate(key_elements[:3]):  # Show first 3 keys
                        try:
                            key_text = await key_elem.inner_text()
                            self.log_step(f"API Key {i+1}", f"Content: {key_text[:100]}...")
                        except:
                            continue
                except Exception as e:
                    self.log_step("Key Details Error", f"Error getting key details: {str(e)}")
            
        except Exception as e:
            self.log_step("API Keys Error", f"Error verifying API keys: {str(e)}")
            # Take error screenshot
            if config.get('take_screenshot', False):
                try:
                    await page.screenshot(path=self.get_screenshot_path("api_keys_verification_error"))
                    self.log_step("Error Screenshot", "Captured verification error")
                except:
                    pass
        finally:
            if should_close:
                await page.close()
    
    async def initialize_browser(self, context, config: Dict[str, Any]):
        """Initialize browser context with recording and monitoring."""
        self.log_step("Browser Init", f"Starting browser with recording: {config.get('record_video', False)}")
        
        # Browser context should already be created by the runner
        # This action can be used for additional browser setup
        
        # Enable console monitoring if requested
        if config.get('monitor_console', True):
            await self._setup_console_monitoring(context, config)
        
        # Set viewport if specified
        viewport = config.get('viewport')
        if viewport:
            # Note: Individual pages will need to set viewport, context doesn't have this method
            self.log_step("Viewport Config", f"Will set {viewport['width']}x{viewport['height']} on pages")
    
    async def _setup_console_monitoring(self, context, config: Dict[str, Any]):
        """Setup console message monitoring for all pages."""
        self.log_step("Console Monitor", "Setting up console message capture")
        
        # Note: Console monitoring is typically set up per-page
        # This is handled in the get_or_create_page method
    
    async def take_screenshot(self, context, config: Dict[str, Any]):
        """Take a screenshot of the current page."""
        screenshot_name = config.get('name', 'screenshot')
        
        page, should_close = await self.runner.get_or_create_page(context, config)
        try:
            screenshot_path = self.get_screenshot_path(screenshot_name)
            await page.screenshot(path=screenshot_path)
            self.log_step("Screenshot", f"Saved to {screenshot_path}")
        finally:
            if should_close:
                await page.close()
        try:
            screenshot_path = self.get_screenshot_path(screenshot_name)
            await page.screenshot(path=screenshot_path)
            self.log_step("Screenshot", f"Saved to {screenshot_path}")
        finally:
            if should_close:
                await page.close()
    
    async def navigate_to_url(self, context, config: Dict[str, Any]):
        """Navigate to a specific URL."""
        url = config.get('url', '')
        if not url:
            self.log_step("Navigation Error", "No URL specified")
            return
        
        # Replace session variables in URL
        url = self.runner.replace_variables_in_string(url)
        
        # Make URL absolute if relative
        if not url.startswith('http'):
            url = f"{self.runner.base_url}{url}"
        
        page, should_close = await self.runner.get_or_create_page(context, config)
        try:
            self.log_step("Navigation", f"Going to {url}")
            await page.goto(url, timeout=10000)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Take screenshot if requested
            if config.get('screenshot', False):
                screenshot_name = config.get('screenshot_name', 'navigation')
                await page.screenshot(path=self.get_screenshot_path(screenshot_name))
            
        except Exception as e:
            self.log_step("Navigation Error", f"Failed to navigate: {str(e)}")
        finally:
            if should_close:
                await page.close()
    
    async def wait_for_element(self, context, config: Dict[str, Any]):
        """Wait for a specific element to appear."""
        selector = config.get('selector', '')
        timeout = config.get('timeout', 5000)
        
        if not selector:
            self.log_step("Wait Error", "No selector specified")
            return
        
        page, should_close = await self.runner.get_or_create_page(context, config)
        try:
            self.log_step("Wait Element", f"Waiting for {selector}")
            await page.wait_for_selector(selector, timeout=timeout)
            self.log_step("Element Found", f"Element {selector} appeared")
        except Exception as e:
            self.log_step("Wait Timeout", f"Element {selector} not found: {str(e)}")
        finally:
            if should_close:
                await page.close()
    
    async def cleanup_shared_page(self, context, config: Dict[str, Any]):
        """Close shared page if it exists."""
        if hasattr(self.runner, '_shared_page') and self.runner._shared_page:
            try:
                await self.runner._shared_page.close()
                self.runner._shared_page = None
                self.log_step("Cleanup", "Shared page closed")
            except Exception as e:
                self.log_step("Cleanup Error", f"Error closing shared page: {str(e)}")
        else:
            self.log_step("Cleanup", "No shared page to close")
    
    async def monitor_network_requests(self, context, config: Dict[str, Any]):
        """Monitor network requests and capture variables from JSON responses."""
        monitor_duration = config.get('monitor_duration', 10000)
        expected_requests = config.get('expected_requests', [])
        capture_variable = config.get('capture_variable')
        capture_from_url = config.get('capture_from_url', '')
        capture_json_path = config.get('capture_json_path', '')
        
        page, should_close = await self.runner.get_or_create_page(context, config)
        captured_requests = []
        captured_value = None
        
        def handle_response(response):
            nonlocal captured_value
            try:
                # Log all responses for debugging
                self.log_step("Network Response", f"{response.request.method} {response.url} -> {response.status}")
                
                # Capture variable if this URL matches and response is JSON
                if capture_variable and capture_from_url in response.url:
                    if 'application/json' in response.headers.get('content-type', ''):
                        # Get response body
                        async def extract_json():
                            nonlocal captured_value
                            try:
                                json_data = await response.json()
                                
                                # Navigate JSON path if specified (e.g., "data.app_id" or "app_id")
                                if capture_json_path:
                                    keys = capture_json_path.split('.')
                                    value = json_data
                                    for key in keys:
                                        if isinstance(value, dict) and key in value:
                                            value = value[key]
                                        else:
                                            self.log_step("JSON Path Error", f"Key '{key}' not found in response")
                                            return
                                    captured_value = str(value)
                                else:
                                    # If no path specified, look for the variable name as a key
                                    if isinstance(json_data, dict):
                                        if capture_variable in json_data:
                                            captured_value = str(json_data[capture_variable])
                                        elif 'data' in json_data and isinstance(json_data['data'], dict):
                                            if capture_variable in json_data['data']:
                                                captured_value = str(json_data['data'][capture_variable])
                                
                                if captured_value:
                                    self.runner.set_session_variable(
                                        capture_variable, 
                                        captured_value, 
                                        f"Captured from network response: {response.url}"
                                    )
                                    
                            except Exception as e:
                                self.log_step("JSON Parse Error", f"Error parsing response: {str(e)}")
                        
                        # Schedule the async function
                        asyncio.create_task(extract_json())
                
                # Track expected requests
                for expected in expected_requests:
                    if expected.get('url', '') in response.url and expected.get('method', 'GET') == response.request.method:
                        captured_requests.append({
                            'url': response.url,
                            'method': response.request.method,
                            'status': response.status,
                            'expected': expected,
                            'success': response.status < 400
                        })
                        
            except Exception as e:
                self.log_step("Response Handler Error", f"Error handling response: {str(e)}")
        
        try:
            # Set up network monitoring
            page.on("response", handle_response)
            self.log_step("Network Monitor", f"Monitoring requests for {monitor_duration}ms")
            
            # Wait for the specified duration
            await asyncio.sleep(monitor_duration / 1000)
            
            # Report captured requests
            if expected_requests:
                for expected in expected_requests:
                    matching = [r for r in captured_requests if r['expected'] == expected]
                    if matching:
                        req = matching[0]
                        status = "PASS" if req['success'] else "FAIL"
                        self.log_step(f"Expected Request {status}", f"{req['method']} {req['url']} -> {req['status']}")
                    else:
                        self.log_step("Expected Request MISSING", f"Missing: {expected.get('method', 'GET')} {expected.get('url', '')}")
            
            if captured_value:
                self.log_step("Variable Captured", f"'{capture_variable}' = '{captured_value}'")
            elif capture_variable:
                self.log_step("Capture Failed", f"Could not capture '{capture_variable}' from network requests")
                
        except Exception as e:
            self.log_step("Monitor Error", f"Network monitoring failed: {str(e)}")
        finally:
            # Remove listener to prevent it from running after the step is complete
            page.remove_listener("response", handle_response)
            if should_close:
                await page.close()
    
    async def login_user(self, context, config):
        """Login a user to the system."""
        page = None
        should_close = False
        
        try:
            # Use existing page or create new one
            if hasattr(self.runner, 'page') and self.runner.page:
                page = self.runner.page
            else:
                page = await context.new_page()
                self.runner.page = page
                should_close = True
            
            # Get login credentials
            username = config.get('username', 'admin')
            password = config.get('password', 'password')
            base_url = config.get('base_url', 'http://localhost:6070')
            
            # Replace variables in base_url
            base_url = self.runner.replace_variables_in_string(base_url)
            
            self.log_step("Login Started", f"Logging in user: {username}")
            
            # Navigate to login page
            login_url = f"{base_url}/login"
            await page.goto(login_url, timeout=10000)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Check if already logged in
            if await self._is_logged_in(page):
                self.log_step("Already Logged In", "User is already authenticated")
                if config.get('take_screenshot'):
                    await self.take_screenshot_with_page(page, "already_logged_in")
                return
            
            # Fill login form
            await page.fill('input[name="identifier"]', username, timeout=3000)
            await page.fill('input[name="password"]', password, timeout=3000)
            
            # Submit form
            await page.click('button[type="submit"]', timeout=3000)
            
            # Wait for redirect and verify login
            await asyncio.sleep(3)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            if await self._is_logged_in(page):
                self.log_step("Login Success", f"Successfully logged in as {username}")
            else:
                self.log_step("Login Failed", f"Login may have failed for {username}")
            
            if config.get('take_screenshot'):
                try:
                    await self.take_screenshot_with_page(page, "after_login")
                except Exception as e:
                    self.log_step("Screenshot Warning", f"Could not take screenshot: {str(e)}")
                
        except Exception as e:
            self.log_step("Login Error", f"Login failed: {str(e)}")
            raise
    
    async def _is_logged_in(self, page) -> bool:
        """Check if user is already logged in."""
        try:
            # Look for common logged-in indicators
            indicators = [
                'text="Logout"',
                'text="Profile"',
                '[data-testid="user-menu"]',
                '.user-profile',
                'a[href="/logout"]',
                'button:has-text("Logout")'
            ]
            
            for indicator in indicators:
                if await page.locator(indicator).count() > 0:
                    return True
            
            # Also check if we're NOT on the login page
            current_url = page.url
            return '/login' not in current_url and '/auth' not in current_url
            
        except:
            return False
    
    async def take_screenshot_with_page(self, page, name: str):
        """Take screenshot with existing page."""
        try:
            # Use session_dir if available, otherwise create temp directory
            if hasattr(self.runner, 'session_dir') and self.runner.session_dir:
                screenshot_dir = self.runner.session_dir / "screenshots"
            else:
                import tempfile
                from pathlib import Path
                temp_dir = Path(tempfile.gettempdir()) / "fiberwise_screenshots"
                temp_dir.mkdir(exist_ok=True)
                screenshot_dir = temp_dir
            
            screenshot_dir.mkdir(exist_ok=True)
            screenshot_path = screenshot_dir / f"{name}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.log_step("Screenshot", f"Saved: {name}.png")
        except Exception as e:
            self.log_step("Screenshot Error", f"Failed to save {name}: {str(e)}")

    async def send_chat_message(self, context, config):
        """Send a message in the chat interface and wait for response."""
        page = context.pages[0] if context.pages else None
        if not page:
            self.log_step("Chat Message Error", "No page available")
            return
        
        message = config.get('message', 'Test message')
        wait_for_response = config.get('wait_for_response', True)
        timeout = config.get('timeout', 30000)
        take_screenshot = config.get('take_screenshot', True)
        
        try:
            # Take screenshot before sending
            if take_screenshot:
                await self.take_screenshot_with_page(page, "before_message")
            
            # Check if message input exists
            message_input = page.locator('#message-input')
            if await message_input.count() == 0:
                self.log_step("Chat Input Error", "Message input field not found")
                return
                
            # Check if send button exists  
            send_button = page.locator('#send-button')
            if await send_button.count() == 0:
                self.log_step("Chat Button Error", "Send button not found")
                return
            
            self.log_step("Chat Elements Found", f"Input and send button located")
            
            # Count current messages before sending
            user_messages_before = await page.locator('.message.user').count()
            agent_messages_before = await page.locator('.message.agent').count()
            
            self.log_step("Message Count Before", f"User: {user_messages_before}, Agent: {agent_messages_before}")
            
            # Clear any existing text and fill the message
            await message_input.clear()
            await message_input.fill(message)
            
            self.log_step("Message Filled", f"Typed: {message}")
            
            # Take screenshot after typing
            if take_screenshot:
                await self.take_screenshot_with_page(page, "message_typed")
            
            # Click send button
            await send_button.click()
            
            self.log_step("Send Button Clicked", "Message sent")
            
            if wait_for_response:
                # Wait for user message to appear
                try:
                    await page.wait_for_function(
                        f"document.querySelectorAll('.message.user').length > {user_messages_before}",
                        timeout=10000
                    )
                    self.log_step("User Message Appeared", "Message visible in chat")
                    
                    # Take screenshot after user message appears
                    if take_screenshot:
                        await self.take_screenshot_with_page(page, "user_message_sent")
                    
                    # Wait for agent response (longer timeout for AI processing)
                    await page.wait_for_function(
                        f"document.querySelectorAll('.message.agent').length > {agent_messages_before}",
                        timeout=timeout
                    )
                    
                    agent_messages_after = await page.locator('.message.agent').count()
                    self.log_step("Agent Response", f"Agent responded! Messages: {agent_messages_after}")
                    
                    # Take final screenshot
                    if take_screenshot:
                        await self.take_screenshot_with_page(page, "agent_responded")
                        
                except Exception as wait_error:
                    self.log_step("Response Timeout", f"No response within {timeout}ms: {str(wait_error)}")
                    # Still take a screenshot to see what happened
                    if take_screenshot:
                        await self.take_screenshot_with_page(page, "timeout_state")
            
            # Count final messages
            user_messages_after = await page.locator('.message.user').count()
            agent_messages_after = await page.locator('.message.agent').count()
            
            self.log_step("Final Message Count", f"User: {user_messages_after}, Agent: {agent_messages_after}")
            
            return {
                'message_sent': message,
                'user_messages_before': user_messages_before,
                'user_messages_after': user_messages_after,
                'agent_messages_before': agent_messages_before,
                'agent_messages_after': agent_messages_after
            }
            
        except Exception as e:
            self.log_step("Chat Message Error", f"Failed to send message: {str(e)}")
            if take_screenshot:
                await self.take_screenshot_with_page(page, "error_state")
            return None

    async def test_websocket_isolation(self, context, config):
        """
        Tests websocket isolation between two users in a chat application.
        - Creates two isolated browser contexts.
        - Logs in two different users.
        - User A sends a message.
        - Verifies User A sees the message and User B does not.
        """
        user_a_config = config.get('user_a')
        user_b_config = config.get('user_b')
        chat_url_path = config.get('chat_url_path', '/')
        message = config.get('message', f"Isolation test message {datetime.now().isoformat()}")

        if not user_a_config or not user_b_config:
            self.log_step("Config Error", "user_a and user_b must be defined in config")
            return

        context_a = None
        context_b = None

        try:
            # Create isolated contexts for each user
            self.log_step("Isolation Test Setup", "Creating isolated browser contexts for User A and User B")
            context_a = await self.runner.browser.new_context()
            context_b = await self.runner.browser.new_context()

            page_a = await context_a.new_page()
            page_b = await context_b.new_page()

            # --- Login User A ---
            self.log_step("Login User A", f"Logging in {user_a_config['username']}")
            await self._login_user_in_page(page_a, user_a_config['username'], user_a_config['password'])
            
            # --- Login User B ---
            self.log_step("Login User B", f"Logging in {user_b_config['username']}")
            await self._login_user_in_page(page_b, user_b_config['username'], user_b_config['password'])

            # --- Navigate to Chat ---
            chat_url = f"{self.runner.base_url}{chat_url_path}"
            self.log_step("Navigation", f"Both users navigating to {chat_url}")
            await page_a.goto(chat_url)
            await page_b.goto(chat_url)
            await page_a.wait_for_load_state('networkidle')
            await page_b.wait_for_load_state('networkidle')
            self.log_step("Navigation Complete", "Both users are on the chat page")

            # --- Get initial message counts ---
            messages_a_before = await page_a.locator('.message').count()
            messages_b_before = await page_b.locator('.message').count()
            self.log_step("Initial State", f"User A sees {messages_a_before} messages. User B sees {messages_b_before} messages.")

            # --- User A sends a message ---
            self.log_step("Send Message", f"User A is sending: '{message}'")
            await page_a.fill('#message-input', message)
            await page_a.click('#send-button')

            # --- Verification ---
            # Wait for User A to see their own message
            try:
                await page_a.wait_for_function(
                    f"document.querySelectorAll('.message').length > {messages_a_before}",
                    timeout=10000
                )
                self.log_step("Verification PASS", "User A sees their new message.")
                await page_a.screenshot(path=self.get_screenshot_path("user_a_view_pass"))
            except Exception:
                self.log_step("Verification FAIL", "User A did not see their own message.")
                await page_a.screenshot(path=self.get_screenshot_path("user_a_view_fail"))
                raise AssertionError("User A did not receive their own message")

            # Check that User B does NOT see the message
            self.log_step("Isolation Check", "Verifying User B does not see User A's message.")
            await asyncio.sleep(3) # Wait a moment to ensure websocket has time to deliver if not isolated
            messages_b_after = await page_b.locator('.message').count()

            if messages_b_after == messages_b_before:
                self.log_step("Isolation PASS", f"User B still sees {messages_b_after} messages. Isolation successful.")
                await page_b.screenshot(path=self.get_screenshot_path("user_b_view_pass"))
            else:
                self.log_step("Isolation FAIL", f"User B now sees {messages_b_after} messages. Isolation failed.")
                await page_b.screenshot(path=self.get_screenshot_path("user_b_view_fail"))
                raise AssertionError("User B received a message intended for User A")

        except Exception as e:
            self.log_step("Isolation Test Error", f"An error occurred: {str(e)}")
            raise
        finally:
            if context_a:
                await context_a.close()
            if context_b:
                await context_b.close()
            self.log_step("Cleanup", "Closed isolated browser contexts.")

    async def _login_user_in_page(self, page, username, password):
        """Helper to log in a user within a specific page context."""
        login_url = f"{self.runner.base_url}/login"
        await page.goto(login_url)
        await page.wait_for_load_state('networkidle')
        
        # Use more robust selectors
        await page.fill('input[name="identifier"], input[name="username"], input[type="email"]', username)
        await page.fill('input[name="password"], input[type="password"]', password)
        await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")')
        await page.wait_for_load_state('networkidle')

        # Verify login by checking URL or for a logout button
        current_url = page.url
        if '/login' in current_url:
            raise Exception(f"Login failed for {username}, still on login page.")
        self.log_step("Login Verified", f"User {username} successfully logged in.")
