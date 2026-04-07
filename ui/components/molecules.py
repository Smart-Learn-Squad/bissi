"""Molecular UI components - combinations of atoms.

Molecules: Chat bubbles, message cards, search bars, etc.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.components.atoms import (
    AtomButton, AtomInput, AtomIconButton, AtomLabel,
    AtomBadge, AtomAvatar, AtomSpinner, AtomDivider
)
from ui.styles.theme import Colors, Typography, Spacing, Radius, Shadows


class ChatBubble(QFrame):
    """Message bubble with avatar and content."""
    
    def __init__(self, text: str, is_user: bool = False, 
                 sender_name: str = "", timestamp: str = "", parent=None):
        super().__init__(parent)
        
        self.is_user = is_user
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)
        
        # Avatar
        if sender_name:
            self.avatar = AtomAvatar(sender_name, size=36)
            if not is_user:
                main_layout.addWidget(self.avatar)
        
        # Content container
        content = QVBoxLayout()
        content.setSpacing(4)
        content.setAlignment(
            Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft
        )
        
        # Sender name (if not user)
        if sender_name and not is_user:
            name_label = AtomLabel(sender_name, "xs")
            content.addWidget(name_label)
        
        # Message bubble
        bubble_frame = QFrame()
        bubble_layout = QVBoxLayout(bubble_frame)
        bubble_layout.setContentsMargins(14, 10, 14, 10)
        
        self.message_label = QLabel(text)
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        bubble_layout.addWidget(self.message_label)
        
        content.addWidget(bubble_frame)
        
        # Timestamp
        if timestamp:
            time_label = AtomLabel(timestamp, "xs")
            content.addWidget(time_label)
        
        main_layout.addLayout(content)
        
        if sender_name and is_user:
            main_layout.addWidget(self.avatar)
        
        main_layout.addStretch() if not is_user else main_layout.insertStretch(0)
        
        # Styling
        self._apply_bubble_style(bubble_frame)
    
    def _apply_bubble_style(self, bubble: QFrame):
        """Apply bubble styling based on sender."""
        if self.is_user:
            bg = Colors.PRIMARY_500
            text_color = "white"
            radius = f"{Radius.XL} {Radius.XL} {Radius.SM} {Radius.XL}"
        else:
            bg = Colors.GRAY_100
            text_color = Colors.TEXT_PRIMARY
            radius = f"{Radius.XL} {Radius.XL} {Radius.XL} {Radius.SM}"
        
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border-radius: {radius};
            }}
            QLabel {{
                color: {text_color};
                font-size: {Typography.BASE};
                font-family: {Typography.FONT_FAMILY};
                line-height: 1.5;
                background: transparent;
            }}
        """)
        
        bubble.setMaximumWidth(600)


class SearchBar(QFrame):
    """Search input with icon and button."""
    
    search_triggered = pyqtSignal(str)
    
    def __init__(self, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Icon
        icon = AtomLabel("🔍", "lg")
        icon.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        layout.addWidget(icon)
        
        # Input
        self.input_field = AtomInput(placeholder)
        self.input_field.returnPressed.connect(self._on_search)
        layout.addWidget(self.input_field, 1)
        
        # Button
        self.search_btn = AtomIconButton("→", size=36)
        self.search_btn.clicked.connect(self._on_search)
        layout.addWidget(self.search_btn)
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.GRAY_200};
                border-radius: {Radius.LG};
                padding: 8px 12px;
            }}
        """)
    
    def _on_search(self):
        text = self.input_field.text().strip()
        if text:
            self.search_triggered.emit(text)
    
    def clear(self):
        self.input_field.clear()


class FileCard(QFrame):
    """File attachment card with icon and info."""
    
    removed = pyqtSignal()
    
    def __init__(self, filename: str, filesize: str = "", filetype: str = "", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        # File icon based on type
        icons = {"pdf": "📄", "docx": "📝", "xlsx": "📊", "image": "🖼", "code": "💻"}
        icon = icons.get(filetype, "📎")
        
        icon_label = AtomLabel(icon, "xl")
        layout.addWidget(icon_label)
        
        # Info
        info = QVBoxLayout()
        info.setSpacing(2)
        
        name_label = AtomLabel(filename, "sm")
        info.addWidget(name_label)
        
        if filesize:
            size_label = AtomLabel(filesize, "xs")
            info.addWidget(size_label)
        
        layout.addLayout(info, 1)
        
        # Remove button
        remove_btn = AtomIconButton("×", size=28)
        remove_btn.clicked.connect(self.removed.emit)
        layout.addWidget(remove_btn)
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.GRAY_50};
                border: 1px solid {Colors.GRAY_200};
                border-radius: {Radius.MD};
            }}
        """)
        
        self.setMaximumWidth(300)


