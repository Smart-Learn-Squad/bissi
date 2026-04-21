"""Filesystem operations for BISSI.

Provides file navigation, search, and metadata extraction.

Functions:
- read_text_file: Read text file content
- list_directory: List directory contents
- search_files: Find files by name pattern
- search_by_content: Find files by content
- get_file_info: Get file metadata
- get_directory_tree: Get directory hierarchy
- get_recent_files: Get recently modified files
"""
import os
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterator
from datetime import datetime

from core.types import ToolResult


def read_text_file(file_path: Union[str, Path], max_lines: Optional[int] = None) -> ToolResult:
    """Read the content of a text file (Python, Markdown, TXT, JSON, etc.).

    Use this tool to read source code files, documentation, config files, and any text-based file.

    Args:
        file_path: Path to the text file
        max_lines: Maximum number of lines to read (default: all)

    Returns:
        ToolResult with 'output' containing content, lines, size, truncated
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return ToolResult.fail(f'File not found: {file_path}', path=str(path.absolute()))

        if not path.is_file():
            return ToolResult.fail(f'Not a file: {file_path}', path=str(path.absolute()))

        # Read file content
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            truncated = False
            if max_lines:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        truncated = True
                        break
                    lines.append(line)
                content = ''.join(lines)
            else:
                content = f.read()

        return ToolResult.ok(
            output={
                'content': content,
                'lines': len(content.split('\n')),
                'size': path.stat().st_size,
                'truncated': truncated,
            },
            path=str(path.absolute()),
            task_done=not truncated,
        )
    except Exception as e:
        return ToolResult.fail(f'Failed to read file: {str(e)}', path=str(Path(file_path).absolute()))


def list_directory(directory: Union[str, Path],
                   pattern: Optional[str] = None,
                   include_hidden: bool = False) -> ToolResult:
    """List contents of a directory with metadata.

    Args:
        directory: Path to directory
        pattern: Glob pattern to filter files (e.g., "*.py", "*.docx")
        include_hidden: Whether to include hidden files

    Returns:
        ToolResult with 'output' containing items list
    """
    path = Path(directory)
    items = []
    
    try:
        for item in path.iterdir():
            # Skip hidden files
            if not include_hidden and item.name.startswith('.'):
                continue
            
            # Apply pattern filter
            if pattern and not item.is_dir():
                if not fnmatch.fnmatch(item.name, pattern):
                    continue
            
            stat = item.stat()
            info = {
                'name': item.name,
                'path': str(item),
                'type': 'directory' if item.is_dir() else 'file',
                'size': stat.st_size if item.is_file() else None,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
            }
            items.append(info)
    except PermissionError as exc:
        return ToolResult.fail(f"Permission denied: {path}")
    
    # Sort: directories first, then alphabetical
    items.sort(key=lambda x: (0 if x['type'] == 'directory' else 1, x['name'].lower()))
    return ToolResult.ok(output={'items': items})


def search_files(directory: Union[str, Path],
                 pattern: str = "*",
                 recursive: bool = True,
                 include_hidden: bool = False) -> ToolResult:
    """Search for files matching pattern in directory and subdirectories.

    CRITICAL: This function searches BOTH the root directory AND all subdirectories.
    When searching for "*.py", it WILL find smartlearn.py, main.py at root level
    AND all __init__.py files in subdirectories.

    Args:
        directory: Root directory to search
        pattern: Glob pattern (e.g., "*.txt", "report*", "*.py")
        recursive: Search in subdirectories (default: True)
        include_hidden: Include hidden files

    Returns:
        ToolResult with 'output' containing results list
    """
    path = Path(directory).resolve()
    if not path.exists():
        return ToolResult.fail(f'Directory not found: {directory}', path=str(path))

    matches = []
    seen_paths = set()

    for item in path.glob(pattern):
        if not include_hidden and any(part.startswith('.') for part in item.parts):
            continue
        if item.is_file():
            file_path = str(item.resolve())
            if file_path not in seen_paths:
                seen_paths.add(file_path)
                stat = item.stat()
                matches.append({
                    'name': item.name,
                    'path': file_path,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'directory': str(item.parent)
                })

    if recursive:
        for item in path.rglob(pattern):
            if not include_hidden and any(part.startswith('.') for part in item.parts):
                continue
            if item.is_file():
                file_path = str(item.resolve())
                if file_path not in seen_paths:
                    seen_paths.add(file_path)
                    stat = item.stat()
                    matches.append({
                        'name': item.name,
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'directory': str(item.parent)
                    })

    return ToolResult.ok(output={'results': sorted(matches, key=lambda x: x['name'].lower())}, path=str(path))


def search_by_content(directory: Union[str, Path],
                      query: str,
                      extensions: Optional[List[str]] = None,
                      case_sensitive: bool = False) -> ToolResult:
    """Search for files containing specific text.

    Args:
        directory: Root directory to search
        query: Text to search for
        extensions: Limit to specific file extensions (e.g., ['.txt', '.py'])
        case_sensitive: Case sensitive search

    Returns:
        ToolResult with 'output' containing results
    """
    path = Path(directory)
    matches = []
    
    search_query = query if case_sensitive else query.lower()
    
    for item in path.rglob('*'):
        if not item.is_file():
            continue
        
        # Filter by extension
        if extensions and item.suffix.lower() not in extensions:
            continue
        
        # Skip binary files
        if _is_binary(item):
            continue
        
        try:
            with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                search_content = content if case_sensitive else content.lower()
                
                if search_query in search_content:
                    # Find line numbers
                    lines = content.split('\n')
                    matching_lines = []
                    for i, line in enumerate(lines, 1):
                        search_line = line if case_sensitive else line.lower()
                        if search_query in search_line:
                            matching_lines.append((i, line.strip()))
                    
                    matches.append({
                        'name': item.name,
                        'path': str(item),
                        'matches': len(matching_lines),
                        'lines': matching_lines[:5]  # First 5 matches
                    })
        except Exception:
            continue

    return ToolResult.ok(output={'results': matches}, path=str(path))


def _is_binary(file_path: Path, chunk_size: int = 1024) -> bool:
    """Check if file is binary by looking for null bytes."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(chunk_size)
            return b'\x00' in chunk
    except:
        return True


