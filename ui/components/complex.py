"""Complex UI components - advanced widgets.

Complex: File drop zones, code blocks with syntax highlighting, markdown renderer, liquid glass.
"""
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QTextEdit, QPushButton, QSizePolicy,
    QFileDialog, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont, QColor, QPainter, QBrush, QRadialGradient

from ui.components.atoms import AtomButton, AtomIconButton, AtomLabel, AtomBadge
from ui.styles.theme import Colors, Typography, Spacing, Radius


class FileDropZone(QFrame):
    """Drag and drop file upload zone."""
    
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAcceptDrops(True)
        self.setMinimumHeight(160)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        
        # Icon
        icon = AtomLabel("📁", "xl3")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        # Text
        self.text = AtomLabel("Drop files here or click to browse", "base")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.text)
        
        # Subtext
        subtext = AtomLabel("Supports PDF, DOCX, XLSX, TXT, images", "xs")
        subtext.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtext.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        layout.addWidget(subtext)
        
        # Browse button
        self.browse_btn = AtomButton("Browse Files", variant="secondary", size="sm")
        self.browse_btn.clicked.connect(self._browse_files)
        layout.addWidget(self.browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Styling
        self._normal_style = f"""
            QFrame {{
                background-color: {Colors.GRAY_50};
                border: 2px dashed {Colors.GRAY_300};
                border-radius: {Radius.XL};
            }}
        """
        self._hover_style = f"""
            QFrame {{
                background-color: {Colors.PRIMARY_50};
                border: 2px dashed {Colors.PRIMARY_400};
                border-radius: {Radius.XL};
            }}
        """
        self.setStyleSheet(self._normal_style)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept drag events with files."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self._hover_style)
    
    def dragLeaveEvent(self, event):
        """Reset style on drag leave."""
        self.setStyleSheet(self._normal_style)
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop."""
        self.setStyleSheet(self._normal_style)
        
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            self.files_dropped.emit(files)
    
    def _browse_files(self):
        """Open file dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files", "",
            "All Files (*.*);;Documents (*.pdf *.docx *.txt);;Images (*.png *.jpg)"
        )
        if files:
            self.files_dropped.emit(files)


class CodeBlock(QFrame):
    """Syntax-highlighted code block with copy button."""
    
    def __init__(self, code: str, language: str = "python", parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with language and copy button
        header = QHBoxLayout()
        header.setContentsMargins(12, 8, 12, 8)
        
        # Language badge
        lang_badge = AtomBadge(language, "gray")
        header.addWidget(lang_badge)
        
        header.addStretch()
        
        # Copy button
        copy_btn = AtomButton("Copy", variant="ghost", size="sm")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(code))
        header.addWidget(copy_btn)
        
        header_widget = QFrame()
        header_widget.setLayout(header)
        header_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.GRAY_800};
                border-top-left-radius: {Radius.MD};
                border-top-right-radius: {Radius.MD};
            }}
        """)
        layout.addWidget(header_widget)
        
        # Code area
        self.code_edit = QTextEdit()
        self.code_edit.setPlainText(code)
        self.code_edit.setReadOnly(True)
        self.code_edit.setFont(QFont("JetBrains Mono, Fira Code, Consolas, monospace", 13))
        self.code_edit.setMaximumHeight(400)
        
        # Simple syntax highlighting with stylesheet
        self.code_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.GRAY_900};
                color: #e5e7eb;
                border: none;
                border-bottom-left-radius: {Radius.MD};
                border-bottom-right-radius: {Radius.MD};
                padding: 16px;
            }}
        """)
        
        layout.addWidget(self.code_edit)
        
        # Container styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: {Radius.MD};
            }}
        """)
    
    def _copy_to_clipboard(self, text: str):
        """Copy code to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)


