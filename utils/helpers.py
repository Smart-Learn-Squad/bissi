"""Common utilities for BISSI.

Shared functions used across multiple modules.
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime


def expand_path(path: Union[str, Path]) -> Path:
    """Expand user home directory and return Path object.
    
    Args:
        path: Path string or Path object
        
    Returns:
        Expanded Path object
    """
    return Path(path).expanduser()


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if needed.
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path = Path(path).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Load JSON file safely.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data or None if error
    """
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return None


def save_json(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> bool:
    """Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Output file path
        indent: JSON indentation
        
    Returns:
        True if saved successfully
    """
    try:
        path = Path(file_path).expanduser()
        ensure_dir(path.parent)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except (IOError, OSError):
        return False


def now_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def generate_id(*args: str) -> str:
    """Generate short hash ID from input strings.
    
    Args:
        *args: Strings to hash
        
    Returns:
        12-character hex hash
    """
    combined = '_'.join(args)
    return hashlib.md5(combined.encode()).hexdigest()[:12]


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def safe_get(d: Dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary.
    
    Args:
        d: Dictionary
        key: Key to get
        default: Default value if key missing
        
    Returns:
        Value or default
    """
    return d.get(key, default)


def chunk_list(lst: list, chunk_size: int):
    """Split list into chunks.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Yields:
        Chunks of the list
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


class SingletonMeta(type):
    """Metaclass for singleton pattern."""
    _instances: Dict[type, Any] = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
    """Truncate string to max length.
    
    Args:
        text: Input string
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def is_valid_file_type(file_path: Union[str, Path], extensions: list) -> bool:
    """Check if file has valid extension.
    
    Args:
        file_path: File path
        extensions: List of valid extensions (e.g., ['.txt', '.pdf'])
        
    Returns:
        True if valid extension
    """
    path = Path(file_path)
    return path.suffix.lower() in [ext.lower() for ext in extensions]
