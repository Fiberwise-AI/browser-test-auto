"""
Test automation and navigation browser actions.
"""

import asyncio
from typing import Dict, Any, List
from .base_action import BaseAction


class TestActions(BaseAction):
    """Handles test automation and navigation actions."""
    
    async def execute(self, step: Dict[str, Any]) -> Any:
        """Execute test-related step."""
        action = step.get('action')
        config = step.get('config', {})
        
        # Initialize browser if needed
        if not self.runner.browser:
            settings = self.runner.script.get('settings', {})
            await self.runner.initialize_browser(settings, config)
        
        context = self.runner.browser_context
        
        if action == "navigate_pages":
            await self.navigate_pages(context, config)
        elif action == "test_form_submission":
            await self.test_form_submission(context, config)
        elif action == "check_responsive_design":
            await self.check_responsive_design(context, config)
        elif action == "measure_performance":
            await self.measure_performance(context, config)
        elif action == "verify_session_variable":
            await self.verify_session_variable(config)
        elif action == "set_session_variables":
            await self.set_session_variables(config)
        else:
            self.log_step("Unknown Test Action", f"Action '{action}' not implemented")
            return None
    
    async def navigate_pages(self, context, config: Dict[str, Any]):
        """Navigate through a list of pages and capture information."""
        pages_to_visit = config.get('pages', [])
        if not pages_to_visit:
            self.log_step("Page Navigation", "No pages specified to visit")
            return
        
        page, should_close = await self.get_or_create_page(context, config)
        try:
            self.log_step("Page Navigation", f"Visiting {len(pages_to_visit)} pages")
            
            for i, page_info in enumerate(pages_to_visit):
                if isinstance(page_info, str):
                    url = page_info
                    page_name = f"Page {i+1}"
                else:
                    url = page_info.get('url', '')
                    page_name = page_info.get('name', f"Page {i+1}")
                
                await self._visit_single_page(page, url, page_name)
                
                # Brief pause between pages
                await asyncio.sleep(1)
            
        except Exception as e:
            self.log_step("Navigation Error", f"Error during page navigation: {str(e)}")
        finally:
            if should_close:
                await page.close()
    
    async def _visit_single_page(self, page, url: str, page_name: str):
        """Visit a single page and capture information."""
        try:
            self.log_step(f"Visiting {page_name}", f"URL: {url}")
            
            # Navigate to page
            full_url = url if url.startswith('http') else f"{self.runner.base_url}{url}"
            await page.goto(full_url, timeout=10000)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Take screenshot
            screenshot_name = page_name.lower().replace(' ', '_')
            await page.screenshot(path=self.get_screenshot_path(screenshot_name))
            
            # Get page title
            try:
                title = await page.title()
                self.log_step(f"{page_name} Title", title)
            except:
                pass
            
            # Check for common page elements
            await self._analyze_page_elements(page, page_name)
            
        except Exception as e:
            self.log_step(f"{page_name} Error", f"Error visiting page: {str(e)}")
    
    async def _analyze_page_elements(self, page, page_name: str):
        """Analyze common elements on the page."""
        try:
            # Check for forms
            forms = await page.locator('form').count()
            if forms > 0:
                self.log_step(f"{page_name} Forms", f"Found {forms} forms")
            
            # Check for buttons
            buttons = await page.locator('button').count()
            if buttons > 0:
                self.log_step(f"{page_name} Buttons", f"Found {buttons} buttons")
            
            # Check for links
            links = await page.locator('a').count()
            if links > 0:
                self.log_step(f"{page_name} Links", f"Found {links} links")
            
            # Check for error messages
            error_indicators = [
                '.error',
                '.alert-danger',
                '[role="alert"]',
                'text="Error"',
                'text="Failed"'
            ]
            
            for indicator in error_indicators:
                if await page.locator(indicator).count() > 0:
                    error_text = await page.locator(indicator).first.text_content()
                    self.log_step(f"{page_name} Error", f"Found error: {error_text}")
                    break
            
        except Exception as e:
            self.log_step(f"{page_name} Analysis", f"Error analyzing elements: {str(e)}")
    
    async def test_form_submission(self, context, config: Dict[str, Any]):
        """Test form submission with specified data."""
        form_url = config.get('url', '')
        form_data = config.get('data', {})
        
        if not form_url or not form_data:
            self.log_step("Form Test", "Missing URL or form data")
            return
        
        page, should_close = await self.get_or_create_page(context, config)
        try:
            self.log_step("Form Submission Test", f"Testing form at {form_url}")
            
            # Navigate to form page
            full_url = form_url if form_url.startswith('http') else f"{self.runner.base_url}{form_url}"
            await page.goto(full_url, timeout=10000)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Take screenshot before filling
            await page.screenshot(path=self.get_screenshot_path("form_before"))
            
            # Fill form fields
            await self._fill_form_fields(page, form_data)
            
            # Take screenshot after filling
            await page.screenshot(path=self.get_screenshot_path("form_filled"))
            
            # Submit form if requested
            if config.get('submit', True):
                await self._submit_form(page)
                
                # Take screenshot after submission
                await page.screenshot(path=self.get_screenshot_path("form_after_submit"))
            
        except Exception as e:
            self.log_step("Form Test Error", f"Error testing form: {str(e)}")
        finally:
            if should_close:
                await page.close()
    
    async def _fill_form_fields(self, page, form_data: Dict[str, Any]):
        """Fill form fields with provided data."""
        for field_name, field_value in form_data.items():
            try:
                # Try multiple selector strategies
                selectors = [
                    f'input[name="{field_name}"]',
                    f'input[id="{field_name}"]',
                    f'textarea[name="{field_name}"]',
                    f'select[name="{field_name}"]',
                    f'[data-testid="{field_name}"]'
                ]
                
                field_filled = False
                for selector in selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            element = page.locator(selector).first
                            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                            
                            if tag_name == 'select':
                                await element.select_option(str(field_value))
                            elif await element.get_attribute('type') == 'checkbox':
                                if field_value:
                                    await element.check()
                                else:
                                    await element.uncheck()
                            else:
                                await element.fill(str(field_value))
                            
                            field_filled = True
                            self.log_step(f"Field {field_name}", f"Filled with: {field_value}")
                            break
                    except:
                        continue
                
                if not field_filled:
                    self.log_step(f"Field {field_name}", "Could not find or fill field")
                    
            except Exception as e:
                self.log_step(f"Field {field_name} Error", f"Error filling field: {str(e)}")
    
    async def _submit_form(self, page):
        """Submit the form using various strategies."""
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit")',
            'button:has-text("Save")',
            'button:has-text("Send")',
            '.btn-submit'
        ]
        
        submitted = False
        for selector in submit_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.click(selector, timeout=3000)
                    submitted = True
                    self.log_step("Form Submit", f"Submitted using: {selector}")
                    break
            except:
                continue
        
        if submitted:
            # Wait for response
            await asyncio.sleep(3)
        else:
            self.log_step("Form Submit", "Could not find submit button")
    
    async def check_responsive_design(self, context, config: Dict[str, Any]):
        """Test responsive design at different viewport sizes."""
        test_url = config.get('url', self.runner.base_url)
        viewports = config.get('viewports', [
            {'width': 1920, 'height': 1080, 'name': 'desktop'},
            {'width': 768, 'height': 1024, 'name': 'tablet'},
            {'width': 375, 'height': 667, 'name': 'mobile'}
        ])
        
        page, should_close = await self.get_or_create_page(context, config)
        try:
            self.log_step("Responsive Test", f"Testing {len(viewports)} viewport sizes")
            
            for viewport in viewports:
                await self._test_viewport(page, test_url, viewport)
                await asyncio.sleep(1)
            
        except Exception as e:
            self.log_step("Responsive Test Error", f"Error testing responsive design: {str(e)}")
        finally:
            if should_close:
                await page.close()
    
    async def _test_viewport(self, page, url: str, viewport: Dict[str, Any]):
        """Test a specific viewport size."""
        try:
            viewport_name = viewport.get('name', 'unknown')
            width = viewport.get('width', 1920)
            height = viewport.get('height', 1080)
            
            self.log_step(f"Viewport {viewport_name}", f"Testing {width}x{height}")
            
            # Set viewport size
            await page.set_viewport_size({'width': width, 'height': height})
            
            # Navigate to page
            await page.goto(url, timeout=10000)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Take screenshot
            await page.screenshot(path=self.get_screenshot_path(f"viewport_{viewport_name}"))
            
            # Check for responsive elements
            await self._check_responsive_elements(page, viewport_name)
            
        except Exception as e:
            self.log_step(f"Viewport Error", f"Error testing {viewport_name}: {str(e)}")
    
    async def _check_responsive_elements(self, page, viewport_name: str):
        """Check for responsive design elements."""
        try:
            # Check for mobile menu toggle
            mobile_menu_selectors = [
                '.mobile-menu-toggle',
                '.hamburger',
                '[data-testid="mobile-menu"]',
                'button[aria-label*="menu" i]'
            ]
            
            for selector in mobile_menu_selectors:
                if await page.locator(selector).count() > 0:
                    is_visible = await page.locator(selector).is_visible()
                    self.log_step(f"{viewport_name} Mobile Menu", f"Found and visible: {is_visible}")
                    break
            
            # Check for hidden elements that should be responsive
            desktop_only_selectors = [
                '.desktop-only',
                '.hidden-mobile',
                '[data-hide-mobile]'
            ]
            
            for selector in desktop_only_selectors:
                if await page.locator(selector).count() > 0:
                    is_visible = await page.locator(selector).is_visible()
                    self.log_step(f"{viewport_name} Desktop Elements", f"Visible: {is_visible}")
                    break
            
        except Exception as e:
            self.log_step(f"{viewport_name} Element Check", f"Error checking elements: {str(e)}")
    
    async def measure_performance(self, context, config: Dict[str, Any]):
        """Measure basic page performance metrics."""
        test_url = config.get('url', self.runner.base_url)
        
        page, should_close = await self.get_or_create_page(context, config)
        try:
            self.log_step("Performance Test", f"Measuring performance for {test_url}")
            
            # Navigate and measure load time
            start_time = asyncio.get_event_loop().time()
            await page.goto(test_url, timeout=30000)
            await page.wait_for_load_state('networkidle', timeout=10000)
            end_time = asyncio.get_event_loop().time()
            
            load_time = (end_time - start_time) * 1000  # Convert to milliseconds
            self.log_step("Load Time", f"{load_time:.2f}ms")
            
            # Check for performance metrics if available
            try:
                metrics = await page.evaluate('''() => {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    return {
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.navigationStart,
                        loadComplete: navigation.loadEventEnd - navigation.navigationStart,
                        firstPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-paint')?.startTime,
                        firstContentfulPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-contentful-paint')?.startTime
                    };
                }''')
                
                for metric_name, metric_value in metrics.items():
                    if metric_value:
                        self.log_step(f"Performance {metric_name}", f"{metric_value:.2f}ms")
                        
            except Exception:
                self.log_step("Performance Metrics", "Browser metrics not available")
            
            # Take screenshot for visual verification
            await page.screenshot(path=self.get_screenshot_path("performance_test"))
            
        except Exception as e:
            self.log_step("Performance Test Error", f"Error measuring performance: {str(e)}")
        finally:
            if should_close:
                await page.close()
    
    async def verify_session_variable(self, config: Dict[str, Any]):
        """Verify that a session variable exists and meets specified criteria."""
        variable_name = config.get('variable', '')
        expected_type = config.get('expected_type', 'string')
        not_empty = config.get('not_empty', True)
        expected_value = config.get('expected_value')
        contains = config.get('contains')
        
        if not variable_name:
            self.log_step("Variable Verification Error", "No variable name specified")
            return False
        
        # Get the variable value
        value = self.runner.get_session_variable(variable_name)
        
        if value is None or value == "":
            if not_empty:
                self.log_step("Variable Verification FAIL", f"Variable '{variable_name}' is empty or not found")
                return False
            else:
                self.log_step("Variable Verification PASS", f"Variable '{variable_name}' is empty as expected")
                return True
        
        # Check type
        if expected_type == 'string' and not isinstance(value, str):
            self.log_step("Variable Verification FAIL", f"Variable '{variable_name}' is not a string: {type(value)}")
            return False
        elif expected_type == 'number':
            try:
                float(value)
            except ValueError:
                self.log_step("Variable Verification FAIL", f"Variable '{variable_name}' is not a number: {value}")
                return False
        
        # Check expected value
        if expected_value is not None and str(value) != str(expected_value):
            self.log_step("Variable Verification FAIL", f"Variable '{variable_name}' = '{value}', expected '{expected_value}'")
            return False
        
        # Check contains
        if contains and contains not in str(value):
            self.log_step("Variable Verification FAIL", f"Variable '{variable_name}' = '{value}', does not contain '{contains}'")
            return False
        
        # All checks passed
        self.log_step("Variable Verification PASS", f"Variable '{variable_name}' = '{value}' meets all criteria")
        return True
    
    async def set_session_variables(self, config: Dict[str, Any]):
        """Set multiple session variables from a dictionary."""
        variables = config.get('variables', {})
        
        if not variables:
            self.log_step("Set Variables Error", "No variables specified")
            return False
        
        set_count = 0
        for var_name, var_value in variables.items():
            self.runner.set_session_variable(var_name, var_value, f"Set from config")
            self.log_step("Variable Set", f"'{var_name}' = '{var_value}'")
            set_count += 1
        
        self.log_step("Variables Set Complete", f"Set {set_count} session variables")
        return True