class MarkdownRenderer(QFrame):
    """Simple markdown to rich text renderer."""
    
    def __init__(self, markdown: str = "", parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        self.content = QLabel()
        self.content.setWordWrap(True)
        self.content.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        layout.addWidget(self.content)
        
        if markdown:
            self.set_markdown(markdown)
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: {Radius.MD};
            }}
            QLabel {{
                font-size: {Typography.BASE};
                font-family: {Typography.FONT_FAMILY};
                color: {Colors.TEXT_PRIMARY};
                line-height: 1.6;
            }}
        """)
    
    def set_markdown(self, text: str):
        """Convert markdown to HTML and display."""
        html = self._markdown_to_html(text)
        self.content.setText(html)
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Simple markdown parser."""
        html = markdown
        
        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
        html = re.sub(r'__(.+?)__', r'<b>\1</b>', html)
        
        # Italic
        html = re.sub(r'\*(.+?)\*', r'<i>\1</i>', html)
        html = re.sub(r'_(.+?)_', r'<i>\1</i>', html)
        
        # Code inline
        html = re.sub(r'`(.+?)`', r'<code style="background:#f3f4f6;padding:2px 4px;border-radius:4px;font-family:monospace;">\1</code>', html)
        
        # Headers
        html = re.sub(r'^### (.+)$', r'<h3 style="margin:16px 0 8px;font-size:18px;font-weight:600;">\1</h3>', html, flags=re.M)
        html = re.sub(r'^## (.+)$', r'<h2 style="margin:20px 0 12px;font-size:20px;font-weight:600;">\1</h2>', html, flags=re.M)
        html = re.sub(r'^# (.+)$', r'<h1 style="margin:24px 0 16px;font-size:24px;font-weight:700;">\1</h1>', html, flags=re.M)
        
        # Lists
        html = re.sub(r'^\* (.+)$', r'<li style="margin:4px 0;">\1</li>', html, flags=re.M)
        
        # Links
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" style="color:#3b82f6;text-decoration:none;">\1</a>', html)
        
        # Line breaks
        html = html.replace('\n\n', '<br><br>')
        html = html.replace('\n', '<br>')
        
        return html


