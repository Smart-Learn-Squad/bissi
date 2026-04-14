"""Application-wide configuration for BISSI."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ColorConfig:
    """Color palette configuration."""
    bg: str = "#f5f5f3"
    bg_white: str = "#ffffff"
    bg_sidebar: str = "#fafaf8"
    border: str = "#e8e8e8"
    border2: str = "#dddddd"
    text: str = "#1a1a1a"
    text2: str = "#2C2C2A"
    text_muted: str = "#888888"
    text_dim: str = "#aaaaaa"
    purple: str = "#534AB7"
    purple_lt: str = "#EEEDFE"
    purple_text: str = "#3C3489"
    teal: str = "#1D9E75"
    teal_lt: str = "#E1F5EE"
    teal_bd: str = "#9FE1CB"
    teal_text: str = "#0F6E56"
    user_bubble: str = "#534AB7"
    tool_dot: str = "#1D9E75"
    code_bg: str = "#f8f8f6"
    hover: str = "#f0f0ee"
    active_file: str = "#EEEDFE"
    red: str = "#E24B4A"
    amber: str = "#BA7517"


@dataclass(frozen=True)
class FontConfig:
    """Font configuration."""
    ui: str = "Inter,Segoe UI,Helvetica Neue,Arial,sans-serif"
    mono: str = "JetBrains Mono,Fira Code,Consolas,Monospace"


@dataclass
class LLMConfig:
    """LLM configuration."""
    model: str = "gemma4:e2b"
    max_iterations: int = 7
    context_limit: int = 15  # messages to include in context


@dataclass
class UIConfig:
    """UI layout configuration."""
    window_width: int = 1100
    window_height: int = 700
    min_width: int = 800
    min_height: int = 520
    sidebar_width: int = 220
    right_panel_min_width: int = 260
    header_height: int = 42
    input_height: int = 52
    status_bar_height: int = 26


@dataclass
class Config:
    """Master configuration container."""
    colors: ColorConfig = field(default_factory=ColorConfig)
    fonts: FontConfig = field(default_factory=FontConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    # Convenience access
    @property
    def C(self) -> Dict[str, str]:
        """Get colors as dict for backward compatibility."""
        return {
            "bg": self.colors.bg,
            "bg_white": self.colors.bg_white,
            "bg_sidebar": self.colors.bg_sidebar,
            "border": self.colors.border,
            "border2": self.colors.border2,
            "text": self.colors.text,
            "text2": self.colors.text2,
            "text_muted": self.colors.text_muted,
            "text_dim": self.colors.text_dim,
            "purple": self.colors.purple,
            "purple_lt": self.colors.purple_lt,
            "purple_text": self.colors.purple_text,
            "teal": self.colors.teal,
            "teal_lt": self.colors.teal_lt,
            "teal_bd": self.colors.teal_bd,
            "teal_text": self.colors.teal_text,
            "user_bubble": self.colors.user_bubble,
            "tool_dot": self.colors.tool_dot,
            "code_bg": self.colors.code_bg,
            "hover": self.colors.hover,
            "active_file": self.colors.active_file,
            "red": self.colors.red,
            "amber": self.colors.amber,
        }

    @property
    def FONT_UI(self) -> str:
        return self.fonts.ui

    @property
    def FONT_MONO(self) -> str:
        return self.fonts.mono

    @property
    def OLLAMA_MODEL(self) -> str:
        return self.llm.model


# Global default config
DEFAULT_CONFIG = Config()
