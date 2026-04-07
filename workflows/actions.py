"""Workflow actions for BISSI.

Provides executable actions for workflow automation.
"""
from pathlib import Path
from typing import Dict, Any, Callable, List
import subprocess
import shutil


class ActionRegistry:
    """Registry of available action types."""
    
    def __init__(self):
        self.actions: Dict[str, Callable] = {}
        self._register_defaults()
    
    def register(self, name: str, action_func: Callable):
        """Register action function."""
        self.actions[name] = action_func
    
    def get(self, name: str) -> Callable:
        """Get action function by name."""
        return self.actions.get(name)
    
    def list_actions(self) -> Dict[str, str]:
        """List available actions with descriptions."""
        return {
            'copy_file': 'Copy file to destination',
            'move_file': 'Move file to destination',
            'delete_file': 'Delete file',
            'run_command': 'Execute shell command',
            'send_notification': 'Send desktop notification',
            'write_log': 'Write to log file',
            'backup_file': 'Create file backup',
            'convert_document': 'Convert document format'
        }
    
    def _register_defaults(self):
        """Register default action types."""
        self.register('copy_file', copy_file)
        self.register('move_file', move_file)
        self.register('delete_file', delete_file)
        self.register('run_command', run_command)
        self.register('send_notification', send_notification)
        self.register('write_log', write_log)
        self.register('backup_file', backup_file)


def copy_file(source: str, destination: str, **kwargs) -> bool:
    """Copy file to destination.
    
    Args:
        source: Source file path
        destination: Destination path
        
    Returns:
        True if successful
    """
    try:
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"Copy error: {e}")
        return False


def move_file(source: str, destination: str, **kwargs) -> bool:
    """Move file to destination.
    
    Args:
        source: Source file path
        destination: Destination path
        
    Returns:
        True if successful
    """
    try:
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, destination)
        return True
    except Exception as e:
        print(f"Move error: {e}")
        return False


def delete_file(file_path: str, **kwargs) -> bool:
    """Delete file.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if successful
    """
    try:
        path = Path(file_path)
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except Exception as e:
        print(f"Delete error: {e}")
        return False


def run_command(command: str, **kwargs) -> bool:
    """Execute shell command.
    
    Args:
        command: Command to execute
        
    Returns:
        True if successful
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=kwargs.get('timeout', 60)
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Command error: {e}")
        return False


def send_notification(title: str, message: str, **kwargs) -> bool:
    """Send desktop notification.
    
    Args:
        title: Notification title
        message: Notification message
        
    Returns:
        True if successful
    """
    try:
        # Try notify-send (Linux)
        subprocess.run(
            ['notify-send', title, message],
            capture_output=True,
            check=True
        )
        return True
    except:
        pass
    
    try:
        # Try zenity
        subprocess.run(
            ['zenity', '--info', '--title', title, '--text', message],
            capture_output=True
        )
        return True
    except:
        pass
    
    print(f"[NOTIFICATION] {title}: {message}")
    return True


def write_log(message: str, log_file: str = '~/.bissi/workflow.log', **kwargs) -> bool:
    """Write message to log file.
    
    Args:
        message: Log message
        log_file: Log file path
        
    Returns:
        True if successful
    """
    try:
        from datetime import datetime
        
        path = Path(log_file).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
        
        return True
    except Exception as e:
        print(f"Log error: {e}")
        return False


def backup_file(file_path: str, backup_dir: str = None, **kwargs) -> bool:
    """Create timestamped backup of file.
    
    Args:
        file_path: File to backup
        backup_dir: Backup directory (default: .backups/ in file's folder)
        
    Returns:
        True if successful
    """
    try:
        from datetime import datetime
        
        path = Path(file_path)
        
        if backup_dir is None:
            backup_dir = path.parent / '.backups'
        else:
            backup_dir = Path(backup_dir)
        
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{path.stem}_{timestamp}{path.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        return True
        
    except Exception as e:
        print(f"Backup error: {e}")
        return False


def convert_document(input_file: str, output_format: str, **kwargs) -> bool:
    """Convert document format using LibreOffice.
    
    Args:
        input_file: Input document path
        output_format: Output format (pdf, docx, etc.)
        
    Returns:
        True if successful
    """
    try:
        input_path = Path(input_file)
        output_dir = input_path.parent
        
        # Use LibreOffice headless conversion
        cmd = [
            'libreoffice',
            '--headless',
            '--convert-to', output_format,
            '--outdir', str(output_dir),
            str(input_file)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Conversion error: {e}")
        return False


class ActionChain:
    """Chain multiple actions together."""
    
    def __init__(self):
        self.actions: List[Dict[str, Any]] = []
    
    def add(self, action_type: str, config: Dict[str, Any]):
        """Add action to chain."""
        self.actions.append({
            'type': action_type,
            'config': config
        })
    
    def execute(self, registry: ActionRegistry = None) -> bool:
        """Execute all actions in chain."""
        if registry is None:
            registry = ActionRegistry()
        
        for action in self.actions:
            func = registry.get(action['type'])
            if func:
                result = func(**action['config'])
                if not result:
                    return False
            else:
                print(f"Unknown action: {action['type']}")
                return False
        
        return True
