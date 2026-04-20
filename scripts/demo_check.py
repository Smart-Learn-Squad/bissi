#!/usr/bin/env python3
"""Minimal preflight for a BISSI demo session."""

from __future__ import annotations

import shutil
import subprocess
import sys


def _check_python() -> tuple[bool, str]:
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 11)
    return ok, f"Python {major}.{minor}"


def _check_ollama() -> tuple[bool, str]:
    if shutil.which("ollama") is None:
        return False, "ollama not found in PATH"
    try:
        result = subprocess.run(
            ["ollama", "show", "gemma4:e2b"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        return False, f"ollama check failed: {exc}"
    if result.returncode == 0:
        return True, "gemma4:e2b available"
    return False, "gemma4:e2b missing. Run: ollama pull gemma4:e2b"


def main() -> int:
    checks = [
        ("python", _check_python),
        ("ollama", _check_ollama),
    ]

    failed = False
    print("BISSI demo preflight")
    print("====================")
    for name, fn in checks:
        ok, message = fn()
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {name}: {message}")
        failed = failed or not ok

    if failed:
        print("\nDemo preflight failed.")
        return 1

    print("\nReady. Suggested commands:")
    print("  python main.py")
    print("  python main.py --edition codes")
    print("  python main.py --edition smartlearn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
