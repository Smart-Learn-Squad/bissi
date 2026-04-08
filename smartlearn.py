"""
SmartLearn — Interface PyQt6
Design: dark theme, sidebar gauche, 4 pages (Accueil, Chat, Résumé, Progression)
Points de connexion marqués: # [CONNECT] — brancher la logique Gemma ici
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QTextEdit, QLineEdit, QScrollArea,
    QFrame, QStackedWidget, QSizePolicy, QGridLayout, QProgressBar,
    QSpacerItem
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QPainter, QBrush


# ─────────────────────────────────────────────
#  PALETTE & STYLES
# ─────────────────────────────────────────────

COLORS = {
    "bg":         "#0a0a0a",
    "surface":    "#111318",
    "surface2":   "#161b22",
    "border":     "#1e2530",
    "blue":       "#3b82f6",
    "blue_dim":   "#1d4ed8",
    "blue_glow":  "#60a5fa",
    "text":       "#e8f0fe",
    "text_dim":   "#6b7280",
    "text_muted": "#374151",
    "accent":     "#0ea5e9",
    "green":      "#10b981",
    "red":        "#ef4444",
    "yellow":     "#f59e0b",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
}}

/* ── Sidebar ── */
#sidebar {{
    background-color: {COLORS['surface']};
    border-right: 1px solid {COLORS['border']};
    min-width: 200px;
    max-width: 200px;
}}

#sidebar_collapsed {{
    background-color: {COLORS['surface']};
    border-right: 1px solid {COLORS['border']};
    min-width: 48px;
    max-width: 48px;
}}

#logo_label {{
    color: {COLORS['text']};
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}

#logo_sub {{
    color: {COLORS['text_dim']};
    font-size: 9px;
    letter-spacing: 2px;
}}

/* ── Nav buttons ── */
QPushButton#nav_btn {{
    background: transparent;
    color: {COLORS['text_dim']};
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#nav_btn:hover {{
    background-color: {COLORS['surface2']};
    color: {COLORS['text']};
}}
QPushButton#nav_btn_active {{
    background-color: {COLORS['blue']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
}}

/* ── New session btn ── */
QPushButton#new_session_btn {{
    background-color: {COLORS['blue']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#new_session_btn:hover {{
    background-color: {COLORS['blue_dim']};
}}

/* ── Main content ── */
#main_content {{
    background-color: {COLORS['bg']};
}}

/* ── Cards ── */
QFrame#card {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}

QFrame#card_blue {{
    background-color: #0f1929;
    border: 1px solid #1e3a5f;
    border-radius: 12px;
}}

/* ── Chat bubbles ── */
QFrame#bubble_user {{
    background-color: #1a2744;
    border: 1px solid #2a3f6f;
    border-radius: 12px;
    padding: 4px;
}}

QFrame#bubble_ai {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 4px;
}}

/* ── Input ── */
QTextEdit#chat_input, QTextEdit#resume_input {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    color: {COLORS['text']};
    font-size: 14px;
    padding: 12px;
}}
QTextEdit#chat_input:focus, QTextEdit#resume_input:focus {{
    border: 1px solid {COLORS['blue']};
}}

/* ── Send button ── */
QPushButton#send_btn {{
    background-color: {COLORS['blue']};
    color: white;
    border: none;
    border-radius: 10px;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
    font-size: 18px;
}}
QPushButton#send_btn:hover {{
    background-color: {COLORS['blue_dim']};
}}

/* ── Suggestion chips ── */
QPushButton#chip {{
    background-color: transparent;
    color: {COLORS['blue_glow']};
    border: 1px solid {COLORS['blue']};
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 12px;
}}
QPushButton#chip:hover {{
    background-color: #1d2d50;
}}

/* ── Subject cards ── */
QPushButton#subject_card {{
    background-color: {COLORS['surface']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px;
    text-align: left;
    font-size: 13px;
}}
QPushButton#subject_card:hover {{
    border-color: {COLORS['blue']};
    background-color: {COLORS['surface2']};
}}

/* ── Analyse btn ── */
QPushButton#analyse_btn {{
    background-color: {COLORS['blue']};
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 600;
}}
QPushButton#analyse_btn:hover {{
    background-color: {COLORS['blue_dim']};
}}

/* ── Stats cards ── */
QFrame#stat_card {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}

/* ── Pomodoro ── */
QFrame#pomodoro_card {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}

QPushButton#pomo_btn {{
    background-color: {COLORS['blue']};
    color: white;
    border: none;
    border-radius: 22px;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
    font-size: 16px;
}}
QPushButton#pomo_btn:hover {{
    background-color: {COLORS['blue_dim']};
}}

QPushButton#pomo_small_btn {{
    background-color: {COLORS['surface2']};
    color: {COLORS['text_dim']};
    border: 1px solid {COLORS['border']};
    border-radius: 16px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    font-size: 13px;
}}

/* ── Badge ── */
QLabel#badge_blue {{
    background-color: #1d3a6e;
    color: {COLORS['blue_glow']};
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
}}
QLabel#badge_red {{
    background-color: #3b1313;
    color: {COLORS['red']};
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
}}
QLabel#badge_yellow {{
    background-color: #3b2a0d;
    color: {COLORS['yellow']};
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
}}

/* ── Footer ── */
QLabel#footer {{
    color: {COLORS['text_muted']};
    font-size: 11px;
}}

/* ── Scrollbar ── */
QScrollBar:vertical {{
    background: {COLORS['bg']};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────

class Sidebar(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.collapsed = False
        self._build()

    def _build(self):
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(12, 16, 12, 16)
        self.layout_.setSpacing(4)

        # Logo
        logo_widget = QWidget()
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(4, 0, 0, 0)
        logo_layout.setSpacing(8)

        infinity = QLabel("∞")
        infinity.setStyleSheet(f"""
            background-color: {COLORS['blue']};
            color: white;
            border-radius: 10px;
            padding: 4px 8px;
            font-size: 16px;
            font-weight: bold;
        """)
        infinity.setFixedSize(36, 36)
        infinity.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        name = QLabel("SmartLearn")
        name.setObjectName("logo_label")
        sub = QLabel("IA PÉDAGOGIQUE")
        sub.setObjectName("logo_sub")
        name_col.addWidget(name)
        name_col.addWidget(sub)

        logo_layout.addWidget(infinity)
        logo_layout.addLayout(name_col)
        logo_layout.addStretch()

        # Collapse btn
        self.collapse_btn = QPushButton("‹")
        self.collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['surface2']};
                color: {COLORS['text_dim']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                min-width: 24px; max-width: 24px;
                min-height: 24px; max-height: 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{ color: {COLORS['text']}; }}
        """)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        logo_layout.addWidget(self.collapse_btn)

        self.layout_.addWidget(logo_widget)
        self.layout_.addSpacing(12)

        # New session
        self.new_btn = QPushButton("+ Nouvelle session")
        self.new_btn.setObjectName("new_session_btn")
        self.new_btn.setFixedHeight(38)
        self.layout_.addWidget(self.new_btn)
        self.new_btn.clicked.connect(lambda: self._on_new_session())  # [CONNECT]

        self.layout_.addSpacing(8)

        # Nav
        self.nav_buttons = []
        nav_items = [
            ("💬", "Chat", 1),
            ("📄", "Résumé", 2),
            ("〜", "Progression", 3),
        ]
        for icon, label, page_idx in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("nav_btn")
            btn.setFixedHeight(40)
            btn.clicked.connect(lambda checked, idx=page_idx: self._set_page(idx))
            self.layout_.addWidget(btn)
            self.nav_buttons.append((btn, page_idx))

        self.layout_.addStretch()

        # Bottom: badge + user
        badge_frame = QFrame()
        badge_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1a2033;
                border: 1px solid #2a3550;
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        badge_layout = QVBoxLayout(badge_frame)
        badge_layout.setContentsMargins(8, 6, 8, 6)
        badge_layout.setSpacing(2)
        b1 = QLabel("🏆 Hack by IFRI 2026")
        b1.setStyleSheet(f"color: {COLORS['yellow']}; font-size: 11px; font-weight: 600;")
        b2 = QLabel("Démo officielle")
        b2.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
        badge_layout.addWidget(b1)
        badge_layout.addWidget(b2)
        self.layout_.addWidget(badge_frame)

        self.layout_.addSpacing(8)

        user_frame = QWidget()
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(4, 0, 0, 0)
        user_layout.setSpacing(8)
        avatar = QLabel("SY")
        avatar.setStyleSheet(f"""
            background-color: {COLORS['blue']};
            color: white;
            border-radius: 14px;
            font-size: 11px;
            font-weight: bold;
        """)
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        u_col = QVBoxLayout()
        u_col.setSpacing(0)
        uname = QLabel("Samuel")
        uname.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; font-weight: 600;")
        urole = QLabel("Informatique")
        urole.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
        u_col.addWidget(uname)
        u_col.addWidget(urole)
        user_layout.addWidget(avatar)
        user_layout.addLayout(u_col)
        self.layout_.addWidget(user_frame)

        self._set_page(1)

    def _set_page(self, idx):
        for btn, page_idx in self.nav_buttons:
            if page_idx == idx:
                btn.setObjectName("nav_btn_active")
            else:
                btn.setObjectName("nav_btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.page_changed.emit(idx)

    def _on_new_session(self):
        pass  # [CONNECT] — réinitialiser la conversation
        self._set_page(1)

    def toggle_collapse(self):
        pass  # [CONNECT] — collapse sidebar (optionnel)


# ─────────────────────────────────────────────
#  PAGE 0 — ACCUEIL (welcome / suggestions)
# ─────────────────────────────────────────────

class HomePage(QWidget):
    subject_selected = pyqtSignal(str)  # [CONNECT] — sujet cliqué → aller en Chat
    chip_selected = pyqtSignal(str)     # [CONNECT] — chip cliqué

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(60, 80, 60, 30)
        inner_layout.setSpacing(32)
        inner_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Logo
        logo = QLabel("∞")
        logo.setStyleSheet(f"""
            background-color: {COLORS['blue']};
            color: white;
            border-radius: 30px;
            font-size: 28px;
            font-weight: bold;
        """)
        logo.setFixedSize(60, 60)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo)
        logo_row.addStretch()
        inner_layout.addLayout(logo_row)

        # Title
        title = QLabel('Apprends avec <span style="color: #3b82f6;">SmartLearn</span>')
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setStyleSheet("font-size: 28px; font-weight: 700; color: #e8f0fe;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(title)

        subtitle = QLabel("Pose tes questions, explore des concepts,\nprépare tes examens avec l'aide de l'IA.")
        subtitle.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 13px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(subtitle)

        # Chips
        chips_row = QHBoxLayout()
        chips_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chips_row.setSpacing(8)
        for chip_text in ["✦ Étape par étape", "◆ Analogies concrètes", "✦ Vérification", "◆ Exemples pratiques"]:
            btn = QPushButton(chip_text)
            btn.setObjectName("chip")
            btn.clicked.connect(lambda checked, t=chip_text: self.chip_selected.emit(t))
            chips_row.addWidget(btn)
        inner_layout.addLayout(chips_row)

        # Subject cards
        subjects = [
            ("📐", "Maths", "Explique-moi les intégrales\ncomme si j'avais 15 ans"),
            ("🧪", "Chimie", "Différence entre liaison\nionique et covalente ?"),
            ("💻", "Algo", "Explique la récursivité\navec un exemple simple"),
            ("📚", "Révision", "Comment bien mémoriser un\ncours la veille d'un exam ?"),
        ]
        grid = QGridLayout()
        grid.setSpacing(12)
        for i, (icon, name, desc) in enumerate(subjects):
            btn = QPushButton(f"{icon}  {name}\n{desc}")
            btn.setObjectName("subject_card")
            btn.setFixedHeight(90)
            btn.clicked.connect(lambda checked, d=desc: self.subject_selected.emit(d))
            grid.addWidget(btn, i // 2, i % 2)
        inner_layout.addLayout(grid)

        # Input (décoratif — même input que chat)
        input_frame = QFrame()
        input_frame.setObjectName("card")
        input_frame.setFixedHeight(90)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 12)
        placeholder = QLabel("Pose ta question à SmartLearn ...")
        placeholder.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        input_layout.addWidget(placeholder)

        bottom_row = QHBoxLayout()
        quiz_badge = QLabel("🔴  Quiz")
        quiz_badge.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        sl_badge = QLabel("⚡ SmartLearn IA")
        sl_badge.setStyleSheet(f"color: {COLORS['blue_glow']}; font-size: 12px;")
        bottom_row.addWidget(quiz_badge)
        bottom_row.addStretch()
        bottom_row.addWidget(sl_badge)
        input_layout.addLayout(bottom_row)
        inner_layout.addWidget(input_frame)

        # Footer
        footer = QLabel("SmartLearn  •  Démo Hack by IFRI 2026")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(footer)

        scroll.setWidget(inner)
        layout.addWidget(scroll)


# ─────────────────────────────────────────────
#  PAGE 1 — CHAT
# ─────────────────────────────────────────────

class ChatBubble(QFrame):
    def __init__(self, text: str, is_user: bool):
        super().__init__()
        self.setObjectName("bubble_user" if is_user else "bubble_ai")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        if not is_user:
            icon = QLabel("⚡")
            icon.setFixedSize(28, 28)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet(f"""
                background-color: {COLORS['blue']};
                color: white;
                border-radius: 14px;
                font-size: 12px;
            """)
            layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(4)

        if not is_user:
            label = QLabel("◆ EXPLICATION PÉDAGOGIQUE")
            label.setStyleSheet(f"color: {COLORS['blue_glow']}; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
            col.addWidget(label)

        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; line-height: 1.5;")
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        col.addWidget(msg)
        layout.addLayout(col)

        if is_user:
            avatar = QLabel("SY")
            avatar.setFixedSize(28, 28)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar.setStyleSheet(f"""
                background-color: {COLORS['blue']};
                color: white;
                border-radius: 14px;
                font-size: 11px;
                font-weight: bold;
            """)
            layout.insertWidget(0, avatar, alignment=Qt.AlignmentFlag.AlignTop)


class ChatPage(QWidget):
    message_sent = pyqtSignal(str)  # [CONNECT] — texte envoyé → appeler Gemma

    def __init__(self):
        super().__init__()
        self.messages = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area messages
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(40, 24, 40, 24)
        self.messages_layout.setSpacing(16)
        self.messages_layout.addStretch()

        self.scroll.setWidget(self.messages_widget)
        layout.addWidget(self.scroll)

        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(40, 12, 40, 12)
        input_layout.setSpacing(8)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.input_box = QTextEdit()
        self.input_box.setObjectName("chat_input")
        self.input_box.setPlaceholderText("Pose ta question à SmartLearn ...")
        self.input_box.setFixedHeight(52)
        self.input_box.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        send_btn = QPushButton("➤")
        send_btn.setObjectName("send_btn")
        send_btn.clicked.connect(self._on_send)

        input_row.addWidget(self.input_box)
        input_row.addWidget(send_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        input_layout.addLayout(input_row)

        meta_row = QHBoxLayout()
        quiz_lbl = QLabel("🔴  Quiz")
        quiz_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        sl_lbl = QLabel("⚡ SmartLearn IA")
        sl_lbl.setStyleSheet(f"color: {COLORS['blue_glow']}; font-size: 12px;")
        meta_row.addWidget(quiz_lbl)
        meta_row.addStretch()
        meta_row.addWidget(sl_lbl)
        input_layout.addLayout(meta_row)

        layout.addWidget(input_frame)

        # Footer
        footer = QLabel("SmartLearn  •  Démo Hack by IFRI 2026")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setContentsMargins(0, 4, 0, 8)
        layout.addWidget(footer)

    def _on_send(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            return
        self.input_box.clear()
        self.add_message(text, is_user=True)
        self.message_sent.emit(text)  # [CONNECT] → appeler Gemma avec `text`

    def add_message(self, text: str, is_user: bool):
        """[CONNECT] Appeler cette méthode pour afficher la réponse de Gemma."""
        bubble = ChatBubble(text, is_user)
        self.messages_layout.addWidget(bubble)
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def inject_prompt(self, text: str):
        """[CONNECT] Injecter un prompt depuis la page d'accueil."""
        self.input_box.setPlainText(text)


# ─────────────────────────────────────────────
#  PAGE 2 — RÉSUMÉ
# ─────────────────────────────────────────────

class ResumePage(QWidget):
    analyse_requested = pyqtSignal(str)  # [CONNECT] — texte du chapitre → appeler Gemma

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(60, 48, 60, 40)
        inner_layout.setSpacing(24)

        # Header
        eyebrow = QLabel("◆ ANALYSE DE CHAPITRE")
        eyebrow.setStyleSheet(f"color: {COLORS['blue_glow']}; font-size: 11px; font-weight: 700; letter-spacing: 2px;")
        inner_layout.addWidget(eyebrow)

        title = QLabel('Transforme ton cours en\n<span style="color: #3b82f6; font-style: italic;">connaissance structurée</span>')
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setStyleSheet("font-size: 26px; font-weight: 700; color: #e8f0fe; line-height: 1.3;")
        inner_layout.addWidget(title)

        sub = QLabel("Colle le texte de ton chapitre – SmartLearn génère un résumé, les concepts clés et les définitions importantes.")
        sub.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 13px;")
        sub.setWordWrap(True)
        inner_layout.addWidget(sub)

        # Input card
        input_card = QFrame()
        input_card.setObjectName("card")
        card_layout = QVBoxLayout(input_card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        file_lbl = QLabel("📄  Texte du chapitre")
        file_lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; font-weight: 600;")
        toolbar.addWidget(file_lbl)
        toolbar.addStretch()
        for btn_text in ["🖼 Image", "📎 PDF"]:
            btn = QPushButton(btn_text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['surface2']};
                    color: {COLORS['text_dim']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ color: {COLORS['text']}; }}
            """)
            toolbar.addWidget(btn)
        self.char_count = QLabel("0 caractères")
        self.char_count.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        toolbar.addWidget(self.char_count)
        card_layout.addLayout(toolbar)

        self.text_input = QTextEdit()
        self.text_input.setObjectName("resume_input")
        self.text_input.setPlaceholderText("Colle ici le texte de ton cours (minimum 80 caractères)…")
        self.text_input.setMinimumHeight(160)
        self.text_input.textChanged.connect(self._on_text_changed)
        card_layout.addWidget(self.text_input)

        inner_layout.addWidget(input_card)

        # Bottom row
        bottom_row = QHBoxLayout()
        self.hint_lbl = QLabel("💡 Minimum 80 caractères pour une analyse pertinente")
        self.hint_lbl.setStyleSheet(f"color: {COLORS['yellow']}; font-size: 12px;")
        bottom_row.addWidget(self.hint_lbl)
        bottom_row.addStretch()

        self.analyse_btn = QPushButton("🔍  Analyser le chapitre")
        self.analyse_btn.setObjectName("analyse_btn")
        self.analyse_btn.clicked.connect(self._on_analyse)
        bottom_row.addWidget(self.analyse_btn)
        inner_layout.addLayout(bottom_row)

        # Result area (caché au départ)
        self.result_card = QFrame()
        self.result_card.setObjectName("card")
        self.result_card.hide()
        result_layout = QVBoxLayout(self.result_card)
        result_layout.setContentsMargins(20, 16, 20, 16)
        result_lbl = QLabel("◆ RÉSULTAT DE L'ANALYSE")
        result_lbl.setStyleSheet(f"color: {COLORS['blue_glow']}; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        result_layout.addWidget(result_lbl)
        self.result_text = QLabel("")
        self.result_text.setWordWrap(True)
        self.result_text.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px;")
        self.result_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        result_layout.addWidget(self.result_text)
        inner_layout.addWidget(self.result_card)

        inner_layout.addStretch()

        footer = QLabel("SmartLearn  •  Démo Hack by IFRI 2026")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(footer)

        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _on_text_changed(self):
        n = len(self.text_input.toPlainText())
        self.char_count.setText(f"{n} caractères")

    def _on_analyse(self):
        text = self.text_input.toPlainText().strip()
        if len(text) < 80:
            return
        self.analyse_requested.emit(text)  # [CONNECT] → appeler Gemma avec le texte

    def show_result(self, result_text: str):
        """[CONNECT] Appeler cette méthode pour afficher la réponse de Gemma."""
        self.result_text.setText(result_text)
        self.result_card.show()


# ─────────────────────────────────────────────
#  PAGE 3 — PROGRESSION
# ─────────────────────────────────────────────

class ProgressionPage(QWidget):
    reset_requested = pyqtSignal()  # [CONNECT] — reset données

    def __init__(self):
        super().__init__()
        # Pomodoro state
        self.pomo_seconds = 25 * 60
        self.pomo_running = False
        self.pomo_timer = QTimer()
        self.pomo_timer.timeout.connect(self._pomo_tick)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(40, 36, 40, 30)
        inner_layout.setSpacing(20)

        # Header
        eyebrow = QLabel("◆ TABLEAU DE BORD")
        eyebrow.setStyleSheet(f"color: {COLORS['blue_glow']}; font-size: 10px; font-weight: 700; letter-spacing: 2px;")
        inner_layout.addWidget(eyebrow)

        title = QLabel('Ma <span style="color: #3b82f6; font-style: italic;">progression</span>')
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setStyleSheet("font-size: 28px; font-weight: 700; color: #e8f0fe;")
        inner_layout.addWidget(title)

        sub = QLabel("Suivez votre maîtrise par chapitre et planifiez vos révisions intelligemment.")
        sub.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 13px;")
        inner_layout.addWidget(sub)

        # Stat cards row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        stat_data = [
            ("📚", "0", "Chapitres étudiés", "sur la session"),
            ("🎯", "0", "Quiz complétés", "cette semaine"),
            ("⭐", "—", "Score moyen", "tous chapitres"),
            ("⏱", "—", "Temps d'étude", "cette semaine"),
        ]
        for icon, val, label, sub_lbl in stat_data:
            card = QFrame()
            card.setObjectName("stat_card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(6)
            ic = QLabel(icon)
            ic.setStyleSheet("font-size: 18px;")
            v = QLabel(val)
            v.setStyleSheet(f"color: {COLORS['text']}; font-size: 20px; font-weight: 700;")
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
            slbl = QLabel(sub_lbl)
            slbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
            card_layout.addWidget(ic)
            card_layout.addWidget(v)
            card_layout.addWidget(lbl)
            card_layout.addWidget(slbl)
            stats_row.addWidget(card)
        inner_layout.addLayout(stats_row)

        # Main row: Maîtrise + Pomodoro
        main_row = QHBoxLayout()
        main_row.setSpacing(16)

        # Maîtrise card
        maitrise_card = QFrame()
        maitrise_card.setObjectName("card")
        maitrise_layout = QVBoxLayout(maitrise_card)
        maitrise_layout.setContentsMargins(20, 16, 20, 16)
        maitrise_layout.setSpacing(12)
        m_header = QHBoxLayout()
        m_title = QLabel("📋  Maîtrise par chapitre")
        m_title.setStyleSheet(f"color: {COLORS['text']}; font-size: 14px; font-weight: 600;")
        m_badge = QLabel("À inscrire")
        m_badge.setObjectName("badge_blue")
        m_header.addWidget(m_title)
        m_header.addStretch()
        m_header.addWidget(m_badge)
        maitrise_layout.addLayout(m_header)

        # Empty state
        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon = QLabel("📚")
        empty_icon.setStyleSheet("font-size: 36px;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_text = QLabel("Aucune activité encore")
        empty_text.setStyleSheet(f"color: {COLORS['text']}; font-size: 14px; font-weight: 600;")
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_sub = QLabel("Fais ton premier quiz sur SmartLearn Chat\npour voir ta progression ici.")
        empty_sub.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_text)
        empty_layout.addWidget(empty_sub)
        maitrise_layout.addWidget(empty)
        maitrise_layout.addStretch()
        main_row.addWidget(maitrise_card, 2)

        # Pomodoro card
        pomo_card = QFrame()
        pomo_card.setObjectName("pomodoro_card")
        pomo_card.setFixedWidth(260)
        pomo_layout = QVBoxLayout(pomo_card)
        pomo_layout.setContentsMargins(20, 16, 20, 16)
        pomo_layout.setSpacing(12)

        pomo_header = QHBoxLayout()
        pomo_title = QLabel("⏱  Timer Pomodoro")
        pomo_title.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; font-weight: 600;")
        pomo_badge = QLabel("Focus")
        pomo_badge.setObjectName("badge_blue")
        pomo_header.addWidget(pomo_title)
        pomo_header.addStretch()
        pomo_header.addWidget(pomo_badge)
        pomo_layout.addLayout(pomo_header)

        # Mode tabs
        tabs_row = QHBoxLayout()
        tabs_row.setSpacing(6)
        focus_tab = QPushButton("Focus · 25min")
        focus_tab.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['blue']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        for tab_text in ["Pause · 5min", "Long · 15min"]:
            t = QPushButton(tab_text)
            t.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['text_dim']};
                    border: none;
                    font-size: 11px;
                }}
                QPushButton:hover {{ color: {COLORS['text']}; }}
            """)
            tabs_row.addWidget(t)
        tabs_row.insertWidget(0, focus_tab)
        pomo_layout.addLayout(tabs_row)

        # Timer display
        self.pomo_display = QLabel("25:00")
        self.pomo_display.setStyleSheet(f"""
            color: {COLORS['text']};
            font-size: 40px;
            font-weight: 700;
            font-family: 'Courier New', monospace;
        """)
        self.pomo_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pomo_layout.addWidget(self.pomo_display)

        focus_lbl = QLabel("FOCUS")
        focus_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; letter-spacing: 2px;")
        focus_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pomo_layout.addWidget(focus_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.setSpacing(12)
        reset_pomo = QPushButton("↺")
        reset_pomo.setObjectName("pomo_small_btn")
        reset_pomo.clicked.connect(self._pomo_reset)

        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("pomo_btn")
        self.play_btn.clicked.connect(self._pomo_toggle)

        skip_pomo = QPushButton("⏭")
        skip_pomo.setObjectName("pomo_small_btn")

        btn_row.addWidget(reset_pomo)
        btn_row.addWidget(self.play_btn)
        btn_row.addWidget(skip_pomo)
        pomo_layout.addLayout(btn_row)

        session_lbl = QLabel("● ● ● ●  Session 1/4")
        session_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
        session_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pomo_layout.addWidget(session_lbl)
        main_row.addWidget(pomo_card)

        inner_layout.addLayout(main_row)

        # Bottom cards row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        for icon, title_txt, badge_obj, badge_txt, body_txt in [
            ("🏆", "Score global", "badge_blue", "Détails", "Aucune donnée\nLance ton premier quiz !"),
            ("⚠", "Points faibles", "badge_red", "À revoir", "Lance un quiz pour identifier\ntes points faibles."),
            ("📅", "Prochaines révisions", "badge_yellow", "Planning", "Le planning se génère\nautomatiquement après\ntes premiers quiz."),
        ]:
            c = QFrame()
            c.setObjectName("card")
            cl = QVBoxLayout(c)
            cl.setContentsMargins(16, 14, 16, 14)
            cl.setSpacing(8)
            h = QHBoxLayout()
            t = QLabel(f"{icon}  {title_txt}")
            t.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; font-weight: 600;")
            b = QLabel(badge_txt)
            b.setObjectName(badge_obj)
            h.addWidget(t)
            h.addStretch()
            h.addWidget(b)
            cl.addLayout(h)
            body = QLabel(body_txt)
            body.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
            body.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(body)
            cl.addStretch()
            bottom_row.addWidget(c)
        inner_layout.addLayout(bottom_row)

        # Reset
        reset_row = QHBoxLayout()
        reset_row.setAlignment(Qt.AlignmentFlag.AlignRight)
        reset_btn = QPushButton("↺  Réinitialiser les données")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_muted']};
                border: none;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {COLORS['text_dim']}; }}
        """)
        reset_btn.clicked.connect(self.reset_requested.emit)  # [CONNECT]
        reset_row.addWidget(reset_btn)
        inner_layout.addLayout(reset_row)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _pomo_toggle(self):
        if self.pomo_running:
            self.pomo_timer.stop()
            self.play_btn.setText("▶")
        else:
            self.pomo_timer.start(1000)
            self.play_btn.setText("⏸")
        self.pomo_running = not self.pomo_running

    def _pomo_tick(self):
        if self.pomo_seconds > 0:
            self.pomo_seconds -= 1
            m, s = divmod(self.pomo_seconds, 60)
            self.pomo_display.setText(f"{m:02d}:{s:02d}")
        else:
            self.pomo_timer.stop()
            self.play_btn.setText("▶")
            self.pomo_running = False

    def _pomo_reset(self):
        self.pomo_timer.stop()
        self.pomo_running = False
        self.pomo_seconds = 25 * 60
        self.pomo_display.setText("25:00")
        self.play_btn.setText("▶")

    def update_stats(self, chapitres=0, quiz=0, score="—", temps="—"):
        """[CONNECT] Mettre à jour les statistiques depuis la logique principale."""
        pass


# ─────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────

class SmartLearnApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartLearn — IA Pédagogique")
        self.resize(1200, 780)
        self.setMinimumSize(900, 600)
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        # Stacked pages
        self.stack = QStackedWidget()
        self.stack.setObjectName("main_content")

        self.home_page = HomePage()
        self.chat_page = ChatPage()
        self.resume_page = ResumePage()
        self.progression_page = ProgressionPage()

        self.stack.addWidget(self.home_page)       # 0
        self.stack.addWidget(self.chat_page)       # 1
        self.stack.addWidget(self.resume_page)     # 2
        self.stack.addWidget(self.progression_page)  # 3

        root.addWidget(self.stack)

        # Signals
        self.sidebar.page_changed.connect(self._on_page_changed)
        self.home_page.subject_selected.connect(self._on_subject_selected)

        # [CONNECT] Brancher ici la logique Gemma:
        # self.chat_page.message_sent.connect(self.handle_chat_message)
        # self.resume_page.analyse_requested.connect(self.handle_analyse)
        # self.progression_page.reset_requested.connect(self.handle_reset)

        self.stack.setCurrentIndex(0)

    def _on_page_changed(self, idx):
        self.stack.setCurrentIndex(idx)

    def _on_subject_selected(self, prompt: str):
        self.chat_page.inject_prompt(prompt)
        self.sidebar.page_changed.emit(1)
        self.stack.setCurrentIndex(1)

    # ── Points de connexion Gemma ─────────────────

    def handle_chat_message(self, text: str):
        """[CONNECT] Appeler Gemma avec `text`, puis chat_page.add_message(réponse, is_user=False)."""
        pass

    def handle_analyse(self, text: str):
        """[CONNECT] Appeler Gemma avec le texte du chapitre, puis resume_page.show_result(réponse)."""
        pass

    def handle_reset(self):
        """[CONNECT] Réinitialiser les données de progression."""
        pass


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = SmartLearnApp()
    window.show()
    sys.exit(app.exec())
