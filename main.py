"""
BISSI — Interface PyQt6
Modular architecture with separated UI components.
"""

import sys

from PyQt6.QtWidgets import QApplication

from ui.themes import get_engine
from ui.main_window import BissiWindow


# ─── ENTRY POINT ──────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Bissi")
    app.setStyle("Fusion")

    # Initialiser et appliquer le thème par défaut
    engine = get_engine()
    engine.apply("light")

    win = BissiWindow(engine)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
