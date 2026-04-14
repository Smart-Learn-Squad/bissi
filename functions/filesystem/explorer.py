"""Filesystem operations for BISSI.

Provides file navigation, search, and metadata extraction.
"""
import os
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterator
from datetime import datetime


def read_text_file(file_path: Union[str, Path], max_lines: Optional[int] = None) -> Dict[str, Any]:
    """Read the content of a text file (Python, Markdown, TXT, JSON, etc.).
    
    Use this tool to read source code files, documentation, config files, and any text-based file.
    
    Args:
        file_path: Path to the text file
        max_lines: Maximum number of lines to read (default: all)
        
    Returns:
        Dictionary with file content and metadata
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {'error': f'File not found: {file_path}'}
        
        if not path.is_file():
            return {'error': f'Not a file: {file_path}'}
        
        # Read file content
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            if max_lines:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                content = ''.join(lines)
            else:
                content = f.read()
        
        return {
            'content': content,
            'lines': len(content.split('\n')),
            'size': path.stat().st_size,
            'path': str(path.absolute())
        }
    except Exception as e:
        return {'error': f'Failed to read file: {str(e)}'}


def list_directory(directory: Union[str, Path], 
                   pattern: Optional[str] = None,
                   include_hidden: bool = False) -> List[Dict[str, Any]]:
    """List contents of a directory with metadata.
    
    Args:
        directory: Path to directory
        pattern: Glob pattern to filter files (e.g., "*.py", "*.docx")
        include_hidden: Whether to include hidden files
        
    Returns:
        List of dictionaries with file/directory info
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
    except PermissionError:
        pass
    
    # Sort: directories first, then alphabetical
    items.sort(key=lambda x: (0 if x['type'] == 'directory' else 1, x['name'].lower()))
    return items


def search_files(directory: Union[str, Path],
                 pattern: str = "*",
                 recursive: bool = True,
                 include_hidden: bool = False) -> List[Dict[str, Any]]:
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
        List of matching files with metadata including size
    """
    path = Path(directory).resolve()  # Resolve to absolute path
    matches = []
    seen_paths = set()
    
    # Search 1: Root directory only (non-recursive)
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
    
    # Search 2: Subdirectories (recursive)
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
    
    return sorted(matches, key=lambda x: x['name'].lower())


def search_by_content(directory: Union[str, Path],
                      query: str,
                      extensions: Optional[List[str]] = None,
                      case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """Search for files containing specific text.
    
    Args:
        directory: Root directory to search
        query: Text to search for
        extensions: Limit to specific file extensions (e.g., ['.txt', '.py'])
        case_sensitive: Case sensitive search
        
    Returns:
        List of files containing the query text
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
    
    return matches


def _is_binary(file_path: Path, chunk_size: int = 1024) -> bool:
    """Check if file is binary by looking for null bytes."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(chunk_size)
            return b'\x00' in chunk
    except:
        return True


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get detailed information about a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file metadata
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
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
    
    return info


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def get_directory_tree(directory: Union[str, Path],
                       max_depth: int = 3,
                       include_files: bool = True) -> Dict[str, Any]:
    """Get hierarchical tree structure of directory.
    
    Args:
        directory: Root directory
        max_depth: Maximum depth to traverse
        include_files: Include files or just directories
        
    Returns:
        Nested dictionary representing directory tree
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
    
    return build_tree(path, 1)


def get_recent_files(directory: Union[str, Path],
                     hours: int = 24,
                     pattern: str = "*") -> List[Dict[str, Any]]:
    """Get files modified within specified hours.
    
    Args:
        directory: Directory to search
        hours: Number of hours to look back
        pattern: File pattern to match
        
    Returns:
        List of recently modified files
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
    return recent
