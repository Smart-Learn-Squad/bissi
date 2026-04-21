"""File writing and modification operations for BISSI.

Provides functionality to create and edit text-based files (code, markdown, etc.).

Functions:
- write_text_file: Create/update text file
- replace_in_file: Find & replace in file
"""
from pathlib import Path
from typing import Union, Optional, List, Dict, Any
import os

from core.types import ToolResult


def write_text_file(file_path: Union[str, Path], content: str, append: bool = False) -> ToolResult:
    """Create or update a text file with content.

    Args:
        file_path: Path to the file
        content: Text content to write
        append: If True, add to end of file. If False, overwrite.

    Returns:
        ToolResult with success status and metadata
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        mode = 'a' if append else 'w'
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)

        return ToolResult.ok(
            output={
                'action': 'append' if append else 'write',
            },
            message=f"File {'updated' if append else 'written'}: {path}",
            path=str(path.absolute()),
            size=path.stat().st_size,
        )
    except Exception as e:
        return ToolResult.fail(str(e))


def replace_in_file(file_path: Union[str, Path],
                    old_text: str,
                    new_text: str,
                    occurrence: int = 0) -> ToolResult:
    """Replace specific text in a file.

    Args:
        file_path: Path to the file
        old_text: Text to find
        new_text: Text to replace with
        occurrence: Which occurrence to replace (0 for all, 1 for first, etc.)

    Returns:
        ToolResult with success status and replacement count
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return ToolResult.fail(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if old_text not in content:
            return ToolResult.fail(f"Text '{old_text}' not found in file.")

        if occurrence == 0:
            new_content = content.replace(old_text, new_text)
            count = content.count(old_text)
        else:
            parts = content.split(old_text)
            if len(parts) <= occurrence:
                return ToolResult.fail(f"Only {len(parts)-1} occurrences found.")

            new_content = old_text.join(parts[:occurrence]) + new_text + old_text.join(parts[occurrence:])
            count = 1

        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return ToolResult.ok(
            output={'replacements': count},
            message=f"Updated {count} occurrence(s) in {path}",
            path=str(path.absolute()),
        )
    except Exception as e:
        return ToolResult.fail(str(e))
