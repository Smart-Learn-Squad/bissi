"""
Bissi Hi - AI Research Assistant (Glass 2026)
Mirror of smartlearn.py for the researcher edition
"""
import sys
from pathlib import Path

# Add parent to path
root = Path(__file__).parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from ui.components import OllamaStyleWindow
from bissi_hi.config import EDITION_DISPLAY, DEFAULT_MODEL, USER_NAME, USER_ROLE
from configs.personas.researcher import get_prompt
from manager import get_manager
from utils.concurrency import InferenceWorker

from bissi_hi.research import PaperAnalyzer, DataVisualizer
from ui.styles.theme import Colors
from PyQt6.QtCore import QTimer, QThread, pyqtSignal


class BissiHiMainWindow(OllamaStyleWindow):
    """Bissi Hi - Research Edition (Glass 2026)."""

    def __init__(self, parent=None):
        super().__init__(
            title=EDITION_DISPLAY,
            user_name=USER_NAME,
            user_role=USER_ROLE,
            parent=parent
        )

        # Configure singleton manager for this edition
        self._manager = get_manager()
        self._manager.model = DEFAULT_MODEL
        self._manager.system_prompt = get_prompt()
        self.set_model(DEFAULT_MODEL)

        # Business Logic
        self.analyzer = PaperAnalyzer(self._manager)
        self.visualizer = DataVisualizer()

        # UI Components Reference (from base class)
        self.viz_display = self.progress_view.viz_display
        self.analyze_btn = self.progress_view.start_analysis

        # Signals
        self.message_sent.connect(self._handle_neural_input)
        self.resume_view.analyze_requested.connect(self._handle_paper_analysis)
        self.analyze_btn.clicked.connect(self._start_analysis)

        self._workers = []

    def _handle_neural_input(self, text: str):
        worker = InferenceWorker(text, self._manager, self)
        worker.response_ready.connect(self.add_ai_message)
        worker.finished.connect(lambda: self._workers.remove(worker))
        self._workers.append(worker)
        worker.start()

    def _start_analysis(self):
        """Start research analysis workflow."""
        self.analyze_btn.setText("Analyse en cours...")
        self.analyze_btn.setEnabled(False)
        self.add_ai_message("🔬 Analyse de recherche en cours...")

    def _handle_paper_analysis(self, text: str):
        """Handle research paper analysis request."""
        self._switch_view(0)  # Switch to chat
        self.add_ai_message("🔬 Analyse du document en cours...")

        class PaperAnalysisWorker(QThread):
            ready = pyqtSignal(str)

            def __init__(self, analyzer, text):
                super().__init__()
                self.analyzer = analyzer
                self.text = text

            def run(self):
                result = self.analyzer.analyze(self.text)
                formatted = f"### 🔬 Résumé de Recherche\n{result['summary']}\n\n"
                formatted += "### 📊 Méthodologie\n" + "\n".join([f"* {m}" for m in result['methods']]) + "\n\n"
                formatted += "### 💡 Contributions\n" + "\n".join([f"* {c}" for c in result['contributions']])
                self.ready.emit(formatted)

        worker = PaperAnalysisWorker(self.analyzer, text)
        worker.ready.connect(self._on_analysis_complete)
        worker.start()
        self._workers.append(worker)

    def _on_analysis_complete(self, text: str):
        """Handle completion of analysis."""
        self.add_ai_message(text)
        self.analyze_btn.setText("Analyser")
        self.analyze_btn.setEnabled(True)


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    font = QFont("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", 13)
    app.setFont(font)
    window = BissiHiMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
