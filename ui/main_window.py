"""Main window for BISSI application."""

import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPalette, QColor

from core.config import DEFAULT_CONFIG
from ui.styles.theme import Theme
from ui.themes import ThemeEngine, get_engine
from ui.renderers.html import configure as _configure_html_renderer
from ui.components import (
    Sidebar,
    ChatPanel,
    FileExplorer,
    RightPanel,
    StatusBar,
    TitleBar,
)
from agent import BissiAgent


# ─── AGENT WORKER ─────────────────────────────────────────────
# All software logic lives in BissiAgent (agent.py).
# AgentWorker is a thin Qt thread bridge: it calls agent.process_request()
# and forwards every event to the UI via signals.
# ─────────────────────────────────────────────────────────────

def _format_tool_result(result: str, max_len: int = 100) -> str:
    """Converts a raw JSON tool result into a readable string for the UI."""
    import json
    try:
        data = json.loads(result)
        if not isinstance(data, dict):
            return result[:max_len]

        # Success with explicit message
        if data.get("message"):
            return data["message"][:max_len]

        # File listing
        if "items" in data:
            items = data["items"]
            names = [i.get("name", "?") for i in items[:6]]
            suffix = f" +{len(items)-6}" if len(items) > 6 else ""
            return f"{len(items)} item(s): {', '.join(names)}{suffix}"

        # Search results
        if "results" in data:
            r = data["results"]
            if isinstance(r, list):
                return f"{len(r)} result(s) found"

        # Error
        if data.get("error"):
            return f"Error: {data['error'][:80]}"

        # Direct output (python_runner, safe_operator)
        if "output" in data:
            out = str(data["output"])
            lines = out.strip().splitlines()
            preview = lines[0] if lines else out
            suffix = f" (+{len(lines)-1} lines)" if len(lines) > 1 else ""
            return (preview[:80] + suffix)[:max_len]

        # Excel / CSV columns
        if "columns" in data:
            cols = data["columns"][:5]
            total = data.get("total_rows", "?")
            return f"{total} rows · columns: {', '.join(str(c) for c in cols)}"

        # Generic success
        if data.get("success"):
            return "✓ OK"

        return result[:max_len]

    except (json.JSONDecodeError, TypeError):
        return result[:max_len] if len(result) > max_len else result


_READ_TOOLS = frozenset({
    'read_word', 'read_excel', 'read_pptx',
    'read_pdf', 'read_text_file',
})


def _args_display(args) -> str:
    """Format tool args as a short human-readable string for the UI."""
    if isinstance(args, dict):
        for key in ('file_path', 'path', 'source', 'operation', 'query', 'code'):
            if key in args:
                val = str(args[key])
                return f"({val[:60]}{'…' if len(val) > 60 else ''})"
        return str(args)[:80]
    return str(args)[:80]


class AgentWorker(QThread):
    """QThread wrapper around BissiAgent.process_request().

    Signals
    -------
    token_received(str)    — streamed text token from the LLM
    tool_started(str, str) — tool name + formatted args (before execution)
    tool_done(str, str)    — tool name + result string (after execution)
    thinking(str)          — status / thinking messages
    file_opened(str)       — absolute path of a file read by the agent
    finished_ok(str)       — final full response when done
    error_occurred(str)    — exception message
    interrupted()          — user stopped the run
    """
    token_received = pyqtSignal(str)
    tool_started = pyqtSignal(str, str)
    tool_done = pyqtSignal(str, str)
    thinking = pyqtSignal(str)
    file_opened = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    interrupted = pyqtSignal()

    def __init__(self, user_input: str, agent: BissiAgent):
        super().__init__()
        self.user_input = user_input
        self.agent = agent
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            result = self.agent.process_request(
                self.user_input,
                on_chunk=self._on_chunk,
                on_tool_start=self._on_tool_start,
                on_tool_done=self._on_tool_done,
                on_thinking=self._on_thinking,
                should_stop=lambda: self._stop,
            )
            if self._stop:
                self.interrupted.emit()
            else:
                self.finished_ok.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _on_chunk(self, token: str):
        self.token_received.emit(token)

    def _on_tool_start(self, name: str, args):
        self.tool_started.emit(name, _args_display(args))
        if name in _READ_TOOLS and isinstance(args, dict):
            fp = args.get('file_path') or args.get('path', '')
            if fp:
                self.file_opened.emit(fp)

    def _on_tool_done(self, name: str, result: str):
        self.tool_done.emit(name, _format_tool_result(result))

    def _on_thinking(self, msg: str):
        self.thinking.emit(msg)


