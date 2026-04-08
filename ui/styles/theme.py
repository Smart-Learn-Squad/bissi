"""Theme constants for BISSI UI.

Design tokens (colors, fonts, spacing) for consistent styling.
"""

# Colors - Tailwind-inspired palette
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication

class Colors:
    @staticmethod
    def is_dark():
        palette = QApplication.palette()
        return palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window).lightness() < 128

    # --- Standard Palette (Restored for compatibility) ---
    PRIMARY_50 = "#eff6ff"
    PRIMARY_100 = "#dbeafe"
    PRIMARY_200 = "#bfdbfe"
    PRIMARY_300 = "#93c5fd"
    PRIMARY_400 = "#60a5fa"
    PRIMARY_500 = "#3b82f6"
    PRIMARY_600 = "#2563eb"
    PRIMARY_700 = "#1d4ed8"
    PRIMARY_800 = "#1e40af"
    PRIMARY_900 = "#1e3a8a"
    
    GRAY_50 = "#f9fafb"
    GRAY_100 = "#f3f4f6"
    GRAY_200 = "#e5e7eb"
    GRAY_300 = "#d1d5db"
    GRAY_400 = "#9ca3af"
    GRAY_500 = "#6b7280"
    GRAY_600 = "#4b5563"
    GRAY_700 = "#374151"
    GRAY_800 = "#1f2937"
    GRAY_900 = "#111827"

    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    INFO = "#3b82f6"

    # --- Adaptive Surface Logic ---
    @classmethod
    def update_tokens(cls):
        dark = cls.is_dark()
        
        # Base backgrounds
        cls.BACKGROUND = "#080808" if dark else "#f8f9fa"
        cls.SURFACE = "#111111" if dark else "#ffffff"
        cls.BORDER = "rgba(255, 255, 255, 0.08)" if dark else "rgba(0, 0, 0, 0.1)"
        
        # Semantic Text (Adaptive)
        cls.TEXT_PRIMARY = "#ffffff" if dark else "#111827"
        cls.TEXT_SECONDARY = "rgba(255, 255, 255, 0.7)" if dark else "#4b5563"
        cls.TEXT_MUTED = "rgba(255, 255, 255, 0.5)" if dark else "#9ca3af"
        
        # Glassmorphism Tokens
        if dark:
            cls.GLASS_BASE = "rgba(15, 15, 20, 0.65)"
            cls.GLASS_SURFACE = "rgba(255, 255, 255, 0.04)"
            cls.GLASS_BORDER = "rgba(255, 255, 255, 0.08)"
            cls.GLASS_BORDER_LIGHT = "rgba(255, 255, 255, 0.15)"
            cls.GLASS_TEXT = "rgba(255, 255, 255, 0.95)"
            cls.GLASS_TEXT_MUTED = "rgba(255, 255, 255, 0.55)"
        else:
            cls.GLASS_BASE = "rgba(255, 255, 255, 0.70)"
            cls.GLASS_SURFACE = "rgba(0, 0, 0, 0.03)"
            cls.GLASS_BORDER = "rgba(0, 0, 0, 0.10)"
            cls.GLASS_BORDER_LIGHT = "rgba(255, 255, 255, 0.40)"
            cls.GLASS_TEXT = "rgba(0, 0, 0, 0.90)"
            cls.GLASS_TEXT_MUTED = "rgba(0, 0, 0, 0.50)"

# Initial token generation
Colors.update_tokens()


# Typography
class Typography:
    FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    
    # Sizes
    XS = "12px"
    SM = "14px"
    BASE = "15px"
    LG = "16px"
    XL = "18px"
    XL2 = "20px"
    XL3 = "24px"
    XL4 = "30px"
    
    # Weights
    NORMAL = "400"
    MEDIUM = "500"
    SEMIBOLD = "600"
    BOLD = "700"


# Spacing
class Spacing:
    XS = "4px"
    SM = "8px"
    MD = "12px"
    BASE = "16px"
    LG = "20px"
    XL = "24px"
    XL2 = "32px"
    XL3 = "40px"
    XL4 = "48px"


# Border radius
class Radius:
    SM = "4px"
    MD = "8px"
    LG = "12px"
    XL = "16px"
    XL2 = "20px"
    FULL = "9999px"


# Shadows
class Shadows:
    SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
    LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
    XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"


# Transitions
class Transitions:
    FAST = "150ms"
    NORMAL = "200ms"
    SLOW = "300ms"
    EASING = "cubic-bezier(0.4, 0, 0.2, 1)"
