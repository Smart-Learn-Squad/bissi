"""Bissi Hi - Researcher Edition.

Advanced AI assistant for researchers and data scientists.
Uses gemma4:e4b (4B parameters) for complex analysis tasks.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from configs.settings import Settings
from configs.personas.researcher import get_prompt
from manager import BissiManager


class BissiHiApp:
    """Bissi Hi application instance."""
    
    DEFAULT_MODEL = "gemma4:e4b"
    EDITION = "bissi_hi"
    
    def __init__(self):
        """Initialize Bissi Hi with researcher persona."""
        self.settings = Settings()
        self.settings.model = self.DEFAULT_MODEL
        self.settings.persona = "researcher"
        
        # Initialize manager with researcher configuration
        self.manager = BissiManager(
            model=self.DEFAULT_MODEL,
            system_prompt=get_prompt()
        )
    
    def run(self):
        """Launch Bissi Hi application."""
        from ui.main_window import main as ui_main
        ui_main()


def main():
    """Entry point for Bissi Hi."""
    print("🔬 Starting Bissi Hi...")
    print(f"   Model: {BissiHiApp.DEFAULT_MODEL}")
    print(f"   Persona: Researcher Edition")
    
    app = BissiHiApp()
    app.run()


if __name__ == "__main__":
    main()
