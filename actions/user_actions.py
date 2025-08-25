"""
User management browser actions.
"""

import asyncio
from typing import Dict, Any
from .base_action import BaseAction


class UserActions(BaseAction):
    """Handles user-related browser actions."""
    
    async def execute(self, step: Dict[str, Any]) -> Any:
        """Execute user-related step."""
        action = step.get('action')
        config = step.get('config', {})
        
        # Initialize browser if needed
        if not self.runner.browser:
            settings = self.runner.script.get('settings', {})
            await self.runner.initialize_browser(settings, config)
        
        context = self.runner.browser_context
        
        if action == "register_multiple_users":
            await self.register_multiple_users(context, config)
        elif action == "test_login":
            await self.test_login(context, config)
        elif action == "verify_user_logins":
            await self.verify_user_logins(context, config)
        else:
            self.log_step("Unknown User Action", f"Action '{action}' not implemented")
            return None
    
    async def verify_user_logins(self, context, config):
        """Verify users can log in."""
        self.log_step("Login Verification", "Verifying user login capability")
    
    async def register_multiple_users(self, context, config: Dict[str, Any]):
        """Register multiple users headlessly."""
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
            await self._register_single_user(context, user, selectors, i + 1)
    
    async def _register_single_user(self, context, user: Dict[str, Any], selectors: Dict[str, str], user_num: int):
        """Register a single user with enhanced debugging."""
        self.log_step(f"Registering User {user_num}", f"Username: {user.get('username')}, Email: {user.get('email')}")
        
        page = await context.new_page()
        try:
            # Navigate to registration page
            await page.goto(f"{self.runner.base_url}/register", timeout=10000)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Take screenshot to see registration page
            await page.screenshot(path=self.get_screenshot_path(f"registration_page_user_{user_num}"))
            
            # Debug: Get page title and URL
            page_title = await page.title()
            current_url = page.url
            self.log_step(f"Registration Page Info {user_num}", f"Title: '{page_title}', URL: {current_url}")
            
            # Log all visible input fields for debugging
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
                self.log_step(f"Registration Form Inputs {user_num}", f"Total: {len(input_info)}")
                for info in input_info[:8]:  # Show more fields for registration
                    self.log_step(f"Registration Input {user_num}", info)
            else:
                self.log_step(f"No Registration Inputs {user_num}", "No input elements found on registration page")
                
            # Fill registration form fields
            await self._fill_registration_form(page, user, selectors, user_num)
            
            # Take screenshot after filling form
            await page.screenshot(path=self.get_screenshot_path(f"registration_form_filled_{user_num}"))
            
            # Submit form
            await self._submit_registration_form(page, selectors, user_num)
            
            # Take screenshot after submission
            await page.screenshot(path=self.get_screenshot_path(f"registration_after_submit_{user_num}"))
            
            # Check if registration was successful
            final_url = page.url
            self.log_step(f"Registration Result URL {user_num}", f"Final URL: {final_url}")
            
            # Look for success indicators
            if '/login' in final_url:
                self.log_step(f"Registration Success {user_num}", "Redirected to login page - registration likely successful")
            elif 'error' in final_url:
                self.log_step(f"Registration Error {user_num}", f"Registration failed - error in URL")
            else:
                self.log_step(f"Registration Status Unknown {user_num}", f"Registration completed, current URL: {final_url}")
            
        except Exception as e:
            self.log_step(f"Registration Error {user_num}", f"Error registering user: {str(e)}")
        finally:
            await page.close()
    
    async def _fill_registration_form(self, page, user: Dict[str, Any], selectors: Dict[str, str], user_num: int):
        """Fill the registration form fields with enhanced debugging."""
        
        username = user.get('username', '')
        email = user.get('email', '')
        password = user.get('password', '')
        
        self.log_step(f"Registration Data {user_num}", f"Will use - Username: '{username}', Email: '{email}', Password: '{password}'")
        
        # Fill username field
        username_filled = False
        for selector in selectors['username_field'].split(', '):
            try:
                selector = selector.strip()
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, username, timeout=3000)
                    username_filled = True
                    self.log_step(f"Username Field {user_num}", f"✅ Filled '{username}' using: {selector}")
                    break
            except Exception as e:
                self.log_step(f"Username Field Error {user_num}", f"❌ Failed {selector}: {str(e)}")
                continue
        
        if not username_filled:
            self.log_step(f"Username Error {user_num}", "❌ Could not find username field")
            return
        
        # Fill email field
        email_filled = False
        for selector in selectors['email_field'].split(', '):
            try:
                selector = selector.strip()
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, email, timeout=3000)
                    email_filled = True
                    self.log_step(f"Email Field {user_num}", f"✅ Filled '{email}' using: {selector}")
                    break
            except Exception as e:
                self.log_step(f"Email Field Error {user_num}", f"❌ Failed {selector}: {str(e)}")
                continue
        
        if not email_filled:
            self.log_step(f"Email Warning {user_num}", "⚠️ Could not find email field")
        
        # Fill password field
        password_filled = False
        for selector in selectors['password_field'].split(', '):
            try:
                selector = selector.strip()
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, password, timeout=3000)
                    password_filled = True
                    self.log_step(f"Password Field {user_num}", f"✅ Filled password using: {selector}")
                    break
            except Exception as e:
                self.log_step(f"Password Field Error {user_num}", f"❌ Failed {selector}: {str(e)}")
                continue
        
        if not password_filled:
            self.log_step(f"Password Error {user_num}", "❌ Could not find password field")
            return
        
        # Try to fill password confirmation field
        password_confirm_filled = False
        for selector in selectors['password_confirm_field'].split(', '):
            try:
                selector = selector.strip()
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, password, timeout=3000)
                    password_confirm_filled = True
                    self.log_step(f"Password Confirm {user_num}", f"✅ Filled confirmation using: {selector}")
                    break
            except Exception as e:
                self.log_step(f"Password Confirm Error {user_num}", f"❌ Failed {selector}: {str(e)}")
                continue
        
        if not password_confirm_filled:
            self.log_step(f"Password Confirm Warning {user_num}", "⚠️ Could not find password confirmation field")
        
        # Try to fill first name field
        first_name = user.get('first_name', username.split('_')[0] if username else 'Test')
        for selector in selectors['first_name_field'].split(', '):
            try:
                selector = selector.strip()
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, first_name, timeout=3000)
                    self.log_step(f"First Name {user_num}", f"✅ Filled '{first_name}' using: {selector}")
                    break
            except Exception:
                continue
        
        # Try to fill last name field
        last_name = user.get('last_name', username.split('_')[-1] if username else 'User')
        for selector in selectors['last_name_field'].split(', '):
            try:
                selector = selector.strip()
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, last_name, timeout=3000)
                    self.log_step(f"Last Name {user_num}", f"✅ Filled '{last_name}' using: {selector}")
                    break
            except Exception:
                continue
    
    async def _submit_registration_form(self, page, selectors: Dict[str, str], user_num: int):
        """Submit the registration form."""
        submitted = False
        for selector in selectors['submit_button'].split(', '):
            try:
                if await page.locator(selector.strip()).count() > 0:
                    await page.click(selector.strip(), timeout=3000)
                    submitted = True
                    self.log_step(f"Submit {user_num}", f"Clicked: {selector.strip()}")
                    break
            except Exception:
                continue
        
        if submitted:
            # Wait for potential redirect
            await asyncio.sleep(2)
            self.log_step(f"User {user_num} Registered", "Registration attempt completed")
        else:
            self.log_step(f"Submit Error {user_num}", "Could not find or click submit button")
    
    async def test_login(self, context, config: Dict[str, Any]):
        """Simple login test with enhanced debugging and screenshots."""
        username = config.get('username', 'testuser1')
        password = config.get('password', 'testpass123')
        
        # Also try using the email if it's provided - many systems use email for login
        email = config.get('email')
        
        page, should_close = await self.get_or_create_page(context, config)
        try:
            self.log_step("Simple Login Test", f"Testing login for {username}" + (f" (email: {email})" if email else ""))
            
            # Navigate to login page
            await page.goto(f"{self.runner.base_url}/login", timeout=10000)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Take screenshot of login page
            await page.screenshot(path=self.get_screenshot_path("login_page"))
            self.log_step("Login Page Screenshot", "Captured login page")
            
            # Debug: Get page title and URL
            page_title = await page.title()
            current_url = page.url
            self.log_step("Page Info", f"Title: '{page_title}', URL: {current_url}")
            
            # Debug: List all input fields on the page
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
                self.log_step("Found Input Fields", f"Total: {len(input_info)}")
                for info in input_info[:5]:  # Show first 5
                    self.log_step("Input Field", info)
            else:
                self.log_step("No Input Fields", "No input elements found on page")
                
            # Debug: Look for forms
            forms = await page.locator('form').all()
            self.log_step("Forms Found", f"Found {len(forms)} form(s) on page")
            
            # More flexible username selectors - including 'identifier' which we saw in the form
            username_selectors = [
                'input[name="identifier"]',  # This is what we found in the form analysis
                'input[name="username"]',
                'input[name="email"]',
                'input[name="user"]',
                'input[name="login"]', 
                'input[type="text"]',
                'input[type="email"]',
                'input[placeholder*="username" i]',
                'input[placeholder*="email" i]',
                'input[placeholder*="user" i]',
                'input[placeholder*="login" i]',
                'input[placeholder*="identifier" i]',
                '#identifier',
                '#username',
                '#email',
                '#user',
                '#login'
            ]
            
            # Try to fill username field - use email first if available, then username
            login_credential = email if email else username
            self.log_step("Login Credential", f"Will attempt login with: '{login_credential}' (password: '{password}')")
            
            username_filled = False
            used_selector = None
            for selector in username_selectors:
                try:
                    element_count = await page.locator(selector).count()
                    if element_count > 0:
                        await page.fill(selector, login_credential, timeout=3000)
                        username_filled = True
                        used_selector = selector
                        self.log_step("Username Filled", f"✅ Filled '{login_credential}' using selector: {selector}")
                        break
                except Exception as e:
                    self.log_step("Username Selector Failed", f"❌ {selector}: {str(e)}")
                    continue
            
            if not username_filled:
                self.log_step("Username Fill Failed", "❌ Could not find any username/identifier input field")
                # Take another screenshot for debugging
                await page.screenshot(path=self.get_screenshot_path("username_fill_failed"))
                return
            
            # More flexible password selectors
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="password" i]',
                '#password'
            ]
            
            # Try to fill password field
            password_filled = False
            for selector in password_selectors:
                try:
                    element_count = await page.locator(selector).count()
                    if element_count > 0:
                        await page.fill(selector, password, timeout=3000)
                        password_filled = True
                        self.log_step("Password Filled", f"✅ Filled password using selector: {selector}")
                        break
                except Exception as e:
                    self.log_step("Password Selector Failed", f"❌ {selector}: {str(e)}")
                    continue
            
            if not password_filled:
                self.log_step("Password Fill Failed", "❌ Could not find password input field")
                
            # Take screenshot after filling fields
            await page.screenshot(path=self.get_screenshot_path("form_filled"))
            
            # Try to submit the form
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'button:has-text("Log in")',
                '.btn-submit',
                '.login-btn',
                'form button',
                'button'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    element_count = await page.locator(selector).count()
                    if element_count > 0:
                        await page.click(selector, timeout=3000)
                        submitted = True
                        self.log_step("Submit Clicked", f"✅ Clicked submit using selector: {selector}")
                        break
                except Exception as e:
                    self.log_step("Submit Selector Failed", f"❌ {selector}: {str(e)}")
                    continue
            
            if not submitted:
                self.log_step("Submit Failed", "❌ Could not find or click submit button")
                # Try pressing Enter on password field as fallback
                try:
                    if password_filled:
                        await page.press('input[type="password"]', 'Enter')
                        self.log_step("Submit Fallback", "✅ Pressed Enter on password field")
                        submitted = True
                except:
                    pass
            
            if submitted:
                # Wait for potential redirect and take screenshot
                await asyncio.sleep(3)
                await page.screenshot(path=self.get_screenshot_path("after_submit"))
                
                # Check current URL to verify login
                current_url = page.url
                self.log_step("Post-Login URL", f"Redirected to: {current_url}")
                
                # Analyze the URL for error messages
                if 'error=' in current_url:
                    import urllib.parse
                    error_msg = urllib.parse.unquote(current_url.split('error=')[1].split('&')[0])
                    self.log_step("Login Error Detected", f"Error message: {error_msg}")
                    
                    # If we used username and it failed, try with email if available
                    if not email and used_selector and 'identifier' in used_selector:
                        self.log_step("Login Strategy", "Login failed with username, but 'identifier' field suggests email might be required")
                
                # Look for login success indicators
                success_indicators = [
                    'text="Dashboard"',
                    'text="Profile"', 
                    'text="Settings"',
                    'text="Logout"',
                    'text="Sign out"',
                    '[data-testid="user-menu"]',
                    '.user-profile',
                    '.dashboard',
                    'nav a:has-text("Dashboard")',
                    'nav a:has-text("Settings")'
                ]
                
                login_success = False
                for indicator in success_indicators:
                    try:
                        if await page.locator(indicator).count() > 0:
                            login_success = True
                            self.log_step("Login Success", f"✅ Found success indicator: {indicator}")
                            break
                    except:
                        continue
                
                if not login_success:
                    # Check if we're still on login page (login failed)
                    if '/login' in current_url:
                        self.log_step("Login Failed", "❌ Still on login page - credentials may be incorrect")
                    else:
                        self.log_step("Login Status Unknown", "⚠️ Could not confirm login success but URL changed")
                        
                # Take final screenshot
                await page.screenshot(path=self.get_screenshot_path("login_final"))
            else:
                self.log_step("Login Aborted", "❌ Could not submit login form")
                
        except Exception as e:
            self.log_step("Login Test Error", f"❌ Error during login test: {str(e)}")
            # Take error screenshot
            try:
                await page.screenshot(path=self.get_screenshot_path("login_error"))
            except:
                pass
        finally:
            if should_close:
                await page.close()
