"""Ultimate Professional UI Library - Master Class 2026 Edition.

High-end, transparent, and responsive components for BISSI.
Strictly following the user's SVG branding and layout requirements.
"""
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QTextEdit, QPushButton, QSizePolicy,
    QFileDialog, QApplication, QGraphicsDropShadowEffect, QLineEdit, 
    QStackedWidget, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QSize
from PyQt6.QtGui import (
    QDragEnterEvent, QDropEvent, QFont, QColor, QPainter, QBrush, 
    QRadialGradient, QLinearGradient, QPen, QPainterPath, QIcon
)

from ui.components.atoms import AtomButton, AtomIconButton, AtomLabel, AtomBadge
from ui.styles.theme import Colors, Typography, Spacing, Radius


class CenteredAvatar(QFrame):
    """SmartLearn Master Logo: Blue Gradient Infinity symbol."""
    def __init__(self, size: int = 48, is_box=True, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.is_box = is_box
        self.size_val = size
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.is_box:
            rect = self.rect().adjusted(2, 2, -2, -2)
            path_bg = QPainterPath()
            path_bg.addRoundedRect(rect.toRectF(), 10, 10)
            grad = QLinearGradient(0, 0, self.width(), self.height())
            grad.setColorAt(0, QColor("#4a90e2"))
            grad.setColorAt(1, QColor("#357abd"))
            painter.fillPath(path_bg, QBrush(grad))
            inf_color = QColor("white")
        else:
            inf_color = QColor("#4a90e2")
        scale = (self.width() * 0.7) / 200.0
        tx, ty = (self.width() - (200 * scale)) / 2, (self.height() - (100 * scale)) / 2
        path = QPainterPath()
        path.moveTo(tx + 50*scale, ty + 10*scale)
        path.cubicTo(tx + 20*scale, ty + 10*scale, tx + 20*scale, ty + 100*scale, tx + 50*scale, ty + 100*scale)
        path.cubicTo(tx + 80*scale, ty + 100*scale, tx + 120*scale, ty + 10*scale, tx + 150*scale, ty + 10*scale)
        path.cubicTo(tx + 180*scale, ty + 10*scale, tx + 180*scale, ty + 100*scale, tx + 150*scale, ty + 100*scale)
        path.cubicTo(tx + 120*scale, ty + 100*scale, tx + 90*scale, ty + 10*scale, tx + 50*scale, ty + 10*scale)
        path.closeSubpath()
        pen = QPen(inf_color, self.size_val/15)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen); painter.drawPath(path); painter.end()


