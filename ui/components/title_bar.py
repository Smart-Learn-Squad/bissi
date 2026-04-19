"""Title bar component for BISSI."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal

from ui.styles.theme import Theme
from core.config import DEFAULT_CONFIG


class TitleBar(QWidget):
    """Top title bar with window controls placeholder and status."""

    theme_toggle_requested = pyqtSignal()

    def __init__(self, theme: Theme = None):
        super().__init__()
        self.theme = theme or Theme()
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(42)
        self.setStyleSheet(f"""
            background: {self.theme.C['bg_white']};
            border-bottom: 0.5px solid {self.theme.C['border']};
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        # Window control dots (macOS style)
        dots_w = QWidget()
        dots_w.setStyleSheet("background:transparent;")
        dl = QHBoxLayout(dots_w)
        dl.setContentsMargins(0, 0, 0, 0)
        dl.setSpacing(5)
        for color in ["#ff5f56", "#ffbd2e", "#27c93f"]:
            d = QLabel()
            d.setFixedSize(11, 11)
            d.setStyleSheet(
                f"background:{color};border-radius:5px;"
            )
            dl.addWidget(d)
        layout.addWidget(dots_w)

        title = QLabel("Bissi — Agent Local")
        title.setStyleSheet(
            f"font-size:13px;color:{self.theme.C['text_muted']};"
            f"font-family:{self.theme.FONT_UI};margin-left:6px;"
        )
        layout.addWidget(title)
        layout.addStretch()

        self.status_badge = QLabel(f"● {DEFAULT_CONFIG.OLLAMA_MODEL} · en ligne")
        self.status_badge.setStyleSheet(f"""
            font-size:11px;color:{self.theme.C['teal_text']};
            background:{self.theme.C['teal_lt']};
            border:0.5px solid {self.theme.C['teal_bd']};
            border-radius:4px;padding:2px 8px;
            font-family:{self.theme.FONT_UI};
        """)
        layout.addWidget(self.status_badge)

        # Theme toggle button
        self.theme_btn = QPushButton("☀")
        self.theme_btn.setObjectName("ThemeToggle")
        self.theme_btn.setFixedSize(28, 22)
        self.theme_btn.setToolTip("Basculer thème clair / sombre")
        self.theme_btn.clicked.connect(self.theme_toggle_requested.emit)
        layout.addWidget(self.theme_btn)

    def set_theme_label(self, name: str):
        """Update the button icon based on the active theme."""
        self.theme_btn.setText("☀" if name == "dark" else "☾")

    def set_model(self, model: str):
        """Update the badge with the active model selected by the router."""
        short = model.split(":")[-1]
        self.status_badge.setText(f"● {model} · en ligne")
        self.status_badge.setStyleSheet(f"""
            font-size:11px;color:{self.theme.C['teal_text']};
            background:{self.theme.C['teal_lt']};
            border:0.5px solid {self.theme.C['teal_bd']};
            border-radius:4px;padding:2px 8px;
            font-family:{self.theme.FONT_UI};
        """)

    def set_busy(self, busy: bool):
        """Update status badge for busy/idle state."""
        if busy:
            self.status_badge.setText(f"⟳ {DEFAULT_CONFIG.OLLAMA_MODEL} · réflexion…")
            self.status_badge.setStyleSheet(f"""
                font-size:11px;color:{self.theme.C['amber']};
                background:#FAEEDA;border:0.5px solid #FAC775;
                border-radius:4px;padding:2px 8px;
                font-family:{self.theme.FONT_UI};
            """)
        else:
            self.status_badge.setText(f"● {DEFAULT_CONFIG.OLLAMA_MODEL} · en ligne")
            self.status_badge.setStyleSheet(f"""
                font-size:11px;color:{self.theme.C['teal_text']};
                background:{self.theme.C['teal_lt']};
                border:0.5px solid {self.theme.C['teal_bd']};
                border-radius:4px;padding:2px 8px;
                font-family:{self.theme.FONT_UI};
            """)
