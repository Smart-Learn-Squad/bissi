"""Bissi Codes — CLI Edition.
Runs the rich terminal REPL with developer-focused prompts.
"""

import sys
import os
from pathlib import Path

# Ensure core is importable
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.memory.conversation_store import ConversationStore
from core.memory.vector_store import VectorStore
from configs.prompts import CODES_PROMPT
from agent import BissiAgent
from editions.codes.repl import BissiREPL

def main():
    # Edition-specific memory
    base_dir = Path("~/.bissi/codes").expanduser()
    conv_store = ConversationStore(db_path=base_dir / "conversations.db")
    vec_store = VectorStore(persist_directory=base_dir / "vector_store")

    # Initialize Agent with Codes Prompt
    agent = BissiAgent(
        system_prompt=CODES_PROMPT,
        conversation_store=conv_store,
        vector_store=vec_store
    )

    # Launch REPL
    repl = BissiREPL(agent)
    repl.run()

if __name__ == "__main__":
    main()
