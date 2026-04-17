"""BissiParser — Markdown → PyQt6 RichText HTML.

Converts LLM responses from BISSI to HTML that QLabel can render
natively via Qt.TextFormat.RichText.

Supported syntax:
  ``` fenced code blocks (with optional language)
  `  inline code
  **bold**, *italic*, ~~strikethrough~~
  # H1  ## H2  ### H3  #### H4
  - / *  unordered lists
  1.     ordered lists
  ---    horizontal rule
  [label](url) links
  Plain paragraphs with preserved line breaks

Streaming-safe: handles unclosed code blocks with a live cursor ▌.
No external dependencies.
"""
from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass, field


# ── Palette (injectée depuis le thème) ────────────────────────
_C: dict[str, str] = {
    "code_bg":    "#f8f8f6",
    "code_text":  "#2C2C2A",
    "code_border":"#e8e8e8",
    "inline_bg":  "#EEEDFE",
    "inline_text":"#3C3489",
    "h1":         "#1a1a1a",
    "h2":         "#2C2C2A",
    "h3":         "#534AB7",
    "hr":         "#e8e8e8",
    "link":       "#534AB7",
    "mono":       "JetBrains Mono,Fira Code,Consolas,Monospace",
    "ui":         "Inter,Segoe UI,Helvetica Neue,Arial,sans-serif",
}


def configure(colors: dict) -> None:
    """Injecte la palette du thème BISSI dans le parser."""
    _C.update(colors)


# ── Résultat ──────────────────────────────────────────────────

@dataclass
class ParseResult:
    html:       str
    has_code:   bool       = False
    languages:  list[str]  = field(default_factory=list)
    is_partial: bool       = False


# ── Inline parser ─────────────────────────────────────────────
#
# Principe : on parcourt le texte une seule fois avec un pattern combiné.
# Les parties qui ne matchent pas sont HTML-échappées.
# Les parties qui matchent sont traitées individuellement (sans ré-échapper).

_INLINE_RE = re.compile(
    r'(`[^`\n]+`)'                              # groupe 1 : inline code
    r'|(\*\*(?:[^*]|\*(?!\*))+\*\*)'           # groupe 2 : **bold**
    r'|(__(?:[^_]|_(?!_))+__)'                 # groupe 3 : __bold__
    r'|(\*(?:[^*\n])+\*)'                      # groupe 4 : *italic*
    r'|(_(?:[^_\n])+_)'                        # groupe 5 : _italic_
    r'|(~~(?:[^~]|~(?!~))+~~)'                 # groupe 6 : ~~strike~~
    r'|(\[([^\]]+)\]\((https?://[^\)]+)\))',   # groupe 7 : [label](url)
)


def _inline(raw: str) -> str:
    """Convertit le texte brut (non-échappé) en HTML inline."""
    result: list[str] = []
    last = 0

    for m in _INLINE_RE.finditer(raw):
        # Texte avant le match → échapper
        result.append(_html.escape(raw[last:m.start()], quote=False))

        g = m.group(0)

        if m.group(1):                          # `code`
            code = g[1:-1]
            result.append(
                f'<code style="background:{_C["inline_bg"]};'
                f'color:{_C["inline_text"]};'
                f'font-family:{_C["mono"]};'
                f'font-size:12px;padding:1px 5px;border-radius:3px;">'
                f'{_html.escape(code, quote=False)}</code>'
            )

        elif m.group(2) or m.group(3):          # **bold** / __bold__
            inner = g[2:-2]
            result.append(f'<b>{_html.escape(inner, quote=False)}</b>')

        elif m.group(4) or m.group(5):          # *italic* / _italic_
            inner = g[1:-1]
            result.append(f'<i>{_html.escape(inner, quote=False)}</i>')

        elif m.group(6):                        # ~~strike~~
            inner = g[2:-2]
            result.append(f'<s>{_html.escape(inner, quote=False)}</s>')

        elif m.group(7):                        # [label](url)
            label = _html.escape(m.group(8), quote=False)
            url   = _html.escape(m.group(9), quote=False)
            result.append(
                f'<a href="{url}" style="color:{_C["link"]};'
                f'text-decoration:none;">{label}</a>'
            )

        last = m.end()

    result.append(_html.escape(raw[last:], quote=False))
    return "".join(result)


