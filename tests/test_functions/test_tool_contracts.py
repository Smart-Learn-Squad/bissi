import json
import time
from types import SimpleNamespace

from agent import BissiAgent
from core.types import ToolResult
from functions.filesystem import explorer


def test_read_text_file_returns_structured_error_for_missing_file(tmp_path):
    missing = tmp_path / "missing.txt"
    result = explorer.read_text_file(missing)

    assert result.success is False
    assert "File not found" in result.error
    assert result.task_done is False


def test_get_recent_files_uses_limit_not_hours(tmp_path):
    files = []
    for idx in range(3):
        path = tmp_path / f"f{idx}.txt"
        path.write_text(str(idx), encoding="utf-8")
        time.sleep(0.01)
        files.append(path)

    result = explorer.get_recent_files(tmp_path, limit=2)
    recent = result.output['files']

    assert len(recent) == 2
    assert recent[0]["name"] == files[-1].name
    assert recent[1]["name"] == files[-2].name


def test_execute_tool_preserves_structured_payload_as_json():
    dummy_agent = SimpleNamespace(
        available_functions={
            "demo_tool": lambda **kwargs: {
                "success": True,
                "output": "ok",
                "path": "/tmp/demo.txt",
                "task_done": True,
            }
        }
    )
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(name="demo_tool", arguments={}),
    )

    raw = BissiAgent._execute_tool(dummy_agent, tool_call, iteration=0)
    payload = json.loads(raw)

    assert payload["success"] is True
    assert payload["path"] == "/tmp/demo.txt"
    assert payload["task_done"] is True


def test_execute_tool_unknown_function_returns_structured_error():
    dummy_agent = SimpleNamespace(available_functions={})
    tool_call = SimpleNamespace(
        id="call_404",
        function=SimpleNamespace(name="unknown_tool", arguments={}),
    )

    raw = BissiAgent._execute_tool(dummy_agent, tool_call, iteration=0)
    payload = json.loads(raw)

    assert payload["success"] is False
    assert "not found" in payload["error"]
    assert payload["task_done"] is False
