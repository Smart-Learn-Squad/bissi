"""Core package for BISSI - configuration, types, and memory."""

from .config import Config, DEFAULT_CONFIG, ColorConfig, FontConfig, LLMConfig, UIConfig
from .types import (
    MessageType,
    ToolStatus,
    ToolCall,
    Message,
    ToolResult,
    ToolError,
    AgentEvent,
    ProcessingContext,
    TokenCallback,
    ToolStartCallback,
    ToolDoneCallback,
    ThinkingCallback,
    StopCallback,
)

__all__ = [
    # Config
    "Config",
    "DEFAULT_CONFIG",
    "ColorConfig",
    "FontConfig",
    "LLMConfig",
    "UIConfig",
    # Types
    "MessageType",
    "ToolStatus",
    "ToolCall",
    "Message",
    "ToolResult",
    "ToolError",
    "AgentEvent",
    "ProcessingContext",
    "TokenCallback",
    "ToolStartCallback",
    "ToolDoneCallback",
    "ThinkingCallback",
    "StopCallback",
]