# ── Rendu d'un bloc de code ───────────────────────────────────

def _code_block(code: str, lang: str = "") -> str:
    norm_lang = _normalize_lang(lang)
    if norm_lang in {"latex", "tex", "math"}:
        return _latex_block(code)

    lines = code.split("\n")
    # Supprimer lignes vides en début/fin
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    html_lines: list[str] = []
    for line in lines:
        spaces = len(line) - len(line.lstrip(" "))
        body   = _html.escape(line.lstrip(" "), quote=False)
        html_lines.append("&nbsp;" * spaces + body)

    body_html = "<br>".join(html_lines)

    ui = _C["ui"]
    badge = (
        f'<span style="float:right;font-size:10px;color:#aaa;'
        f'font-family:{ui};">{_html.escape(norm_lang or lang)}</span>'
        if (norm_lang or lang) else ""
    )
    code_tag = (
        f'<pre style="margin:0;white-space:pre-wrap;">'
        f'<code class="language-{_html.escape(norm_lang)}">{body_html}</code>'
        f'</pre>'
        if norm_lang
        else f'<pre style="margin:0;white-space:pre-wrap;"><code>{body_html}</code></pre>'
    )

    return (
        f'<table width="100%" cellpadding="0" cellspacing="0"'
        f' style="margin:6px 0;">'
        f'<tr><td style="'
        f'background:{_C["code_bg"]};'
        f'border:1px solid {_C["code_border"]};'
        f'border-radius:6px;'
        f'padding:10px 12px;'
        f'font-family:{_C["mono"]};'
        f'font-size:12px;'
        f'color:{_C["code_text"]};'
        f'line-height:1.6;">'
        f'{badge}{code_tag}</td></tr></table>'
    )


def _latex_block(code: str) -> str:
    expr = code.strip()
    if not expr:
        expr = r"\text{ }"
    safe = _html.escape(expr, quote=False)
    return (
        f'<div class="bissi-latex-block" style="margin:8px 0;'
        f'padding:8px 10px;border:1px solid {_C["code_border"]};'
        f'border-radius:6px;background:{_C["code_bg"]};">'
        f'$$\n{safe}\n$$'
        f'</div>'
    )


_LANG_ALIASES = {
    "py": "python",
    "python3": "python",
    "rs": "rust",
    "js": "javascript",
    "ts": "typescript",
    "sh": "bash",
    "shell": "bash",
    "yml": "yaml",
    "md": "markdown",
    "c++": "cpp",
    "c#": "csharp",
}


def _normalize_lang(lang: str) -> str:
    raw = (lang or "").strip().lower()
    if not raw:
        return ""
    return _LANG_ALIASES.get(raw, raw)


# ── Parser de bloc (hors code) ────────────────────────────────

_RE_H3 = re.compile(r'^###\s+(.*)')
_RE_H4 = re.compile(r'^####\s+(.*)')
_RE_H2 = re.compile(r'^##\s+(.*)')
_RE_H1 = re.compile(r'^#\s+(.*)')
_RE_HR = re.compile(r'^-{3,}\s*$')
_RE_UL = re.compile(r'^[-*•]\s+(.*)')
_RE_OL = re.compile(r'^\d+\.\s+(.*)')
_TABLE_SEP_RE = re.compile(r'^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$')


def _split_table_row(line: str) -> list[str]:
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [cell.strip() for cell in row.split("|")]


def _looks_like_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    header = lines[index]
    separator = lines[index + 1]
    return "|" in header and _TABLE_SEP_RE.match(separator) is not None


