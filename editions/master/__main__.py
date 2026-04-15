"""Bissi Master — Professional Edition.
Launches the WebEngine UI with professional branding and prompts.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Ensure core is importable if running as a script
sys.path.append(str(Path(__file__).parent.parent.parent))

from ui.web_window import WebWindow
from ui.themes import get_engine
from core.memory.conversation_store import ConversationStore
from core.memory.vector_store import VectorStore
from configs.prompts import MASTER_PROMPT

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Bissi Master")
    app.setStyle("Fusion")

    engine = get_engine()
    engine.apply("light")

    # Edition-specific memory
    base_dir = Path("~/.bissi/master").expanduser()
    conv_store = ConversationStore(db_path=base_dir / "conversations.db")
    vec_store = VectorStore(persist_directory=base_dir / "vector_store")

    # Initialize Agent with Master Prompt
    from agent import BissiAgent
    agent = BissiAgent(
        system_prompt=MASTER_PROMPT,
        conversation_store=conv_store,
        vector_store=vec_store
    )

    # Edition-specific UI assets
    web_dir = Path(__file__).parent / "ui" / "web"

    win = WebWindow(web_dir=web_dir, agent=agent)
    win.setWindowTitle("Bissi Master")
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
