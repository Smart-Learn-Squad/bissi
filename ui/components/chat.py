"""Chat panel and message bubble components for BISSI."""

from PyQt6.QtWidgets import (
    QWidget, QSizePolicy, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QLineEdit, QPushButton, QScrollArea,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QKeyEvent

from ui.styles.theme import Theme
from ui.parser import parse, configure as _configure_parser
from core.config import DEFAULT_CONFIG


class MessageBubble(QFrame):
    """Chat message bubble widget."""

    def __init__(self, role: str, theme: Theme = None, parent=None):
        super().__init__(parent)
        self.role = role
        self.theme = theme or Theme()
        self._text = ""
        # Injecter la palette dans le parser
        _configure_parser({
            "code_bg":    self.theme.C["code_bg"],
            "code_text":  self.theme.C["text2"],
            "code_border":self.theme.C["border"],
            "inline_bg":  self.theme.C["purple_lt"],
            "inline_text":self.theme.C["purple_text"],
            "h1_color":   self.theme.C["text"],
            "h2_color":   self.theme.C["text2"],
            "h3_color":   self.theme.C["purple"],
            "hr_color":   self.theme.C["border2"],
            "text":       self.theme.C["text2"],
            "mono":       self.theme.FONT_MONO,
            "ui":         self.theme.FONT_UI,
        })
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 4, 0, 4)
        self._layout.setSpacing(3)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")

        if self.role == "assistant":
            name_row = QHBoxLayout()
            name_row.setSpacing(6)
            dot = QLabel()
            dot.setFixedSize(7, 7)
            dot.setStyleSheet(
                f"background:{self.theme.C['teal']};border-radius:3px;"
            )
            name = QLabel("Bissi")
            name.setStyleSheet(
                f"font-size:11px;color:{self.theme.C['text_muted']};"
                f"font-family:{self.theme.FONT_UI};"
            )
            name_row.addWidget(dot)
            name_row.addWidget(name)
            name_row.addStretch()
            self._layout.addLayout(name_row)

        self._bubble = QLabel()
        self._bubble.setWordWrap(True)
        self._bubble.setTextFormat(Qt.TextFormat.RichText)
        self._bubble.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        if self.role == "user":
            self._bubble.setAlignment(Qt.AlignmentFlag.AlignRight)
            self._bubble.setStyleSheet(f"""
                background: {self.theme.C['user_bubble']};
                color: #ffffff;
                border-radius: 12px 12px 2px 12px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: {self.theme.FONT_UI};
                line-height: 1.5;
            """)
        else:
            self._bubble.setStyleSheet(f"""
                background: {self.theme.C['bg']};
                color: {self.theme.C['text2']};
                border: 0.5px solid {self.theme.C['border']};
                border-radius: 2px 12px 12px 12px;
                padding: 10px 12px;
                font-size: 13px;
                font-family: {self.theme.FONT_UI};
                line-height: 1.6;
            """)

        self._layout.addWidget(self._bubble)

    def set_text(self, text: str):
        self._text = text
        if self.role == "assistant":
            self._bubble.setText(parse(text).html)
        else:
            self._bubble.setText(text)

    def append_text(self, token: str):
        self._text += token
        if self.role == "assistant":
            self._bubble.setText(parse(self._text).html)
        else:
            self._bubble.setText(self._text)

    def add_tool_line(self, name: str, args: str, result: str = None):
        """Add a tool execution line to the message."""
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QVBoxLayout(row)
        rl.setContentsMargins(0, 2, 0, 2)
        rl.setSpacing(1)

        call_row = QHBoxLayout()
        call_row.setSpacing(6)
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{self.theme.C['teal']};font-size:10px;")
        nm = QLabel(name)
        nm.setStyleSheet(
            f"color:{self.theme.C['teal_text']};font-weight:500;"
            f"font-size:12px;font-family:{self.theme.FONT_UI};"
        )
        ar = QLabel(args)
        ar.setStyleSheet(
            f"color:{self.theme.C['text_dim']};font-size:12px;"
            f"font-family:{self.theme.FONT_UI};"
        )
        call_row.addWidget(dot)
        call_row.addWidget(nm)
        call_row.addWidget(ar)
        call_row.addStretch()
        rl.addLayout(call_row)

        if result:
            res = QLabel(f"  └ {result}")
            res.setStyleSheet(
                f"color:{self.theme.C['text_muted']};font-size:11px;"
                f"font-family:{self.theme.FONT_UI};padding-left:14px;"
            )
            rl.addWidget(res)

        self._layout.insertWidget(self._layout.count() - 1, row)