def _render_table(headers: list[str], rows: list[list[str]]) -> str:
    width = len(headers)
    for row in rows:
        width = max(width, len(row))
    if width == 0:
        return ""

    padded_headers = headers + [""] * (width - len(headers))
    padded_rows = [row + [""] * (width - len(row)) for row in rows]
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
        f'<th style="{th_style}">{_inline(cell)}</th>' for cell in padded_headers
    )
    body_html = "".join(
        "<tr>"
        + "".join(f'<td style="{td_style}">{_inline(cell)}</td>' for cell in row)
        + "</tr>"
        for row in padded_rows
    )

    return (
        f'<table style="{table_style}">'
        f'<thead><tr>{head_html}</tr></thead>'
        f'<tbody>{body_html}</tbody>'
        f'</table>'
    )


def _render_block(text: str) -> str:
    """Convertit un segment de texte (sans bloc code) en HTML."""
    lines = text.split("\n")
    out:  list[str] = []
    ul_buf: list[str] = []
    ol_buf: list[str] = []
    para_buf: list[str] = []
    i = 0
    just_spaced = False

    def _flush_ul():
        if ul_buf:
            items = "".join(
                f'<li style="margin:2px 0;">{x}</li>' for x in ul_buf
            )
            out.append(
                f'<ul style="margin:3px 0 3px 16px;padding:0;">{items}</ul>'
            )
            ul_buf.clear()

    def _flush_ol():
        if ol_buf:
            items = "".join(
                f'<li style="margin:2px 0;">{x}</li>' for x in ol_buf
            )
            out.append(
                f'<ol style="margin:3px 0 3px 16px;padding:0;">{items}</ol>'
            )
            ol_buf.clear()

    def _flush_para():
        if para_buf:
            merged = " ".join(x.strip() for x in para_buf if x.strip())
            if merged:
                out.append(
                    f'<p style="margin:3px 0;line-height:1.6;">'
                    f'{_inline(merged)}</p>'
                )
            para_buf.clear()

    while i < len(lines):
        line = lines[i]

        if _looks_like_table_start(lines, i):
            _flush_ul(); _flush_ol(); _flush_para()
            headers = _split_table_row(line)
            i += 2
            rows: list[list[str]] = []
            while i < len(lines):
                row_line = lines[i]
                if not row_line.strip() or "|" not in row_line:
                    break
                rows.append(_split_table_row(row_line))
                i += 1
            table_html = _render_table(headers, rows)
            if table_html:
                out.append(table_html)
            just_spaced = False
            continue

        # Horizontal rule
        if _RE_HR.match(line):
            _flush_ul(); _flush_ol(); _flush_para()
            out.append(
                f'<hr style="border:none;border-top:1px solid'
                f' {_C["hr"]};margin:6px 0;">'
            )
            just_spaced = False
            i += 1
            continue

        # #### H4
        m = _RE_H4.match(line)
        if m:
            _flush_ul(); _flush_ol(); _flush_para()
            out.append(
                f'<p style="font-size:12px;font-weight:600;'
                f'color:{_C["h3"]};margin:6px 0 2px;">'
                f'{_inline(m.group(1))}</p>'
            )
            just_spaced = False
            i += 1
            continue

        # ### H3
        m = _RE_H3.match(line)
        if m:
            _flush_ul(); _flush_ol(); _flush_para()
            out.append(
                f'<p style="font-size:13px;font-weight:600;'
                f'color:{_C["h3"]};margin:7px 0 2px;">'
                f'{_inline(m.group(1))}</p>'
            )
            just_spaced = False
            i += 1
            continue

        # ## H2
        m = _RE_H2.match(line)
        if m:
            _flush_ul(); _flush_ol(); _flush_para()
            out.append(
                f'<p style="font-size:15px;font-weight:600;'
                f'color:{_C["h2"]};margin:8px 0 2px;">'
                f'{_inline(m.group(1))}</p>'
            )
            just_spaced = False
            i += 1
            continue

        # # H1
        m = _RE_H1.match(line)
        if m:
            _flush_ul(); _flush_ol(); _flush_para()
            out.append(
                f'<p style="font-size:17px;font-weight:700;'
                f'color:{_C["h1"]};margin:8px 0 3px;">'
                f'{_inline(m.group(1))}</p>'
            )
            just_spaced = False
            i += 1
            continue

        # Unordered list
        m = _RE_UL.match(line)
        if m:
            _flush_ol(); _flush_para()
            ul_buf.append(_inline(m.group(1)))
            just_spaced = False
            i += 1
            continue

        # Ordered list
        m = _RE_OL.match(line)
        if m:
            _flush_ul(); _flush_para()
            ol_buf.append(_inline(m.group(1)))
            just_spaced = False
            i += 1
            continue

        # Ligne vide -> un seul espacement visuel entre blocs
        if not line.strip():
            _flush_ul(); _flush_ol(); _flush_para()
            if not just_spaced:
                out.append('<div style="height:4px;"></div>')
                just_spaced = True
            i += 1
            continue

        # Ligne normale : accumuler en paragraphe compact
        _flush_ul(); _flush_ol()
        para_buf.append(line)
        just_spaced = False
        i += 1

    _flush_ul()
    _flush_ol()
    _flush_para()

    spacer = '<div style="height:4px;"></div>'
    while out and out[-1] == spacer:
        out.pop()
    while out and out[0] == spacer:
        out.pop(0)

    return "".join(out)


