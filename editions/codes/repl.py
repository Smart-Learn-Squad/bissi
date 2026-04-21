"""Bissi Codes REPL

Layout:
  ┌─────────────────────────────────────┐
  │  [Scrollable RichLog — messages]     │
  │  ● You › message                     │
  │  ● Bissi                             │
  │    └ response...                     │
  ├─────────────────────────────────────┤
  │  bissi @ ~/path ›  [input]           │  ← fixed bottom
  └─────────────────────────────────────┘
"""

import difflib
import os
import re
import signal
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import RichLog, Input, Static, LoadingIndicator, ListView, ListItem
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual import work, on

from rich.text import Text
from rich.markdown import Markdown
from rich.console import Group
from rich.table import Table
from rich import box
from rich.cells import cell_len

from agent import BissiAgent
from ui.renderers.rich_text import render as _render_rich


# ─── Persistence ──────────────────────────────────────────────────────────────
_HISTORY_FILE = Path.home() / ".bissi" / "codes_history"


def _load_history() -> list[str]:
    """Load persisted command history (newest first)."""
    try:
        _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if _HISTORY_FILE.exists():
            lines = _HISTORY_FILE.read_text(encoding="utf-8").splitlines()
            return [l for l in reversed(lines) if l.strip()][:500]
    except Exception as exc:
        import sys
        print(f"Warning: failed to load history from {_HISTORY_FILE}: {exc}", file=sys.stderr)
    return []


def _save_history(history: list[str]) -> None:
    """Persist command history to disk (oldest first)."""
    try:
        _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Keep at most 500 entries, oldest first on disk
        entries = list(reversed(history[:500]))
        _HISTORY_FILE.write_text("\n".join(entries) + "\n", encoding="utf-8")
    except Exception as exc:
        import sys
        print(f"Warning: failed to save history to {_HISTORY_FILE}: {exc}", file=sys.stderr)


# ─── Palette ──────────────────────────────────────────────────────────────────
C_BLUE    = "#1E90FF"
C_PURPLE  = "#534AB7"
C_GREEN   = "#1DB854"
C_YELLOW  = "#F5A623"
C_RED     = "#FF5555"
C_DIM     = "dim"
C_WHITE   = "white"


BISSI_LOGO = (
    "██████╗ ██╗███████╗███████╗██╗\n"
    "██╔══██╗██║██╔════╝██╔════╝██║\n"
    "██████╔╝██║███████╗███████╗██║\n"
    "██╔══██╗██║╚════██║╚════██║██║\n"
    "██████╔╝██║███████║███████║██║\n"
    "╚═════╝ ╚═╝╚══════╝╚══════╝╚═╝"
)

ASCII_LOGO = (
    "BBBB  III  SSSS  SSSS  III\n"
    "B   B  I  S     S       I \n"
    "BBBB   I   SSS   SSS    I \n"
    "B   B  I      S     S   I \n"
    "BBBB  III SSSS  SSSS  III"
)


def _supports_unicode() -> bool:
    if os.environ.get("BISSI_CODES_ASCII", "").strip().lower() in {"1", "true", "yes", "on"}:
        return False
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "┌┐└┘│─●├⠋".encode(encoding)
        return True
    except Exception:
        return False


_UNICODE_OK = _supports_unicode()


def _glyph(unicode_char: str, ascii_char: str) -> str:
    return unicode_char if _UNICODE_OK else ascii_char


def _branch(last: bool) -> str:
    return f"  {_glyph('└' if last else '├', '+')} "


def _pipe() -> str:
    return f"  {_glyph('│', '|')}  "


def _ellipsis() -> str:
    return _glyph("…", "...")


# ─── Tool call formatting ─────────────────────────────────────────────
def _format_tool_call(name: str, args: dict) -> str:
    """Format tool call like Bash(cmd) or Read(path=...)."""
    if not args:
        return f"{name}()"

    formatted = []
    for k, v in args.items():
        v_str = str(v)
        if len(v_str) > 40:
            v_str = v_str[:37] + "..."
        formatted.append(f"{k}={v_str!r}")

    return f"{name}({', '.join(formatted)})"


