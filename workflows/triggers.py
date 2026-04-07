"""Workflow triggers for BISSI.

Provides trigger conditions for workflow automation.
"""
from pathlib import Path
from datetime import datetime, time
from typing import Dict, Any, Callable, Optional
import os


class TriggerRegistry:
    """Registry of available trigger types."""
    
    def __init__(self):
        self.triggers: Dict[str, Callable] = {}
        self._register_defaults()
    
    def register(self, name: str, trigger_func: Callable):
        """Register trigger function."""
        self.triggers[name] = trigger_func
    
    def get(self, name: str) -> Optional[Callable]:
        """Get trigger function by name."""
        return self.triggers.get(name)
    
    def list_triggers(self) -> Dict[str, str]:
        """List available triggers with descriptions."""
        return {
            'time': 'Trigger at specific time',
            'interval': 'Trigger at regular intervals',
            'file_created': 'Trigger when file is created',
            'file_modified': 'Trigger when file is modified',
            'folder_changed': 'Trigger when folder contents change'
        }
    
    def _register_defaults(self):
        """Register default trigger types."""
        self.register('time', time_trigger)
        self.register('interval', interval_trigger)
        self.register('file_created', file_created_trigger)
        self.register('file_modified', file_modified_trigger)
        self.register('folder_changed', folder_changed_trigger)


def time_trigger(hour: int, minute: int = 0, **kwargs) -> bool:
    """Check if current time matches.
    
    Args:
        hour: Hour (0-23)
        minute: Minute (0-59)
        
    Returns:
        True if current time matches
    """
    now = datetime.now()
    return now.hour == hour and now.minute == minute


def interval_trigger(minutes: int, last_run: Optional[datetime] = None, **kwargs) -> bool:
    """Check if interval has passed since last run.
    
    Args:
        minutes: Interval in minutes
        last_run: Last execution time
        
    Returns:
        True if interval passed
    """
    if last_run is None:
        return True
    
    now = datetime.now()
    delta = (now - last_run).total_seconds() / 60
    return delta >= minutes


def file_created_trigger(file_path: str, **kwargs) -> bool:
    """Check if file was created recently.
    
    Args:
        file_path: Path to monitor
        
    Returns:
        True if file exists and is new
    """
    path = Path(file_path)
    
    if not path.exists():
        return False
    
    # Check if created in last minute
    creation_time = datetime.fromtimestamp(path.stat().st_ctime)
    delta = (datetime.now() - creation_time).total_seconds()
    
    return delta < 60


def file_modified_trigger(file_path: str, last_modified: float = 0, **kwargs) -> bool:
    """Check if file was modified.
    
    Args:
        file_path: Path to monitor
        last_modified: Last known modification timestamp
        
    Returns:
        True if file modified since last check
    """
    path = Path(file_path)
    
    if not path.exists():
        return False
    
    current_modified = path.stat().st_mtime
    return current_modified > last_modified


def folder_changed_trigger(folder_path: str, file_count: Optional[int] = None, **kwargs) -> bool:
    """Check if folder contents changed.
    
    Args:
        folder_path: Folder to monitor
        file_count: Last known file count
        
    Returns:
        True if file count changed
    """
    path = Path(folder_path)
    
    if not path.exists():
        return False
    
    current_count = len(list(path.iterdir()))
    
    if file_count is None:
        return True  # First check
    
    return current_count != file_count


class FileWatcher:
    """Simple file system watcher."""
    
    def __init__(self):
        self.states: Dict[str, Dict[str, Any]] = {}
    
    def check_file(self, file_path: str) -> bool:
        """Check if file changed.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if changed since last check
        """
        path = Path(file_path)
        
        if not path.exists():
            if file_path in self.states:
                del self.states[file_path]
            return False
        
        stat = path.stat()
        current_state = {
            'size': stat.st_size,
            'mtime': stat.st_mtime
        }
        
        if file_path not in self.states:
            self.states[file_path] = current_state
            return False
        
        changed = self.states[file_path] != current_state
        self.states[file_path] = current_state
        
        return changed
    
    def check_folder(self, folder_path: str) -> bool:
        """Check if folder contents changed.
        
        Args:
            folder_path: Path to folder
            
        Returns:
            True if changed
        """
        path = Path(folder_path)
        
        if not path.exists():
            if folder_path in self.states:
                del self.states[folder_path]
            return False
        
        # Get file list with sizes
        current_state = {}
        for f in path.iterdir():
            if f.is_file():
                stat = f.stat()
                current_state[f.name] = {
                    'size': stat.st_size,
                    'mtime': stat.st_mtime
                }
        
        if folder_path not in self.states:
            self.states[folder_path] = current_state
            return False
        
        changed = self.states[folder_path] != current_state
        self.states[folder_path] = current_state
        
        return changed


# Global watcher instance
_watcher_instance: Optional[FileWatcher] = None


def get_watcher() -> FileWatcher:
    """Get global file watcher."""
    global _watcher_instance
    if _watcher_instance is None:
        _watcher_instance = FileWatcher()
    return _watcher_instance
