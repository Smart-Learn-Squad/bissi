"""AgentWorker — QThread bridge for BissiAgent (shared by PyQt and WebEngine UIs)."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from agent import BissiAgent

_READ_TOOLS = frozenset({
    'read_word', 'read_excel', 'read_pptx',
    'read_pdf', 'read_text_file',
})


def _args_display(args) -> str:
    if isinstance(args, dict):
        for key in ('file_path', 'path', 'source', 'operation', 'query', 'code'):
            if key in args:
                val = str(args[key])
                return f"({val[:60]}{'…' if len(val) > 60 else ''})"
        return str(args)[:80]
    return str(args)[:80]


class AgentWorker(QThread):
    token_received  = pyqtSignal(str)
    tool_started    = pyqtSignal(str, str)
    tool_done       = pyqtSignal(str, str)
    thinking        = pyqtSignal(str)
    file_opened     = pyqtSignal(str)
    finished_ok     = pyqtSignal(str)
    error_occurred  = pyqtSignal(str)
    interrupted     = pyqtSignal()

    def __init__(self, user_input: str, agent: BissiAgent):
        super().__init__()
        self.user_input = user_input
        self.agent      = agent
        self._stop      = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            result = self.agent.process_request(
                self.user_input,
                on_chunk      = lambda t: self.token_received.emit(t),
                on_tool_start = self._on_tool_start,
                on_tool_done  = lambda n, r: self.tool_done.emit(n, r),
                on_thinking   = lambda m: self.thinking.emit(m),
                should_stop   = lambda: self._stop,
            )
            if self._stop:
                self.interrupted.emit()
            else:
                self.finished_ok.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _on_tool_start(self, name: str, args):
        self.tool_started.emit(name, _args_display(args))
        if name in _READ_TOOLS and isinstance(args, dict):
            fp = args.get('file_path') or args.get('path', '')
            if fp:
                self.file_opened.emit(fp)
