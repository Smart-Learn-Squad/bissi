"""Status bar component for BISSI."""

import time

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer

from ui.styles.theme import Theme
from core.config import DEFAULT_CONFIG


class StatusBar(QWidget):
    """Bottom status bar showing session info and status."""

    def __init__(self, theme: Theme = None):
        super().__init__()
        self.theme = theme or Theme()
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(26)
        self.setStyleSheet(f"""
            background: {self.theme.C['bg_white']};
            border-top: 0.5px solid {self.theme.C['border']};
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(16)

        self._dot = QLabel()
        self._dot.setFixedSize(6, 6)
        self._dot.setStyleSheet(
            f"background:{self.theme.C['teal']};border-radius:3px;"
        )

        def stat(text: str) -> QLabel:
            l = QLabel(text)
            l.setStyleSheet(
                f"font-size:11px;color:{self.theme.C['text_dim']};font-family:{self.theme.FONT_UI};"
            )
            return l

        self._model_lbl = stat(f"Ollama · {DEFAULT_CONFIG.OLLAMA_MODEL}")
        self._mem_lbl = stat("Mémoire · 0 souvenirs")
        self._session_lbl = stat("Session · 00:00")
        self._rag_lbl = stat("RAG · ChromaDB")

        layout.addWidget(self._dot)
        layout.addWidget(self._model_lbl)
        layout.addWidget(self._mem_lbl)
        layout.addWidget(self._session_lbl)
        layout.addStretch()
        layout.addWidget(self._rag_lbl)

        self._start = time.time()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

    def _tick(self):
        """Update session timer."""
        e = int(time.time() - self._start)
        h, r = divmod(e, 3600)
        m, s = divmod(r, 60)
        self._session_lbl.setText(
            f"Session · {h:02d}:{m:02d}:{s:02d}"
        )

    def set_busy(self, busy: bool):
        """Update status dot color for busy/idle state."""
        color = self.theme.C["amber"] if busy else self.theme.C["teal"]
        self._dot.setStyleSheet(
            f"background:{color};border-radius:3px;"
        )

    def set_memory(self, n: int):
        """Update memory count display."""
        self._mem_lbl.setText(f"Mémoire · {n} souvenirs")

    def set_rag(self, n: int):
        """Update RAG chunks display."""
        self._rag_lbl.setText(f"RAG · {n} chunks")

    def set_routing(self, model: str, score: float):
        """Affiche le modèle actif (gemma4:e2b)."""
        color = self.theme.C["teal"]
        self._model_lbl.setText(f"Ollama · {model}")
        self._model_lbl.setStyleSheet(
            f"font-size:11px;color:{color};font-family:{self.theme.FONT_UI};"
        )
        self._dot.setStyleSheet(
            f"background:{color};border-radius:3px;"
        )