class NavItem(QFrame):
    """Navigation sidebar item."""
    
    clicked = pyqtSignal()
    
    def __init__(self, icon: str, label: str, active: bool = False, parent=None):
        super().__init__(parent)
        
        self.active = active
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        # Icon
        icon_label = AtomLabel(icon, "base")
        layout.addWidget(icon_label)
        
        # Label
        self.text_label = AtomLabel(label, "sm")
        layout.addWidget(self.text_label, 1)
        
        # Badge (optional)
        self.badge = AtomBadge("", "blue")
        self.badge.setVisible(False)
        layout.addWidget(self.badge)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = lambda e: self.clicked.emit()
        
        self._apply_style()
    
    def _apply_style(self):
        if self.active:
            bg = Colors.PRIMARY_50
            border = Colors.PRIMARY_200
        else:
            bg = "transparent"
            border = "transparent"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: {Radius.MD};
            }}
            QFrame:hover {{
                background-color: {Colors.GRAY_100 if not self.active else Colors.PRIMARY_50};
            }}
        """)
    
    def set_active(self, active: bool):
        self.active = active
        self._apply_style()
    
    def set_badge(self, count: int):
        if count > 0:
            self.badge.setText(str(count))
            self.badge.setVisible(True)
        else:
            self.badge.setVisible(False)


class MessageInput(QFrame):
    """Input area with attachments and send button."""
    
    message_sent = pyqtSignal(str)
    file_attached = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Attachments area
        self.attachments_layout = QHBoxLayout()
        self.attachments_layout.setSpacing(8)
        layout.addLayout(self.attachments_layout)
        
        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        
        # Attach button
        self.attach_btn = AtomIconButton("📎", size=40)
        self.attach_btn.setToolTip("Attach file")
        self.attach_btn.clicked.connect(self._attach_file)
        input_row.addWidget(self.attach_btn)
        
        # Text input
        self.input_field = AtomInput("Type a message...")
        self.input_field.returnPressed.connect(self._send)
        input_row.addWidget(self.input_field, 1)
        
        # Send button
        self.send_btn = AtomButton("➤", variant="primary")
        self.send_btn.setFixedWidth(44)
        self.send_btn.clicked.connect(self._send)
        input_row.addWidget(self.send_btn)
        
        layout.addLayout(input_row)
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-top: 1px solid {Colors.GRAY_200};
                padding: 16px 20px;
            }}
        """)
        
        self._attached_files = []
    
    def _attach_file(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Attach File", "",
            "All Files (*.*)"
        )
        if file_path:
            self._attached_files.append(file_path)
            self._add_file_card(file_path)
            self.file_attached.emit(file_path)
    
    def _add_file_card(self, file_path: str):
        from pathlib import Path
        from utils.helpers import format_file_size
        
        path = Path(file_path)
        size = format_file_size(path.stat().st_size)
        
        filetype = "pdf" if path.suffix == ".pdf" else \
                   "docx" if path.suffix in [".docx", ".doc"] else \
                   "xlsx" if path.suffix in [".xlsx", ".xls"] else \
                   "image" if path.suffix in [".png", ".jpg", ".jpeg"] else "file"
        
        card = FileCard(path.name, size, filetype)
        card.removed.connect(lambda: self._remove_file(file_path, card))
        self.attachments_layout.addWidget(card)
    
    def _remove_file(self, file_path: str, card: FileCard):
        if file_path in self._attached_files:
            self._attached_files.remove(file_path)
        card.deleteLater()
    
    def _send(self):
        text = self.input_field.text().strip()
        if text or self._attached_files:
            self.message_sent.emit(text)
            self.input_field.clear()
            # Clear attachments
            while self.attachments_layout.count():
                item = self.attachments_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self._attached_files.clear()
    
    def set_enabled(self, enabled: bool):
        self.input_field.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self.attach_btn.setEnabled(enabled)


class ConversationItem(QFrame):
    """Conversation list item with title and preview."""
    
    selected = pyqtSignal()
    
    def __init__(self, title: str, preview: str = "", timestamp: str = "", 
                 active: bool = False, parent=None):
        super().__init__(parent)
        
        self.active = active
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        
        # Header row
        header = QHBoxLayout()
        
        # Title
        self.title_label = AtomLabel(title, "sm")
        header.addWidget(self.title_label, 1)
        
        # Timestamp
        if timestamp:
            time_label = AtomLabel(timestamp, "xs")
            header.addWidget(time_label)
        
        layout.addLayout(header)
        
        # Preview
        if preview:
            preview_text = preview[:50] + "..." if len(preview) > 50 else preview
            self.preview_label = AtomLabel(preview_text, "xs")
            layout.addWidget(self.preview_label)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = lambda e: self.selected.emit()
        
        self._apply_style()
    
    def _apply_style(self):
        if self.active:
            bg = Colors.PRIMARY_50
            border = Colors.PRIMARY_200
            title_color = Colors.PRIMARY_700
        else:
            bg = Colors.SURFACE
            border = Colors.GRAY_200
            title_color = Colors.TEXT_PRIMARY
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: {Radius.MD};
            }}
            QFrame:hover {{
                background-color: {Colors.GRAY_50 if not self.active else Colors.PRIMARY_50};
                border-color: {Colors.GRAY_300 if not self.active else Colors.PRIMARY_300};
            }}
        """)
        
        self.title_label.setStyleSheet(f"color: {title_color};")
    
    def set_active(self, active: bool):
        self.active = active
        self._apply_style()
