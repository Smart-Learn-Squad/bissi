from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text

from ui.parser import CodeBlockNode, HRNode, TextNode, UListNode, parse
from ui.renderers import rich_text
from ui.renderers.rich_text import render


def test_parser_handles_unclosed_fence_as_partial_code_block():
    result = parse("Avant\n```python\nprint('x')")

    code_blocks = [block for block in result.blocks if isinstance(block, CodeBlockNode)]
    assert result.is_partial is True
    assert len(code_blocks) == 1
    assert code_blocks[0].lang == "python"
    assert code_blocks[0].is_partial is True
    assert "▌" in code_blocks[0].code


def test_parser_supports_tilde_fences():
    result = parse("~~~js\nconsole.log('ok')\n~~~")

    code_blocks = [block for block in result.blocks if isinstance(block, CodeBlockNode)]
    assert len(code_blocks) == 1
    assert code_blocks[0].lang == "javascript"


def test_rich_renderer_never_crashes_on_broken_markdown():
    rendered = render("**bold\n\n```python\nprint('ok')")
    assert rendered
    assert any(isinstance(item, Text) for item in rendered)


def test_rich_renderer_uses_syntax_for_code_blocks():
    rendered = render("```python\nprint('ok')\n```")
    assert any(isinstance(item, Syntax) for item in rendered)


def test_rich_renderer_can_fallback_to_rich_markdown_for_nested_structures():
    rendered = render("- parent\n    - child\n> quote")
    assert any(isinstance(item, Markdown) for item in rendered)


def test_rich_renderer_ascii_fallback_for_hr_and_lists(monkeypatch):
    monkeypatch.setattr(rich_text, "_UNICODE_OK", False)

    hr_items = rich_text._render_block(HRNode())
    list_items = rich_text._render_block(UListNode(items=[[TextNode("item")]]))

    assert hr_items[0].plain.startswith("-")
    assert "*" in list_items[0].plain


def test_rich_renderer_ascii_fallback_for_partial_code_marker(monkeypatch):
    monkeypatch.setattr(rich_text, "_UNICODE_OK", False)

    node = CodeBlockNode(lang="", raw_lang="", code="", is_partial=True)
    rendered = rich_text._render_block(node)

    assert any(isinstance(item, Text) and "|" in item.plain for item in rendered)


def test_rich_renderer_supports_ascii_env_override(monkeypatch):
    monkeypatch.setenv("BISSI_CODES_ASCII", "1")
    assert rich_text._supports_unicode() is False
