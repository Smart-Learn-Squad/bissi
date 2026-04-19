"""ui/renderers/rich_text.py — Rich/Textual renderer (CLI REPL).

Takes a ParseResult from ui/parser.py and produces a flat list of
Rich renderables (Text, Markdown, Table) for use with RichLog.write().
"""
from __future__ import annotations

from rich.text import Text
from rich.table import Table
from rich import box as rich_box

from ui.parser import (
    ParseResult, Block,
    TextNode, BoldNode, ItalicNode, StrikeNode, InlineCodeNode, LinkNode,
    ParagraphNode, HeadingNode, HRNode, CodeBlockNode,
    UListNode, OListNode, TableNode, SpacerNode,
    parse, parse_streaming,
)

# ── Palette ───────────────────────────────────────────────────────────────────

_C = {
    "blue":   "#1E90FF",
    "purple": "#534AB7",
    "green":  "#1DB854",
    "yellow": "#F5A623",
    "red":    "#FF5555",
    "white":  "white",
    "dim":    "dim",
}


def configure(colors: dict) -> None:
    """Override default palette (e.g. from theme config)."""
    _C.update(colors)


# ── Inline → Rich Text ───────────────────────────────────────────────────────

def _inline_to_text(nodes, base_style: str = "white") -> Text:
    result = Text()
    for node in nodes:
        if isinstance(node, TextNode):
            result.append(node.text, style=base_style)
        elif isinstance(node, BoldNode):
            result.append(node.text, style=f"bold {base_style}")
        elif isinstance(node, ItalicNode):
            result.append(node.text, style=f"italic {base_style}")
        elif isinstance(node, StrikeNode):
            result.append(node.text, style=f"strike {base_style}")
        elif isinstance(node, InlineCodeNode):
            result.append(node.text, style=f"bold {_C['purple']} on #1a1a2e")
        elif isinstance(node, LinkNode):
            result.append(node.label, style=f"underline {_C['blue']}")
    return result


# ── Block → list[renderable] ─────────────────────────────────────────────────

def _render_block(block: Block) -> list:
    """Return a list of Rich renderables for this block."""

    if isinstance(block, SpacerNode):
        return [Text("")]

    if isinstance(block, HRNode):
        return [Text("─" * 64, style=f"dim {_C['blue']}")]

    if isinstance(block, HeadingNode):
        color = {
            1: _C["green"],
            2: _C["blue"],
            3: _C["purple"],
            4: _C["yellow"],
        }.get(block.level, _C["blue"])
        prefix = "#" * block.level + " "
        t = Text(prefix, style=f"bold {color}")
        t.append_text(_inline_to_text(block.inlines, base_style=f"bold {color}"))
        return [t]

    if isinstance(block, ParagraphNode):
        return [_inline_to_text(block.inlines)]

    if isinstance(block, UListNode):
        items = []
        for item_nodes in block.items:
            t = Text("  • ", style=f"dim {_C['blue']}")
            t.append_text(_inline_to_text(item_nodes))
            items.append(t)
        return items

    if isinstance(block, OListNode):
        items = []
        for idx, item_nodes in enumerate(block.items, 1):
            t = Text(f"  {idx}. ", style=f"dim {_C['blue']}")
            t.append_text(_inline_to_text(item_nodes))
            items.append(t)
        return items

    if isinstance(block, CodeBlockNode):
        lines = block.code.split("\n")
        # Trim blank edges
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        renderables = []
        if block.lang:
            renderables.append(
                Text(f" {block.lang} ", style=f"bold {_C['purple']} on #1a1a2e")
            )
        for line in lines:
            renderables.append(Text(f"  {line}", style=f"{_C['white']} on #0d0d0d"))
        return renderables

    if isinstance(block, TableNode):
        width = max(
            len(block.headers),
            max((len(r) for r in block.rows), default=0),
            1,
        )
        tbl = Table(box=rich_box.SIMPLE_HEAVY, show_lines=False,
                    header_style=f"bold {_C['blue']}")
        for cell in block.headers:
            label = _inline_to_text(cell).plain or " "
            tbl.add_column(label, overflow="fold")
        # pad missing columns
        for _ in range(width - len(block.headers)):
            tbl.add_column(" ", overflow="fold")
        for row in block.rows:
            cells = [_inline_to_text(c).plain for c in row]
            cells += [""] * (width - len(cells))
            tbl.add_row(*cells)
        return [tbl]

    return []


# ── Public API ────────────────────────────────────────────────────────────────

def render(text: str) -> list:
    """Parse text and return a flat list of Rich renderables.

    Usage in BissiApp._write_response:
        from ui.renderers.rich_text import render
        renderables = render(response)
    """
    result = parse(text)
    out: list = []
    for block in result.blocks:
        out.extend(_render_block(block))
    # Strip trailing empty Text items so └ lands on real content
    while out and isinstance(out[-1], Text) and not out[-1].plain.strip():
        out.pop()
    return out


def render_streaming(accumulated: str) -> list:
    """Alias for streaming token-by-token mode."""
    return render(accumulated)