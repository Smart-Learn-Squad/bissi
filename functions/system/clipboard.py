"""System clipboard operations for BISSI.

Provides read/write access to system clipboard.
"""
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

from typing import Optional


def get_clipboard() -> str:
    """Get text from system clipboard.
    
    Returns:
        Clipboard text content
    """
    if not PYPERCLIP_AVAILABLE:
        raise ImportError("pyperclip not available. Install with: pip install pyperclip")
    
    try:
        return pyperclip.paste()
    except Exception as e:
        raise RuntimeError(f"Failed to read clipboard: {e}")


def set_clipboard(text: str) -> None:
    """Set text to system clipboard.
    
    Args:
        text: Text to copy to clipboard
    """
    if not PYPERCLIP_AVAILABLE:
        raise ImportError("pyperclip not available. Install with: pip install pyperclip")
    
    try:
        pyperclip.copy(text)
    except Exception as e:
        raise RuntimeError(f"Failed to write clipboard: {e}")


def copy_file_contents(file_path: str) -> str:
    """Copy file contents to clipboard.
    
    Args:
        file_path: Path to file
        
    Returns:
        The copied text
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    set_clipboard(content)
    return content


def is_available() -> bool:
    """Check if clipboard functionality is available.
    
    Returns:
        True if clipboard operations are supported
    """
    return PYPERCLIP_AVAILABLE