class NavIcon(QWidget):
    """Precision Vector Icons for Navigation."""
    def __init__(self, type="chat", active=False, parent=None):
        super().__init__(parent); self.setFixedSize(22, 22); self.type = type; self.active = active
    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("white") if self.active else QColor("rgba(255,255,255,0.4)")
        painter.setPen(QPen(color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if self.type == "chat":
            painter.drawRoundedRect(QRectF(3, 3, 16, 12), 3, 3)
            painter.drawLine(6, 15, 6, 18); painter.drawLine(6, 18, 11, 15)
        elif self.type == "resume":
            painter.drawRect(4, 3, 14, 16)
            painter.drawLine(7, 7, 15, 7); painter.drawLine(7, 11, 15, 11); painter.drawLine(7, 15, 11, 15)
        elif self.type == "progress":
            painter.drawLine(3, 18, 19, 18)
            painter.drawRect(5, 11, 3, 7); painter.drawRect(10, 6, 3, 12); painter.drawRect(15, 9, 3, 9)
        painter.end()


class SuggestionCard(QFrame):
    """Landing page suggestion tiles."""
    clicked = pyqtSignal(str)
    def __init__(self, title, text, icon, parent=None):
        super().__init__(parent); self.setFixedSize(240, 120); self.query = text
        layout = QVBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20)
        h = QHBoxLayout(); h.addWidget(QLabel(icon)); h.addWidget(QLabel(title)); h.addStretch()
        layout.addLayout(h); layout.addWidget(QLabel(text))
        self.setStyleSheet(f"QFrame {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; }}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    def mousePressEvent(self, e): self.clicked.emit(self.query)


class LiquidGlassInput(QFrame):
    """The Floating Input Pill - Minimalist (No Tag)."""
    message_sent = pyqtSignal(str)
    def __init__(self, placeholder: str = "Pose ta question à SmartLearn...", parent=None):
        super().__init__(parent); self.setMinimumHeight(64); self.setFixedWidth(850)
        layout = QHBoxLayout(self); layout.setContentsMargins(16, 0, 16, 0); layout.setSpacing(12)
        
        self.btn_add = QPushButton("+"); self.btn_add.setFixedSize(36, 36)
        self.btn_add.setStyleSheet("background: rgba(255,255,255,0.05); color: white; border-radius: 18px; border: 1px solid rgba(255,255,255,0.1);")
        layout.addWidget(self.btn_add)
        
        self.field = QLineEdit(); self.field.setPlaceholderText(placeholder); self.field.setFrame(False)
        self.field.returnPressed.connect(self._send); self.field.setStyleSheet("background: transparent; color: white; font-size: 15px;")
        layout.addWidget(self.field, 1)
        
        self.btn_send = QPushButton("↑"); self.btn_send.setFixedSize(36, 36); self.btn_send.clicked.connect(self._send)
        self.btn_send.setStyleSheet(f"background: {Colors.PRIMARY_600}; color: white; border-radius: 18px; font-weight: 900; font-size: 18px;")
        layout.addWidget(self.btn_send)
        
        self.setStyleSheet(f"QFrame {{ background: {Colors.GLASS_BASE}; border: 1px solid {Colors.GLASS_BORDER}; border-top: 1px solid rgba(255,255,255,0.15); border-radius: 24px; }}")
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(40); shadow.setOffset(0, 10); self.setGraphicsEffect(shadow)

    def _send(self):
        t = self.field.text().strip()
        if t: self.message_sent.emit(t); self.field.clear()


class WelcomeView(QWidget):
    """Landing page."""
    suggestion_clicked = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent); layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.setSpacing(30)
        logo = CenteredAvatar(size=80, is_box=False); layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Apprends avec <span style='color:#3b82f6'>SmartLearn</span>"); title.setStyleSheet("color: white; font-size: 32px; font-weight: 900;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        grid = QGridLayout(); grid.setSpacing(16)
        suggestions = [("Maths", "Explique-moi les intégrales...", "📐"), ("Algo", "Explique la récursivité...", "💻")]
        for i, (t, q, icon) in enumerate(suggestions):
            card = SuggestionCard(t, q, icon); card.clicked.connect(self.suggestion_clicked.emit); grid.addWidget(card, i // 2, i % 2)
        gl_wrapper = QWidget(); gl_wrapper.setLayout(grid); layout.addWidget(gl_wrapper, alignment=Qt.AlignmentFlag.AlignCenter)


class ResumeView(QFrame):
    """Analysis View."""
    analyze_requested = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent); layout = QVBoxLayout(self); layout.setContentsMargins(100, 80, 100, 80); layout.setSpacing(20)
        layout.addWidget(QLabel("✦ ANALYSE DE CHAPITRE"))
        self.text_edit = QTextEdit(); self.text_edit.setPlaceholderText("Colle ton texte ici...")
        self.text_edit.setStyleSheet(f"background: {Colors.GLASS_BASE}; border: 1px solid {Colors.GLASS_BORDER}; border-radius: 24px; color: white; padding: 20px;")
        layout.addWidget(self.text_edit)
        self.analyze = QPushButton("Analyser le chapitre"); self.analyze.setFixedHeight(46); self.analyze.clicked.connect(lambda: self.analyze_requested.emit(self.text_edit.toPlainText()))
        layout.addWidget(self.analyze)


class ProgressView(QFrame):
    """Dashboard."""
    def __init__(self, parent=None):
        super().__init__(parent); layout = QVBoxLayout(self); layout.setContentsMargins(60, 60, 60, 60)
        self.timer_display = QLabel("25:00")
        self.timer_display.setStyleSheet("font-size: 64px; color: white; font-weight: 900;")
        layout.addWidget(self.timer_display, alignment=Qt.AlignmentFlag.AlignCenter)
        self.start_pomo = QPushButton("Démarrer"); layout.addWidget(self.start_pomo, alignment=Qt.AlignmentFlag.AlignCenter)


class OllamaStyleWindow(QWidget):
    """Master Class Window with Real Retractable Sidebar."""
    message_sent = pyqtSignal(str)
    def __init__(self, title="SmartLearn", user_name="Samuel YEVI", user_role="Génie Logiciel", parent=None):
        super().__init__(parent); Colors.update_tokens(); self.setWindowTitle(title); self.setMinimumSize(1300, 900)
        self.root_layout = QHBoxLayout(self); self.root_layout.setContentsMargins(0, 0, 0, 0); self.root_layout.setSpacing(0)
        
        # 1. Sidebar Architecture
        self.sidebar = QFrame(); self.sidebar.setFixedWidth(320); self.sidebar.setStyleSheet(f"background: {Colors.GLASS_BASE}; border-right: 1px solid {Colors.GLASS_BORDER};")
        self.sl = QVBoxLayout(self.sidebar); self.sl.setContentsMargins(20, 40, 20, 32); self.sl.setSpacing(10)
        
        # Header Sidebar
        bh = QHBoxLayout(); self.logo_widget = CenteredAvatar(size=44); bh.addWidget(self.logo_widget)
        self.brand_text_box = QWidget(); bl = QVBoxLayout(self.brand_text_box); bl.setContentsMargins(0,0,0,0); bl.setSpacing(0)
        l1 = QLabel("SmartLearn"); l1.setStyleSheet("color: white; font-weight: 900; font-size: 18px;")
        l2 = QLabel("IA PÉDAGOGIQUE"); l2.setStyleSheet(f"color: {Colors.PRIMARY_400}; font-size: 9px; font-weight: 900; letter-spacing: 1px;")
        bl.addWidget(l1); bl.addWidget(l2); bh.addWidget(self.brand_text_box)
        bh.addStretch()
        self.btn_toggle = QPushButton("◀"); self.btn_toggle.setFixedSize(30, 30); self.btn_toggle.clicked.connect(self._toggle_sidebar)
        self.btn_toggle.setStyleSheet("background: transparent; color: rgba(255,255,255,0.3); border: none; font-size: 14px;")
        bh.addWidget(self.btn_toggle); self.sl.addLayout(bh); self.sl.addSpacing(40)
        
        # Navigation
        self.nav_btns = {}
        for i, (name, icon) in enumerate([("Chat", "chat"), ("Résumé", "resume"), ("Progression", "progress")]):
            btn = QPushButton(f"      {name}"); btn.setFixedHeight(44); btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, x=i: self._switch(x))
            icon_w = NavIcon(icon, i==0, btn); icon_w.move(14, 11)
            self.sl.addWidget(btn); self.nav_btns[i] = (btn, icon_w, name); self._update_nav(i, i==0)
        
        self.sl.addStretch()
        
        # Profile
        self.prof_box = QWidget(); pl = QHBoxLayout(self.prof_box); pl.setContentsMargins(0,0,0,0); pl.setSpacing(12)
        av = QLabel(user_name[:2].upper()); av.setFixedSize(40,40); av.setAlignment(Qt.AlignmentFlag.AlignCenter); av.setStyleSheet(f"background: {Colors.PRIMARY_600}; color: white; border-radius: 20px; font-weight: 900;")
        pl.addWidget(av)
        self.u_info = QWidget(); ul = QVBoxLayout(self.u_info); ul.setContentsMargins(0,0,0,0); ul.setSpacing(0)
        un = QLabel(user_name); un.setStyleSheet("color: white; font-weight: 800; font-size: 13px;")
        ur = QLabel(user_role); ur.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 10px;")
        ul.addWidget(un); ul.addWidget(ur); pl.addWidget(self.u_info); self.sl.addWidget(self.prof_box)
        
        self.root_layout.addWidget(self.sidebar)
        
        # 2. Main Area
        self.main_area = QFrame(); self.main_area.setStyleSheet("background: qradialgradient(cx:0.5, cy:0.5, radius:1, fx:0.5, fy:0.5, stop:0 #121215, stop:1 #080808);")
        ma_l = QVBoxLayout(self.main_area); ma_l.setContentsMargins(0,0,0,0); self.root_layout.addWidget(self.main_area, 1)
        self.stack = QStackedWidget(); ma_l.addWidget(self.stack)
        
        # Chat View
        self.cv = QWidget(); cvl = QVBoxLayout(self.cv)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.Shape.NoFrame); self.scroll.setStyleSheet("background: transparent;")
        cw = QWidget(); cwl = QHBoxLayout(cw); self.chat_layout = QVBoxLayout(); self.chat_layout.setContentsMargins(0, 80, 0, 80); self.chat_layout.setSpacing(32); self.chat_layout.addStretch()
        cc = QWidget(); cc.setFixedWidth(850); cc.setLayout(self.chat_layout)
        cwl.addStretch(); cwl.addWidget(cc); cwl.addStretch(); self.scroll.setWidget(cw); cvl.addWidget(self.scroll, 1)
        
        self.welcome = WelcomeView(); self.welcome.suggestion_clicked.connect(self._on_msg); self.chat_layout.insertWidget(0, self.welcome)
        self.input_widget = LiquidGlassInput(); self.input_widget.message_sent.connect(self._on_msg); ir = QHBoxLayout(); ir.addStretch(); ir.addWidget(self.input_widget); ir.addStretch(); cvl.addLayout(ir)
        
        self.resume_view = ResumeView(); self.stack.addWidget(self.cv); self.stack.addWidget(self.resume_view)
        self.progress_view = ProgressView(); self.stack.addWidget(self.progress_view)
        
        self._side_anim = QPropertyAnimation(self.sidebar, b"minimumWidth"); self._is_collapsed = False

    def _toggle_sidebar(self):
        target = 80 if not self._is_collapsed else 320
        self.btn_toggle.setText("▶" if not self._is_collapsed else "◀")
        self._side_anim.setDuration(300); self._side_anim.setStartValue(self.sidebar.width()); self._side_anim.setEndValue(target); self._side_anim.start()
        self.sidebar.setMaximumWidth(target); self._is_collapsed = not self._is_collapsed
        self.brand_text_box.setVisible(not self._is_collapsed)
        self.u_info.setVisible(not self._is_collapsed)
        for i, (b, ic, name) in self.nav_btns.items(): b.setText(f"      {name}" if not self._is_collapsed else "")

    def _switch(self, i):
        self.stack.setCurrentIndex(i)
        for idx in self.nav_btns: self._update_nav(idx, idx == i)

    def _update_nav(self, i, act):
        btn, ic, _ = self.nav_btns[i]
        btn.setStyleSheet(f"QPushButton {{ text-align: left; background: {'rgba(255,255,255,0.05)' if act else 'transparent'}; color: white; border-radius: 10px; padding: 10px; border: none; }}")
        ic.active = act; ic.update()

    def _on_msg(self, t):
        if self.welcome.isVisible(): self.welcome.hide()
        self._add_bubble(t, True); self.message_sent.emit(t)

    def _add_bubble(self, t, user):
        b = QFrame(); bl = QHBoxLayout(b); bl.setContentsMargins(0,0,0,0); bl.setSpacing(16); content = QLabel(t); content.setWordWrap(True); content.setMaximumWidth(700)
        if user:
            bl.addStretch(); content.setStyleSheet("background: rgba(255,255,255,0.05); color: white; border-radius: 15px; padding: 12px;")
            bl.addWidget(content)
        else:
            av = QLabel("∞"); av.setFixedSize(32, 32); av.setAlignment(Qt.AlignmentFlag.AlignCenter); av.setStyleSheet(f"background: rgba(255,255,255,0.05); color: {Colors.PRIMARY_400}; border-radius: 16px; font-weight: 900;")
            bl.addWidget(av, 0, Qt.AlignmentFlag.AlignTop); content.setStyleSheet("color: white; padding: 4px;"); bl.addWidget(content); bl.addStretch()
        self.chat_layout.insertWidget(self.chat_layout.count()-1, b)
        QTimer.singleShot(10, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

    def set_model(self, m): pass
    def add_ai_message(self, t): self._add_bubble(t, False)


# Restored Core classes for compatibility
class FileDropZone(QFrame):
    files_dropped = pyqtSignal(list)
    def __init__(self, parent=None):
        super().__init__(parent); self.setAcceptDrops(True); self.setMinimumHeight(160)
        l = QVBoxLayout(self); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text = QLabel("Drop files here"); l.addWidget(self.text)
        self.setStyleSheet(f"QFrame {{ background: {Colors.GLASS_BASE}; border: 2px dashed {Colors.GLASS_BORDER}; border-radius: 16px; }}")
    def dragEnterEvent(self, e): e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()
    def dropEvent(self, e): self.files_dropped.emit([u.toLocalFile() for u in e.mimeData().urls()])

class CodeBlock(QFrame):
    def __init__(self, code, lang="python", parent=None):
        super().__init__(parent); l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0)
        e = QTextEdit(); e.setPlainText(code); e.setReadOnly(True); e.setStyleSheet(f"background: {Colors.GRAY_900}; color: #e5e7eb; padding: 16px; border-radius: 8px;")
        l.addWidget(e)

