"""Bissi Hi configuration for researchers.

Advanced settings for BISSI Hi edition.
"""

EDITION_NAME = "bissi_hi"
EDITION_DISPLAY = "Bissi Hi"
EDITION_ICON = "🔬"

# Model configuration
DEFAULT_MODEL = "gemma4:e4b"
MODEL_SIZE = "4B"

# All capabilities enabled for researchers
ENABLED_MODULES = [
    # Office
    "office.word",
    "office.excel",
    "office.powerpoint",
    "office.pdf",
    "office.ocr",
    # Database
    "database.access",
    # Communication
    "communication.email_client",
    "communication.calendar",
    "communication.contacts",
    # Media
    "media.audio",
    "media.image",
    "media.video",
    # Data & Analysis
    "data.analysis",
    "code.python_runner",
    # Templates
    "templates.engine",
    "templates.repository",
    # Finance
    "finance.expense_manager",
    # Web
    "web.search",
    # Filesystem
    "filesystem.explorer",
    # System
    "system.clipboard",
    "system.operations",
    # Workflows
    "workflows.engine",
    "workflows.triggers",
    "workflows.actions",
    # Memory
    "memory.conversation_store",
    "memory.vector_store",
]

# UI Theme
THEME = {
    "primary_color": "#7c3aed",  # Purple
    "accent_color": "#f59e0b",   # Amber
    "logo_text": "Bissi Hi",
    "welcome_message": """🔬 Welcome to Bissi Hi!

I'm your AI research assistant. I can help you with:
• Literature review and synthesis
• Data analysis and visualization
• Statistical modeling
• DNA sequence analysis
• Research paper writing
• Experimental design

What research are you working on?"""
}
