"""Smartlearn configuration for students.

Optimized settings for BISSI Lite edition.
"""

EDITION_NAME = "smartlearn"
EDITION_DISPLAY = "Smartlearn"
EDITION_ICON = "🎓"

# Model configuration
DEFAULT_MODEL = "gemma4:e2b"
MODEL_SIZE = "2B"

# Capabilities enabled for students
ENABLED_MODULES = [
    "office.word",
    "office.excel",
    "office.powerpoint",
    "office.pdf",
    "office.ocr",
    "filesystem.explorer",
    "communication.email_client",
    "communication.calendar",
    "communication.contacts",
    "media.audio",
    "media.image",
    "templates.engine",
    "finance.expense_manager",
    "code.python_runner",
    "web.search",
    "system.clipboard",
]

# UI Theme
THEME = {
    "primary_color": "#3b82f6",  # Blue
    "accent_color": "#10b981",   # Green
    "logo_text": "Smartlearn",
    "welcome_message": """🎓 Welcome to Smartlearn!

I'm your AI study companion. I can help you with:
• Understanding complex topics
• Analyzing documents and notes
• Solving homework problems
• Creating study plans
• Managing your schedule

What are you working on today?"""
}
