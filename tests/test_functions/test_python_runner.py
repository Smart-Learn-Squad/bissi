from functions.code.python_runner import PythonSandbox, run_code


def test_python_runner_executes_safe_code():
    result = run_code("print(sum([1, 2, 3]))")
    assert result["success"] is True
    assert result["output"].strip() == "6"


def test_python_runner_blocks_forbidden_import():
    result = run_code("import os\nprint('bad')")
    assert result["success"] is False
    assert "Forbidden import" in result["error"]


def test_python_runner_times_out():
    sandbox = PythonSandbox(timeout=1)
    result = sandbox.execute("while True:\n    pass")
    assert result["success"] is False
    assert "Timeout" in result["error"]