# ─── MAIN WINDOW ──────────────────────────────────────────────
class BissiWindow(QMainWindow):
    """Main application window."""

    def __init__(self, engine: ThemeEngine = None):
        super().__init__()
        self._engine = engine or get_engine()
        # Backward-compat: Theme wrapper reads tokens from the engine
        self.theme = Theme()
        self.setWindowTitle("Bissi")
        self.resize(DEFAULT_CONFIG.ui.window_width, DEFAULT_CONFIG.ui.window_height)
        self.setMinimumSize(DEFAULT_CONFIG.ui.min_width, DEFAULT_CONFIG.ui.min_height)

        # Sync parser with current theme
        _configure_html_renderer(self._engine.parser_colors())
        self._engine.theme_changed.connect(self._on_theme_changed)

        # Agent
        self._agent = BissiAgent(model=DEFAULT_CONFIG.OLLAMA_MODEL)
        self._worker = None
        self._current_bubble = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        self.title_bar = TitleBar(self.theme)
        root.addWidget(self.title_bar)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(
            "QSplitter::handle { background: #e8e8e8; }"
        )

        self.sidebar = Sidebar(self.theme)
        self.chat = ChatPanel(self.theme)
        self.right = RightPanel(str(Path.home()), self.theme)

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.chat)
        splitter.addWidget(self.right)
        splitter.setSizes([220, 560, 320])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(2, False)

        root.addWidget(splitter, stretch=1)

        self.status_bar = StatusBar(self.theme)
        root.addWidget(self.status_bar)

        # Connections
        self.chat.message_submitted.connect(self._on_submit)
        self.chat.interrupt_requested.connect(self._on_interrupt)
        self.title_bar.theme_toggle_requested.connect(
            lambda: self._engine.toggle()
        )
        self.right.explorer.file_selected.connect(
            lambda p: self.right.open_file(p)
        )

        # Welcome message
        self.chat.add_system_msg(
            f"Bissi prêt · {DEFAULT_CONFIG.OLLAMA_MODEL} · tape un message pour démarrer",
            color=self.theme.C['text_dim']
        )

    def _on_submit(self, text: str):
        self.chat.add_user_message(text)

        self.chat.lock()
        self.title_bar.set_busy(True)
        self.status_bar.set_busy(True)

        self._current_bubble = self.chat.start_agent_message()

        self._worker = AgentWorker(text, self._agent)
        self._worker.token_received.connect(self._on_token)
        self._worker.tool_started.connect(self._on_tool_started)
        self._worker.tool_done.connect(self._on_tool_done)
        self._worker.thinking.connect(self._on_thinking)
        self._worker.file_opened.connect(self._on_file_opened)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.interrupted.connect(self._on_interrupted)
        self._worker.start()

    def _on_token(self, tok: str):
        self.chat.append_token_to_current(tok)

    def _on_tool_started(self, name: str, args: str):
        self.chat.add_tool_to_current(name, args)

    def _on_tool_done(self, name: str, result: str):
        if self._current_bubble:
            self._current_bubble.add_tool_line(name, "", result)

    def _on_thinking(self, msg: str):
        """Display routing info in the status bar."""
        if not msg:
            return
        # Expected format: "→ gemma4:e2b · score 0.72"
        if "gemma4:" in msg:
            try:
                parts = msg.split("·")
                model = parts[0].replace("→", "").strip()
                score = float(parts[1].replace("score", "").strip())
                self.status_bar.set_routing(model, score)
                self.title_bar.set_model(model)
            except (IndexError, ValueError):
                pass

    def _on_file_opened(self, path: str):
        """Open file in the right-panel editor when the agent reads it."""
        if not os.path.isabs(path):
            for root_dir in [str(Path.home()), "."]:
                candidate = os.path.join(root_dir, path)
                if os.path.isfile(candidate):
                    path = candidate
                    break
        if os.path.isfile(path):
            self.right.open_file(path, by_agent=True)

    def _on_done(self, full: str):
        history_len = len(self._agent.get_conversation_history())
        turn_count = history_len // 2
        self.sidebar.set_memory(turn_count)
        self.status_bar.set_memory(turn_count)
        self._unlock()

    def _on_error(self, msg: str):
        self.chat.add_system_msg(f"✗ {msg}", color=self.theme.C['red'])
        self._unlock()

    def _on_interrupted(self):
        self.chat.add_system_msg("⊘ interrompu", color=self.theme.C['amber'])
        self._unlock()

    def _on_interrupt(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()

    def _on_theme_changed(self, name: str):
        """Resync parser colors when theme switches."""
        _configure_html_renderer(self._engine.parser_colors())
        self.title_bar.set_theme_label(name)

    def _unlock(self):
        self.chat.unlock()
        self.title_bar.set_busy(False)
        self.status_bar.set_busy(False)
        self._current_bubble = None


def create_palette(theme: Theme) -> QPalette:
    """Create application color palette."""
    pal = QPalette()
    for role, color in [
        (QPalette.ColorRole.Window, theme.C["bg"]),
        (QPalette.ColorRole.WindowText, theme.C["text"]),
        (QPalette.ColorRole.Base, theme.C["bg_white"]),
        (QPalette.ColorRole.Text, theme.C["text"]),
        (QPalette.ColorRole.Button, theme.C["bg"]),
        (QPalette.ColorRole.ButtonText, theme.C["text"]),
        (QPalette.ColorRole.Highlight, theme.C["purple"]),
        (QPalette.ColorRole.HighlightedText, "#ffffff"),
    ]:
        pal.setColor(role, QColor(color))
    return pal
