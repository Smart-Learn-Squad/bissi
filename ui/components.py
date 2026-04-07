"""Atomic UI components for BISSI.

Web-styled PyQt6 components using QSS.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QScrollArea,
    QFrame, QFileDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QFont


class AtomButton(QPushButton):
    """Atomic button with web styling."""
    
    def __init__(self, text: str = "", icon: str = "", parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Web-style CSS
        self.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)


class AtomInput(QLineEdit):
    """Atomic input field with web styling."""
    
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(44)
        
        self.setStyleSheet("""
            QLineEdit {
                background-color: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                padding: 10px 16px;
                font-size: 15px;
                color: #1f2937;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
        """)


class AtomLabel(QLabel):
    """Atomic label with web typography."""
    
    def __init__(self, text: str = "", size: str = "normal", parent=None):
        super().__init__(text, parent)
        
        sizes = {
            "small": "font-size: 12px; color: #6b7280;",
            "normal": "font-size: 14px; color: #374151;",
            "medium": "font-size: 16px; color: #1f2937; font-weight: 500;",
            "large": "font-size: 20px; color: #111827; font-weight: 600;",
            "title": "font-size: 24px; color: #111827; font-weight: 700;"
        }
        
        self.setStyleSheet(f"""
            QLabel {{
                {sizes.get(size, sizes['normal'])}
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
            }}
        """)


class MoleculeChatBubble(QFrame):
    """Chat bubble message component (molecule)."""
    
    def __init__(self, text: str, is_user: bool = False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(0)
        
        # Message label
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # Spacer for alignment
        if is_user:
            layout.addStretch()
            layout.addWidget(self.label)
        else:
            layout.addWidget(self.label)
            layout.addStretch()
        
        # Styling based on sender
        self._apply_style()
        
        self.setMaximumWidth(800)
    
    def _apply_style(self):
        """Apply bubble styling."""
        if self.is_user:
            # User message - blue bubble
            bg_color = "#3b82f6"
            text_color = "white"
            radius = "18px 18px 4px 18px"
        else:
            # AI message - gray bubble
            bg_color = "#f3f4f6"
            text_color = "#1f2937"
            radius = "18px 18px 18px 4px"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: {radius};
                border: none;
            }}
            QLabel {{
                color: {text_color};
                font-size: 15px;
                line-height: 1.5;
                padding: 4px;
                background: transparent;
            }}
        """)


class MoleculeNavBar(QFrame):
    """Navigation bar component (molecule)."""
    
    new_chat_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(16)
        
        # Logo/Title
        self.title = AtomLabel("BISSI", "title")
        layout.addWidget(self.title)
        
        layout.addStretch()
        
        # New chat button
        self.new_btn = AtomButton("+ New Chat")
        self.new_btn.clicked.connect(self.new_chat_clicked.emit)
        layout.addWidget(self.new_btn)
        
        # Settings button
        self.settings_btn = AtomButton("⚙")
        self.settings_btn.setFixedWidth(44)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)
        
        # Styling
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e5e7eb;
            }
        """)
        self.setMaximumHeight(70)


class OrganismChatArea(QScrollArea):
    """Chat conversation area (organism)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Container widget
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(16)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.addStretch()
        
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        
        # Styling
        self.setStyleSheet("""
            QScrollArea {
                background-color: #fafafa;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #fafafa;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: #d1d5db;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9ca3af;
            }
        """)
    
    def add_message(self, text: str, is_user: bool = False):
        """Add message bubble to chat."""
        # Remove stretch at end
        if self.layout.count() > 0:
            item = self.layout.takeAt(self.layout.count() - 1)
            if item.spacerItem():
                del item
        
        # Add bubble
        bubble = MoleculeChatBubble(text, is_user)
        self.layout.addWidget(bubble)
        
        # Add stretch back
        self.layout.addStretch()
        
        # Scroll to bottom
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        )
    
    def clear_chat(self):
        """Clear all messages."""
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class OrganismInputArea(QFrame):
    """Input area with send button (organism)."""
    
    message_sent = pyqtSignal(str)
    file_attached = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)
        
        # File attach button
        self.attach_btn = AtomButton("📎")
        self.attach_btn.setFixedWidth(44)
        self.attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #6b7280;
                border: none;
                border-radius: 10px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        self.attach_btn.clicked.connect(self._attach_file)
        layout.addWidget(self.attach_btn)
        
        # Input field
        self.input_field = AtomInput("Type your message...")
        self.input_field.returnPressed.connect(self._send_message)
        layout.addWidget(self.input_field, 1)
        
        # Send button
        self.send_btn = AtomButton("➤")
        self.send_btn.setFixedWidth(44)
        self.send_btn.clicked.connect(self._send_message)
        layout.addWidget(self.send_btn)
        
        # Styling
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #e5e7eb;
            }
        """)
        self.setMaximumHeight(90)
    
    def _send_message(self):
        """Send message signal."""
        text = self.input_field.text().strip()
        if text:
            self.message_sent.emit(text)
            self.input_field.clear()
    
    def _attach_file(self):
        """Open file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Attach File", "",
            "Documents (*.pdf *.docx *.txt *.xlsx);;Images (*.png *.jpg);;All Files (*.*)"
        )
        if file_path:
            self.file_attached.emit(file_path)
    
    def set_enabled(self, enabled: bool):
        """Enable/disable input."""
        self.input_field.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
