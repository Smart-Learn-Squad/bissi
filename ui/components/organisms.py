"""Organism UI components - complex structures.

Organisms: Sidebars, headers, chat areas composed of molecules.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QScrollArea, QStackedWidget, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ui.components.atoms import (
    AtomButton, AtomLabel, AtomIconButton, AtomSpinner, 
    AtomDivider, AtomBadge
)
from ui.components.molecules import (
    ChatBubble, NavItem, ConversationItem, 
    MessageInput, SearchBar
)
from ui.styles.theme import Colors, Typography, Spacing, Radius, Shadows


class Sidebar(QFrame):
    """Left sidebar with navigation and conversations."""
    
    conversation_selected = pyqtSignal(int)
    new_chat_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)
        
        # Header with logo and new chat
        header = QHBoxLayout()
        
        # Logo
        logo = AtomLabel("BISSI", "xl2")
        logo.setStyleSheet(f"color: {Colors.PRIMARY_600};")
        header.addWidget(logo)
        
        header.addStretch()
        
        # New chat button
        new_btn = AtomIconButton("+", size=36)
        new_btn.setToolTip("New chat")
        new_btn.clicked.connect(self.new_chat_clicked.emit)
        header.addWidget(new_btn)
        
        layout.addLayout(header)
        
        # Search
        self.search = SearchBar("Search conversations...")
        layout.addWidget(self.search)
        
        # Divider
        layout.addWidget(AtomDivider())
        
        # Conversations list
        self.conversations_layout = QVBoxLayout()
        self.conversations_layout.setSpacing(8)
        self.conversations_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Scroll area for conversations
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        container.setLayout(self.conversations_layout)
        scroll.setWidget(container)
        
        layout.addWidget(scroll, 1)
        
        # Footer - user info
        footer = QHBoxLayout()
        user_avatar = AtomIconButton("👤", size=36)
        footer.addWidget(user_avatar)
        
        user_name = AtomLabel("User", "sm")
        footer.addWidget(user_name)
        footer.addStretch()
        
        settings_btn = AtomIconButton("⚙", size=32)
        footer.addWidget(settings_btn)
        
        layout.addLayout(footer)
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.GRAY_50};
                border-right: 1px solid {Colors.GRAY_200};
            }}
        """)
        
        self.setMaximumWidth(320)
        self.setMinimumWidth(260)
        
        self._conversations = {}
        self._active_id = None
    
    def add_conversation(self, conv_id: int, title: str, preview: str = "", 
                        timestamp: str = ""):
        """Add conversation to sidebar."""
        item = ConversationItem(title, preview, timestamp)
        item.selected.connect(lambda: self._on_select(conv_id))
        self.conversations_layout.addWidget(item)
        self._conversations[conv_id] = item
    
    def _on_select(self, conv_id: int):
        """Handle conversation selection."""
        self.set_active_conversation(conv_id)
        self.conversation_selected.emit(conv_id)
    
    def set_active_conversation(self, conv_id: int):
        """Set active conversation highlight."""
        # Deactivate previous
        if self._active_id in self._conversations:
            self._conversations[self._active_id].set_active(False)
        
        # Activate new
        if conv_id in self._conversations:
            self._conversations[conv_id].set_active(True)
            self._active_id = conv_id
    
    def update_conversation_preview(self, conv_id: int, preview: str):
        """Update conversation preview text."""
        if conv_id in self._conversations:
            item = self._conversations[conv_id]
            item.preview_label.setText(preview[:50] + "..." if len(preview) > 50 else preview)
    
    def clear_conversations(self):
        """Clear all conversations."""
        while self.conversations_layout.count():
            item = self.conversations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._conversations.clear()
        self._active_id = None


