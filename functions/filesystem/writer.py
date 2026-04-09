"""File writing and modification operations for BISSI.

Provides functionality to create and edit text-based files (code, markdown, etc.).
"""
from pathlib import Path
from typing import Union, Optional, List, Dict, Any
import os


def write_text_file(file_path: Union[str, Path], content: str, append: bool = False) -> Dict[str, Any]:
    """Create or update a text file with content.
    
    Args:
        file_path: Path to the file
        content: Text content to write
        append: If True, add to end of file. If False, overwrite.
        
    Returns:
        Success status and metadata
    """
    try:
        path = Path(file_path)
        # Ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = 'a' if append else 'w'
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)
            
        return {
            'success': True,
            'path': str(path.absolute()),
            'size': path.stat().st_size,
            'action': 'append' if append else 'write'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def replace_in_file(file_path: Union[str, Path], 
                    old_text: str, 
                    new_text: str, 
                    occurrence: int = 0) -> Dict[str, Any]:
    """Replace specific text in a file.
    
    Args:
        file_path: Path to the file
        old_text: Text to find
        new_text: Text to replace with
        occurrence: Which occurrence to replace (0 for all, 1 for first, etc.)
        
    Returns:
        Success status and number of replacements
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {'success': False, 'error': f"File not found: {file_path}"}
            
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        if old_text not in content:
            return {'success': False, 'error': f"Text '{old_text}' not found in file."}
            
        if occurrence == 0:
            new_content = content.replace(old_text, new_text)
            count = content.count(old_text)
        else:
            parts = content.split(old_text)
            if len(parts) <= occurrence:
                return {'success': False, 'error': f"Only {len(parts)-1} occurrences found."}
            
            # Rebuild content with replacement at specific occurrence
            new_content = old_text.join(parts[:occurrence]) + new_text + old_text.join(parts[occurrence:])
            count = 1
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return {
            'success': True,
            'replacements': count,
            'path': str(path.absolute())
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
