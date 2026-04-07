"""Workflow engine for BISSI.

Provides IFTTT-style automation with triggers and actions.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime
import threading
import time


@dataclass
class Workflow:
    """Workflow definition."""
    id: str
    name: str
    trigger_type: str
    trigger_config: Dict[str, Any]
    action_type: str
    action_config: Dict[str, Any]
    enabled: bool = True
    created_at: str = None
    last_run: str = None
    run_count: int = 0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class WorkflowEngine:
    """IFTTT-style workflow automation engine."""
    
    def __init__(self, storage_path: Union[str, Path] = '~/.bissi/workflows.json'):
        """Initialize workflow engine.
        
        Args:
            storage_path: Path to workflow storage
        """
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.workflows: List[Workflow] = []
        self.triggers: Dict[str, Callable] = {}
        self.actions: Dict[str, Callable] = {}
        self.running = False
        self.monitor_thread = None
        
        self._load_workflows()
    
    def register_trigger(self, name: str, trigger_func: Callable):
        """Register a trigger type.
        
        Args:
            name: Trigger type name
            trigger_func: Function that checks if trigger condition is met
        """
        self.triggers[name] = trigger_func
    
    def register_action(self, name: str, action_func: Callable):
        """Register an action type.
        
        Args:
            name: Action type name
            action_func: Function to execute when triggered
        """
        self.actions[name] = action_func
    
    def _load_workflows(self):
        """Load saved workflows."""
        if self.storage_path.exists():
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.workflows = [Workflow(**w) for w in data]
    
    def _save_workflows(self):
        """Save workflows to disk."""
        data = []
        for w in self.workflows:
            w_dict = {
                'id': w.id,
                'name': w.name,
                'trigger_type': w.trigger_type,
                'trigger_config': w.trigger_config,
                'action_type': w.action_type,
                'action_config': w.action_config,
                'enabled': w.enabled,
                'created_at': w.created_at,
                'last_run': w.last_run,
                'run_count': w.run_count
            }
            data.append(w_dict)
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def create_workflow(self,
                       name: str,
                       trigger_type: str,
                       trigger_config: Dict[str, Any],
                       action_type: str,
                       action_config: Dict[str, Any]) -> Workflow:
        """Create new workflow.
        
        Args:
            name: Workflow name
            trigger_type: Registered trigger type
            trigger_config: Trigger configuration
            action_type: Registered action type
            action_config: Action configuration
            
        Returns:
            Created workflow
        """
        import hashlib
        
        workflow_id = hashlib.md5(
            f"{name}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        workflow = Workflow(
            id=workflow_id,
            name=name,
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            action_type=action_type,
            action_config=action_config
        )
        
        self.workflows.append(workflow)
        self._save_workflows()
        
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if deleted
        """
        original_len = len(self.workflows)
        self.workflows = [w for w in self.workflows if w.id != workflow_id]
        
        if len(self.workflows) < original_len:
            self._save_workflows()
            return True
        return False
    
    def enable_workflow(self, workflow_id: str) -> bool:
        """Enable workflow."""
        for w in self.workflows:
            if w.id == workflow_id:
                w.enabled = True
                self._save_workflows()
                return True
        return False
    
    def disable_workflow(self, workflow_id: str) -> bool:
        """Disable workflow."""
        for w in self.workflows:
            if w.id == workflow_id:
                w.enabled = False
                self._save_workflows()
                return True
        return False
    
    def list_workflows(self) -> List[Workflow]:
        """List all workflows."""
        return sorted(self.workflows, key=lambda w: w.name)
    
    def execute_workflow(self, workflow: Workflow) -> bool:
        """Execute single workflow.
        
        Args:
            workflow: Workflow to execute
            
        Returns:
            True if executed successfully
        """
        if workflow.action_type not in self.actions:
            print(f"Unknown action type: {workflow.action_type}")
            return False
        
        try:
            action_func = self.actions[workflow.action_type]
            action_func(**workflow.action_config)
            
            workflow.last_run = datetime.now().isoformat()
            workflow.run_count += 1
            self._save_workflows()
            
            return True
            
        except Exception as e:
            print(f"Workflow execution error: {e}")
            return False
    
    def check_and_run(self):
        """Check all workflows and run triggered ones."""
        for workflow in self.workflows:
            if not workflow.enabled:
                continue
            
            if workflow.trigger_type not in self.triggers:
                continue
            
            try:
                trigger_func = self.triggers[workflow.trigger_type]
                if trigger_func(**workflow.trigger_config):
                    self.execute_workflow(workflow)
            except Exception as e:
                print(f"Trigger check error: {e}")
    
    def start_monitoring(self, interval: int = 60):
        """Start background monitoring thread.
        
        Args:
            interval: Check interval in seconds
        """
        if self.running:
            return
        
        self.running = True
        
        def monitor_loop():
            while self.running:
                self.check_and_run()
                time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)


# Global engine instance
_engine_instance: Optional[WorkflowEngine] = None


def get_engine() -> WorkflowEngine:
    """Get or create workflow engine singleton."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = WorkflowEngine()
    return _engine_instance


def quick_workflow(name: str,
                   trigger_type: str,
                   trigger_config: Dict[str, Any],
                   action_type: str,
                   action_config: Dict[str, Any]) -> Workflow:
    """Quick create workflow."""
    engine = get_engine()
    return engine.create_workflow(name, trigger_type, trigger_config, action_type, action_config)
