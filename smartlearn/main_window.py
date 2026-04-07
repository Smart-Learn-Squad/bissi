"""Smartlearn main window - Ollama-style centered interface.

Student edition with liquid glass input and centered avatar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.components import OllamaStyleWindow, LiquidGlassInput, CenteredAvatar
from smartlearn.config import EDITION_DISPLAY, DEFAULT_MODEL, THEME


class SmartlearnMainWindow(OllamaStyleWindow):
    """Smartlearn main window with student-focused UI."""
    
    def __init__(self, parent=None):
        super().__init__(
            title=EDITION_DISPLAY,
            icon=THEME["icon"],
            parent=parent
        )
        
        # Set student theme colors
        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
            }
        """)
        
        # Update model badge
        self.set_model(DEFAULT_MODEL)
        
        # Connect message handler
        self.message_sent.connect(self._handle_message)
        
        # Initialize manager (lazy import to avoid circular deps)
        self._manager = None
    
    def _get_manager(self):
        """Lazy load manager."""
        if self._manager is None:
            from smartlearn import SmartlearnApp
            app = SmartlearnApp()
            self._manager = app.manager
        return self._manager
    
    def _handle_message(self, text: str):
        """Process user message."""
        print(f"[Smartlearn] User: {text}")
        # TODO: Send to manager and display response
        # For now just echo back
        self._show_response(f"You said: {text}")
    
    def _show_response(self, text: str):
        """Display AI response."""
        # TODO: Add chat display area
        print(f"[Smartlearn] AI: {text}")


def main():
    """Entry point for Smartlearn GUI."""
    app = QApplication(sys.argv)
    
    # Set global font
    font = QFont("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", 14)
    app.setFont(font)
    
    # Create and show window
    window = SmartlearnMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
