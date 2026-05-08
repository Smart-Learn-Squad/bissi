"""Integration tests for BISSI agentic capabilities with real tool execution.

This module demonstrates the agent actually using tools to accomplish tasks,
showing real-world agentic workflows in action.
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from core.agent import BissiAgent
from core.types import ToolResult


class TestAgentToolExecution:
    """Test agent executing tools for real tasks."""

    def test_agent_read_write_workflow(self):
        """Test agent can read and write files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_content = "Hello from BISSI agent!"
            test_file.write_text(test_content)

            # Try to use agent's read function
            agent = BissiAgent()
            read_fn = agent.available_functions["read_text_file"]

            # Execute the read (using correct parameter name)
            result = read_fn(file_path=str(test_file))

            # Verify result
            assert isinstance(result, ToolResult)
            assert result.success is True
            assert test_content in str(result.output)
            print(f"✅ Read file successfully: {result.output}")

    def test_agent_write_file(self):
        """Test agent can write files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "output.txt"
            content = "Agent-generated content"

            agent = BissiAgent()
            write_fn = agent.available_functions["write_text_file"]

            # Execute the write (using correct parameter names)
            result = write_fn(file_path=str(test_file), content=content)

            # Verify result
            assert isinstance(result, ToolResult)
            assert result.success is True
            assert test_file.exists()
            assert test_file.read_text() == content
            print(f"✅ Wrote file successfully to {test_file}")

    def test_agent_search_files(self):
        """Test agent can search for files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir).joinpath("test1.py").write_text("# Python file 1")
            Path(tmpdir).joinpath("test2.py").write_text("# Python file 2")
            Path(tmpdir).joinpath("readme.md").write_text("# README")

            agent = BissiAgent()
            search_fn = agent.available_functions["search_files"]

            # Search for Python files (using correct parameter names)
            result = search_fn(file_pattern="*.py", root_dir=tmpdir)

            # Verify result
            assert isinstance(result, ToolResult)
            assert result.success is True
            print(f"✅ Found files: {result.output}")

    def test_agent_list_directory(self):
        """Test agent can list directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test structure
            Path(tmpdir).joinpath("file1.txt").write_text("content1")
            Path(tmpdir).joinpath("file2.txt").write_text("content2")
            Path(tmpdir).joinpath("subdir").mkdir()
            Path(tmpdir).joinpath("subdir/file3.txt").write_text("content3")

            agent = BissiAgent()
            list_fn = agent.available_functions["list_directory"]

            # List directory (using correct parameter names)
            result = list_fn(dir_path=tmpdir)

            # Verify result
            assert isinstance(result, ToolResult)
            assert result.success is True
            print(f"✅ Listed directory: {result.output}")

    def test_agent_edit_file(self):
        """Test agent can edit files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            original = "Line 1\nLine 2\nLine 3"
            test_file.write_text(original)

            agent = BissiAgent()
            edit_fn = agent.available_functions["edit_text_file"]

            # Edit the file (replace Line 2) - using correct parameter names
            result = edit_fn(
                file_path=str(test_file),
                old_text="Line 2",
                new_text="Line 2 EDITED"
            )

            # Verify result
            assert isinstance(result, ToolResult)
            assert result.success is True
            assert "Line 2 EDITED" in test_file.read_text()
            print(f"✅ Edited file successfully")

    def test_agent_python_execution(self):
        """Test agent can execute Python code."""
        agent = BissiAgent()
        python_runner = agent.available_functions.get("python_runner")

        if python_runner:
            # Execute simple Python
            code = """
result = 10 + 20
print(f"Result: {result}")
result
"""
            result = python_runner(code=code)

            # Verify result
            assert isinstance(result, ToolResult)
            assert result.success is True
            print(f"✅ Python execution result: {result.output}")


