"""ThemeEngine — Live theme switching for BISSI.

Single source of truth for the app's visual design.
Swap themes at runtime without restarting.

Usage:
    engine = ThemeEngine.instance()
    engine.apply("dark")          # switch to dark mode
    engine.apply("light")         # switch to light mode
    engine.toggle()               # flip between light ↔ dark

    engine.theme_changed.connect(callback)   # react to theme changes
"""
from __future__ import annotations

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import QObject, pyqtSignal

from ui.themes.tokens import THEMES, LIGHT
from ui.themes.stylesheet import MASTER_QSS


class ThemeEngine(QObject):
    """Manages application-wide theming via QSS token substitution."""

    theme_changed = pyqtSignal(str)   # emits the new theme name

    _instance: ThemeEngine | None = None

    def __init__(self):
        super().__init__()
        self._current: str = "light"
        self._tokens: dict[str, str] = dict(LIGHT)

    # ── Singleton ─────────────────────────────────────────────

    @classmethod
    def instance(cls) -> ThemeEngine:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Public API ────────────────────────────────────────────

    @property
    def current(self) -> str:
        """Name of the active theme."""
        return self._current

    @property
    def tokens(self) -> dict[str, str]:
        """Current design tokens (read-only copy)."""
        return dict(self._tokens)

    def apply(self, name: str) -> None:
        """Apply a named theme to the entire application.

        Args:
            name: Theme name — must be a key in tokens.THEMES.
        """
        if name not in THEMES:
            raise ValueError(f"Theme '{name}' not found. Available: {list(THEMES)}")

        self._current = name
        self._tokens  = dict(THEMES[name])

        app = QApplication.instance()
        if app:
            # Substitute tokens into the QSS template
            qss = MASTER_QSS.format(**self._tokens)
            app.setStyleSheet(qss)

            # Update the Qt palette for native widgets
            self._apply_palette(app)

        self.theme_changed.emit(name)

    def toggle(self) -> str:
        """Flip between light and dark. Returns the new theme name."""
        new = "dark" if self._current == "light" else "light"
        self.apply(new)
        return new

    def token(self, key: str) -> str:
        """Get a single token value by name."""
        return self._tokens.get(key, "")

    # ── Qt Palette ────────────────────────────────────────────

    def _apply_palette(self, app: QApplication) -> None:
        """Sync Qt color palette with current tokens."""
        t   = self._tokens
        pal = QPalette()

        pairs = [
            (QPalette.ColorRole.Window,          t["bg"]),
            (QPalette.ColorRole.WindowText,       t["text"]),
            (QPalette.ColorRole.Base,             t["bg_white"]),
            (QPalette.ColorRole.AlternateBase,    t["bg_sidebar"]),
            (QPalette.ColorRole.Text,             t["text"]),
            (QPalette.ColorRole.BrightText,       t["text"]),
            (QPalette.ColorRole.Button,           t["bg"]),
            (QPalette.ColorRole.ButtonText,       t["text"]),
            (QPalette.ColorRole.Highlight,        t["accent"]),
            (QPalette.ColorRole.HighlightedText,  "#ffffff"),
            (QPalette.ColorRole.PlaceholderText,  t["text_dim"]),
            (QPalette.ColorRole.ToolTipBase,      t["bg_white"]),
            (QPalette.ColorRole.ToolTipText,      t["text"]),
        ]

        for role, color in pairs:
            pal.setColor(role, QColor(color))

        app.setPalette(pal)

    # ── Parser integration ────────────────────────────────────

    def parser_colors(self) -> dict[str, str]:
        """Return the color dict expected by ui.parser.configure()."""
        t = self._tokens
        return {
            "code_bg":     t["bg_code"],
            "code_text":   t["text2"],
            "code_border": t["border"],
            "inline_bg":   t["accent_lt"],
            "inline_text": t["accent_dark"],
            "h1":          t["text"],
            "h2":          t["text2"],
            "h3":          t["accent"],
            "hr":          t["border2"],
            "link":        t["accent"],
            "mono":        t["font_mono"],
            "ui":          t["font_ui"],
        }


# ── Module-level convenience ──────────────────────────────────

def get_engine() -> ThemeEngine:
    """Shortcut to get the singleton ThemeEngine."""
    return ThemeEngine.instance()
