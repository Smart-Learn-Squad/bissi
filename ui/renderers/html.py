"""ui/renderers/html.py — HTML renderer (PyQt6 / QLabel).

Takes a ParseResult from ui/parser.py and produces HTML.
Drop-in replacement for the old parser.parse() return value:
  result.html, result.has_code, result.languages, result.is_partial
"""
from __future__ import annotations

import html as _html
import re

from ui.parser import (
    ParseResult, Block,
    TextNode, BoldNode, ItalicNode, StrikeNode, InlineCodeNode, LinkNode,
    ParagraphNode, HeadingNode, HRNode, CodeBlockNode,
    UListNode, OListNode, TableNode, SpacerNode,
    parse, parse_streaming,
)


# ── Palette (injected from BISSI theme) ──────────────────────────────────────

_C: dict[str, str] = {
    "code_bg":    "#f8f8f6",
    "code_text":  "#222219",
    "code_border":"#e8e8e8",
    "inline_bg":  "#EEEDFE",
    "inline_text":"#3C3489",
    "h1":         "#55e326",
    "h2":         "#1BE2D5F8",
    "h3":         "#534AB7",
    "hr":         "#fffafa",
    "link":       "#258EC7",
    "mono":       "JetBrains Mono,Fira Code,Consolas,Monospace",
    "ui":         "Inter,Segoe UI,Helvetica Neue,Arial,sans-serif",
}


def configure(colors: dict) -> None:
    """Inject the BISSI theme palette into the renderer."""
    _C.update(colors)


# ── Inline rendering ─────────────────────────────────────────────────────────

def _render_inline(nodes) -> str:
    parts: list[str] = []
    for node in nodes:
        if isinstance(node, TextNode):
            parts.append(_html.escape(node.text, quote=False))
        elif isinstance(node, BoldNode):
            parts.append(f"<b>{_html.escape(node.text, quote=False)}</b>")
        elif isinstance(node, ItalicNode):
            parts.append(f"<i>{_html.escape(node.text, quote=False)}</i>")
        elif isinstance(node, StrikeNode):
            parts.append(f"<s>{_html.escape(node.text, quote=False)}</s>")
        elif isinstance(node, InlineCodeNode):
            code = _html.escape(node.text, quote=False)
            parts.append(
                f'<code style="background:{_C["inline_bg"]};'
                f'color:{_C["inline_text"]};'
                f'font-family:{_C["mono"]};'
                f'font-size:12px;padding:1px 5px;border-radius:3px;">'
                f'{code}</code>'
            )
        elif isinstance(node, LinkNode):
            label = _html.escape(node.label, quote=False)
            url   = _html.escape(node.url,   quote=False)
            parts.append(
                f'<a href="{url}" style="color:{_C["link"]};'
                f'text-decoration:none;">{label}</a>'
            )
    return "".join(parts)


# ── Code block ───────────────────────────────────────────────────────────────

def _render_code_block(node: CodeBlockNode) -> str:
    if node.lang in {"latex", "tex", "math"}:
        safe = _html.escape(node.code.strip(), quote=False)
        return (
            f'<div class="bissi-latex-block" style="margin:8px 0;'
            f'padding:8px 10px;border:1px solid {_C["code_border"]};'
            f'border-radius:6px;background:{_C["code_bg"]};">'
            f'$$\n{safe}\n$$</div>'
        )

    code_body = node.code.strip("\n")
    # Some models occasionally collapse sample code into one very long line.
    # Recover basic readability for common tutorial patterns.
    if "\n" not in code_body:
        if re.search(r"#\s*\d+\.", code_body):
            code_body = re.sub(r"\s*#\s*(\d+\.)", r"\n# \1", code_body)
        if ";" in code_body:
            code_body = re.sub(r";\s+", ";\n", code_body)
    safe_code = _html.escape(code_body, quote=False)

    ui    = _C["ui"]
    badge = (
        f'<div style="padding:6px 10px;border-bottom:1px solid {_C["code_border"]};'
        f'font-family:{ui};font-size:10px;letter-spacing:.12em;text-transform:uppercase;'
        f'color:{_C["inline_text"]};background:{_C["inline_bg"]};">'
        f'{_html.escape(node.raw_lang or node.lang)}</div>'
        if (node.raw_lang or node.lang) else ""
    )
    code_tag = (
        f'<pre style="margin:0;padding:12px 14px;overflow:auto;white-space:pre-wrap;'
        f'word-break:normal;'
        f'font-family:{_C["mono"]};font-size:12px;line-height:1.6;'
        f'color:{_C["code_text"]};background:{_C["code_bg"]};">'
        f'<code class="language-{_html.escape(node.lang)}">{safe_code}</code></pre>'
        if node.lang else
        f'<pre style="margin:0;padding:12px 14px;overflow:auto;white-space:pre-wrap;'
        f'word-break:normal;'
        f'font-family:{_C["mono"]};font-size:12px;line-height:1.6;'
        f'color:{_C["code_text"]};background:{_C["code_bg"]};"><code>{safe_code}</code></pre>'
    )
    return (
        f'<div class="bissi-code-wrap" style="margin:8px 0;border:1px solid {_C["code_border"]};'
        f'border-radius:10px;overflow:hidden;background:{_C["code_bg"]};">'
        f'{badge}{code_tag}</div>'
    )


