"""Atomic UI components - the smallest building blocks.

Atoms: Buttons, inputs, labels, icons that can't be broken down further.
"""
from PyQt6.QtWidgets import (
    QPushButton, QLineEdit, QLabel, QCheckBox, 
    QComboBox, QSpinBox, QProgressBar, QTextEdit,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor

from ui.styles.theme import Colors, Typography, Spacing, Radius, Shadows, Transitions


class AtomButton(QPushButton):
    """Atomic button with multiple variants."""
    
    VARIANTS = {
        "primary": {
            "bg": Colors.PRIMARY_500,
            "color": "white",
            "hover": Colors.PRIMARY_600,
            "active": Colors.PRIMARY_700,
        },
        "secondary": {
            "bg": Colors.GRAY_100,
            "color": Colors.GRAY_700,
            "hover": Colors.GRAY_200,
            "active": Colors.GRAY_300,
        },
        "ghost": {
            "bg": "transparent",
            "color": Colors.GRAY_600,
            "hover": Colors.GRAY_100,
            "active": Colors.GRAY_200,
        },
        "danger": {
            "bg": Colors.ERROR,
            "color": "white",
            "hover": "#dc2626",
            "active": "#b91c1c",
        },
        "success": {
            "bg": Colors.SUCCESS,
            "color": "white",
            "hover": "#059669",
            "active": "#047857",
        }
    }
    
    SIZES = {
        "sm": {"height": "32px", "padding": "6px 12px", "font": Typography.SM},
        "md": {"height": "40px", "padding": "8px 16px", "font": Typography.BASE},
        "lg": {"height": "48px", "padding": "12px 24px", "font": Typography.LG},
    }
    
    def __init__(self, text: str = "", variant: str = "primary", size: str = "md", 
                 parent=None, icon: str = ""):
        super().__init__(text, parent)
        
        self.variant = variant
        self.size = size
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()
        
        if icon:
            self.setText(f"{icon} {text}" if text else icon)
    
    def _apply_style(self):
        """Apply QSS styling."""
        v = self.VARIANTS.get(self.variant, self.VARIANTS["primary"])
        s = self.SIZES.get(self.size, self.SIZES["md"])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {v['bg']};
                color: {v['color']};
                border: none;
                border-radius: {Radius.MD};
                padding: {s['padding']};
                font-size: {s['font']};
                font-weight: {Typography.MEDIUM};
                font-family: {Typography.FONT_FAMILY};
                min-height: {s['height']};
            }}
            QPushButton:hover {{
                background-color: {v['hover']};
            }}
            QPushButton:pressed {{
                background-color: {v['active']};
            }}
            QPushButton:disabled {{
                background-color: {Colors.GRAY_300};
                color: {Colors.GRAY_500};
            }}
        """)


class AtomIconButton(QPushButton):
    """Icon-only circular button."""
    
    def __init__(self, icon: str, size: int = 40, parent=None):
        super().__init__(icon, parent)
        
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.GRAY_600};
                border: 1px solid {Colors.GRAY_200};
                border-radius: {size // 2}px;
                font-size: 18px;
                font-family: {Typography.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Colors.GRAY_100};
                color: {Colors.GRAY_700};
            }}
            QPushButton:pressed {{
                background-color: {Colors.GRAY_200};
            }}
        """)


class AtomInput(QLineEdit):
    """Atomic text input field."""
    
    def __init__(self, placeholder: str = "", multiline: bool = False, parent=None):
        super().__init__(parent)
        
        self.setPlaceholderText(placeholder)
        
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.SURFACE};
                border: 2px solid {Colors.GRAY_200};
                border-radius: {Radius.LG};
                padding: 12px 16px;
                font-size: {Typography.BASE};
                font-family: {Typography.FONT_FAMILY};
                color: {Colors.TEXT_PRIMARY};
                min-height: 44px;
            }}
            QLineEdit:focus {{
                border-color: {Colors.PRIMARY_500};
                background-color: {Colors.SURFACE};
            }}
            QLineEdit::placeholder {{
                color: {Colors.TEXT_MUTED};
            }}
            QLineEdit:disabled {{
                background-color: {Colors.GRAY_100};
                color: {Colors.GRAY_400};
            }}
        """)


class AtomTextArea(QTextEdit):
    """Multi-line text input."""
    
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        
        self.setPlaceholderText(placeholder)
        self.setMaximumHeight(120)
        
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.SURFACE};
                border: 2px solid {Colors.GRAY_200};
                border-radius: {Radius.LG};
                padding: 12px 16px;
                font-size: {Typography.BASE};
                font-family: {Typography.FONT_FAMILY};
                color: {Colors.TEXT_PRIMARY};
            }}
            QTextEdit:focus {{
                border-color: {Colors.PRIMARY_500};
            }}
            QTextEdit::placeholder {{
                color: {Colors.TEXT_MUTED};
            }}
        """)


