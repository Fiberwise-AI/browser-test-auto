"""
Base action class for JSON Script Runner actions.
"""

import re
from typing import Dict, Any


class BaseAction:
    """Base class for all script actions."""
    
    def __init__(self, runner):
        """Initialize with reference to the main runner."""
        self.runner = runner
    
    def log_step(self, step_name: str, details: str = ""):
        """Log a step using the runner's logging system."""
        self.runner.log_step(step_name, details)
    
    def get_screenshot_path(self, name: str) -> str:
        """Get path for screenshot with step number."""
        return self.runner.get_screenshot_path(name)
    
    async def get_or_create_page(self, context, config):
        """Delegate to runner's page management."""
        return await self.runner.get_or_create_page(context, config)
    
    def _clean_unicode_text(self, text: str) -> str:
        """Clean Unicode characters that cause encoding issues."""
        if not text:
            return text
        
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
    
    async def execute(self, step: Dict[str, Any]) -> Any:
        """Execute action step - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement execute method")
