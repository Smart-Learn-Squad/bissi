"""Right panel component for BISSI (Explorer + Editor tabs)."""

import os
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from ui.styles.theme import Theme
from .explorer import FileExplorer
from .editor import CodeEditor


class RightPanel(QWidget):
    """Right panel with Explorer and Editor tabs."""

    def __init__(self, home_dir: str = None, theme: Theme = None):
        super().__init__()
        self.home_dir = home_dir or str(Path.home())
        self.theme = theme or Theme()
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumWidth(260)
        self.setStyleSheet(
            f"background:{self.theme.C['bg_sidebar']};"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tabs header
        tabs_w = QWidget()
        tabs_w.setFixedHeight(36)
        tabs_w.setStyleSheet(f"""
            background: {self.theme.C['bg_white']};
            border-bottom: 0.5px solid {self.theme.C['border']};
        """)
        tl = QHBoxLayout(tabs_w)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)

        self._tabs = []
        self._panels = []
        self.stack = QWidget()
        self.stack_l = QVBoxLayout(self.stack)
        self.stack_l.setContentsMargins(0, 0, 0, 0)

        for i, name in enumerate(["Explorateur", "Éditeur"]):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    border-bottom: 2px solid transparent;
                    background: transparent;
                    padding: 8px 14px;
                    font-size: 12px;
                    color: {self.theme.C['text_muted']};
                    font-family: {self.theme.FONT_UI};
                }}
                QPushButton:checked {{
                    color: {self.theme.C['purple']};
                    border-bottom-color: {self.theme.C['purple']};
                    font-weight: 500;
                }}
                QPushButton:hover:!checked {{ color: {self.theme.C['text2']}; }}
            """)
            btn.clicked.connect(lambda _, idx=i: self._switch(idx))
            tl.addWidget(btn)
            self._tabs.append(btn)

        tl.addStretch()
        layout.addWidget(tabs_w)

        # Explorer
        self.explorer = FileExplorer(self.home_dir, self.theme)
        self._panels.append(self.explorer)

        # Editor
        self.editor_panel = QWidget()
        ep_l = QVBoxLayout(self.editor_panel)
        ep_l.setContentsMargins(0, 0, 0, 0)
        ep_l.setSpacing(0)
        self.code_editor = CodeEditor(self.theme)
        ep_l.addWidget(self.code_editor)
        self.editor_panel.hide()
        self._panels.append(self.editor_panel)

        layout.addWidget(self.explorer, stretch=1)
        layout.addWidget(self.editor_panel, stretch=1)

    def _switch(self, idx: int):
        """Switch between Explorer and Editor tabs."""
        for i, (tab, panel) in enumerate(zip(self._tabs, self._panels)):
            tab.setChecked(i == idx)
            panel.setVisible(i == idx)

    def open_file(self, path: str, by_agent: bool = False):
        """Open file in editor and navigate explorer to it."""
        self.code_editor.open_file(path, by_agent=by_agent)
        self.explorer.navigate_to(path)
        self.explorer.highlight_file(os.path.basename(path))
        self._switch(1)  # Switch to Editor tab