# ── Table ────────────────────────────────────────────────────────────────────

def _render_table(node: TableNode) -> str:
    width = max(len(node.headers), max((len(r) for r in node.rows), default=0), 1)

    def pad_row(row, w):
        return row + [[]] * (w - len(row))

    th_style = (
        f'padding:7px 9px;border-bottom:1px solid {_C["code_border"]};'
        f'background:#f4f4f7;text-align:left;font-weight:600;'
        f'color:{_C["h2"]};vertical-align:top;'
    )
    td_style = (
        f'padding:7px 9px;border-top:1px solid {_C["code_border"]};'
        f'vertical-align:top;'
    )
    table_style = (
        f'width:100%;border-collapse:collapse;border:1px solid {_C["code_border"]};'
        f'border-radius:6px;overflow:hidden;margin:8px 0;'
        f'font-family:{_C["ui"]};font-size:12px;line-height:1.5;'
    )
    head_html = "".join(
        f'<th style="{th_style}">{_render_inline(cell)}</th>'
        for cell in pad_row(node.headers, width)
    )
    body_html = "".join(
        "<tr>" + "".join(
            f'<td style="{td_style}">{_render_inline(cell)}</td>'
            for cell in pad_row(row, width)
        ) + "</tr>"
        for row in node.rows
    )
    return (
        f'<table style="{table_style}">'
        f'<thead><tr>{head_html}</tr></thead>'
        f'<tbody>{body_html}</tbody>'
        f'</table>'
    )


# ── Block rendering ──────────────────────────────────────────────────────────

def _render_block(block: Block) -> str:
    if isinstance(block, SpacerNode):
        return '<div style="height:4px;"></div>'

    if isinstance(block, HRNode):
        return f'<hr style="border:none;border-top:1px solid {_C["hr"]};margin:6px 0;">'

    if isinstance(block, HeadingNode):
        color = {1: _C["h1"], 2: _C["h2"], 3: _C["h3"], 4: _C["h3"]}.get(block.level, _C["h3"])
        size  = {1: "17px",   2: "15px",   3: "13px",   4: "12px"}.get(block.level, "13px")
        weight = "700" if block.level == 1 else "600"
        margin = "8px 0 3px" if block.level <= 2 else "7px 0 2px"
        return (
            f'<p style="font-size:{size};font-weight:{weight};'
            f'color:{color};margin:{margin};">'
            f'{_render_inline(block.inlines)}</p>'
        )

    if isinstance(block, ParagraphNode):
        return (
            f'<p style="margin:3px 0;line-height:1.6;">'
            f'{_render_inline(block.inlines)}</p>'
        )

    if isinstance(block, UListNode):
        items = "".join(
            f'<li style="margin:2px 0;">{_render_inline(item)}</li>'
            for item in block.items
        )
        return f'<ul style="margin:3px 0 3px 16px;padding:0;">{items}</ul>'

    if isinstance(block, OListNode):
        items = "".join(
            f'<li style="margin:2px 0;">{_render_inline(item)}</li>'
            for item in block.items
        )
        return f'<ol style="margin:3px 0 3px 16px;padding:0;">{items}</ol>'

    if isinstance(block, CodeBlockNode):
        return _render_code_block(block)

    if isinstance(block, TableNode):
        return _render_table(block)

    return ""


# ── Public API ───────────────────────────────────────────────────────────────

class RenderResult:
    """Mirrors the old ParseResult interface for drop-in compatibility."""
    def __init__(self, html: str, has_code: bool,
                 languages: list[str], is_partial: bool):
        self.html       = html
        self.has_code   = has_code
        self.languages  = languages
        self.is_partial = is_partial


def render(text: str) -> RenderResult:
    """Parse text and return HTML. Drop-in for old parser.parse()."""
    result = parse(text)
    spacer = '<div style="height:4px;"></div>'
    parts  = [_render_block(b) for b in result.blocks]
    # Trim leading/trailing spacers
    while parts and parts[0]  == spacer: parts.pop(0)
    while parts and parts[-1] == spacer: parts.pop()
    return RenderResult(
        html       = "".join(parts),
        has_code   = result.has_code,
        languages  = result.languages,
        is_partial = result.is_partial,
    )


def render_streaming(accumulated: str) -> RenderResult:
    """Alias for streaming token-by-token mode."""
    return render(accumulated)
