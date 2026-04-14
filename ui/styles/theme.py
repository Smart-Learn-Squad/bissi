"""Theme and styling utilities for BISSI UI."""

from core.config import Config, ColorConfig, FontConfig

DEFAULT_CONFIG = Config()


def get_color_palette() -> dict:
    """Get color palette as dict for backward compatibility."""
    return DEFAULT_CONFIG.C


def get_fonts() -> tuple:
    """Get font tuple for backward compatibility."""
    return DEFAULT_CONFIG.fonts.ui, DEFAULT_CONFIG.fonts.mono


class Theme:
    """Theme manager for consistent styling."""

    def __init__(self, config: Config = None):
        self.config = config or DEFAULT_CONFIG
        self.C = self.config.C
        self.FONT_UI = self.config.FONT_UI
        self.FONT_MONO = self.config.FONT_MONO

    # Common style templates
    @property
    def sidebar_style(self) -> str:
        return f"""
            background: {self.C['bg_sidebar']};
            border-right: 0.5px solid {self.C['border']};
        """

    @property
    def base_widget_style(self) -> str:
        return f"""
            background: {self.C['bg_white']};
            border: none;
        """

    @property
    def border_style(self) -> str:
        return f"border: 0.5px solid {self.C['border']};"

    @property
    def text_style_primary(self) -> str:
        return f"""
            font-size: 13px;
            font-weight: 500;
            color: {self.C['text']};
            font-family: {self.FONT_UI};
        """

    @property
    def text_style_secondary(self) -> str:
        return f"""
            font-size: 12px;
            color: {self.C['text_muted']};
            font-family: {self.FONT_UI};
        """

    @property
    def text_style_dimmed(self) -> str:
        return f"""
            font-size: 11px;
            color: {self.C['text_dim']};
            font-family: {self.FONT_UI};
        """

    @property
    def code_style(self) -> str:
        return f"""
            background: {self.C['code_bg']};
            font-family: {self.FONT_MONO};
        """

    @property
    def scroll_bar_style(self) -> str:
        return f"""
            QScrollBar:vertical {{
                background: {self.C['bg']};
                width: 5px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.C['border2']};
                border-radius: 2px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """

    @property
    def header_style(self) -> str:
        return f"""
            background: {self.C['bg_white']};
            border-bottom: 0.5px solid {self.C['border']};
        """

    @property
    def footer_style(self) -> str:
        return f"""
            background: {self.C['bg_sidebar']};
            border-top: 0.5px solid {self.C['border']};
        """

    @property
    def hover_style(self) -> str:
        return f"background: {self.C['hover']};"

    @property
    def active_style(self) -> str:
        return f"background: {self.C['active_file']};"

    @property
    def purple_accent_style(self) -> str:
        return f"""
            color: {self.C['purple_text']};
            background: {self.C['purple_lt']};
        """

    @property
    def teal_accent_style(self) -> str:
        return f"""
            color: {self.C['teal_text']};
            background: {self.C['teal_lt']};
            border: 0.5px solid {self.C['teal_bd']};
        """

    @property
    def error_style(self) -> str:
        return f"color: {self.C['red']};"

    @property
    def warning_style(self) -> str:
        return f"color: {self.C['amber']};"


# Global theme instance
theme = Theme()