# ─── CSS ──────────────────────────────────────────────────────────────────────
APP_CSS = """
Screen {
    layout: vertical;
    background: #0d0d0d;
}

#log-area {
    height: 1fr;
    border: solid #1E3A5F;
    padding: 0 1;
}

#log-area:focus,
#log-area > .:focus {
    border: solid #1E3A5F;
}

/* Hide scrollbar but keep scrolling functional */
#log-area ScrollBar {
    width: 0;
    display: none;
}

#log-area > .virtual-scroll {
    scrollbar-size: 0 0;
}

#status-bar {
    height: 1;
    background: #111111;
    padding: 0 2;
    color: #888888;
}

#input-row {
    height: 3;
    border-top: solid #534AB7;
    background: #0d0d0d;
    padding: 0 1;
    align: left middle;
}

#prompt-label {
    width: auto;
    height: 1;
    padding: 0 0;
    content-align: left middle;
}

#user-input {
    border: none;
    height: 1;
    padding: 0 0;
    background: transparent;
    color: #ffffff;
}

#user-input:focus {
    border: none;
}

#loading {
    width: auto;
    height: 1;
    display: none;
    color: #1DB854;
    padding: 0 1;
}

#loading.active {
    display: block;
}

#suggest-box {
    display: none;
    height: auto;
    max-height: 8;
    background: #1a1a2e;
    border: solid #534AB7;
    border-bottom: none;
    padding: 0 1;
}

#suggest-box.active {
    display: block;
}

.suggest-item {
    height: 1;
    padding: 0 1;
    color: #888888;
}

.suggest-item.-selected {
    background: #2a2a4e;
    color: #ffffff;
}
"""


def _copy_to_clipboard(text: str) -> bool:
    """Try to copy text to the system clipboard.

    Attempts xclip then xsel. Returns True on success, False if unavailable.
    """
    import subprocess
    for cmd in (
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
    ):
        try:
            result = subprocess.run(cmd, input=text.encode(), capture_output=True)
            if result.returncode == 0:
                return True
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return False


