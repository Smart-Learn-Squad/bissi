#!/usr/bin/env python3
"""Demonstration script showing BISSI agent capabilities in action.

This script runs several pre-written prompts to demonstrate how the agent
uses tools to accomplish real tasks.

Usage:
    python test_agent_demo.py
"""

import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.agent import BissiAgent


class AgentDemo:
    """Demonstrates BISSI agent capabilities."""

    def __init__(self):
        """Initialize the demo."""
        print("\n" + "="*80)
        print("🚀 BISSI AGENT - CAPABILITY DEMONSTRATION")
        print("="*80 + "\n")

        print("Initializing agent...")
        self.agent = BissiAgent()
        self.workdir = tempfile.mkdtemp()
        print(f"✅ Agent initialized")
        print(f"📁 Working directory: {self.workdir}\n")

    def demo_section(self, title: str):
        """Print a demo section header."""
        print("\n" + "─"*80)
        print(f"📌 {title}")
        print("─"*80 + "\n")

    def run_demo(self, description: str, prompt: str) -> str:
        """Run a demonstration prompt."""
        print(f"📝 Task: {description}")
        print(f"💬 Prompt: '{prompt}'\n")

        try:
            response = self.agent.process_request(
                user_input=prompt,
                max_iterations=5,
            )

            print(f"🤖 Agent Response:\n{response}\n")
            return response

        except Exception as e:
            print(f"❌ Error: {e}\n")
            return None

    def run_all_demos(self):
        """Run all demonstrations."""
        # Demo 1: File Operations
        self.demo_section("1. FILE OPERATIONS")
        self.run_demo(
            "Create a test file",
            f"Crée un fichier appelé 'test.txt' dans {self.workdir} avec le contenu 'Hello from BISSI!'"
        )

        # Demo 2: Read File
        self.demo_section("2. READING FILES")
        self.run_demo(
            "Read the file we just created",
            f"Lis le contenu du fichier {self.workdir}/test.txt et dis-moi ce qu'il y a dedans"
        )

        # Demo 3: Directory Listing
        self.demo_section("3. DIRECTORY LISTING")
        self.run_demo(
            "List directory contents",
            f"Liste le contenu du répertoire {self.workdir}"
        )

        # Demo 4: File Search
        self.demo_section("4. FILE SEARCH")
        self.run_demo(
            "Search for files",
            f"Cherche tous les fichiers avec l'extension .txt dans {self.workdir}"
        )

        # Demo 5: File Editing
        self.demo_section("5. FILE EDITING")
        self.run_demo(
            "Modify file content",
            f"Modifie le fichier {self.workdir}/test.txt en remplaçant 'BISSI' par 'BISSI Agent v2'"
        )

        # Demo 6: Multiple Files
        self.demo_section("6. MULTIPLE FILE OPERATIONS")
        self.run_demo(
            "Create multiple files",
            f"Crée 3 fichiers dans {self.workdir}: config.txt (contenu: debug=true), data.txt (contenu: records=100), notes.txt (contenu: BISSI est awesome)"
        )

        # Demo 7: Code Execution
        self.demo_section("7. PYTHON CODE EXECUTION")
        self.run_demo(
            "Execute Python code",
            "Exécute du code Python pour calculer la factorielle de 5"
        )

        # Demo 8: Report Generation
        self.demo_section("8. DATA ANALYSIS")
        self.run_demo(
            "Analyze files",
            f"Analyse tous les fichiers dans {self.workdir} et crée un résumé"
        )

        # Closing
        self.demo_section("DEMONSTRATION COMPLETE")
        print("✅ All capabilities demonstrated successfully!")
        print(f"\n📁 Working directory: {self.workdir}")
        print("You can inspect the files created during the demo\n")

    def print_capabilities(self):
        """Print agent capabilities."""
        print("\n" + "="*80)
        print("📊 AGENT CAPABILITIES")
        print("="*80 + "\n")

        print(f"Total Tools: {len(self.agent.available_functions)}\n")

        # Categorize
        categories = {
            "File Operations": ["read_text_file", "write_text_file", "edit_text_file", "delete_file"],
            "Search & Browse": ["search_files", "search_by_content", "list_directory", "get_directory_tree"],
            "Data Processing": ["read_excel", "write_excel"],
            "Documents": ["read_word", "write_word", "read_pdf", "read_pptx", "write_pptx"],
            "Code": ["python_runner"],
            "Vision": ["describe_image", "extract_text_from_image", "analyze_chart", "analyze_screenshot"],
            "System": ["get_file_info", "get_recent_files", "get_clipboard", "set_clipboard", "move_file"],
        }

        for category, tools in categories.items():
            available = [t for t in tools if t in self.agent.available_functions]
            if available:
                print(f"✓ {category}: {len(available)} tools")

        print("\n" + "="*80 + "\n")


def main():
    """Run the demonstration."""
    try:
        demo = AgentDemo()

        # Show capabilities
        demo.print_capabilities()

        # Ask user if they want to run demos or REPL
        print("Choose an option:")
        print("  1. Run automated demonstrations")
        print("  2. Interactive REPL (see agent_repl.py)")
        print("  3. Exit")

        choice = input("\nYour choice (1-3): ").strip()

        if choice == "1":
            demo.run_all_demos()
        elif choice == "2":
            print("\n💡 To use interactive REPL, run: python agent_repl.py\n")
        else:
            print("\n👋 Goodbye!\n")

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!\n")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
