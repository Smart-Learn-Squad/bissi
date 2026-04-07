"""Theme constants for BISSI UI.

Design tokens (colors, fonts, spacing) for consistent styling.
"""

# Colors - Tailwind-inspired palette
class Colors:
    # Primary
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
    
    # Gray
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
    
    # Semantic
    BACKGROUND = "#fafafa"
    SURFACE = "#ffffff"
    BORDER = "#e5e7eb"
    TEXT_PRIMARY = "#111827"
    TEXT_SECONDARY = "#6b7280"
    TEXT_MUTED = "#9ca3af"
    
    # Status
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    INFO = "#3b82f6"


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
