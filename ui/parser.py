"""ui/parser.py — BissiParser core.

Parses LLM output into a language-agnostic AST.
Renderers (html.py, rich_text.py) turn that AST into their target format.

Supported syntax
  ``` fenced code blocks (with optional language)
  `  inline code
  **bold**, *italic*, ~~strikethrough~~
  # H1  ## H2  ### H3  #### H4
  - / *  unordered lists
  1.     ordered lists
  ---    horizontal rule
  [label](url) links
  | table | rows |
  $$...$$ / $...$ LaTeX → Unicode math (super/subscripts)
  Plain paragraphs

Streaming-safe: unclosed fences are flagged with is_partial=True.
No external dependencies.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ── AST node types ────────────────────────────────────────────────────────────

@dataclass
class TextNode:
    """A run of plain text with optional inline formatting."""
    text: str

@dataclass
class BoldNode:
    text: str

@dataclass
class ItalicNode:
    text: str

@dataclass
class StrikeNode:
    text: str

@dataclass
class InlineCodeNode:
    text: str

@dataclass
class LinkNode:
    label: str
    url: str

# Inline = one of the above
Inline = TextNode | BoldNode | ItalicNode | StrikeNode | InlineCodeNode | LinkNode


@dataclass
class ParagraphNode:
    inlines: list[Inline]

@dataclass
class HeadingNode:
    level: int          # 1-4
    inlines: list[Inline]

@dataclass
class HRNode:
    pass

@dataclass
class CodeBlockNode:
    lang: str           # normalised (e.g. "python"), "" if none
    raw_lang: str       # original label
    code: str
    is_partial: bool = False

@dataclass
class UListNode:
    items: list[list[Inline]]

@dataclass
class OListNode:
    items: list[list[Inline]]

@dataclass
class TableNode:
    headers: list[list[Inline]]
    rows: list[list[list[Inline]]]

@dataclass
class SpacerNode:
    pass

Block = (ParagraphNode | HeadingNode | HRNode | CodeBlockNode
         | UListNode | OListNode | TableNode | SpacerNode)


@dataclass
class ParseResult:
    blocks:     list[Block]
    has_code:   bool      = False
    languages:  list[str] = field(default_factory=list)
    is_partial: bool      = False


# ── Language aliases ──────────────────────────────────────────────────────────

_LANG_ALIASES: dict[str, str] = {
    "py":      "python",
    "python3": "python",
    "rs":      "rust",
    "js":      "javascript",
    "ts":      "typescript",
    "sh":      "bash",
    "shell":   "bash",
    "yml":     "yaml",
    "md":      "markdown",
    "c++":     "cpp",
    "c#":      "csharp",
}


def _normalize_lang(lang: str) -> str:
    raw = (lang or "").strip().lower()
    return _LANG_ALIASES.get(raw, raw)


# ── Math: super/subscript conversion ─────────────────────────────────────────

_SUPERSCRIPTS = str.maketrans(
    "0123456789+-=()abcdefghijklmnoprstuvwxyz",
    "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ"
)
_SUBSCRIPTS = str.maketrans(
    "0123456789aehijklmnoprstuvx",
    "₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"
)


def _apply_scripts(text: str) -> str:
    """Convert ^{...}/^x and _{...}/_x to Unicode super/subscripts."""
    def _rep(m: re.Match, table: dict) -> str:
        body = m.group(1) if m.group(1) else m.group(2)
        return body.translate(table)
    text = re.sub(r"\^\{([^}]*)\}|\^([^\s{])",  lambda m: _rep(m, _SUPERSCRIPTS), text)
    text = re.sub(r"_\{([^}]*)\}|_([^\s{_])",   lambda m: _rep(m, _SUBSCRIPTS),   text)
    return text


_LATEX_BLOCK_RE  = re.compile(r"\$\$[^$]*?\$\$", re.DOTALL)
_LATEX_INLINE_RE = re.compile(r"\$[^$\n]+?\$")


def _strip_latex(text: str) -> str:
    """Strip LaTeX delimiters and apply Unicode math conversion."""
    text = text.replace(r"\$", "$")
    text = _LATEX_BLOCK_RE.sub(lambda m: _apply_scripts(m.group(0)[2:-2].strip()), text)
    text = _LATEX_INLINE_RE.sub(lambda m: _apply_scripts(m.group(0)[1:-1]), text)
    text = _apply_scripts(text)
    return text


# ── Inline parser ─────────────────────────────────────────────────────────────

_INLINE_RE = re.compile(
    r"(`[^`\n]+`)"                              # 1: `code`
    r"|(\*\*(?:[^*]|\*(?!\*))+\*\*)"           # 2: **bold**
    r"|(__(?:[^_]|_(?!_))+__)"                 # 3: __bold__
    r"|(\*(?:[^*\n])+\*)"                      # 4: *italic*
    r"|(_(?:[^_\n])+_)"                        # 5: _italic_
    r"|(~~(?:[^~]|~(?!~))+~~)"                # 6: ~~strike~~
    r"|(\[([^\]]+)\]\((https?://[^\)]+)\))",   # 7: [label](url)
)


def _parse_inline(raw: str) -> list[Inline]:
    nodes: list[Inline] = []
    last = 0
    for m in _INLINE_RE.finditer(raw):
        before = raw[last:m.start()]
        if before:
            nodes.append(TextNode(before))
        g = m.group(0)
        if m.group(1):
            nodes.append(InlineCodeNode(g[1:-1]))
        elif m.group(2) or m.group(3):
            nodes.append(BoldNode(g[2:-2]))
        elif m.group(4) or m.group(5):
            nodes.append(ItalicNode(g[1:-1]))
        elif m.group(6):
            nodes.append(StrikeNode(g[2:-2]))
        elif m.group(7):
            nodes.append(LinkNode(label=m.group(8), url=m.group(9)))
        last = m.end()
    tail = raw[last:]
    if tail:
        nodes.append(TextNode(tail))
    return nodes


# ── Block-level regexes ───────────────────────────────────────────────────────

_RE_H4        = re.compile(r"^####\s+(.*)")
_RE_H3        = re.compile(r"^###\s+(.*)")
_RE_H2        = re.compile(r"^##\s+(.*)")
_RE_H1        = re.compile(r"^#\s+(.*)")
_RE_HR        = re.compile(r"^-{3,}\s*$")
_RE_UL        = re.compile(r"^[-*•]\s+(.*)")
_RE_OL        = re.compile(r"^\d+[.)]\s+(.*)")
_TABLE_SEP_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$")
_FENCE_OPEN_RE = re.compile(r"^\s*(```+|~~~+)\s*([A-Za-z0-9_+\-#.]*)\s*$")


def _split_table_row(line: str) -> list[str]:
    row = line.strip().lstrip("|").rstrip("|")
    return [c.strip() for c in row.split("|")]


def _is_closing_fence(line: str, marker: str) -> bool:
    stripped = line.strip()
    return stripped.startswith(marker) and set(stripped) == {marker[0]} and len(stripped) >= len(marker)


def _looks_like_table(lines: list[str], i: int) -> bool:
    return (i + 1 < len(lines)
            and "|" in lines[i]
            and bool(_TABLE_SEP_RE.match(lines[i + 1])))


# ── Block parser (non-code segments) ─────────────────────────────────────────

def _parse_block_segment(text: str) -> list[Block]:
    """Parse a segment of text that contains no fenced code blocks."""
    lines = text.split("\n")
    blocks: list[Block] = []
    ul_items: list[list[Inline]] = []
    ol_items: list[list[Inline]] = []
    para_lines: list[str] = []
    just_spaced = False

    def flush_ul():
        if ul_items:
            blocks.append(UListNode(items=list(ul_items)))
            ul_items.clear()

    def flush_ol():
        if ol_items:
            blocks.append(OListNode(items=list(ol_items)))
            ol_items.clear()

    def flush_para():
        if para_lines:
            merged = " ".join(l.strip() for l in para_lines if l.strip())
            if merged:
                blocks.append(ParagraphNode(inlines=_parse_inline(merged)))
            para_lines.clear()

    i = 0
    while i < len(lines):
        line = lines[i]

        # Table
        if _looks_like_table(lines, i):
            flush_ul(); flush_ol(); flush_para()
            headers_raw = _split_table_row(line)
            i += 2
            rows_raw: list[list[str]] = []
            while i < len(lines):
                if not lines[i].strip() or "|" not in lines[i]:
                    break
                rows_raw.append(_split_table_row(lines[i]))
                i += 1
            blocks.append(TableNode(
                headers=[_parse_inline(h) for h in headers_raw],
                rows=[[_parse_inline(c) for c in row] for row in rows_raw],
            ))
            just_spaced = False
            continue

        # HR
        if _RE_HR.match(line):
            flush_ul(); flush_ol(); flush_para()
            blocks.append(HRNode())
            just_spaced = False
            i += 1
            continue

        # Headings (check H4 before H3 before H2 before H1)
        for level, regex in ((4, _RE_H4), (3, _RE_H3), (2, _RE_H2), (1, _RE_H1)):
            m = regex.match(line)
            if m:
                flush_ul(); flush_ol(); flush_para()
                blocks.append(HeadingNode(level=level, inlines=_parse_inline(m.group(1))))
                just_spaced = False
                i += 1
                break
        else:
            # Unordered list
            m = _RE_UL.match(line)
            if m:
                flush_ol(); flush_para()
                ul_items.append(_parse_inline(m.group(1)))
                just_spaced = False
                i += 1
                continue

            # Ordered list
            m = _RE_OL.match(line)
            if m:
                flush_ul(); flush_para()
                ol_items.append(_parse_inline(m.group(1)))
                just_spaced = False
                i += 1
                continue

            # Blank line
            if not line.strip():
                flush_ul(); flush_ol(); flush_para()
                if not just_spaced:
                    blocks.append(SpacerNode())
                    just_spaced = True
                i += 1
                continue

            # Normal line → accumulate paragraph
            flush_ul(); flush_ol()
            para_lines.append(line)
            just_spaced = False
            i += 1
            continue

        continue  # heading matched — already incremented i

    flush_ul()
    flush_ol()
    flush_para()

    # Trim leading/trailing spacers
    while blocks and isinstance(blocks[0], SpacerNode):
        blocks.pop(0)
    while blocks and isinstance(blocks[-1], SpacerNode):
        blocks.pop()

    return blocks


def _parse_with_fences(text: str) -> tuple[list[Block], bool, list[str], bool]:
    """Parse text while tolerating malformed or partial fenced code blocks."""
    lines = text.split("\n")
    blocks: list[Block] = []
    has_code = False
    languages: list[str] = []
    is_partial = False
    text_buffer: list[str] = []
    i = 0

    def flush_text_buffer() -> None:
        if text_buffer:
            blocks.extend(_parse_block_segment("\n".join(text_buffer)))
            text_buffer.clear()

    while i < len(lines):
        line = lines[i]
        open_match = _FENCE_OPEN_RE.match(line)
        if not open_match:
            text_buffer.append(line)
            i += 1
            continue

        flush_text_buffer()

        marker = open_match.group(1)
        raw_lang = open_match.group(2).strip()
        lang = _normalize_lang(raw_lang)
        code_lines: list[str] = []
        i += 1
        closed = False

        while i < len(lines):
            candidate = lines[i]
            if _is_closing_fence(candidate, marker):
                closed = True
                i += 1
                break
            code_lines.append(candidate)
            i += 1

        code = "\n".join(code_lines)
        if not closed:
            is_partial = True
            code = f"{code}\n▌" if code else "▌"

        blocks.append(
            CodeBlockNode(
                lang=lang,
                raw_lang=raw_lang,
                code=code,
                is_partial=not closed,
            )
        )
        has_code = True
        if lang and lang not in languages:
            languages.append(lang)

    flush_text_buffer()
    return blocks, has_code, languages, is_partial


# ── Main parse entry point ────────────────────────────────────────────────────

def parse(text: str) -> ParseResult:
    """Parse a complete or partial LLM message into a ParseResult AST."""
    if not text:
        return ParseResult(blocks=[])

    # Keep LaTeX delimiters for frontend KaTeX rendering; only unescape \$.
    text = text.replace(r"\$", "$")
    # Models sometimes escape code fences as \`\`\`; normalize them back.
    text = text.replace(r"\`\`\`", "```")
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse excessive blank lines

    blocks, has_code, languages, is_partial = _parse_with_fences(text)

    return ParseResult(blocks=blocks, has_code=has_code,
                       languages=languages, is_partial=is_partial)


def parse_streaming(accumulated: str) -> ParseResult:
    """Alias explicite pour le mode streaming token-par-token."""
    return parse(accumulated)