class ChatArea(QScrollArea):
    """Scrollable chat message area."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Container
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(16)
        self.layout.addStretch()
        
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        
        # Hide scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Styling
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {Colors.BACKGROUND};
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {Colors.BACKGROUND};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.GRAY_300};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.GRAY_400};
            }}
        """)
    
    def add_message(self, text: str, is_user: bool = False, 
                   sender: str = "", timestamp: str = ""):
        """Add message bubble to chat."""
        # Remove bottom stretch
        item = self.layout.takeAt(self.layout.count() - 1)
        if item.spacerItem():
            del item
        
        # Create bubble
        bubble = ChatBubble(text, is_user, sender, timestamp)
        self.layout.addWidget(bubble)
        
        # Add stretch back
        self.layout.addStretch()
        
        # Auto-scroll
        QTimer.singleShot(50, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """Scroll to bottom of chat."""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_chat(self):
        """Clear all messages."""
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def show_typing_indicator(self):
        """Show typing indicator."""
        self._typing_indicator = AtomLabel("● ● ●", "base")
        self._typing_indicator.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            padding: 12px 20px;
        """)
        
        # Remove stretch and add indicator
        item = self.layout.takeAt(self.layout.count() - 1)
        if item.spacerItem():
            del item
        
        self.layout.addWidget(self._typing_indicator)
        self.layout.addStretch()
        self._scroll_to_bottom()
    
    def hide_typing_indicator(self):
        """Remove typing indicator."""
        if hasattr(self, '_typing_indicator'):
            self._typing_indicator.deleteLater()
            del self._typing_indicator


class Header(QFrame):
    """Top header bar with title and actions."""
    
    menu_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    
    def __init__(self, title: str = "New Conversation", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(16)
        
        # Menu button (mobile style)
        self.menu_btn = AtomIconButton("☰", size=36)
        self.menu_btn.setVisible(False)  # Hidden on desktop
        self.menu_btn.clicked.connect(self.menu_clicked.emit)
        layout.addWidget(self.menu_btn)
        
        # Title
        self.title_label = AtomLabel(title, "lg")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Model badge
        self.model_badge = AtomBadge("Gemma 3", "blue")
        layout.addWidget(self.model_badge)
        
        # Actions
        self.export_btn = AtomIconButton("💾", size=36)
        self.export_btn.setToolTip("Export conversation")
        self.export_btn.clicked.connect(self.export_clicked.emit)
        layout.addWidget(self.export_btn)
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-bottom: 1px solid {Colors.GRAY_200};
            }}
        """)
        
        self.setMaximumHeight(64)
    
    def set_title(self, title: str):
        """Update header title."""
        self.title_label.setText(title)
    
    def set_model(self, model: str):
        """Update model badge."""
        self.model_badge.setText(model)


class InputArea(QFrame):
    """Bottom input area with message composition."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 20)
        layout.setSpacing(0)
        
        # Message input molecule
        self.message_input = MessageInput()
        layout.addWidget(self.message_input)
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND};
                border-top: 1px solid {Colors.GRAY_200};
            }}
        """)
    
    def connect_signals(self, send_slot, attach_slot):
        """Connect input signals."""
        self.message_input.message_sent.connect(send_slot)
        self.message_input.file_attached.connect(attach_slot)
    
    def set_enabled(self, enabled: bool):
        """Enable/disable input."""
        self.message_input.set_enabled(enabled)


class WelcomeScreen(QFrame):
    """Initial welcome screen with suggestions."""
    
    suggestion_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Logo
        logo = AtomLabel("🤖", "xl3")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        
        # Welcome text
        title = AtomLabel("Welcome to BISSI", "xl3")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = AtomLabel(
            "Your smart office assistant powered by local AI",
            "base"
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(subtitle)
        
        layout.addSpacing(30)
        
        # Suggestions
        suggestions_title = AtomLabel("Try asking:", "sm")
        suggestions_title.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        layout.addWidget(suggestions_title)
        
        suggestions = [
            "📄 Analyze a PDF document",
            "📊 Create a spreadsheet from data",
            "🔍 Search files in my documents",
            "✉️ Draft an email response",
            "💻 Explain this Python code",
        ]
        
        for suggestion in suggestions:
            btn = AtomButton(suggestion, variant="ghost", size="sm")
            btn.clicked.connect(lambda checked, s=suggestion: self.suggestion_clicked.emit(s))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.SURFACE};
                    border: 1px solid {Colors.GRAY_200};
                    color: {Colors.TEXT_PRIMARY};
                    text-align: left;
                    padding: 12px 16px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.GRAY_50};
                    border-color: {Colors.GRAY_300};
                }}
            """)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND};
                border: none;
            }}
        """)


class ToastNotification(QFrame):
    """Temporary toast notification."""
    
    def __init__(self, message: str, variant: str = "info", duration: int = 3000, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        
        # Icon based on variant
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        icon = AtomLabel(icons.get(variant, "ℹ️"), "base")
        layout.addWidget(icon)
        
        # Message
        label = AtomLabel(message, "sm")
        layout.addWidget(label, 1)
        
        # Colors
        colors = {
            "info": (Colors.PRIMARY_100, Colors.PRIMARY_700),
            "success": ("#d1fae5", "#047857"),
            "warning": ("#fef3c7", "#b45309"),
            "error": ("#fee2e2", "#b91c1c"),
        }
        bg, fg = colors.get(variant, colors["info"])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {Colors.GRAY_200};
                border-radius: {Radius.LG};
                color: {fg};
            }}
        """)
        
        # Auto-hide
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(duration, self.deleteLater)
