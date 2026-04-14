"""File explorer component for BISSI."""

import os
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt

from ui.styles.theme import Theme


class FileExplorer(QWidget):
    """File explorer tree widget."""

    file_selected = pyqtSignal(str)

    def __init__(self, home_dir: str = None, theme: Theme = None):
        super().__init__()
        self.home_dir = home_dir or str(Path.home())
        self.theme = theme or Theme()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {self.theme.C['bg_sidebar']};
                border: none;
                font-size: 12px;
                font-family: {self.theme.FONT_UI};
                color: {self.theme.C['text2']};
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 3px 6px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: {self.theme.C['hover']};
            }}
            QTreeWidget::item:selected {{
                background: {self.theme.C['purple_lt']};
                color: {self.theme.C['purple_text']};
            }}
            QTreeWidget::branch {{
                background: {self.theme.C['bg_sidebar']};
            }}
        """)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)
        self._load_dir(self.home_dir)

    def _load_dir(self, path: str, max_depth: int = 2):
        """Load directory into tree."""
        self.tree.clear()
        root = QTreeWidgetItem(self.tree, [os.path.basename(path) or path])
        root.setData(0, Qt.ItemDataRole.UserRole, path)
        self._populate(root, path, 0, max_depth)
        root.setExpanded(True)

    def _populate(self, parent: QTreeWidgetItem, path: str, depth: int, max_depth: int):
        """Recursively populate tree items."""
        if depth >= max_depth:
            return
        try:
            entries = sorted(
                os.scandir(path),
                key=lambda e: (not e.is_dir(), e.name.lower())
            )
            for entry in entries[:40]:
                if entry.name.startswith("."):
                    continue
                item = QTreeWidgetItem(parent, [entry.name])
                item.setData(0, Qt.ItemDataRole.UserRole, entry.path)
                if entry.is_dir():
                    self._populate(item, entry.path, depth + 1, max_depth)
        except PermissionError:
            pass

    def _on_item_clicked(self, item: QTreeWidgetItem, col: int):
        """Handle item click - emit signal for files."""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.isfile(path):
            self.file_selected.emit(path)

    def highlight_file(self, filename: str) -> bool:
        """Highlight file in tree by name."""
        def search(parent: QTreeWidgetItem) -> bool:
            for i in range(parent.childCount()):
                child = parent.child(i)
                if filename.lower() in child.text(0).lower():
                    self.tree.setCurrentItem(child)
                    return True
                if search(child):
                    return True
            return False
        root = self.tree.invisibleRootItem()
        return search(root)

    def navigate_to(self, path: str):
        """Navigate tree to show directory containing path."""
        dirpath = os.path.dirname(path) if os.path.isfile(path) else path
        if os.path.isdir(dirpath):
            self._load_dir(dirpath)