def get_file_info(file_path: Union[str, Path]) -> ToolResult:
    """Get detailed information about a file.

    Args:
        file_path: Path to file

    Returns:
        ToolResult with 'output' containing info dict
    """
    path = Path(file_path)

    if not path.exists():
        return ToolResult.fail(f"File not found: {path}")

    stat = path.stat()

    info = {
        'name': path.name,
        'path': str(path.absolute()),
        'type': 'directory' if path.is_dir() else 'file',
        'size': stat.st_size,
        'size_human': _format_size(stat.st_size),
        'extension': path.suffix.lower() if path.is_file() else None,
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
        'permissions': oct(stat.st_mode)[-3:],
        'is_hidden': path.name.startswith('.')
    }

    return ToolResult.ok(output=info, path=str(path.absolute()))


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def get_directory_tree(directory: Union[str, Path],
                       max_depth: int = 3,
                       include_files: bool = True) -> ToolResult:
    """Get hierarchical tree structure of directory.

    Args:
        directory: Root directory
        max_depth: Maximum depth to traverse
        include_files: Include files or just directories

    Returns:
        ToolResult with 'output' containing tree dict
    """
    path = Path(directory)
    
    def build_tree(current_path: Path, depth: int) -> Dict[str, Any]:
        if depth > max_depth:
            return {'name': current_path.name, 'truncated': True}
        
        result = {
            'name': current_path.name,
            'type': 'directory',
            'children': []
        }
        
        try:
            for item in sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    result['children'].append(build_tree(item, depth + 1))
                elif include_files:
                    result['children'].append({
                        'name': item.name,
                        'type': 'file',
                        'size': item.stat().st_size
                    })
        except PermissionError:
            result['error'] = 'Permission denied'

        return result

    return ToolResult.ok(output=build_tree(path, 1), path=str(Path(directory).absolute()))


def get_recent_files(
    directory: Union[str, Path],
    limit: int = 10,
    hours: int = 24,
    pattern: str = "*",
) -> ToolResult:
    """Get files modified within specified hours.

    Args:
        directory: Directory to search
        hours: Number of hours to look back
        pattern: File pattern to match

    Returns:
        ToolResult with 'output' containing files list
    """
    from datetime import timedelta

    path = Path(directory)
    cutoff = datetime.now() - timedelta(hours=hours)
    recent = []

    for item in path.rglob(pattern):
        if not item.is_file():
            continue

        stat = item.stat()
        modified = datetime.fromtimestamp(stat.st_mtime)

        if modified > cutoff:
            recent.append({
                'name': item.name,
                'path': str(item),
                'modified': modified.isoformat(),
                'size': stat.st_size
            })

    # Sort by modification time (newest first)
    recent.sort(key=lambda x: x['modified'], reverse=True)
    return ToolResult.ok(output={'files': recent[:max(1, int(limit))]}, path=str(Path(directory).absolute()))
