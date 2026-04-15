"""
BISSI — Interface PyQt6 + WebEngine
Launches the Chromium-based HTML/CSS/JS frontend via QWebEngineView.
Pass --legacy to use the old PyQt6 widget UI instead.
"""

import sys

# WebEngine MUST be imported before QApplication is created
from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
from PyQt6.QtWidgets import QApplication

from ui.themes import get_engine


# ─── ENTRY POINT ──────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="BISSI — AI Agent Suite")
    parser.add_argument("--edition", choices=["master", "codes", "smartlearn"], default="master")
    parser.add_argument("--legacy", action="store_true", help="Use legacy PyQt widgets UI")
    args = parser.parse_args()

    if args.edition == "codes":
        from editions.codes.__main__ import main as codes_main
        codes_main()
    elif args.edition == "smartlearn":
        from editions.smartlearn.__main__ import main as smartlearn_main
        smartlearn_main()
    else:
        # Default to Master
        if args.legacy:
            # Legacy only works for Master / General for now
            app = QApplication(sys.argv)
            from ui.themes import get_engine
            engine = get_engine()
            from ui.main_window import BissiWindow
            win = BissiWindow(engine)
            win.show()
            sys.exit(app.exec())
        else:
            from editions.master.__main__ import main as master_main
            master_main()



if __name__ == "__main__":
    main()