class AtomLabel(QLabel):
    """Atomic text label with size variants."""
    
    STYLES = {
        "xs": {"size": Typography.XS, "weight": Typography.NORMAL, "color": Colors.TEXT_MUTED},
        "sm": {"size": Typography.SM, "weight": Typography.NORMAL, "color": Colors.TEXT_SECONDARY},
        "base": {"size": Typography.BASE, "weight": Typography.NORMAL, "color": Colors.TEXT_PRIMARY},
        "lg": {"size": Typography.LG, "weight": Typography.MEDIUM, "color": Colors.TEXT_PRIMARY},
        "xl": {"size": Typography.XL, "weight": Typography.SEMIBOLD, "color": Colors.TEXT_PRIMARY},
        "xl2": {"size": Typography.XL2, "weight": Typography.SEMIBOLD, "color": Colors.TEXT_PRIMARY},
        "xl3": {"size": Typography.XL3, "weight": Typography.BOLD, "color": Colors.TEXT_PRIMARY},
    }
    
    def __init__(self, text: str = "", size: str = "base", parent=None):
        super().__init__(text, parent)
        
        style = self.STYLES.get(size, self.STYLES["base"])
        
        self.setStyleSheet(f"""
            QLabel {{
                font-size: {style['size']};
                font-weight: {style['weight']};
                color: {style['color']};
                font-family: {Typography.FONT_FAMILY};
            }}
        """)
        
        self.setWordWrap(True)


class AtomBadge(QFrame):
    """Status badge/pill."""
    
    COLORS = {
        "gray": (Colors.GRAY_100, Colors.GRAY_600),
        "blue": (Colors.PRIMARY_100, Colors.PRIMARY_700),
        "green": ("#d1fae5", "#047857"),
        "yellow": ("#fef3c7", "#b45309"),
        "red": ("#fee2e2", "#b91c1c"),
    }
    
    def __init__(self, text: str, variant: str = "gray", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        label = QLabel(text)
        layout.addWidget(label)
        
        bg, fg = self.COLORS.get(variant, self.COLORS["gray"])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border-radius: {Radius.FULL};
            }}
            QLabel {{
                color: {fg};
                font-size: {Typography.XS};
                font-weight: {Typography.MEDIUM};
                font-family: {Typography.FONT_FAMILY};
            }}
        """)


class AtomCheckbox(QCheckBox):
    """Styled checkbox."""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        
        self.setStyleSheet(f"""
            QCheckBox {{
                font-size: {Typography.SM};
                font-family: {Typography.FONT_FAMILY};
                color: {Colors.TEXT_PRIMARY};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {Colors.GRAY_300};
                border-radius: {Radius.SM};
                background: {Colors.SURFACE};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.PRIMARY_500};
                border-color: {Colors.PRIMARY_500};
            }}
        """)


class AtomSelect(QComboBox):
    """Dropdown select."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMinimumHeight(40)
        
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.SURFACE};
                border: 2px solid {Colors.GRAY_200};
                border-radius: {Radius.MD};
                padding: 8px 12px;
                font-size: {Typography.SM};
                font-family: {Typography.FONT_FAMILY};
                color: {Colors.TEXT_PRIMARY};
            }}
            QComboBox:hover {{
                border-color: {Colors.GRAY_300};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.GRAY_200};
                border-radius: {Radius.MD};
                selection-background-color: {Colors.PRIMARY_100};
            }}
        """)


class AtomSpinner(QProgressBar):
    """Loading spinner indicator."""
    
    def __init__(self, size: int = 24, parent=None):
        super().__init__(parent)
        
        self.setMaximum(size)
        self.setTextVisible(False)
        self.setMaximumWidth(size)
        self.setMaximumHeight(size)
        
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: transparent;
                border: 2px solid {Colors.GRAY_200};
                border-radius: {size // 2}px;
            }}
            QProgressBar::chunk {{
                background-color: {Colors.PRIMARY_500};
                border-radius: {size // 2}px;
            }}
        """)


class AtomDivider(QFrame):
    """Horizontal divider line."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFrameShape(QFrame.Shape.HLine)
        self.setMaximumHeight(1)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.GRAY_200};
                border: none;
            }}
        """)


class AtomAvatar(QFrame):
    """User avatar circle with initials."""
    
    def __init__(self, name: str, size: int = 40, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(size, size)
        
        # Get initials
        initials = "".join([n[0].upper() for n in name.split()[:2]])
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(initials)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # Generate color from name
        colors = [Colors.PRIMARY_500, Colors.SUCCESS, Colors.WARNING, Colors.ERROR, "#8b5cf6", "#ec4899"]
        color = colors[hash(name) % len(colors)]
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: {size // 2}px;
            }}
            QLabel {{
                color: white;
                font-size: {size // 2}px;
                font-weight: {Typography.BOLD};
                font-family: {Typography.FONT_FAMILY};
            }}
        """)


class AtomTooltip(QLabel):
    """Tooltip popup."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {Colors.GRAY_800};
                color: white;
                font-size: {Typography.XS};
                font-family: {Typography.FONT_FAMILY};
                padding: 6px 10px;
                border-radius: {Radius.MD};
            }}
        """)
        
        self.setVisible(False)


class AtomTag(QPushButton):
    """Removable tag/pill."""
    
    removed = pyqtSignal()
    
    def __init__(self, text: str, removable: bool = True, parent=None):
        super().__init__(text, parent)
        
        if removable:
            self.setText(f"{text} ×")
            self.clicked.connect(self.removed.emit)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor if removable else Qt.CursorShape.ArrowCursor)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.GRAY_100};
                color: {Colors.GRAY_700};
                border: none;
                border-radius: {Radius.FULL};
                padding: 4px 10px;
                font-size: {Typography.XS};
                font-weight: {Typography.MEDIUM};
                font-family: {Typography.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Colors.GRAY_200};
            }}
        """)
