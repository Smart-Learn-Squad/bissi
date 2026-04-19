"""Sidebar component for BISSI."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal

from ui.styles.theme import Theme


class Sidebar(QWidget):
    """Left sidebar showing sessions and memory status."""

    session_clicked = pyqtSignal(str)

    def __init__(self, theme: Theme = None):
        super().__init__()
        self.theme = theme or Theme()
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(220)
        self.setStyleSheet(f"QWidget {{ {self.theme.sidebar_style} }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QLabel("Sessions")  # section label
        hdr.setStyleSheet(f"""
            padding: 12px 14px 8px;
            font-size: 11px;
            color: {self.theme.C['text_dim']};
            letter-spacing: 0.06em;
            font-weight: 500;
            border-bottom: 0.5px solid {self.theme.C['border']};
            background: {self.theme.C['bg_sidebar']};
            font-family: {self.theme.FONT_UI};
        """)
        layout.addWidget(hdr)

        # Sessions
        self.sessions_layout = QVBoxLayout()
        self.sessions_layout.setContentsMargins(0, 4, 0, 4)
        self.sessions_layout.setSpacing(0)
        sessions_w = QWidget()
        sessions_w.setLayout(self.sessions_layout)
        sessions_w.setStyleSheet(f"background: {self.theme.C['bg_sidebar']};")
        layout.addWidget(sessions_w)

        self._add_session("Session active", "Maintenant", active=True)
        self._add_session("IFRI Budget", "Hier")
        self._add_session("Cours Python", "Lundi")

        layout.addStretch()

        # Footer memory
        footer = QWidget()
        footer.setStyleSheet(f"""
            background: {self.theme.C['bg_sidebar']};
            border-top: 0.5px solid {self.theme.C['border']};
        """)
        fl = QVBoxLayout(footer)
        fl.setContentsMargins(14, 10, 14, 12)
        fl.setSpacing(4)

        mem_lbl = QLabel("Mémoire")
        mem_lbl.setStyleSheet(
            f"font-size:11px;color:{self.theme.C['text_dim']};font-family:{self.theme.FONT_UI};"
            f"border:none;background:transparent;"
        )
        self.mem_count = QLabel("0 souvenir")
        self.mem_count.setStyleSheet(
            f"font-size:12px;color:{self.theme.C['purple']};font-weight:500;"
            f"font-family:{self.theme.FONT_UI};border:none;background:transparent;"
        )
        self.rag_lbl = QLabel("Documents · 0")
        self.rag_lbl.setStyleSheet(
            f"font-size:11px;color:{self.theme.C['text_dim']};font-family:{self.theme.FONT_UI};"
            f"border:none;background:transparent;"
        )
        fl.addWidget(mem_lbl)
        fl.addWidget(self.mem_count)
        fl.addWidget(self.rag_lbl)
        layout.addWidget(footer)

    def _add_session(self, title, sub, active=False):
        btn = QWidget()
        bg = self.theme.C['purple_lt'] if active else self.theme.C['bg_sidebar']
        btn.setStyleSheet(f"""
            QWidget {{ background: {bg}; padding: 0; }}
            QWidget:hover {{ background: {self.theme.C['hover']}; }}
        """)
        bl = QVBoxLayout(btn)
        bl.setContentsMargins(14, 7, 14, 7)
        bl.setSpacing(2)
        t = QLabel(title)
        tc = self.theme.C['purple_text'] if active else self.theme.C['text2']
        t.setStyleSheet(
            f"font-size:12px;color:{tc};font-weight:500;"
            f"font-family:{self.theme.FONT_UI};background:transparent;"
        )
        s = QLabel(sub)
        s.setStyleSheet(
            f"font-size:11px;color:{self.theme.C['text_muted']};"
            f"font-family:{self.theme.FONT_UI};background:transparent;"
        )
        bl.addWidget(t)
        bl.addWidget(s)
        self.sessions_layout.addWidget(btn)

    def set_memory(self, n: int):
        """Update memory count display."""
        self.mem_count.setText(f"{n} souvenir{'s' if n > 1 else ''}")

    def set_rag(self, n: int):
        """Update knowledge base count display."""
        self.rag_lbl.setText(f"Documents · {n}")
