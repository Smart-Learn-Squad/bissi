"""Code editor component for BISSI."""

import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor

from ui.styles.theme import Theme


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code."""

    def __init__(self, doc, theme: Theme = None):
        super().__init__(doc)
        self.theme = theme or Theme()
        self.rules = []
        self._setup_rules()

    def _setup_rules(self):
        """Configure highlighting rules."""
        def rule(pattern: str, color: str, bold: bool = False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:
                fmt.setFontWeight(700)
            self.rules.append((QRegularExpression(pattern), fmt))

        # Keywords
        rule(r"\b(import|from|def|class|return|if|elif|else|for|while|"
             r"in|not|and|or|True|False|None|with|as|try|except|pass|"
             r"lambda|yield|raise|break|continue|global|del)\b",
             self.theme.C["purple"], bold=True)
        # Strings
        rule(r"\"[^\"]*\"|'[^']*'", self.theme.C["amber"])
        # Comments
        rule(r"#[^\n]*", self.theme.C["text_dim"])
        # Numbers
        rule(r"\b\d+\.?\d*\b", self.theme.C["teal"])

    def highlightBlock(self, text: str):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class CodeEditor(QWidget):
    """Read-only code editor with syntax highlighting."""

    def __init__(self, theme: Theme = None):
        super().__init__()
        self.theme = theme or Theme()
        self._hl = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = QWidget()
        self.header.setFixedHeight(34)
        self.header.setStyleSheet(f"""
            background: {self.theme.C['bg_white']};
            border-top: 0.5px solid {self.theme.C['border']};
            border-bottom: 0.5px solid {self.theme.C['border']};
        """)
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(8)

        self.file_label = QLabel("Aucun fichier ouvert")
        self.file_label.setStyleSheet(
            f"font-size:12px;color:{self.theme.C['text_muted']};font-family:{self.theme.FONT_UI};"
        )
        self.agent_badge = QLabel()
        self.agent_badge.hide()
        self.agent_badge.setStyleSheet(f"""
            font-size:10px;color:{self.theme.C['teal_text']};
            background:{self.theme.C['teal_lt']};
            border-radius:3px;padding:1px 6px;
            font-family:{self.theme.FONT_UI};
        """)
        hl.addWidget(self.file_label)
        hl.addWidget(self.agent_badge)
        hl.addStretch()
        layout.addWidget(self.header)

        # Editor
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background: {self.theme.C['bg_white']};
                color: {self.theme.C['text2']};
                border: none;
                padding: 12px 14px;
                font-family: {self.theme.FONT_MONO};
                font-size: 12px;
                line-height: 1.7;
                selection-background-color: {self.theme.C['purple_lt']};
            }}
            {self.theme.scroll_bar_style}
        """)
        layout.addWidget(self.editor, stretch=1)

    def open_file(self, path: str, by_agent: bool = False):
        """Open file in editor with optional syntax highlighting."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.file_label.setText(os.path.basename(path))
            self.file_label.setStyleSheet(
                f"font-size:12px;color:{self.theme.C['text']};font-weight:500;"
                f"font-family:{self.theme.FONT_UI};"
            )
            if path.endswith(".py"):
                self._hl = PythonHighlighter(self.editor.document(), self.theme)
            else:
                self._hl = None

            if by_agent:
                self.agent_badge.setText("ouvert par Bissi")
                self.agent_badge.show()
            else:
                self.agent_badge.hide()
        except Exception as e:
            self.editor.setPlainText(f"Impossible d'ouvrir : {e}")

    def show_placeholder(self):
        """Clear editor and show placeholder."""
        self.editor.setPlainText("")
        self.file_label.setText("Aucun fichier ouvert")
        self.file_label.setStyleSheet(
            f"font-size:12px;color:{self.theme.C['text_muted']};font-family:{self.theme.FONT_UI};"
        )
        self.agent_badge.hide()