class MarkdownRenderer(QFrame):
    def __init__(self, markdown="", parent=None):
        super().__init__(parent); l = QVBoxLayout(self); self.content = QLabel(); self.content.setWordWrap(True); l.addWidget(self.content)
        self.setStyleSheet("color: white;"); self.set_markdown(markdown)
    def set_markdown(self, t): self.content.setText(t.replace('\n', '<br>'))

class ThinkingIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedSize(60, 30); self.setStyleSheet(f"background: {Colors.GLASS_SURFACE}; border-radius: 15px;")
    def start(self): self.show()
    def stop(self): self.hide()

class PersonaSelector(QFrame):
    persona_selected = pyqtSignal(str)
    def __init__(self, current="default", parent=None):
        super().__init__(parent); l = QHBoxLayout(self)
        for p in ["default", "researcher", "student"]:
            b = QPushButton(p); b.clicked.connect(lambda _, x=p: self.persona_selected.emit(x)); l.addWidget(b)

class FilePreviewCard(QFrame):
    removed = pyqtSignal()
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent); layout = QHBoxLayout(self); layout.setContentsMargins(12, 10, 12, 10)
        layout.addWidget(AtomLabel("📎", "xl")); layout.addWidget(AtomLabel(file_path.split('/')[-1], "sm"), 1)
        btn = AtomIconButton("×", size=28); btn.clicked.connect(self.removed.emit); layout.addWidget(btn)
        self.setStyleSheet(f"QFrame {{ background: {Colors.GLASS_SURFACE}; border: 1px solid {Colors.GLASS_BORDER}; border-radius: 12px; }}")
