"""ui/renderers/rich_text.py — Rich/Textual renderer (CLI REPL).

Takes a ParseResult from ui/parser.py and produces a flat list of
Rich renderables (Text, Markdown, Table) for use with RichLog.write().
"""
from __future__ import annotations

import os
import re
import sys

from rich.console import Group
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table
from rich import box as rich_box
from markdown_it import MarkdownIt

try:
    from mdit_py_plugins.dollarmath import dollarmath_plugin
except Exception:  # optional dependency
    dollarmath_plugin = None

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


def _supports_unicode() -> bool:
    if os.environ.get("BISSI_CODES_ASCII", "").strip().lower() in {"1", "true", "yes", "on"}:
        return False
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "─•▌".encode(encoding)
        return True
    except Exception:
        return False


_UNICODE_OK = _supports_unicode()


def _glyph(unicode_char: str, ascii_char: str) -> str:
    return unicode_char if _UNICODE_OK else ascii_char


def configure(colors: dict) -> None:
    """Override default palette (e.g. from theme config)."""
    _C.update(colors)


_MD_VALIDATOR = MarkdownIt("commonmark")
if dollarmath_plugin is not None:
    _MD_VALIDATOR.use(dollarmath_plugin)

_MATH_RE = re.compile(r"\$\$([^$]+)\$\$|\$([^$\n]+)\$")
_SUPERSCRIPTS = str.maketrans(
    "0123456789+-=()abcdefghijklmnoprstuvwxyz",
    "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ",
)
_SUBSCRIPTS = str.maketrans(
    "0123456789aehijklmnoprstuvx",
    "₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ",
)
_LATEX_SYMBOLS = {
    r"\omega": "ω",
    r"\Omega": "Ω",
    r"\infty": "∞",
    r"\pi": "π",
    r"\theta": "θ",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\Delta": "Δ",
    r"\sqrt{-1}": "√-1",
    r"\cdot": "·",
    r"\times": "×",
    r"\int": "∫",
    r"\sum": "∑",
}


def _clean_markdown(text: str) -> str:
    """Light markdown normalization for terminal rendering stability."""
    cleaned = (text or "").replace("\r\n", "\n").replace(r"\$", "$")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"^(#{1,6})(\S)", r"\1 \2", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^([*+-]|\d+\.)([^\s])", r"\1 \2", cleaned, flags=re.MULTILINE)
    # Force tokenization once with markdown-it + math plugin so malformed blocks
    # are handled consistently before our AST parser transforms to Rich renderables.
    try:
        _MD_VALIDATOR.parse(cleaned)
    except Exception:
        # Keep the terminal renderer usable on malformed model output.
        pass
    return cleaned


# ── Inline → Rich Text ───────────────────────────────────────────────────────

def _apply_scripts(text: str) -> str:
    text = re.sub(
        r"\^\{([^}]*)\}|\^([^\s{])",
        lambda m: (m.group(1) if m.group(1) is not None else m.group(2)).translate(_SUPERSCRIPTS),
        text,
    )
    text = re.sub(
        r"_\{([^}]*)\}|_([^\s{_])",
        lambda m: (m.group(1) if m.group(1) is not None else m.group(2)).translate(_SUBSCRIPTS),
        text,
    )
    return text


def _latex_to_unicode(expr: str) -> str:
    out = expr.strip()
    out = out.replace("\\\\", "\\")
    out = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)", out)
    out = out.replace(r"\mathcal{F}", "ℱ")
    out = out.replace(r"\{", "{").replace(r"\}", "}")
    for src, dst in _LATEX_SYMBOLS.items():
        out = out.replace(src, dst)
    out = _apply_scripts(out)
    return out


def _append_with_math(target: Text, raw: str, base_style: str) -> None:
    raw = raw.replace(r"\$", "$")
    last = 0
    for m in _MATH_RE.finditer(raw):
        if m.start() > last:
            target.append(raw[last:m.start()], style=base_style)
        expr = m.group(1) if m.group(1) is not None else m.group(2)
        target.append(_latex_to_unicode(expr), style=f"bold {_C['yellow']}")
        last = m.end()
    if last < len(raw):
        target.append(raw[last:], style=base_style)

def _inline_to_text(nodes, base_style: str = "white") -> Text:
    result = Text()
    for node in nodes:
        if isinstance(node, TextNode):
            _append_with_math(result, node.text, base_style)
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
        return [Text(_glyph("─", "-") * 64, style=f"dim {_C['blue']}")]

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
            t = Text(f"  {_glyph('•', '*')} ", style=f"dim {_C['blue']}")
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
        code = "\n".join(lines) if lines else ""
        if code:
            syntax = Syntax(
                code,
                block.lang or "text",
                theme="monokai",
                line_numbers=False,
                word_wrap=False,
                indent_guides=False,
                background_color="#0d0d0d",
            )
            renderables.append(syntax)
        elif block.is_partial:
            renderables.append(Text(f"  {_glyph('▌', '|')}", style=f"{_C['white']} on #0d0d0d"))
        return renderables

    if isinstance(block, TableNode):
        width = max(
            len(block.headers),
            max((len(r) for r in block.rows), default=0),
            1,
        )
        table_box = rich_box.SIMPLE_HEAVY if _UNICODE_OK else rich_box.ASCII
        tbl = Table(box=table_box, show_lines=False,
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
    try:
        cleaned = _clean_markdown(text)
        result = parse(cleaned)
        out: list = []
        for block in result.blocks:
            out.extend(_render_block(block))
        if _should_fallback_to_markdown(cleaned, result, out):
            return [Markdown(cleaned, hyperlinks=False, code_theme="monokai")]
    except Exception:
        out = []
        for line in (text or "").splitlines() or [""]:
            out.append(Text(line))
    # Strip trailing empty Text items so └ lands on real content
    while out and isinstance(out[-1], Text) and not out[-1].plain.strip():
        out.pop()
    return out


def render_streaming(accumulated: str) -> list:
    """Streaming-friendly variant with gentler fallback on incomplete markdown."""
    cleaned = _clean_markdown(accumulated)
    try:
        result = parse_streaming(cleaned)
        out: list = []
        for block in result.blocks:
            out.extend(_render_block(block))
        if out:
            return out
    except Exception:
        pass
    return [Text(line) for line in (accumulated or "").splitlines() or [""]]


def _should_fallback_to_markdown(cleaned: str, result, out: list) -> bool:
    """Use Rich Markdown for structures our home-grown AST still handles poorly."""
    if not cleaned.strip():
        return False
    if any(token in cleaned for token in ("\n> ", "\n-   ", "\n    - ", "\n    1.", "<details>", "</details>")):
        return True
    if "|" in cleaned and "\n" in cleaned and any(isinstance(item, Table) for item in out):
        return False
    if len(result.blocks) <= 1 and cleaned.count("\n") >= 6 and any(marker in cleaned for marker in ("#", "-", "*", "1.", "```", "~~~")):
        return True
    return False
