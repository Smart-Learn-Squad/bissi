"""BissiBridge — Python ↔ JavaScript via QWebChannel.

Exposes agent events to the web UI and receives user actions from JS.
This is the ONLY connection point between agent.py and the HTML frontend.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from agent import BissiAgent, get_agent
from core.config import DEFAULT_CONFIG
from ui.parser import configure as _configure_parser, parse as _parse_markdown, parse_streaming as _parse_streaming
from ui.themes import get_engine


class BissiBridge(QObject):
    """QWebChannel object exposed to JavaScript as `window.bissi`."""

    # ── Python → JS signals ───────────────────────────────────
    tokenReceived    = pyqtSignal(str)          # streaming token
    toolStarted      = pyqtSignal(str, str)     # name, args
    toolDone         = pyqtSignal(str, str)     # name, result
    thinkingChanged  = pyqtSignal(str)          # status / routing info
    responseFinished = pyqtSignal(str)          # full response
    errorOccurred    = pyqtSignal(str)          # error message
    interrupted      = pyqtSignal()             # user stopped
    conversationUpdated = pyqtSignal(str)       # JSON conversations list
    profileUpdated   = pyqtSignal(str)          # JSON user profile stats
    themeChanged     = pyqtSignal(str)          # theme name

    def __init__(self, agent: BissiAgent | None = None, parent=None):
        super().__init__(parent)
        self._agent  = agent or get_agent(DEFAULT_CONFIG.OLLAMA_MODEL)
        self._engine = get_engine()
        self._worker = None

        # Keep parser colors aligned with current theme for realtime rendering.
        _configure_parser(self._engine.parser_colors())

        # Forward theme changes to JS
        self._engine.theme_changed.connect(
            self._on_theme_changed
        )

    # ── JS → Python slots ─────────────────────────────────────

    @pyqtSlot(str)
    def sendMessage(self, text: str) -> None:
        """Called by JS when user submits a message."""
        from ui.agent_worker import AgentWorker

        if self._worker and self._worker.isRunning():
            return

        self._worker = AgentWorker(text, self._agent)
        self._worker.token_received.connect(self.tokenReceived)
        self._worker.tool_started.connect(self._on_tool_started)
        self._worker.tool_done.connect(self._on_tool_done)
        self._worker.thinking.connect(self._on_thinking)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.error_occurred.connect(self.errorOccurred)
        self._worker.interrupted.connect(self.interrupted)
        self._worker.start()

    @pyqtSlot()
    def stopGeneration(self) -> None:
        """Called by JS when user clicks Stop."""
        if self._worker and self._worker.isRunning():
            self._worker.stop()

    @pyqtSlot()
    def newConversation(self) -> None:
        """Start a fresh conversation."""
        self._agent.start_conversation()
        self._emit_conversations()

    @pyqtSlot(result=str)
    def getInitialData(self) -> str:
        """Called once by JS on load — returns full app state as JSON."""
        profile = self._agent._profile.stats
        convs   = self._agent.conversation_store.get_recent_conversations(10)
        return json.dumps({
            "model":         DEFAULT_CONFIG.OLLAMA_MODEL,
            "theme":         self._engine.current,
            "tokens":        self._engine.tokens,
            "profile":       profile,
            "conversations": convs,
        })

    @pyqtSlot(str)
    def applyTheme(self, name: str) -> None:
        """Switch theme from JS."""
        self._engine.apply(name)

    @pyqtSlot(result=str)
    def toggleTheme(self) -> str:
        """Toggle light/dark, return new theme name."""
        return self._engine.toggle()

    @pyqtSlot(str, result=str)
    def parseMarkdown(self, text: str) -> str:
        """Parse final markdown to themed HTML via ui/parser.py."""
        result = _parse_markdown(text)
        return json.dumps({
            "html": result.html,
            "has_code": result.has_code,
            "languages": result.languages,
            "is_partial": result.is_partial,
        })

    @pyqtSlot(str, result=str)
    def parseStreaming(self, accumulated: str) -> str:
        """Parse streaming markdown token-by-token to themed HTML."""
        result = _parse_streaming(accumulated)
        return json.dumps({
            "html": result.html,
            "has_code": result.has_code,
            "languages": result.languages,
            "is_partial": result.is_partial,
        })

    @pyqtSlot(str, result=str)
    def listDirectory(self, path: str) -> str:
        """Quick directory listing for file explorer in JS."""
        try:
            entries = []
            for e in sorted(os.scandir(path), key=lambda x: (not x.is_dir(), x.name.lower())):
                if e.name.startswith("."):
                    continue
                entries.append({
                    "name": e.name,
                    "path": e.path,
                    "is_dir": e.is_dir(),
                })
            return json.dumps({"success": True, "items": entries[:60]})
        except Exception as ex:
            return json.dumps({"success": False, "error": str(ex)})

    @pyqtSlot(str, result=str)
    def readFile(self, path: str) -> str:
        """Read file content for the editor panel."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(50_000)   # max 50KB
            ext = Path(path).suffix.lower()
            return json.dumps({
                "success": True,
                "content": content,
                "name":    Path(path).name,
                "ext":     ext,
            })
        except Exception as ex:
            return json.dumps({"success": False, "error": str(ex)})

    # ── Internal handlers ─────────────────────────────────────

    def _on_tool_started(self, name: str, args: str) -> None:
        self.toolStarted.emit(name, args)

    def _on_tool_done(self, name: str, result: str) -> None:
        from ui.main_window import _format_tool_result
        self.toolDone.emit(name, _format_tool_result(result))

    def _on_thinking(self, msg: str) -> None:
        self.thinkingChanged.emit(msg)

    def _on_done(self, full: str) -> None:
        history_len = len(self._agent.get_conversation_history())
        turn_count  = history_len // 2
        profile     = self._agent._profile.stats
        self.responseFinished.emit(json.dumps({
            "full":       full,
            "turns":      turn_count,
            "profile":    profile,
            "model":      self._agent.model,
        }))
        self._emit_conversations()

    def _emit_conversations(self) -> None:
        convs = self._agent.conversation_store.get_recent_conversations(10)
        self.conversationUpdated.emit(json.dumps(convs))

    def _on_theme_changed(self, name: str) -> None:
        _configure_parser(self._engine.parser_colors())
        self.themeChanged.emit(name)
