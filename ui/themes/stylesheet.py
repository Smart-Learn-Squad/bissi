"""Master QSS template for BISSI.

Uses {token} placeholders that ThemeEngine substitutes at runtime.
Think of this as the global CSS of the app.
"""

MASTER_QSS = """
/* ── App & Window ─────────────────────────────────────────── */
QMainWindow, QWidget#BissiRoot {{
    background: {bg};
    color: {text};
    font-family: {font_ui};
}}

/* ── Sidebar ──────────────────────────────────────────────── */
QWidget#Sidebar {{
    background: {bg_sidebar};
    border-right: 1px solid {border};
}}

QWidget#SessionItem {{
    background: {bg_sidebar};
    border-radius: {radius_sm};
}}

QWidget#SessionItem:hover {{
    background: {bg_hover};
}}

QWidget#SessionItem[active="true"] {{
    background: {bg_active};
}}

/* ── TitleBar ─────────────────────────────────────────────── */
QWidget#TitleBar {{
    background: {bg_white};
    border-bottom: 1px solid {border};
}}

/* ── ChatPanel ────────────────────────────────────────────── */
QWidget#ChatPanel {{
    background: {bg_white};
}}

QWidget#ChatHeader {{
    background: {bg_white};
    border-bottom: 1px solid {border};
}}

/* ── Message bubbles ──────────────────────────────────────── */
QLabel#BubbleUser {{
    background: {bubble_user};
    color: {bubble_user_text};
    border-radius: {radius_lg} {radius_lg} 2px {radius_lg};
    padding: 8px 12px;
    font-size: 13px;
    font-family: {font_ui};
}}

QLabel#BubbleAI {{
    background: {bubble_ai};
    color: {bubble_ai_text};
    border: 1px solid {bubble_ai_bd};
    border-radius: 2px {radius_lg} {radius_lg} {radius_lg};
    padding: 10px 12px;
    font-size: 13px;
    font-family: {font_ui};
}}

/* ── Input bar ────────────────────────────────────────────── */
QWidget#InputBar {{
    background: {bg_white};
    border-top: 1px solid {border};
}}

QLineEdit#ChatInput {{
    background: {bg_input};
    color: {text};
    border: 1px solid {border2};
    border-radius: {radius_md};
    padding: 7px 12px;
    font-size: 13px;
    font-family: {font_ui};
    selection-background-color: {accent_lt};
}}

QLineEdit#ChatInput:focus {{
    border-color: {accent};
    outline: none;
}}

QPushButton#SendButton {{
    background: {accent};
    color: #ffffff;
    border: none;
    border-radius: {radius_md};
    font-size: 16px;
    font-weight: 500;
}}

QPushButton#SendButton:hover {{
    background: {accent_dark};
}}

QPushButton#SendButton:pressed {{
    background: {accent_deep};
}}

/* ── Right panel ──────────────────────────────────────────── */
QWidget#RightPanel {{
    background: {bg_sidebar};
}}

QWidget#TabBar {{
    background: {bg_white};
    border-bottom: 1px solid {border};
}}

QPushButton#TabButton {{
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: {text_muted};
    font-size: 12px;
    font-family: {font_ui};
    padding: 8px 14px;
}}

QPushButton#TabButton:checked {{
    color: {accent};
    border-bottom-color: {accent};
    font-weight: 500;
}}

QPushButton#TabButton:hover:!checked {{
    color: {text2};
}}

/* ── File Explorer ────────────────────────────────────────── */
QTreeWidget#FileTree {{
    background: {bg_sidebar};
    border: none;
    font-size: 12px;
    font-family: {font_ui};
    color: {text2};
    outline: none;
}}

QTreeWidget#FileTree::item {{
    padding: 3px 6px;
    border-radius: {radius_sm};
}}

QTreeWidget#FileTree::item:hover {{
    background: {bg_hover};
}}

QTreeWidget#FileTree::item:selected {{
    background: {bg_active};
    color: {accent_dark};
}}

QTreeWidget#FileTree::branch {{
    background: {bg_sidebar};
}}

/* ── Code Editor ──────────────────────────────────────────── */
QWidget#EditorHeader {{
    background: {bg_white};
    border-bottom: 1px solid {border};
}}

QTextEdit#CodeEditor {{
    background: {bg_white};
    color: {text2};
    border: none;
    padding: 12px 14px;
    font-family: {font_mono};
    font-size: 12px;
    selection-background-color: {bg_active};
}}

/* ── Status bar ───────────────────────────────────────────── */
QWidget#StatusBar {{
    background: {bg_white};
    border-top: 1px solid {border};
}}

/* ── Scroll bars ──────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {bg};
    width: 5px;
    border-radius: 2px;
}}

QScrollBar::handle:vertical {{
    background: {border2};
    border-radius: 2px;
    min-height: 20px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {bg};
    height: 5px;
    border-radius: 2px;
}}

QScrollBar::handle:horizontal {{
    background: {border2};
    border-radius: 2px;
    min-width: 20px;
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── Splitter ─────────────────────────────────────────────── */
QSplitter::handle {{
    background: {border};
}}

/* ── Theme toggle button ──────────────────────────────────── */
QPushButton#ThemeToggle {{
    background: {bg_hover};
    color: {text_muted};
    border: 1px solid {border};
    border-radius: {radius_sm};
    padding: 3px 8px;
    font-size: 11px;
    font-family: {font_ui};
}}

QPushButton#ThemeToggle:hover {{
    background: {bg_active};
    color: {accent};
    border-color: {accent};
}}
"""
