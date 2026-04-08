"""
    ____  ______________ ____
   / __ )/  _/ ___/ ___//  _/
  / __  |/ / \__ \\__ \ / /
 / /_/ // / ___/ /__/ // /
/_____/___//____/____/___/


—————————————————————————————————————————————
  Smart-Learn Squad | Offline AI Agent
  Motto: Optima, immo absoluta perfectio
—————————————————————————————————————————————
"""

import sys
from pathlib import Path

# Ensure root is in path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ui.components import OllamaStyleWindow
from manager import get_manager

from utils.concurrency import InferenceWorker
from manager import get_manager

class BissiMainApp(OllamaStyleWindow):
    """Core application launcher for BISSI Pro with Neural Function Calling."""
    
    def __init__(self, parent=None):
        super().__init__(title="BISSI AI - Professional 2026", parent=parent)
        
        self._manager = get_manager()
        self.set_model(self._manager.model)
        
        self.message_sent.connect(self._handle_input)
        self._workers = []
        
    def _handle_input(self, text: str):
        worker = InferenceWorker(text, self._manager, self)
        worker.response_ready.connect(self.add_ai_message)
        worker.finished.connect(lambda: self._workers.remove(worker))
        self._workers.append(worker)
        worker.start()

def main():
    # Performance & Aesthetics tuning
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # Modern Typography 2026
    font = QFont("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif", 13)
    app.setFont(font)
    
    window = BissiMainApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