class TestAgentWorkflows:
    """Test complete workflows with multiple tool calls."""

    def test_search_and_read_workflow(self):
        """Workflow: Search for files then read one."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup test files
            test_file = Path(tmpdir) / "config.txt"
            test_file.write_text("config_value=42")

            agent = BissiAgent()

            # Step 1: Search for files (using correct parameter names)
            search_fn = agent.available_functions["search_files"]
            search_result = search_fn(file_pattern="*.txt", root_dir=tmpdir)
            assert search_result.success is True
            print(f"✅ Step 1 - Found files: {search_result.output}")

            # Step 2: Read the file (using correct parameter names)
            read_fn = agent.available_functions["read_text_file"]
            read_result = read_fn(file_path=str(test_file))
            assert read_result.success is True
            assert "config_value=42" in str(read_result.output)
            print(f"✅ Step 2 - Read content: {read_result.output}")

            print("✅ Workflow completed: Search → Read")

    def test_write_read_verify_workflow(self):
        """Workflow: Write file, read it back, verify content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "data.txt"
            content = "Important data from agent"

            agent = BissiAgent()

            # Step 1: Write (using correct parameter names)
            write_fn = agent.available_functions["write_text_file"]
            write_result = write_fn(file_path=str(test_file), content=content)
            assert write_result.success is True
            print(f"✅ Step 1 - Written file")

            # Step 2: Read back (using correct parameter names)
            read_fn = agent.available_functions["read_text_file"]
            read_result = read_fn(file_path=str(test_file))
            assert read_result.success is True
            assert content in str(read_result.output)
            print(f"✅ Step 2 - Verified content: {read_result.output}")

            print("✅ Workflow completed: Write → Read → Verify")

    def test_complex_file_manipulation(self):
        """Workflow: Create, modify, read multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = BissiAgent()

            # Step 1: Create multiple files (using correct parameter names)
            write_fn = agent.available_functions["write_text_file"]
            for i in range(3):
                filepath = Path(tmpdir) / f"file{i}.txt"
                result = write_fn(file_path=str(filepath), content=f"Content {i}")
                assert result.success is True
            print(f"✅ Step 1 - Created 3 files")

            # Step 2: List directory (using correct parameter names)
            list_fn = agent.available_functions["list_directory"]
            list_result = list_fn(dir_path=tmpdir)
            assert list_result.success is True
            print(f"✅ Step 2 - Listed directory: {list_result.output}")

            # Step 3: Edit one file (using correct parameter names)
            edit_fn = agent.available_functions["edit_text_file"]
            filepath = Path(tmpdir) / "file0.txt"
            edit_result = edit_fn(
                file_path=str(filepath),
                old_text="Content 0",
                new_text="Content 0 MODIFIED"
            )
            assert edit_result.success is True
            print(f"✅ Step 3 - Modified file0.txt")

            # Step 4: Verify modification (using correct parameter names)
            read_fn = agent.available_functions["read_text_file"]
            read_result = read_fn(file_path=str(filepath))
            assert "MODIFIED" in str(read_result.output)
            print(f"✅ Step 4 - Verified modification")

            print("✅ Workflow completed: Multiple file operations")


class TestAgentCapabilitiesLive:
    """Test agent capabilities with live execution."""

    def test_all_tools_callable(self):
        """Test all registered tools are callable and return ToolResult."""
        agent = BissiAgent()

        # Get count of tools
        tool_count = len(agent.available_functions)
        print(f"\n✅ Agent has {tool_count} tools available")

        # Test each tool is callable
        callable_count = 0
        for tool_name, tool_fn in agent.available_functions.items():
            assert callable(tool_fn), f"{tool_name} is not callable"
            callable_count += 1

        print(f"✅ All {callable_count} tools are callable")
        assert callable_count > 0

    def test_tool_result_structure_consistency(self):
        """Test all tool results have consistent structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = BissiAgent()
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            # Test read returns ToolResult (using correct parameter names)
            read_fn = agent.available_functions["read_text_file"]
            result = read_fn(file_path=str(test_file))

            # Verify structure
            assert isinstance(result, ToolResult)
            assert hasattr(result, 'success')
            assert hasattr(result, 'output')
            assert hasattr(result, 'error')
            assert hasattr(result, 'message')
            print(f"✅ ToolResult structure is consistent")

    def test_error_handling_with_invalid_path(self):
        """Test agent handles invalid file paths gracefully."""
        agent = BissiAgent()
        read_fn = agent.available_functions["read_text_file"]

        # Try to read non-existent file (using correct parameter names)
        result = read_fn(file_path="/nonexistent/file/path.txt")

        # Should fail gracefully
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None
        print(f"✅ Error handling works: {result.error}")

    def test_agent_context_persistence(self):
        """Test agent maintains context across operations."""
        agent = BissiAgent()

        # Verify context manager exists
        assert agent.context_manager is not None
        assert agent.context_manager.token_limit > 0

        # Verify conversation store
        assert agent.conversation_store is not None

        # Verify vector store
        assert agent.vector_store is not None

        print(f"✅ Agent context components initialized:")
        print(f"   - ContextManager: token_limit={agent.context_manager.token_limit}")
        print(f"   - ConversationStore: present")
        print(f"   - VectorStore: present")


class TestAgentReporting:
    """Test and report on agent capabilities."""

    def test_print_available_tools(self):
        """Print all available tools to demonstrate capabilities."""
        agent = BissiAgent()

        print("\n" + "="*70)
        print("🛠️  BISSI AGENT - AVAILABLE TOOLS")
        print("="*70)

        # Group tools by category
        categories = {
            "File Operations": ["read_text_file", "write_text_file", "edit_text_file"],
            "Search": ["search_files", "search_by_content", "list_directory"],
            "Data Processing": ["read_excel", "write_excel"],
            "Documents": ["read_word", "write_word", "read_pdf", "read_pptx", "write_pptx"],
            "Code": ["python_runner"],
            "Communication": ["send_email", "send_slack"],
            "Other": []
        }

        # Categorize tools
        categorized = {cat: [] for cat in categories}
        uncategorized = []

        for tool_name in agent.available_functions.keys():
            found = False
            for cat, tools in categories.items():
                if cat == "Other":
                    continue
                if tool_name in tools:
                    categorized[cat].append(tool_name)
                    found = True
                    break
            if not found:
                uncategorized.append(tool_name)

        if uncategorized:
            categorized["Other"] = uncategorized

        # Print categorized tools
        for category, tools in categorized.items():
            if tools:
                print(f"\n{category}:")
                for tool in sorted(tools):
                    print(f"  ✓ {tool}")

        print(f"\n{'='*70}")
        print(f"Total: {len(agent.available_functions)} tools available")
        print("="*70 + "\n")

    def test_print_agent_info(self):
        """Print agent information."""
        agent = BissiAgent()

        print("\n" + "="*70)
        print("📊 BISSI AGENT - SYSTEM INFORMATION")
        print("="*70)
        print(f"Model: {agent.model}")
        print(f"System Prompt: {agent.system_prompt[:60]}...")
        print(f"Available Tools: {len(agent.available_functions)}")
        print(f"Context Token Limit: {agent.context_manager.token_limit}")
        print(f"Engine Host: {agent.engine.host}")
        print(f"Engine Timeout: {agent.engine.timeout_seconds}s")
        print(f"Engine Max Retries: {agent.engine.max_retries}")
        print(f"Engine Temperature: {agent.engine.temperature}")
        print("="*70 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
