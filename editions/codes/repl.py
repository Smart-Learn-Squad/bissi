"""Bissi Codes REPL — Rich CLI interface for developers."""

import sys
import os
import re
from pathlib import Path
from typing import Optional

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.table import Table
from rich.status import Status
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PromptStyle

from agent import BissiAgent

class BissiREPL:
    def __init__(self, agent: BissiAgent):
        self.agent = agent
        self.console = Console()
        self.session = PromptSession(
            history=FileHistory(os.path.expanduser("~/.bissi/codes_history"))
        )
        self.style = PromptStyle.from_dict({
            'prompt': 'bold #534AB7',
            'path': '#888888',
        })

    def _get_prompt(self):
        cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
        return [
            ('class:prompt', 'bissi '),
            ('class:path', f'@ {cwd} › '),
        ]

    def run(self):
        self.console.print(Panel(
            Text("BISSI — agent local · Gemma 4 via Ollama", justify="center", style="bold purple"),
            border_style="purple"
        ))

        while True:
            try:
                user_input = self.session.prompt(self._get_prompt(), style=self.style)
                if not user_input.strip():
                    continue
                
                if user_input.startswith('/'):
                    if self._handle_command(user_input):
                        break
                    continue

                self._process_input(user_input)

            except KeyboardInterrupt:
                continue
            except EOFError:
                break

    def _handle_command(self, cmd: str) -> bool:
        cmd = cmd.strip().lower()
        if cmd in ['/exit', '/quit']:
            return True
        elif cmd == '/new':
            self.agent.start_conversation()
            self.console.print("[dim]Nouvelle conversation démarrée.[/dim]")
        elif cmd == '/help':
            self.console.print("[bold]Commandes disponibles:[/bold]")
            self.console.print("  /new     - Démarrer une nouvelle conversation")
            self.console.print("  /exit    - Quitter")
            self.console.print("  /model   - Afficher les infos du modèle")
            self.console.print("  /history - Afficher l'historique récent")
        return False

    def _process_input(self, text: str):
        full_response = ""
        current_markdown = ""
        
        with Live(console=self.console, refresh_per_second=12, vertical_overflow="visible") as live:
            def on_chunk(chunk: str):
                nonlocal full_response, current_markdown
                full_response += chunk
                current_markdown += chunk
                live.update(self._render_markdown(current_markdown))

            def on_tool_start(name: str, args: any):
                self.console.print(f"[bold green]●[/bold green] [cyan]{name}[/cyan] [dim]{args}[/dim]")

            def on_tool_done(name: str, result: any):
                # We could show a summary of the result
                pass

            def on_thinking(msg: str):
                # live.update(Text(f"Thinking: {msg}", style="dim italic"))
                pass

            try:
                self.agent.process_request(
                    text,
                    on_chunk=on_chunk,
                    on_tool_start=on_tool_start,
                    on_tool_done=on_tool_done,
                    on_thinking=on_thinking
                )
            except Exception as e:
                self.console.print(f"[bold red]Erreur:[/bold red] {e}")

        self.console.print() # spacer


    def _on_token(self, token: str):
        pass # Handle streaming

    _TABLE_SEP_RE = re.compile(r'^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$')

    @staticmethod
    def _split_table_row(line: str) -> list[str]:
        row = line.strip()
        if row.startswith("|"):
            row = row[1:]
        if row.endswith("|"):
            row = row[:-1]
        return [cell.strip() for cell in row.split("|")]

    def _is_table_separator(self, line: str) -> bool:
        return bool(self._TABLE_SEP_RE.match(line))

    def _render_table(self, headers: list[str], rows: list[list[str]]) -> Table:
        width = max([len(headers)] + [len(r) for r in rows] + [1])
        padded_headers = headers + [""] * (width - len(headers))
        padded_rows = [row + [""] * (width - len(row)) for row in rows]

        table = Table(box=box.SIMPLE_HEAVY, show_lines=False, header_style="bold magenta")
        for header in padded_headers:
            table.add_column(header or " ", overflow="fold")
        for row in padded_rows:
            table.add_row(*[cell or "" for cell in row])
        return table

    def _render_markdown(self, text: str):
        blocks = []
        lines = text.splitlines()
        buffer: list[str] = []
        in_code = False
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped.startswith("```"):
                in_code = not in_code
                buffer.append(line)
                i += 1
                continue

            if not in_code and i + 1 < len(lines) and "|" in line and self._is_table_separator(lines[i + 1]):
                if buffer:
                    blocks.append(Markdown("\n".join(buffer)))
                    buffer = []
                headers = self._split_table_row(line)
                i += 2
                rows: list[list[str]] = []
                while i < len(lines):
                    row_line = lines[i]
                    if not row_line.strip() or "|" not in row_line:
                        break
                    rows.append(self._split_table_row(row_line))
                    i += 1
                blocks.append(self._render_table(headers, rows))
                continue

            buffer.append(line)
            i += 1

        if buffer:
            blocks.append(Markdown("\n".join(buffer)))

        if not blocks:
            return Text("")
        if len(blocks) == 1:
            return blocks[0]
        return Group(*blocks)
