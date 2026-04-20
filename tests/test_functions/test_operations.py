from pathlib import Path

from functions.operations import SafeOperator


def test_default_policy_allows_create_and_delete(tmp_path):
    operator = SafeOperator()
    created = tmp_path / "demo.txt"

    ok = operator.write_new(
        created,
        lambda path: path.write_text("hello", encoding="utf-8"),
        description="create document",
    )
    assert ok is True
    assert created.read_text(encoding="utf-8") == "hello"

    deleted = operator.delete(created, description="delete file")
    assert deleted is True
    assert not created.exists()


def test_move_uses_callback_and_creates_destination(tmp_path):
    source = tmp_path / "src.txt"
    source.write_text("payload", encoding="utf-8")
    destination = tmp_path / "nested" / "dst.txt"

    operator = SafeOperator(confirm_callback=lambda operation, target: True)

    ok = operator.move(source, destination)

    assert ok is True
    assert destination.read_text(encoding="utf-8") == "payload"
    assert not source.exists()
