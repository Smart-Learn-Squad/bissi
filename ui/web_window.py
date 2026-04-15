"""WebWindow — QWebEngineView + QWebChannel main window for BISSI.

Replaces the old PyQt6 widget-based UI with a Chromium-rendered HTML frontend.
The bridge (BissiBridge) is exposed to JS as window.bissi via QWebChannel.
"""
from __future__ import annotations

import sys
from pathlib import Path

from typing import TYPE_CHECKING
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineScript
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QApplication, QMainWindow

from core.config import DEFAULT_CONFIG
from ui.bridge import BissiBridge
from ui.themes import get_engine

if TYPE_CHECKING:
    from agent import BissiAgent

# Default path to the web assets folder (fallback)
_DEFAULT_WEB_DIR = Path(__file__).parent / "web"


class WebWindow(QMainWindow):
    """Main window: a full-screen QWebEngineView loading the HTML frontend."""

    def __init__(self, web_dir: Path | str | None = None, agent: BissiAgent | None = None):
        super().__init__()
        self.setWindowTitle("Bissi")
        self.resize(DEFAULT_CONFIG.ui.window_width, DEFAULT_CONFIG.ui.window_height)
        self.setMinimumSize(DEFAULT_CONFIG.ui.min_width, DEFAULT_CONFIG.ui.min_height)

        # ── WebEngine view ────────────────────────────────────
        self._view = QWebEngineView(self)
        self.setCentralWidget(self._view)

        page = self._view.page()

        # Allow local file access (for app.css, app.js, qwebchannel.js)
        settings = page.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True
        )

        # ── QWebChannel ───────────────────────────────────────
        self._channel = QWebChannel(page)
        self._bridge  = BissiBridge(agent=agent, parent=self)
        self._channel.registerObject("bissi", self._bridge)
        page.setWebChannel(self._channel)

        # Inject the OFFICIAL qwebchannel.js from Qt's internal resources.
        # This is always in sync with the Qt version installed — no manual copy needed.
        self._inject_qwebchannel(page)

        # ── Load index.html ───────────────────────────────────
        web_dir = Path(web_dir) if web_dir else _DEFAULT_WEB_DIR
        index = web_dir / "index.html"
        self._view.load(QUrl.fromLocalFile(str(index)))

        # Forward theme changes from engine → bridge → JS
        engine = get_engine()
        engine.theme_changed.connect(self._bridge.themeChanged)

    @staticmethod
    def _inject_qwebchannel(page) -> None:
        """Inject Qt's built-in qwebchannel.js before any page script runs."""
        from PyQt6.QtWebEngineCore import QWebEngineScript
        from PyQt6.QtCore import QFile, QIODevice

        # Qt ships qwebchannel.js as an internal Qt resource
        f = QFile(":/qtwebchannel/qwebchannel.js")
        if f.open(QIODevice.OpenModeFlag.ReadOnly):
            src = bytes(f.readAll()).decode()
            f.close()

            script = QWebEngineScript()
            script.setName("qwebchannel")
            script.setSourceCode(src)
            script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
            script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
            script.setRunsOnSubFrames(False)
            page.scripts().insert(script)


def run_web():
    """Entry point: launch BISSI in WebEngine mode."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    engine = get_engine()
    engine.apply("light")

    win = WebWindow()
    win.show()
    sys.exit(app.exec())
