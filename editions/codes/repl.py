"""Bissi Codes REPL — Rich CLI interface for developers."""

import sys
import os
import re
from pathlib import Path

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.table import Table
from rich import box
from rich.align import Align
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

    def _render_header(self):
        """Render the fixed header with logo and title."""
        # Build the title line: "Bi" (blue) + "Bissi Codes" (Codes in violet)
        logo = Text("Bi", style="bold #1E90FF")
        bissi_text = Text("Bissi ", style="white")
        codes_text = Text("Codes", style="bold #A855F7")
        
        # Combine with proper spacing
        title_line = logo + Text("  ") + bissi_text + codes_text
        
        return Panel(
            Align.left(title_line),
            border_style="#1DB854",
            expand=True,
            padding=(0, 1)
        )

    def _render_status_bar(self):
        """Render the status bar with model and token info."""
        model_info = Text(f"Model: {self.agent.model}", style="cyan")
        tokens_info = Text("(21%)", style="dim")
        spacer = Text(" " * 40)
        
        # Right-align tokens
        line = Group(model_info, spacer, tokens_info)
        return line

    def _render_footer(self):
        """Render the bottom footer with commands."""
        left = Text("/ commands · ? help", style="dim")
        right = Text("Claude Haiku 4.5", style="dim")
        
        # Create a simple footer with spacing
        return Group(
            Text("─" * 80, style="#1DB854"),
            left
        )

    def run(self):
        """Main REPL loop with polished UI."""
        # Render header
        self.console.print(self._render_header())
        self.console.print()

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
        
        # Print footer on exit
        self.console.print()
        self.console.print(self._render_footer())

    def _handle_command(self, cmd: str) -> bool:
        cmd = cmd.strip().lower()
        if cmd in ['/exit', '/quit', 'exit', 'quit']:
            return True
        elif cmd == '/new':
            self.agent.start_conversation()
            self.console.print("[dim]Nouvelle conversation démarrée.[/dim]")
            self.console.print()
        elif cmd == '/model':
            self.console.print(f"[bold]Modèle actif:[/bold] [cyan]{self.agent.model}[/cyan]")
            self.console.print()
        elif cmd == '/history':
            history = self.agent.get_conversation_history()
            if not history:
                self.console.print("[dim]Aucun historique pour cette conversation.[/dim]")
                self.console.print()
                return False

            self.console.print("[bold]Historique (derniers 10 messages):[/bold]")
            self.console.print()
            table = Table(box=box.SIMPLE_HEAVY, show_lines=False, header_style="bold #A855F7")
            table.add_column("Rôle", style="cyan", no_wrap=True)
            table.add_column("Message", overflow="fold")
            for item in history[-10:]:
                role = str(item.get("role", "?")).capitalize()
                content = str(item.get("content", ""))
                preview = content.replace("\n", " ")
                if len(preview) > 180:
                    preview = preview[:180] + "…"
                table.add_row(role, preview)
            self.console.print(table)
            self.console.print()
        elif cmd in ['/help', '?', '/h']:
            self.console.print()
            self.console.print("[bold #1DB854]Commandes disponibles:[/bold #1DB854]")
            self.console.print()
            
            commands_table = Table(box=box.SIMPLE, show_header=False)
            commands_table.add_column(style="cyan")
            commands_table.add_column(style="dim")
            
            commands_table.add_row("/new", "Démarrer une nouvelle conversation")
            commands_table.add_row("/model", "Afficher les infos du modèle actif")
            commands_table.add_row("/history", "Afficher l'historique récent (10 derniers)")
            commands_table.add_row("/help, ?", "Afficher cette aide")
            commands_table.add_row("/exit", "Quitter Bissi Codes")
            
            self.console.print(commands_table)
            self.console.print()
        else:
            self.console.print(f"[yellow]Commande inconnue: {cmd}[/yellow]")
            self.console.print("[dim]Tape /help ou ? pour l'aide.[/dim]")
            self.console.print()
        return False

    def _process_input(self, text: str):
        """Process user input and stream response with live rendering."""
        full_response = ""
        current_markdown = ""
        
        # Show thinking indicator
        with self.console.status("[bold #1DB854]Thinking...[/bold #1DB854]", spinner="dots"):
            try:
                # Collect response
                def on_chunk(chunk: str):
                    nonlocal full_response, current_markdown
                    full_response += chunk
                    current_markdown += chunk

                def on_tool_start(name: str, args: any):
                    pass  # Silent tool execution

                def on_tool_done(name: str, result: any):
                    pass

                def on_thinking(msg: str):
                    pass

                self.agent.process_request(
                    text,
                    on_chunk=on_chunk,
                    on_tool_start=on_tool_start,
                    on_tool_done=on_tool_done,
                    on_thinking=on_thinking
                )
            except Exception as e:
                self.console.print(f"[bold red]✗ Erreur:[/bold red] {e}")
                self.console.print()
                return

        # Render full response with live update
        with Live(console=self.console, refresh_per_second=12, vertical_overflow="visible") as live:
            rendered = self._render_markdown(full_response)
            live.update(rendered)

        self.console.print()
        self.console.print(Text("─" * 80, style="#1DB854"))
        self.console.print()

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
