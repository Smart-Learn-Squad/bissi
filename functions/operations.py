"""Safe file operations with validation and confirmation.

All destructive operations (write, modify, move, delete) should go through
this module so the UI can inject a non-blocking confirmation policy and BISSI
can keep a local rollback trail.
"""
from pathlib import Path
from typing import Union, Optional, Callable
from datetime import datetime
import shutil

ConfirmCallback = Callable[[str, str], bool]


class OperationError(Exception):
    """Raised when an operation is rejected or fails."""
    pass


class SafeOperator:
    """Gatekeeper for all destructive file operations.
    
    Ensures:
    - User confirmation for destructive actions
    - Automatic backup creation
    - Audit logging
    - Rollback capability
    """
    
    def __init__(self, auto_backup: bool = True, confirm_callback: Optional[ConfirmCallback] = None):
        """Initialize the safe operator.
        
        Args:
            auto_backup: Whether to create backups automatically
            confirm_callback: Function to call for user confirmation (returns bool)
        """
        self.auto_backup = auto_backup
        self.confirm_callback = confirm_callback or self._default_confirm
        self.operations_log = []
    
    def _default_confirm(self, operation: str, target: str) -> bool:
        """Default non-interactive confirmation policy.

        Keep historical behavior: when no UI callback is injected, operations
        proceed so delete/move/rollback remain usable in local automation.
        """
        return True
    
    def _create_backup(self, file_path: Union[str, Path]) -> Path:
        """Create timestamped backup of file."""
        path = Path(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = path.parent / ".bissi_backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"{path.stem}_{timestamp}{path.suffix}"
        shutil.copy2(path, backup_path)
        return backup_path
    
    def _log_operation(self, operation: str, target: str, success: bool, backup_path: Optional[Path] = None):
        """Log operation for audit trail."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'target': str(target),
            'success': success,
            'backup': str(backup_path) if backup_path else None
        }
        self.operations_log.append(entry)
    
    def modify_document(self, 
                       file_path: Union[str, Path],
                       modifier_func: Callable,
                       description: str = "modify document") -> bool:
        """Safely modify a document with confirmation and backup.
        
        Args:
            file_path: Path to document to modify
            modifier_func: Function that performs the modification
            description: Human-readable description of the operation
            
        Returns:
            True if operation succeeded, False otherwise
        """
        path = Path(file_path)
        
        if not path.exists():
            raise OperationError(f"File not found: {path}")
        
        # Get user confirmation
        if not self.confirm_callback(description, str(path)):
            self._log_operation(description, path, False)
            print(f"❌ {description} cancelled by user")
            return False
        
        # Create backup
        backup_path = None
        if self.auto_backup:
            backup_path = self._create_backup(path)
            print(f"💾 Backup created: {backup_path}")
        
        # Perform modification
        try:
            modifier_func(path)
            self._log_operation(description, path, True, backup_path)
            print(f"✅ {description} completed successfully")
            return True
        except Exception as e:
            self._log_operation(description, path, False, backup_path)
            raise OperationError(f"{description} failed: {e}")
    
    def write_new(self, 
                  file_path: Union[str, Path],
                  writer_func: Callable,
                  description: str = "create document") -> bool:
        """Safely write new file (checks for overwrite).
        
        Args:
            file_path: Path for new file
            writer_func: Function that creates the file
            description: Human-readable description
            
        Returns:
            True if operation succeeded, False otherwise
        """
        path = Path(file_path)
        
        # Check for overwrite
        backup_path = None
        if path.exists():
            if not self.confirm_callback(f"overwrite existing {description}", str(path)):
                self._log_operation(f"overwrite {description}", path, False)
                print(f"❌ Overwrite cancelled by user")
                return False
            if self.auto_backup:
                backup_path = self._create_backup(path)
                print(f"💾 Backup created: {backup_path}")
        
        # Perform write
        try:
            writer_func(path)
            self._log_operation(description, path, True, backup_path)
            print(f"✅ {description} completed: {path}")
            return True
        except Exception as e:
            self._log_operation(description, path, False, backup_path)
            raise OperationError(f"{description} failed: {e}")

    def move(self,
             source: Union[str, Path],
             destination: Union[str, Path],
             description: str = "move file") -> bool:
        """Safely move a file with confirmation and backup."""
        src = Path(source)
        dst = Path(destination)

        if not src.exists():
            raise OperationError(f"File not found: {src}")

        if not self.confirm_callback(description, f"{src} -> {dst}"):
            self._log_operation(description, f"{src} -> {dst}", False)
            print("❌ Move cancelled by user")
            return False

        backup_path = None
        if self.auto_backup:
            backup_path = self._create_backup(src)
            print(f"💾 Backup created: {backup_path}")

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            self._log_operation(description, f"{src} -> {dst}", True, backup_path)
            print(f"✅ Moved: {src} -> {dst}")
            return True
        except Exception as e:
            self._log_operation(description, f"{src} -> {dst}", False, backup_path)
            raise OperationError(f"Move failed: {e}")
    
    def delete(self, file_path: Union[str, Path], description: str = "delete file") -> bool:
        """Safely delete file with confirmation.
        
        Args:
            file_path: Path to file to delete
            description: Human-readable description
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        path = Path(file_path)
        
        if not path.exists():
            print(f"⚠️  File does not exist: {path}")
            return False
        
        if not self.confirm_callback(description, str(path)):
            self._log_operation(description, path, False)
            print(f"❌ Delete cancelled by user")
            return False
        
        # Create backup before delete
        backup_path = None
        if self.auto_backup:
            backup_path = self._create_backup(path)
        
        try:
            path.unlink()
            self._log_operation(description, path, True, backup_path)
            print(f"✅ Deleted: {path}")
            return True
        except Exception as e:
            self._log_operation(description, path, False, backup_path)
            raise OperationError(f"Delete failed: {e}")
    
    def get_operations_history(self) -> list:
        """Return log of all operations."""
        return self.operations_log.copy()
    
    def rollback(self, file_path: Union[str, Path], timestamp: Optional[str] = None) -> bool:
        """Restore file from backup.
        
        Args:
            file_path: Original file path
            timestamp: Specific backup timestamp, or latest if None
            
        Returns:
            True if rollback succeeded
        """
        path = Path(file_path)
        backup_dir = path.parent / ".bissi_backups"
        
        if not backup_dir.exists():
            raise OperationError(f"No backup directory found for {path}")
        
        # Find backup
        if timestamp:
            backup_name = f"{path.stem}_{timestamp}{path.suffix}"
            backup_path = backup_dir / backup_name
        else:
            # Get latest backup
            backups = sorted(backup_dir.glob(f"{path.stem}_*{path.suffix}"))
            if not backups:
                raise OperationError(f"No backups found for {path}")
            backup_path = backups[-1]
        
        if not backup_path.exists():
            raise OperationError(f"Backup not found: {backup_path}")
        
        if not self.confirm_callback("rollback to backup", str(backup_path)):
            return False
        
        # Perform rollback
        shutil.copy2(backup_path, path)
        self._log_operation("rollback", path, True, backup_path)
        print(f"✅ Rolled back to: {backup_path}")
        return True


# Global operator instance
_default_operator = None


def get_operator(
    *,
    auto_backup: bool = True,
    confirm_callback: Optional[ConfirmCallback] = None,
    force_new: bool = False,
) -> SafeOperator:
    """Get or create default safe operator instance."""
    global _default_operator
    if force_new or _default_operator is None:
        _default_operator = SafeOperator(
            auto_backup=auto_backup,
            confirm_callback=confirm_callback,
        )
    elif confirm_callback is not None:
        _default_operator.confirm_callback = confirm_callback
    return _default_operator