class ChatPanel(QWidget):
    """Main chat panel with message history and input."""

    message_submitted = pyqtSignal(str)
    interrupt_requested = pyqtSignal()

    def __init__(self, theme: Theme = None):
        super().__init__()
        self.theme = theme or Theme()
        self._setup_ui()
        self._history = []
        self._hist_idx = -1
        self._locked = False
        self._current_bubble = None

    def _setup_ui(self):
        self.setStyleSheet(
            f"background:{self.theme.C['bg_white']};border:none;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(42)
        hdr.setStyleSheet(f"""
            background: {self.theme.C['bg_white']};
            border-bottom: 0.5px solid {self.theme.C['border']};
        """)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)
        self.chat_title = QLabel("Nouvelle session")
        self.chat_title.setStyleSheet(
            f"font-size:13px;font-weight:500;color:{self.theme.C['text']};"
            f"font-family:{self.theme.FONT_UI};"
        )
        model_badge = QLabel(DEFAULT_CONFIG.OLLAMA_MODEL)
        model_badge.setStyleSheet(f"""
            font-size:11px;color:{self.theme.C['purple']};
            background:{self.theme.C['purple_lt']};
            border-radius:4px;padding:2px 7px;
            font-family:{self.theme.FONT_UI};
        """)
        hl.addWidget(self.chat_title)
        hl.addStretch()
        hl.addWidget(model_badge)
        layout.addWidget(hdr)

        # Scroll area for messages
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {self.theme.C['bg_white']}; }}
            {self.theme.scroll_bar_style}
        """)

        self.messages_w = QWidget()
        self.messages_w.setStyleSheet(
            f"background:{self.theme.C['bg_white']};"
        )
        self.messages_layout = QVBoxLayout(self.messages_w)
        self.messages_layout.setContentsMargins(16, 16, 16, 16)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        self.scroll.setWidget(self.messages_w)
        layout.addWidget(self.scroll, stretch=1)

        # Input bar
        input_w = QWidget()
        input_w.setFixedHeight(52)
        input_w.setStyleSheet(f"""
            background: {self.theme.C['bg_white']};
            border-top: 0.5px solid {self.theme.C['border']};
        """)
        il = QHBoxLayout(input_w)
        il.setContentsMargins(12, 9, 12, 9)
        il.setSpacing(8)

        self.input = QLineEdit()
        self.input.setPlaceholderText(
            "Pose une question à Bissi…  (↑↓ historique · Ctrl+C interrupt)"
        )
        self.input.setStyleSheet(f"""
            QLineEdit {{
                border: 0.5px solid {self.theme.C['border2']};
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 13px;
                color: {self.theme.C['text']};
                background: {self.theme.C['bg_white']};
                font-family: {self.theme.FONT_UI};
            }}
            QLineEdit:focus {{
                border-color: {self.theme.C['purple']};
                outline: none;
            }}
        """)
        self.input.returnPressed.connect(self._submit)
        self.input.installEventFilter(self)

        send_btn = QPushButton()
        send_btn.setFixedSize(32, 32)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.C['purple']};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background: {self.theme.C['purple_text']}; }}
            QPushButton:pressed {{ background: #26215C; }}
        """)
        send_btn.setText("→")
        send_btn.setStyleSheet(send_btn.styleSheet() +
            f"color: white; font-size: 16px; font-weight: 500;"
        )
        send_btn.clicked.connect(self._submit)

        il.addWidget(self.input, stretch=1)
        il.addWidget(send_btn)
        layout.addWidget(input_w)

    def eventFilter(self, obj, event):
        if obj == self.input and isinstance(event, QKeyEvent):
            if (event.key() == Qt.Key.Key_C and
                    event.modifiers() == Qt.KeyboardModifier.ControlModifier):
                self.interrupt_requested.emit()
                return True
            if event.key() == Qt.Key.Key_Up and self._history:
                self._hist_idx = min(
                    self._hist_idx + 1, len(self._history) - 1
                )
                self.input.setText(self._history[self._hist_idx])
                return True
            if event.key() == Qt.Key.Key_Down:
                if self._hist_idx > 0:
                    self._hist_idx -= 1
                    self.input.setText(self._history[self._hist_idx])
                else:
                    self._hist_idx = -1
                    self.input.clear()
                return True
        return super().eventFilter(obj, event)

    def _submit(self):
        text = self.input.text().strip()
        if not text or self._locked:
            return
        self._history.insert(0, text)
        self._hist_idx = -1
        self.input.clear()
        self.message_submitted.emit(text)

    def lock(self):
        """Lock input while agent is processing."""
        self._locked = True
        self.input.setEnabled(False)
        self.input.setPlaceholderText("Bissi réfléchit… (Ctrl+C pour interrompre)")

    def unlock(self):
        """Unlock input after processing."""
        self._locked = False
        self.input.setEnabled(True)
        self.input.setPlaceholderText(
            "Pose une question à Bissi…  (↑↓ historique · Ctrl+C interrupt)"
        )
        self.input.setFocus()

    def add_user_message(self, text: str):
        """Add user message to chat."""
        self.chat_title.setText(text[:40] + ("…" if len(text) > 40 else ""))
        bubble = MessageBubble("user", self.theme)
        bubble.set_text(text)
        self._insert_bubble(bubble)

    def start_agent_message(self) -> MessageBubble:
        """Create and return assistant message bubble for streaming."""
        self._current_bubble = MessageBubble("assistant", self.theme)
        self._current_bubble.set_text("▌")   # curseur en attente
        self._insert_bubble(self._current_bubble)
        return self._current_bubble

    def _insert_bubble(self, bubble: MessageBubble):
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, bubble)
        QTimer.singleShot(50, self._scroll_bottom)

    def _scroll_bottom(self):
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def add_tool_to_current(self, name: str, args: str, result: str = None):
        """Add tool line to current assistant message."""
        if self._current_bubble:
            self._current_bubble.add_tool_line(name, args, result)
            QTimer.singleShot(50, self._scroll_bottom)

    def append_token_to_current(self, token: str):
        """Append streaming token to current message."""
        if self._current_bubble:
            self._current_bubble.append_text(token)
            QTimer.singleShot(10, self._scroll_bottom)

    def add_system_msg(self, text: str, color: str = None):
        """Add system message (e.g., errors, status)."""
        lbl = QLabel(text)
        c = color or self.theme.C['text_muted']
        lbl.setStyleSheet(
            f"color:{c};font-size:12px;font-family:{self.theme.FONT_UI};"
            f"padding:4px 0;background:transparent;"
        )
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, lbl)
        QTimer.singleShot(50, self._scroll_bottom)
