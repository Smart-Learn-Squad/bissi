#!/usr/bin/env python3
"""Bridge between the Rust backend and the proven Python tool implementations.

The Rust backend must not ship all office/vision/code logic (heavy native
deps). Instead it shells out to this helper with the repo's `.venv` Python.

Protocol
--------
Reads ONE JSON object per line on stdin:
    {"tool": "<name>", "args": {<canonical Rust param names>}}
Prints ONE JSON object (a `ToolResult.to_dict()`) on stdout.

The output shapes mirror `core/agent.py` `_tool_*` wrappers, so the LLM sees
exactly the same JSON as with the Python backend. Write operations run
unguarded (the Rust backend has no confirmation UI yet) and return the
`_file_result` shape (message/path/size).
"""
import json
import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # bissi-master-backend/.. == repo root
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.types import ToolResult  # noqa: E402


def _file_result(target, message):
    p = Path(target)
    size = p.stat().st_size if p.exists() and p.is_file() else None
    return ToolResult.ok(message=message, path=str(p), size=size)


def _do_read_word(args):
    from functions.office.word import DocxAgent
    agent = DocxAgent(args["file_path"])
    return ToolResult.ok(output={
        "content": agent.read_paragraphs()[:500],
        "tables_count": len(agent.read_tables()),
    })


def _do_write_word(args):
    from functions.office import word
    target = Path(args["file_path"]).expanduser()
    word.write_document(str(target), args.get("content", ""), bool(args.get("append", False)))
    return _file_result(target, f"Document saved to {target}")


def _do_read_excel(args):
    from functions.office import excel
    df = excel.read_excel(args["file_path"])
    max_rows = int(args.get("max_rows", 100))
    data = df.head(max_rows).to_dict("records")
    return ToolResult.ok(output={
        "columns": list(df.columns),
        "data": data,
        "total_rows": len(df),
    })


def _do_write_excel(args):
    import pandas as pd
    from functions.office import excel
    target = Path(args["file_path"]).expanduser()
    excel.write_excel(str(target), pd.DataFrame(args["data"]), sheet_name=args.get("sheet_name", "Sheet1"))
    return _file_result(target, f"Excel file saved to {target}")


def _do_read_pptx(args):
    from functions.office import powerpoint
    slides = powerpoint.read_presentation(args["file_path"])
    return ToolResult.ok(output={"slides": slides})


def _do_write_pptx(args):
    from functions.office import powerpoint
    target = Path(args["file_path"]).expanduser()
    presentation = powerpoint.create_presentation(args.get("title", ""))
    for slide_data in args.get("slides", []):
        presentation.add_slide(slide_data.get("title", ""), slide_data.get("content", ""))
    presentation.save(str(target))
    return _file_result(target, f"Presentation saved to {target}")


def _do_read_pdf(args):
    from functions.office import ocr
    result = ocr.smart_pdf_extract(args["file_path"])
    text = result.get("text", "") if isinstance(result, dict) else ""
    max_chars = int(args.get("max_chars", 2000))
    content = text[:max_chars]
    if len(text) > max_chars:
        content += f"\n\n... [TRUNCATED: {len(text) - max_chars} chars]"
    return ToolResult.ok(output={
        "content": content,
        "is_scanned": result.get("is_scanned", False) if isinstance(result, dict) else False,
        "total_length": len(text),
    })


def _do_describe_image(args):
    from functions.vision import describe_image
    return describe_image(
        file_path=args["file_path"],
        prompt=args.get("prompt", "Describe this image in detail."),
        detail=args.get("detail", "high"),
    )


def _do_analyze_screenshot(args):
    from functions.vision import analyze_screenshot
    return analyze_screenshot(file_path=args["file_path"])


def _do_analyze_chart(args):
    from functions.vision import analyze_chart
    return analyze_chart(file_path=args["file_path"])


def _do_extract_text_from_image(args):
    from functions.vision import extract_text_from_image
    return extract_text_from_image(file_path=args["file_path"], language=args.get("language", "eng"))


def _do_python_runner(args):
    from functions.code import python_runner
    result = python_runner.run_code(args["code"], timeout=int(args.get("timeout", 30)))
    return ToolResult.ok(output=result)


HANDLERS = {
    "read_word": _do_read_word,
    "write_word": _do_write_word,
    "read_excel": _do_read_excel,
    "write_excel": _do_write_excel,
    "read_pptx": _do_read_pptx,
    "write_pptx": _do_write_pptx,
    "read_pdf": _do_read_pdf,
    "describe_image": _do_describe_image,
    "analyze_screenshot": _do_analyze_screenshot,
    "analyze_chart": _do_analyze_chart,
    "extract_text_from_image": _do_extract_text_from_image,
    "python_runner": _do_python_runner,
}


def main():
    line = sys.stdin.readline()
    if not line:
        return
    try:
        req = json.loads(line)
        tool = req.get("tool")
        handler = HANDLERS.get(tool)
        if handler is None:
            result = ToolResult.fail(f"Unknown tool: {tool}")
        else:
            result = handler(req.get("args") or {})
            if not isinstance(result, ToolResult):
                result = ToolResult.ok(output=result)
    except Exception as exc:
        result = ToolResult.fail(str(exc))
    try:
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=False))
    except Exception as exc:
        sys.stdout.write(json.dumps({"success": False, "error": str(exc), "task_done": False}))
    finally:
        sys.stdout.flush()


if __name__ == "__main__":
    main()