# ── Parser principal ──────────────────────────────────────────

_FENCE_RE = re.compile(
    r'```([A-Za-z0-9_+\-#.]*)\n(.*?)(?:\n```|(?=```))',
    re.DOTALL,
)


def parse(text: str) -> ParseResult:
    """Parse un message complet ou partiel de Bissi.

    Args:
        text: Texte brut sorti par le LLM (Markdown).

    Returns:
        ParseResult avec le HTML final prêt pour QLabel.
    """
    if not text:
        return ParseResult(html="")

    # LLM output frequently escapes math delimiters as \$...\$.
    # Normalize before markdown parsing so KaTeX can render formulas.
    text = text.replace(r"\$", "$")
    # Avoid giant visual gaps from excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    parts:     list[str] = []
    has_code               = False
    languages: list[str] = []
    is_partial             = False
    last                   = 0

    for m in _FENCE_RE.finditer(text):
        before = text[last:m.start()]
        if before:
            parts.append(_render_block(before))

        lang = _normalize_lang(m.group(1).strip())
        code = m.group(2)
        raw  = m.group(0)

        # Bloc fermé si le raw se termine par ```
        closed = raw.rstrip().endswith("```")
        if not closed:
            is_partial = True

        parts.append(_code_block(code, lang))
        has_code = True
        if lang and lang not in languages:
            languages.append(lang)

        last = m.end()

    tail = text[last:]
    if tail:
        # Détecter un ``` ouvert sans fermeture
        fence_count = tail.count("```")
        if fence_count % 2 == 1:
            is_partial    = True
            fence_pos     = tail.rfind("```")
            before_fence  = tail[:fence_pos]
            partial_raw   = tail[fence_pos + 3:]

            first_nl = partial_raw.find("\n")
            if first_nl != -1:
                partial_lang = _normalize_lang(partial_raw[:first_nl].strip())
                partial_body = partial_raw[first_nl + 1:]
            else:
                partial_lang = _normalize_lang(partial_raw.strip())
                partial_body = ""

            if before_fence:
                parts.append(_render_block(before_fence))
            # Curseur de streaming
            parts.append(_code_block(partial_body + "▌", partial_lang))
            has_code = True
        else:
            parts.append(_render_block(tail))

    return ParseResult(
        html       = "".join(parts),
        has_code   = has_code,
        languages  = languages,
        is_partial = is_partial,
    )


def parse_streaming(accumulated: str) -> ParseResult:
    """Alias explicite pour le mode streaming token-par-token."""
    return parse(accumulated)
