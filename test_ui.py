"""Test script to preview Smartlearn and Bissi Hi UIs.

Run with: python test_ui.py [smartlearn|bissihi|both]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont


def test_smartlearn():
    """Launch Smartlearn UI."""
    from smartlearn.main_window import SmartlearnMainWindow
    
    app = QApplication(sys.argv)
    font = QFont("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", 14)
    app.setFont(font)
    
    window = SmartlearnMainWindow()
    window.show()
    
    print("🎓 Smartlearn UI launched")
    print(f"   Model: {window.input_widget.model_badge.text()}")
    
    return app.exec()


def test_bissihi():
    """Launch Bissi Hi UI."""
    from bissi_hi.main_window import BissiHiMainWindow
    
    app = QApplication(sys.argv)
    font = QFont("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", 14)
    app.setFont(font)
    
    window = BissiHiMainWindow()
    window.show()
    
    print("🔬 Bissi Hi UI launched")
    print(f"   Model: {window.input_widget.model_badge.text()}")
    
    return app.exec()


def test_both():
    """Launch both UIs in separate processes."""
    import subprocess
    import time
    
    print("Launching both UIs...")
    
    # Launch Smartlearn
    p1 = subprocess.Popen([sys.executable, "-c", 
        "import sys; sys.path.insert(0, '.'); "
        "from test_ui import test_smartlearn; "
        "import sys; sys.exit(test_smartlearn())"])
    
    time.sleep(2)
    
    # Launch Bissi Hi
    p2 = subprocess.Popen([sys.executable, "-c",
        "import sys; sys.path.insert(0, '.'); "
        "from test_ui import test_bissihi; "
        "import sys; sys.exit(test_bissihi())"])
    
    p1.wait()
    p2.wait()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ui.py [smartlearn|bissihi|both]")
        print("\nExamples:")
        print("  python test_ui.py smartlearn   # Launch Smartlearn only")
        print("  python test_ui.py bissihi      # Launch Bissi Hi only")
        print("  python test_ui.py both         # Launch both (separate processes)")
        sys.exit(1)
    
    arg = sys.argv[1].lower()
    
    if arg == "smartlearn":
        sys.exit(test_smartlearn())
    elif arg in ["bissihi", "hi"]:
        sys.exit(test_bissihi())
    elif arg == "both":
        test_both()
    else:
        print(f"Unknown option: {arg}")
        sys.exit(1)
