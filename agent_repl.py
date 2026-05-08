#!/usr/bin/env python3
"""Interactive REPL to demonstrate BISSI agent capabilities with real tool execution.

Usage:
    python agent_repl.py

This script starts an interactive session where you can see the agent use tools
to accomplish tasks.

Example prompts:
    - "Crée un fichier test.txt avec 'Hello World'"
    - "Lis le contenu de test.txt"
    - "Cherche tous les fichiers .py dans le répertoire courant"
    - "Calcule 2 + 2 en Python"
    - "Liste le contenu du répertoire courant"
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.agent import BissiAgent
from core.types import ToolResult


class AgentREPL:
    """Interactive REPL for BISSI agent."""

    def __init__(self):
        """Initialize the REPL."""
        print("🚀 Initializing BISSI Agent REPL...")
        self.agent = BissiAgent()
        self.conversation_id = None
        self.tool_calls_log = []

    def print_header(self):
        """Print welcome header."""
        print("\n" + "="*80)
        print("🤖 BISSI AGENT - INTERACTIVE CAPABILITY DEMONSTRATION")
        print("="*80)
        print("\n📋 Available commands:")
        print("  - Type your prompt to see the agent use tools")
        print("  - Type 'tools' to see available tools")
        print("  - Type 'info' to see agent information")
        print("  - Type 'history' to see tool execution log")
        print("  - Type 'exit' or 'quit' to close")
        print("\n" + "="*80 + "\n")

    def print_tools(self):
        """Print available tools."""
        print("\n" + "="*80)
        print("🛠️  AVAILABLE TOOLS ({} total)".format(len(self.agent.available_functions)))
        print("="*80 + "\n")

        categories = {
            "📁 File Operations": ["read_text_file", "write_text_file", "edit_text_file", "delete_file"],
            "🔍 Search": ["search_files", "search_by_content", "list_directory", "get_directory_tree"],
            "📊 Data": ["read_excel", "write_excel"],
            "📄 Documents": ["read_word", "write_word", "read_pdf", "read_pptx", "write_pptx"],
            "🐍 Code": ["python_runner"],
            "🖼️  Vision": ["describe_image", "extract_text_from_image", "analyze_chart", "analyze_screenshot"],
            "📋 Other": ["get_file_info", "get_recent_files", "get_clipboard", "set_clipboard", "move_file", "safe_operator"],
        }

        for category, tools in categories.items():
            available = [t for t in tools if t in self.agent.available_functions]
            if available:
                print(f"{category}")
                for tool in available:
                    print(f"  ✓ {tool}")
                print()

        print("="*80 + "\n")

    def print_info(self):
        """Print agent information."""
        print("\n" + "="*80)
        print("📊 AGENT INFORMATION")
        print("="*80)
        print(f"Model: {self.agent.model}")
        print(f"Available Tools: {len(self.agent.available_functions)}")
        print(f"Context Token Limit: {self.agent.context_manager.token_limit}")
        print(f"Engine Host: {self.agent.engine.host}")
        print(f"Engine Timeout: {self.agent.engine.timeout_seconds}s")
        print(f"Engine Max Retries: {self.agent.engine.max_retries}")
        print(f"Engine Temperature: {self.agent.engine.temperature}")
        print("="*80 + "\n")

    def print_history(self):
        """Print tool execution log."""
        if not self.tool_calls_log:
            print("\n❌ No tool calls yet\n")
            return

        print("\n" + "="*80)
        print("📜 TOOL EXECUTION HISTORY")
        print("="*80 + "\n")

        for i, log_entry in enumerate(self.tool_calls_log, 1):
            print(f"{i}. {log_entry['tool']} - {log_entry['status']}")
            if log_entry['status'] == "✅ Success":
                print(f"   Output: {str(log_entry['output'])[:100]}...")
            else:
                print(f"   Error: {log_entry['error']}")
            print()

        print("="*80 + "\n")

    def on_tool_start(self, tool_name: str, args):
        """Callback when tool starts."""
        print(f"\n  🔧 Calling tool: {tool_name}")
        print(f"     Args: {args}")

    def on_tool_done(self, tool_name: str, result: str):
        """Callback when tool completes."""
        print(f"     ✅ Result: {result[:100]}...")

    def on_thinking(self, message: str):
        """Callback for thinking messages."""
        if message:
            print(f"\n  💭 Thinking: {message[:100]}...")

    def on_chunk(self, chunk: str):
        """Callback for response chunks."""
        print(chunk, end="", flush=True)

    def process_prompt(self, prompt: str) -> str:
        """Process a user prompt through the agent."""
        print(f"\n{'='*80}")
        print(f"👤 User: {prompt}")
        print(f"{'='*80}\n")

        try:
            # Process the request
            response = self.agent.process_request(
                user_input=prompt,
                max_iterations=5,
                on_chunk=self.on_chunk,
                on_tool_start=self.on_tool_start,
                on_tool_done=self.on_tool_done,
                on_thinking=self.on_thinking,
            )

            # Log the execution
            self.tool_calls_log.append({
                "prompt": prompt,
                "tool": "agent",
                "status": "✅ Success",
                "output": response,
                "error": None,
            })

            print("\n")
            return response

        except Exception as e:
            error_msg = str(e)
            print(f"\n\n❌ Error: {error_msg}\n")
            self.tool_calls_log.append({
                "prompt": prompt,
                "tool": "agent",
                "status": "❌ Error",
                "output": None,
                "error": error_msg,
            })
            return f"Error: {error_msg}"

    def run(self):
        """Run the interactive REPL."""
        self.print_header()

        while True:
            try:
                # Get user input
                user_input = input("🤔 You: ").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ["exit", "quit"]:
                    print("\n👋 Goodbye!\n")
                    break

                elif user_input.lower() == "tools":
                    self.print_tools()

                elif user_input.lower() == "info":
                    self.print_info()

                elif user_input.lower() == "history":
                    self.print_history()

                else:
                    # Process as agent prompt
                    self.process_prompt(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!\n")
                break

            except Exception as e:
                print(f"\n❌ Error: {e}\n")


def main():
    """Main entry point."""
    try:
        repl = AgentREPL()
        repl.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