# ─── App ──────────────────────────────────────────────────────────────────────
class BissiApp(App):
    CSS = APP_CSS

    BINDINGS = [
        Binding("ctrl+c", "app.quit", "Quit", show=False),
        Binding("ctrl+l", "clear_log",  "Clear", show=False),
        Binding("ctrl+v", "paste_image", "Paste Image", show=False),
    ]

    def __init__(self, agent: BissiAgent, no_splash: bool = False):
        super().__init__()
        self.agent = agent
        self._busy = False
        self._history: list[str] = _load_history()
        self._hist_idx = -1
        self._no_splash = no_splash
        self._splash_visible = False
        self._last_response = ""
        self._pending_images: list[str] = []  # Images en attente d'analyse

    COMMANDS = [
        ("/new",     "Nouvelle conversation"),
        ("/cd",      "Changer le répertoire courant"),
        ("/model",   "Afficher le modèle actif"),
        ("/history", "Afficher l'historique récent"),
        ("/copy",    "Copier la dernière réponse"),
        ("/attach",  "Ajouter une image"),
        ("/analyze", "Analyser les images en attente"),
        ("/help",    "Afficher l'aide"),
        ("/exit",    "Quitter Bissi Codes"),
    ]

    # ── Layout ────────────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield RichLog(id="log-area", highlight=True, markup=False, wrap=False)
        yield Vertical(id="suggest-box")
        with Horizontal(id="input-row"):
            yield Static(self._prompt_text(), id="prompt-label")
            yield Input(placeholder="", id="user-input")
            yield Static(f"{_glyph('⠋', '...')} réflexion", id="loading")

    def _prompt_text(self) -> str:
        cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
        return f"[bold {C_PURPLE}]bissi[/] [dim]@ {cwd} ›[/] "

    # ── Mount ─────────────────────────────────────────────────────────────────
    def on_mount(self) -> None:
        log = self.query_one(RichLog)
        if not self._no_splash:
            self._print_splash(log)
            self._splash_visible = True
        log.scroll_end(animate=False)
        self.query_one("#user-input", Input).focus()
        self._suggest_idx = -1
        # Install signal handlers for graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._handle_signal)
            except (OSError, ValueError):
                # Some environments (non-main thread / unsupported platform) cannot install
                # process signal handlers; ignore and continue startup.
                pass

    def _handle_signal(self, signum, frame) -> None:
        """Persist state then exit cleanly on SIGINT/SIGTERM."""
        _save_history(self._history)
        self.exit()

    # ── Suggestion box ────────────────────────────────────────────────────────
    @on(Input.Changed, "#user-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        val = event.value
        box = self.query_one("#suggest-box", Vertical)
        if val.startswith("/") and not self._busy:
            matches = [(cmd, desc) for cmd, desc in self.COMMANDS if cmd.startswith(val.lower())]
            box.remove_children()
            if matches:
                for cmd, desc in matches:
                    item = Static(
                        Text(f" {cmd:<12}", style="cyan") + Text(f"  {desc}", style=C_DIM),
                        classes="suggest-item"
                    )
                    item._cmd = cmd
                    box.mount(item)
                box.add_class("active")
                self._suggest_idx = -1
                self._update_suggest_highlight()
            else:
                box.remove_class("active")
        else:
            box.remove_class("active")
            box.remove_children()
            self._suggest_idx = -1

    def _suggest_items(self) -> list:
        return list(self.query(".suggest-item"))

    def _update_suggest_highlight(self) -> None:
        items = self._suggest_items()
        for i, item in enumerate(items):
            if i == self._suggest_idx:
                item.add_class("-selected")
            else:
                item.remove_class("-selected")

    def _accept_suggestion(self) -> None:
        items = self._suggest_items()
        if not items:
            return
        idx = self._suggest_idx if self._suggest_idx >= 0 else 0
        if idx < len(items):
            cmd = items[idx]._cmd
            inp = self.query_one("#user-input", Input)
            inp.value = cmd
            inp.cursor_position = len(cmd)
        box = self.query_one("#suggest-box", Vertical)
        box.remove_class("active")
        box.remove_children()
        self._suggest_idx = -1

    def on_key(self, event) -> None:
        box = self.query_one("#suggest-box", Vertical)
        inp = self.query_one("#user-input", Input)

        # ── History navigation (when suggest-box is closed and not busy) ──────
        if "active" not in box.classes and not self._busy:
            if event.key == "up":
                event.prevent_default()
                limit = len(self._history)
                if limit == 0:
                    return
                self._hist_idx = min(self._hist_idx + 1, limit - 1)
                inp.value = self._history[self._hist_idx]
                inp.cursor_position = len(inp.value)
                return
            elif event.key == "down":
                event.prevent_default()
                if self._hist_idx <= 0:
                    self._hist_idx = -1
                    inp.value = ""
                    return
                self._hist_idx -= 1
                inp.value = self._history[self._hist_idx]
                inp.cursor_position = len(inp.value)
                return

        if "active" not in box.classes:
            return
        items = self._suggest_items()
        if not items:
            return
        if event.key == "up":
            event.prevent_default()
            self._suggest_idx = max(0, self._suggest_idx - 1)
            self._update_suggest_highlight()
        elif event.key == "down":
            event.prevent_default()
            self._suggest_idx = min(len(items) - 1, self._suggest_idx + 1)
            self._update_suggest_highlight()
        elif event.key in ("tab", "enter"):
            if self._suggest_idx >= 0:
                event.prevent_default()
                self._accept_suggestion()
        elif event.key == "escape":
            box.remove_class("active")
            box.remove_children()
            self._suggest_idx = -1

    def _sep_width(self) -> int:
        """Dynamic separator width from terminal."""
        try:
            if hasattr(self, 'size') and self.size:
                return max(40, self.size.width - 4)
        except Exception:
            pass
        return 64

    def _print_splash(self, log: RichLog) -> None:
        splash_width = min(92, max(64, self.size.width - 8))
        W = splash_width  # alias kept for local readability

        # Compact splash: logo + title only.
        log.write(Text(_glyph("┌", "+") + _glyph("─", "-") * (W - 2) + _glyph("┐", "+"), style=f"dim {C_BLUE}"))

        logo_lines = BISSI_LOGO.split("\n")
        max_logo_width = max(cell_len(line) for line in logo_lines)
        if not _UNICODE_OK or max_logo_width > (W - 6):
            logo_lines = ASCII_LOGO.split("\n")
        for line in logo_lines:
            visible_width = cell_len(line)
            pad_left  = max(0, (W - 2 - visible_width) // 2)
            pad_right = max(0, (W - 2 - visible_width) - pad_left)
            log.write(
                Text(_glyph("│", "|"), style=f"dim {C_BLUE}") +
                Text(" " * pad_left) +
                Text(line, style=f"bold {C_BLUE}") +
                Text(" " * pad_right) +
                Text(_glyph("│", "|"), style=f"dim {C_BLUE}")
            )

        subtitle = "Codes v1.0.0"
        s_pad_l = (W - 2 - len(subtitle)) // 2
        s_pad_r = (W - 2 - len(subtitle)) - s_pad_l
        log.write(
            Text(_glyph("│", "|"), style=f"dim {C_BLUE}") +
            Text(" " * s_pad_l) +
            Text(subtitle, style=f"bold {C_WHITE}") +
            Text(" " * s_pad_r) +
            Text(_glyph("│", "|"), style=f"dim {C_BLUE}")
        )
        log.write(Text(_glyph("└", "+") + _glyph("─", "-") * (W - 2) + _glyph("┘", "+"), style=f"dim {C_BLUE}"))
        log.write(Text(""))
        log.write(Text("Tape /help pour démarrer.", style=C_DIM))
        log.write(Text(f"{_branch(last=False)}Astuce: /new pour repartir à zéro", style=C_DIM))
        log.write(Text(f"{_branch(last=False)}Astuce: /history pour revoir le fil récent", style=C_DIM))
        log.write(Text(f"{_branch(last=True)}Astuce: /copy pour copier la dernière réponse", style=C_DIM))
        log.write(Text(""))

    # ── Input handling ────────────────────────────────────────────────────────
    @on(Input.Submitted, "#user-input")
    def handle_submit(self, event: Input.Submitted) -> None:
        if self._busy:
            return
        text = event.value.strip()
        event.input.clear()
        if not text:
            return

        self._history.insert(0, text)
        self._hist_idx = -1
        _save_history(self._history)

        log = self.query_one(RichLog)
        self._clear_splash_if_needed(log)

        if text.startswith("/"):
            self._handle_command(text, log)
            return

        # ── User bubble (Claude Code style) ───────────────────────────────
        log.write(Text(""))
        log.write(
            Text(f"{_glyph('●', '*')} ", style=f"bold {C_GREEN}") +
            Text(text, style=C_WHITE)
        )

        self._set_busy(True)
        self._run_agent(text)

    def _clear_splash_if_needed(self, log: RichLog) -> None:
        if self._splash_visible:
            log.clear()
            self._splash_visible = False

    # ── Agent worker ──────────────────────────────────────────────────────────
    @work(thread=True)
    def _run_agent(self, text: str) -> None:
        full_response = ""
        tool_events: list[str] = []

        try:
            def on_chunk(chunk: str):
                nonlocal full_response
                full_response += chunk

            def _format_tool_call(name: str, args: dict) -> str:
                """Format tool call like Bash(cmd) or Read(path=...)"""
                if not args:
                    return f"{name}()"

                # Format args for display
                formatted = []
                for k, v in args.items():
                    v_str = str(v)
                    if len(v_str) > 40:
                        v_str = v_str[:37] + "..."
                    formatted.append(f"{k}={v_str!r}")

                return f"{name}({', '.join(formatted)})"

            def on_tool_start(name: str, args):
                tool_events.append(name)
                # Format as ● ToolName(args)
                call_str = _format_tool_call(name, args or {})
                self.call_from_thread(
                    self.query_one(RichLog).write,
                    Text(f"{_glyph('●', '*')} ", style=f"bold {C_YELLOW}") +
                    Text(f"{call_str}", style=C_WHITE)
                )

            def on_tool_done(name: str, result):
                # Parse result for nice display
                import json
                try:
                    parsed = json.loads(result or "{}")
                    success = parsed.get("success", False)
                    msg = parsed.get("message") or parsed.get("path") or ""
                    error = parsed.get("error")
                except:
                    success = False
                    msg = ""
                    error = None

                # Status icon
                if success:
                    status_icon = _glyph("✓", "v")
                    icon_style = f"bold {C_GREEN}"
                    status_text = f"{status_icon} completed"
                else:
                    status_icon = _glyph("✗", "x")
                    icon_style = f"bold {C_RED}"
                    status_text = f"{status_icon} failed"

                # Add details
                details = ""
                if msg:
                    details = f" — {msg}"
                elif error:
                    details = f" — {error[:80]}"
                elif success:
                    details = ""

                self.call_from_thread(
                    self.query_one(RichLog).write,
                    Text(_pipe(), style=f"dim {C_BLUE}") +
                    Text(status_text, style=icon_style) +
                    (Text(details, style=C_DIM) if details else Text(""))
                )

            def on_thinking(msg: str):
                pass

            # Process pending images if any
            text = self._process_pending_images(text)

            self.agent.process_request(
                text,
                on_chunk=on_chunk,
                on_tool_start=on_tool_start,
                on_tool_done=on_tool_done,
                on_thinking=on_thinking,
            )

        except Exception as exc:
            self.call_from_thread(self._write_error, str(exc))
            self.call_from_thread(self._set_busy, False)
            return

        self.call_from_thread(self._write_response, full_response)
        self.call_from_thread(self._set_busy, False)

    # ── Response rendering ────────────────────────────────────────────────────
    def _write_response(self, response: str) -> None:
        log = self.query_one(RichLog)
        self._last_response = response.strip()
        log.write(Text(""))
        log.write(
            Text(f"{_glyph('●', '*')} ", style=f"bold {C_BLUE}") +
            Text("Bissi", style=f"bold {C_BLUE}")
        )

        renderables = _render_rich(response.strip())
        lines_total = len(renderables)

        for i, item in enumerate(renderables):
            is_last = i == lines_total - 1
            branch = f"  {_glyph('└', '+')} " if is_last else f"  {_glyph('│', '|')} "
            branch_style = f"dim {C_BLUE}"

            if isinstance(item, Text):
                if not item.plain.strip():
                    log.write(Text(f"  {_glyph('│', '|')}", style=branch_style))
                else:
                    log.write(Text(branch, style=branch_style) + item)
            elif isinstance(item, Table):
                log.write(Text(branch, style=branch_style))
                log.write(item)
            else:
                log.write(Text(branch, style=branch_style))
                log.write(item)

        log.write(Text(""))
        log.write(Text(_glyph("─", "-") * self._sep_width(), style=C_DIM))
        log.write(Text(""))

    def _write_error(self, error: str) -> None:
        log = self.query_one(RichLog)
        log.write(Text(""))
        log.write(
            Text(f"{_glyph('●', '*')} ", style=f"bold {C_RED}") +
            Text("Erreur", style=f"bold {C_RED}")
        )
        log.write(
            Text(f"  {_glyph('└', '+')} ", style=C_DIM) +
            Text(error, style=C_RED)
        )
        log.write(Text(""))
        log.write(Text(_glyph("─", "-") * self._sep_width(), style=C_DIM))
        log.write(Text(""))


    # ── Commands ──────────────────────────────────────────────────────────────
    def _handle_command(self, cmd: str, log: RichLog) -> None:
        parts = cmd.strip().split(None, 1)
        cmd_lower = parts[0].lower()
        cmd_arg = parts[1] if len(parts) > 1 else ""

        log.write(Text(""))
        log.write(
            Text(f"{_glyph('●', '*')} ", style=f"bold cyan") +
            Text(cmd, style="cyan")
        )

        if cmd_lower in ("/exit", "/quit"):
            log.write(
                Text(_branch(last=True), style=C_DIM) +
                Text("À bientôt !", style=C_DIM)
            )
            _save_history(self._history)
            self.exit()
            return

        elif cmd_lower == "/new":
            self.agent.start_conversation()
            log.write(
                Text(_branch(last=True), style=C_DIM) +
                Text("Nouvelle conversation démarrée.", style=f"dim {C_GREEN}")
            )

        elif cmd_lower == "/cd":
            target = cmd_arg.strip() or str(Path.home())
            target = os.path.expanduser(target)
            target = os.path.abspath(target)
            if not os.path.isdir(target):
                log.write(
                    Text(_branch(last=True), style=C_DIM) +
                    Text(f"Répertoire introuvable : {target}", style=C_RED)
                )
            else:
                os.chdir(target)
                label = self.query_one("#prompt-label", Static)
                label.update(self._prompt_text())
                disp = target.replace(str(Path.home()), "~")
                log.write(
                    Text(_branch(last=True), style=C_DIM) +
                    Text(f"{_glyph('→', '->')} {disp}", style=f"dim {C_GREEN}")
                )

        elif cmd_lower == "/model":
            log.write(
                Text(_branch(last=True), style=C_DIM) +
                Text("Modèle actif : ", style=C_DIM) +
                Text(self.agent.model, style=f"bold {C_BLUE}")
            )

        elif cmd_lower == "/analyze":
            if not self._pending_images:
                log.write(
                    Text(_branch(last=True), style=C_DIM) +
                    Text("Aucune image en attente. Utilise /attach <path>.", style=C_DIM)
                )
            else:
                count = len(self._pending_images)
                log.write(
                    Text(_branch(last=True), style=C_DIM) +
                    Text(f"📎 {count} image(s) prête(s) à analyser.", style=f"bold {C_GREEN}")
                )
                for img in self._pending_images:
                    log.write(Text(f"  • {Path(img).name}", style=C_DIM))

        elif cmd_lower == "/attach":
            # Use cmd_arg which already has the path
            image_path = cmd_arg.strip()
            if not image_path:
                log.write(Text("Usage: /attach <image_path>", style=C_DIM))
            else:
                self._add_pending_image(image_path)

        elif cmd_lower == "/history":
            history = self.agent.get_conversation_history()
            if not history:
                log.write(
                    Text(_branch(last=True), style=C_DIM) +
                    Text("Aucun historique pour cette conversation.", style=C_DIM)
                )
            else:
                items = history[-20:]
                for j, item in enumerate(items):
                    is_last = j == len(items) - 1
                    branch = _branch(last=is_last)
                    role = str(item.get("role", "?")).capitalize()
                    raw_content = str(item.get("content", ""))
                    content = raw_content.replace("\n", " ")[:160]
                    if len(raw_content) > 160:
                        content += _ellipsis()
                    log.write(
                        Text(branch, style=C_DIM) +
                        Text(f"[{role}] ", style="cyan") +
                        Text(content, style=C_DIM)
                    )

        elif cmd_lower == "/copy":
            if self._last_response:
                if _copy_to_clipboard(self._last_response):
                    log.write(
                        Text(_branch(last=True), style=C_DIM) +
                        Text("Copié dans le presse-papiers.", style=f"dim {C_GREEN}")
                    )
                else:
                    log.write(
                        Text(_branch(last=False), style=C_DIM) +
                        Text("Presse-papiers non disponible.", style=C_YELLOW)
                    )
                    # Display the response so the user can copy manually
                    preview = self._last_response[:400]
                    for line in preview.splitlines()[:10]:
                        log.write(Text(f"{_pipe()}{line}", style=C_DIM))
                    if len(self._last_response) > 400:
                        log.write(Text(f"{_branch(last=True)} {_ellipsis()}", style=C_DIM))
            else:
                log.write(
                    Text(_branch(last=True), style=C_DIM) +
                    Text("Aucune réponse à copier.", style=C_DIM)
                )

        elif cmd_lower in ("/help", "/?", "/h"):
            tips = [
                ("/new",     "Démarrer une nouvelle conversation"),
                ("/cd",      "Changer le répertoire courant"),
                ("/model",   "Afficher le modèle actif"),
                ("/history", "Afficher l'historique (20 derniers)"),
                ("/copy",    "Copier la dernière réponse"),
                ("/help",    "Afficher cette aide"),
                ("/exit",    "Quitter Bissi Codes"),
            ]
            for j, (c, d) in enumerate(tips):
                is_last = j == len(tips) - 1
                branch = _branch(last=is_last)
                log.write(
                    Text(branch, style=C_DIM) +
                    Text(f"{c:<12}", style="cyan") +
                    Text(f"— {d}", style=C_DIM)
                )

        else:
            # Suggest closest command on typo
            known = [c for c, _ in self.COMMANDS]
            matches = difflib.get_close_matches(cmd_lower, known, n=1, cutoff=0.6)
            if matches:
                log.write(
                    Text(_branch(last=True), style=C_DIM) +
                    Text(f"Commande inconnue : {parts[0]}  ", style=C_YELLOW) +
                    Text(f"— vouliez-vous dire ", style=C_DIM) +
                    Text(matches[0], style="cyan") +
                    Text(" ?", style=C_DIM)
                )
            else:
                log.write(
                    Text(_branch(last=True), style=C_DIM) +
                    Text(f"Commande inconnue : {parts[0]}  (tapez /help)", style=C_YELLOW)
                )

        log.write(Text(""))
        log.write(Text(_glyph("─", "-") * self._sep_width(), style=C_DIM))
        log.write(Text(""))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        loader = self.query_one("#loading", Static)
        if busy:
            loader.add_class("active")
        else:
            loader.remove_class("active")
        inp = self.query_one("#user-input", Input)
        inp.disabled = busy
        if not busy:
            inp.focus()

    def action_clear_log(self) -> None:
        """Ctrl+L — clear the log without re-printing the splash screen."""
        self.query_one(RichLog).clear()

    def action_paste_image(self) -> None:
        """Ctrl+V — paste image from clipboard (if available)."""
        try:
            # Try to get image from clipboard via pyperclip
            from pathlib import Path
            import tempfile

            # Check clipboard for image (platform-dependent)
            # For now, show a message to drop a file
            log = self.query_one(RichLog)
            log.write(Text(""))
            log.write(Text(f"📎 Drop an image file here or use /analyze <path>", style=C_DIM))
        except Exception as e:
            pass

    def _add_pending_image(self, image_path: str) -> None:
        """Add an image to pending analysis queue."""
        path = Path(image_path)
        if not path.exists():
            return

        valid_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}
        if path.suffix.lower() not in valid_exts:
            return

        self._pending_images.append(str(path.absolute()))

        # Show confirmation
        log = self.query_one(RichLog)
        log.write(Text(f"📎 Image added: {path.name} ({len(self._pending_images)} pending)"))

    def _process_pending_images(self, text: str) -> str:
        """Process any pending images before running the agent."""
        if not self._pending_images:
            return text

        # Build image analysis prompt
        images_to_analyze = self._pending_images.copy()
        self._pending_images.clear()

        # If user just sent "analyze", analyze the images
        if text.strip().lower() in {"analyze", "décris", "describe", ""}:
            prompt = f"Analyze these {len(images_to_analyze)} image(s)."
            for img in images_to_analyze:
                prompt += f" Image: {Path(img).name}"
        else:
            # User provided a question, use it
            prompt = text

        return prompt


# ─── Public interface (unchanged from original) ────────────────────────────
class BissiREPL:
    """Drop-in replacement — same interface as before."""

    def __init__(self, agent: BissiAgent, no_splash: bool = False):
        self.agent = agent
        self.no_splash = no_splash

    def run(self) -> None:
        app = BissiApp(self.agent, no_splash=self.no_splash)
        app.run()
