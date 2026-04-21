"""Shared type definitions for BISSI."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Protocol


class MessageType(Enum):
    """Type of message in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolStatus(Enum):
    """Status of tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]
    status: ToolStatus = ToolStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Message:
    """Represents a message in conversation history."""
    role: MessageType
    content: str
    metadata: Optional[Dict[str, Any]] = None

    # For assistant messages with tool calls
    tool_calls: Optional[List[ToolCall]] = None

    # For tool response messages
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None


@dataclass
class ToolResult:
    """Standardized tool result structure."""
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
    path: Optional[str] = None
    size: Optional[int] = None
    task_done: bool = True

    @classmethod
    def ok(cls, output=None, message: str = None, path: str = None, size: int = None, task_done: bool = True):
        """Create a success result."""
        return cls(success=True, output=output, message=message, path=path, size=size, task_done=task_done)

    @classmethod
    def fail(cls, error: str, path: str = None, task_done: bool = False):
        """Create an error result."""
        return cls(success=False, error=error, path=path, task_done=task_done)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM consumption."""
        result = {"success": self.success}
        if self.output is not None:
            result["output"] = self.output
        if self.error:
            result["error"] = self.error
        if self.message:
            result["message"] = self.message
        if self.path:
            result["path"] = self.path
        if self.size is not None:
            result["size"] = self.size
        result["task_done"] = self.task_done
        return result


class ToolError(Exception):
    """Raised when a tool fails."""
    pass


@dataclass
class AgentEvent:
    """Event emitted during agent processing."""
    event_type: str
    data: Any = None


class TokenCallback(Protocol):
    """Callback for streaming tokens."""
    def __call__(self, token: str) -> None: ...


class ToolStartCallback(Protocol):
    """Callback when tool starts execution."""
    def __call__(self, name: str, args: Any) -> None: ...


class ToolDoneCallback(Protocol):
    """Callback when tool completes."""
    def __call__(self, name: str, result: str) -> None: ...


class ThinkingCallback(Protocol):
    """Callback for thinking/status messages."""
    def __call__(self, message: str) -> None: ...


class StopCallback(Protocol):
    """Callback to check if processing should stop."""
    def __call__(self) -> bool: ...


@dataclass
class ProcessingContext:
    """Context passed through agent processing loop."""
    messages: List[Dict[str, Any]]
    iteration: int = 0
    max_iterations: int = 7
    tool_calls_count: int = 0
