"""Design tokens for BISSI themes.

Each token dict is a complete set of CSS variables.
Add a new dict here to create a new theme.
"""
from __future__ import annotations

# ── Light (défaut) ────────────────────────────────────────────
LIGHT: dict[str, str] = {
    # Backgrounds
    "bg":           "#f5f5f3",
    "bg_white":     "#ffffff",
    "bg_sidebar":   "#fafaf8",
    "bg_input":     "#ffffff",
    "bg_hover":     "#f0f0ee",
    "bg_active":    "#EEEDFE",
    "bg_code":      "#f8f8f6",

    # Borders
    "border":       "#e8e8e8",
    "border2":      "#dddddd",

    # Text
    "text":         "#1a1a1a",
    "text2":        "#2C2C2A",
    "text_muted":   "#888888",
    "text_dim":     "#aaaaaa",

    # Accent — Purple
    "accent":       "#534AB7",
    "accent_lt":    "#EEEDFE",
    "accent_dark":  "#3C3489",
    "accent_deep":  "#26215C",

    # Teal
    "teal":         "#1D9E75",
    "teal_lt":      "#E1F5EE",
    "teal_bd":      "#9FE1CB",
    "teal_dark":    "#0F6E56",

    # Status
    "red":          "#E24B4A",
    "amber":        "#BA7517",
    "amber_lt":     "#FAEEDA",
    "amber_bd":     "#FAC775",

    # Bubbles
    "bubble_user":  "#534AB7",
    "bubble_user_text": "#ffffff",
    "bubble_ai":    "#ffffff",
    "bubble_ai_text":"#2C2C2A",
    "bubble_ai_bd": "#e8e8e8",

    # Typography
    "font_ui":   "Inter, Segoe UI, Helvetica Neue, Arial, sans-serif",
    "font_mono": "JetBrains Mono, Fira Code, Consolas, Monospace",

    # Radius
    "radius_sm":    "4px",
    "radius_md":    "8px",
    "radius_lg":    "12px",
    "radius_xl":    "16px",
}

# ── Dark ──────────────────────────────────────────────────────
DARK: dict[str, str] = {
    # Backgrounds
    "bg":           "#111111",
    "bg_white":     "#1a1a1a",
    "bg_sidebar":   "#151515",
    "bg_input":     "#1e1e1e",
    "bg_hover":     "#242424",
    "bg_active":    "#2a2560",
    "bg_code":      "#161616",

    # Borders
    "border":       "#2a2a2a",
    "border2":      "#333333",

    # Text
    "text":         "#f0f0ee",
    "text2":        "#d4d4d2",
    "text_muted":   "#777777",
    "text_dim":     "#555555",

    # Accent — Purple (légèrement plus vif en dark)
    "accent":       "#7C71E1",
    "accent_lt":    "#2a2560",
    "accent_dark":  "#9B92F5",
    "accent_deep":  "#b0aaff",

    # Teal
    "teal":         "#22C98E",
    "teal_lt":      "#0d2e22",
    "teal_bd":      "#1a6648",
    "teal_dark":    "#4ADBA8",

    # Status
    "red":          "#F06060",
    "amber":        "#F0A030",
    "amber_lt":     "#2a1f00",
    "amber_bd":     "#705000",

    # Bubbles
    "bubble_user":  "#534AB7",
    "bubble_user_text": "#ffffff",
    "bubble_ai":    "#1e1e1e",
    "bubble_ai_text":"#d4d4d2",
    "bubble_ai_bd": "#2a2a2a",

    # Typography (identique)
    "font_ui":   "Inter, Segoe UI, Helvetica Neue, Arial, sans-serif",
    "font_mono": "JetBrains Mono, Fira Code, Consolas, Monospace",

    # Radius (identique)
    "radius_sm":    "4px",
    "radius_md":    "8px",
    "radius_lg":    "12px",
    "radius_xl":    "16px",
}

# ── Registre des thèmes disponibles ──────────────────────────
THEMES: dict[str, dict[str, str]] = {
    "light": LIGHT,
    "dark":  DARK,
}