class FilePreviewCard(QFrame):
    """Preview card for attached files with thumbnail/info."""
    
    removed = pyqtSignal()
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        
        from pathlib import Path
        from utils.helpers import format_file_size
        
        path = Path(file_path)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # Thumbnail or icon
        if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            # Try to show image thumbnail
            try:
                from PyQt6.QtGui import QPixmap
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                    thumb = QLabel()
                    thumb.setPixmap(pixmap)
                    thumb.setFixedSize(48, 48)
                    thumb.setStyleSheet(f"border-radius: {Radius.SM}; overflow: hidden;")
                    layout.addWidget(thumb)
                else:
                    raise ValueError("Invalid image")
            except:
                icon = AtomLabel("🖼", "xl")
                layout.addWidget(icon)
        else:
            # File type icon
            icons = {
                '.pdf': '📄', '.doc': '📝', '.docx': '📝',
                '.xls': '📊', '.xlsx': '📊', '.csv': '📊',
                '.py': '🐍', '.js': '📜', '.html': '🌐',
                '.txt': '📃', '.md': '📋', '.json': '📋'
            }
            icon = icons.get(path.suffix.lower(), '📎')
            icon_label = AtomLabel(icon, "xl")
            layout.addWidget(icon_label)
        
        # File info
        info = QVBoxLayout()
        info.setSpacing(2)
        
        name = AtomLabel(path.name, "sm")
        info.addWidget(name)
        
        size_text = format_file_size(path.stat().st_size)
        size = AtomLabel(size_text, "xs")
        size.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        info.addWidget(size)
        
        layout.addLayout(info, 1)
        
        # Remove button
        remove = AtomIconButton("×", size=28)
        remove.clicked.connect(self.removed.emit)
        layout.addWidget(remove)
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.GRAY_50};
                border: 1px solid {Colors.GRAY_200};
                border-radius: {Radius.MD};
            }}
        """)
        
        self.setMaximumWidth(280)


class ThinkingIndicator(QFrame):
    """Animated thinking/typing indicator."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Dots
        self.dots = []
        for i in range(3):
            dot = QLabel("●")
            dot.setStyleSheet(f"""
                color: {Colors.GRAY_400};
                font-size: 10px;
            """)
            layout.addWidget(dot)
            self.dots.append(dot)
        
        layout.addStretch()
        
        # Timer for animation
        from PyQt6.QtCore import QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self._step = 0
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.GRAY_100};
                border-radius: {Radius.XL};
                max-width: 80px;
            }}
        """)
    
    def start(self):
        """Start animation."""
        self.timer.start(400)
        self.show()
    
    def stop(self):
        """Stop animation."""
        self.timer.stop()
        self.hide()
    
    def _animate(self):
        """Animate dots."""
        colors = [Colors.GRAY_400, Colors.GRAY_500, Colors.GRAY_600, Colors.GRAY_500]
        for i, dot in enumerate(self.dots):
            color_idx = (self._step + i) % len(colors)
            dot.setStyleSheet(f"color: {colors[color_idx]}; font-size: 10px;")
        self._step += 1


class PersonaSelector(QFrame):
    """Persona/role selector cards."""
    
    persona_selected = pyqtSignal(str)
    
    PERSONAS = {
        "default": {"icon": "🤖", "name": "Default", "desc": "General purpose assistant"},
        "researcher": {"icon": "🔬", "name": "Researcher", "desc": "Academic & scientific analysis"},
        "student": {"icon": "📚", "name": "Student", "desc": "Learning & study support"},
        "office": {"icon": "💼", "name": "Office", "desc": "Productivity & documents"},
    }
    
    def __init__(self, current: str = "default", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        
        for key, info in self.PERSONAS.items():
            card = self._create_card(key, info, key == current)
            layout.addWidget(card)
        
        layout.addStretch()
        
        self.setStyleSheet("background: transparent; border: none;")
    
    def _create_card(self, key: str, info: dict, active: bool) -> QFrame:
        """Create persona card."""
        card = QFrame()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        
        # Icon
        icon = AtomLabel(info["icon"], "xl")
        layout.addWidget(icon)
        
        # Name
        name = AtomLabel(info["name"], "sm")
        layout.addWidget(name)
        
        # Description
        desc = AtomLabel(info["desc"], "xs")
        desc.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        layout.addWidget(desc)
        
        # Active indicator
        if active:
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.PRIMARY_50};
                    border: 2px solid {Colors.PRIMARY_500};
                    border-radius: {Radius.LG};
                }}
            """)
        else:
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.SURFACE};
                    border: 1px solid {Colors.GRAY_200};
                    border-radius: {Radius.LG};
                }}
                QFrame:hover {{
                    border-color: {Colors.GRAY_300};
                    background-color: {Colors.GRAY_50};
                }}
            """)
        
        card.mousePressEvent = lambda e: self.persona_selected.emit(key)
        
        return card


class LiquidGlassInput(QFrame):
    """Chat input with liquid glass (frosted) effect."""
    
    message_sent = pyqtSignal(str)
    file_attached = pyqtSignal(str)
    
    def __init__(self, placeholder: str = "Send a message", parent=None):
        super().__init__(parent)
        
        self.setMinimumHeight(56)
        self.setMaximumWidth(720)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Plus button (attach)
        self.attach_btn = self._create_icon_button("+", size=32)
        self.attach_btn.clicked.connect(self._attach_file)
        layout.addWidget(self.attach_btn)
        
        # Globe/shortcut button
        self.globe_btn = self._create_icon_button("🌐", size=32)
        layout.addWidget(self.globe_btn)
        
        # Text input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setFrame(False)
        self.input_field.returnPressed.connect(self._send_message)
        self.input_field.textChanged.connect(self._update_send_button)
        
        # Style input (transparent)
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: white;
                font-size: {Typography.BASE};
                font-family: {Typography.FONT_FAMILY};
                padding: 0;
            }}
            QLineEdit::placeholder {{
                color: {Colors.GRAY_400};
            }}
        """)
        
        layout.addWidget(self.input_field, 1)
        
        # Model selector badge
        self.model_badge = QLabel("gemma4:e2b ▾")
        self.model_badge.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {Colors.GRAY_300};
                border-radius: {Radius.FULL};
                padding: 6px 12px;
                font-size: {Typography.XS};
                font-family: {Typography.FONT_FAMILY};
            }}
        """)
        layout.addWidget(self.model_badge)
        
        # Send button
        self.send_btn = self._create_icon_button("↑", size=32)
        self.send_btn.setEnabled(False)
        self.send_btn.setStyleSheet(self.send_btn.styleSheet() + f"""
            QPushButton:enabled {{
                background-color: white;
                color: {Colors.GRAY_900};
            }}
        """)
        self.send_btn.clicked.connect(self._send_message)
        layout.addWidget(self.send_btn)
        
        # Enable blur/frosted effect
        self._setup_liquid_glass()
    
    def _create_icon_button(self, icon: str, size: int = 32):
        """Create circular icon button."""
        btn = QPushButton(icon)
        btn.setFixedSize(size, size)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.08);
                color: {Colors.GRAY_300};
                border: none;
                border-radius: {size // 2}px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
        """)
        return btn
    
    def _setup_liquid_glass(self):
        """Setup the frosted glass appearance."""
        # Semi-transparent dark background
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 45, 0.75);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {Radius.XL2};
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
    
    def _update_send_button(self):
        """Enable send button when there's text."""
        has_text = bool(self.input_field.text().strip())
        self.send_btn.setEnabled(has_text)
    
    def _send_message(self):
        """Emit message signal."""
        text = self.input_field.text().strip()
        if text:
            self.message_sent.emit(text)
            self.input_field.clear()
    
    def _attach_file(self):
        """Open file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Attach File", "", "All Files (*.*)"
        )
        if file_path:
            self.file_attached.emit(file_path)
    
    def set_model(self, model: str):
        """Update model badge."""
        self.model_badge.setText(f"{model} ▾")


class CenteredAvatar(QFrame):
    """Centered logo/avatar with glow effect."""
    
    def __init__(self, icon: str = "🤖", size: int = 80, parent=None):
        super().__init__(parent)
        
        self.icon = icon
        self.size = size
        self.setFixedSize(size, size)
        
        # Setup glow animation
        self._glow_opacity = 0.6
        self._glow_direction = 1
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_glow)
        self._timer.start(50)
        
        self.setStyleSheet("background: transparent; border: none;")
    
    def _animate_glow(self):
        """Animate glow effect."""
        self._glow_opacity += 0.02 * self._glow_direction
        if self._glow_opacity >= 0.8 or self._glow_opacity <= 0.4:
            self._glow_direction *= -1
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for glowing effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw glow
        glow_color = QColor(255, 255, 255, int(self._glow_opacity * 255))
        gradient = QRadialGradient(
            self.size // 2, self.size // 2, self.size // 2
        )
        gradient.setColorAt(0, glow_color)
        gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())
        
        # Draw icon
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(self.size // 3)
        painter.setFont(font)
        
        rect = self.rect()
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.icon)
        
        painter.end()


class OllamaStyleWindow(QWidget):
    """Main window with Ollama-style centered interface."""
    
    message_sent = pyqtSignal(str)
    
    def __init__(self, title: str = "BISSI", icon: str = "🤖", parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)
        
        # Dark background
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(20, 16, 20, 16)
        
        # Menu button
        menu_btn = self._create_top_button("☰")
        top_bar.addWidget(menu_btn)
        
        top_bar.addStretch()
        
        # New chat button
        new_chat_btn = self._create_top_button("✎")
        top_bar.addWidget(new_chat_btn)
        
        top_widget = QWidget()
        top_widget.setLayout(top_bar)
        layout.addWidget(top_widget)
        
        # Center content
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(24)
        
        # Avatar
        self.avatar = CenteredAvatar(icon, size=80)
        center_layout.addWidget(self.avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Spacer to push input to bottom
        center_layout.addStretch()
        
        # Input container
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_layout.setContentsMargins(40, 0, 40, 40)
        
        # Liquid glass input
        self.input_widget = LiquidGlassInput("Send a message")
        self.input_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Fixed
        )
        self.input_widget.message_sent.connect(self.message_sent.emit)
        
        input_layout.addWidget(self.input_widget)
        input_container.setMaximumWidth(800)
        
        center_layout.addWidget(input_container, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        layout.addWidget(center_widget, 1)
    
    def _create_top_button(self, icon: str):
        """Create top bar button."""
        btn = QPushButton(icon)
        btn.setFixedSize(36, 36)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.GRAY_400};
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }}
        """)
        return btn
    
    def set_model(self, model: str):
        """Update model in input."""
        self.input_widget.set_model(model)
