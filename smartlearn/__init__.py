"""Smartlearn (BISSI Lite) - Student Edition.

Lightweight AI assistant optimized for students.
Uses gemma4:e2b (2B parameters) for efficient local inference.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from configs.settings import Settings
from configs.personas.student import get_prompt
from manager import BissiManager


class SmartlearnApp:
    """Smartlearn application instance."""
    
    DEFAULT_MODEL = "gemma4:e2b"
    EDITION = "smartlearn"
    
    def __init__(self):
        """Initialize Smartlearn with student persona."""
        self.settings = Settings()
        self.settings.model = self.DEFAULT_MODEL
        self.settings.persona = "student"
        
        # Initialize manager with student configuration
        self.manager = BissiManager(
            model=self.DEFAULT_MODEL,
            system_prompt=get_prompt()
        )
    
    def run(self):
        """Launch Smartlearn application."""
        from smartlearn.main_window import main as ui_main
        ui_main()


def main():
    """Entry point for Smartlearn."""
    print("🎓 Starting Smartlearn (BISSI Lite)...")
    print(f"   Model: {SmartlearnApp.DEFAULT_MODEL}")
    print(f"   Persona: Student Edition")
    
    app = SmartlearnApp()
    app.run()


if __name__ == "__main__":
    main()
