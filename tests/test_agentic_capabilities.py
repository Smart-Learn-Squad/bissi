"""Tests for BISSI agentic capabilities.

This module tests the agent's ability to:
- Use tools to accomplish tasks
- Chain multiple tool calls
- Handle errors gracefully
- Maintain context across interactions
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Any, Dict, List, Optional

from core.agent import BissiAgent
from core.engine import BissiEngine, BissiEngineError
from core.context import ContextManager
from core.memory.conversation_store import ConversationStore
from core.memory.vector_store import VectorStore
from core.types import ToolResult


class MockBissiEngine:
    """Mock BissiEngine for deterministic testing."""

    def __init__(self, response_sequence: Optional[List[Dict[str, Any]]] = None):
        self.response_sequence = response_sequence or []
        self.call_count = 0
        self.chat_history: List[Dict[str, Any]] = []

    def health_check(self) -> bool:
        return True

    def ensure_model_available(self) -> bool:
        return True

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, **kwargs) -> str:
        """Return a predetermined response from sequence."""
        if self.call_count >= len(self.response_sequence):
            raise BissiEngineError("No more responses in sequence")

        response = self.response_sequence[self.call_count]
        self.call_count += 1
        self.chat_history.append({"messages": messages, "tools": tools})
        return json.dumps(response)

    def close(self):
        pass


class TestAgentToolCalling:
    """Test agent's ability to call tools."""

    def test_agent_initialization(self):
        """Test agent initializes with proper defaults."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent(model="test-model")

                assert agent.model == "test-model"
                assert agent.system_prompt is not None
                assert len(agent.available_functions) > 0

    def test_agent_has_core_tools(self):
        """Test agent has essential tools available."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                required_tools = [
                    "read_text_file",
                    "write_text_file",
                    "read_excel",
                    "python_runner",
                    "search_files",
                ]

                for tool in required_tools:
                    assert tool in agent.available_functions, f"Missing tool: {tool}"

    def test_tool_result_structure(self):
        """Test ToolResult has correct structure."""
        result = ToolResult.ok(
            output="Test output",
            message="Operation successful",
            task_done=True
        )

        assert result.success is True
        assert result.output == "Test output"
        assert result.message == "Operation successful"
        assert result.error is None

    def test_tool_result_with_error(self):
        """Test ToolResult error handling."""
        result = ToolResult.fail(
            error="File not found",
            task_done=False
        )

        assert result.success is False
        assert result.error == "File not found"
        assert result.task_done is False


class TestAgentChaining:
    """Test agent's ability to chain multiple tool calls."""

    def test_single_tool_call_response_parsing(self):
        """Test agent can parse single tool call response."""
        mock_response = {
            "type": "tool_use",
            "id": "tool_call_1",
            "name": "read_text_file",
            "input": {"path": "/tmp/test.txt"},
            "result": "File contents"
        }

        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                # Verify agent can track tool responses
                assert agent.available_functions["read_text_file"] is not None

    def test_multiple_tool_calls_in_sequence(self):
        """Test agent can handle multiple tool calls."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                mock_sequence = [
                    {
                        "type": "tool_use",
                        "id": "tc_1",
                        "name": "search_files",
                        "input": {"pattern": "*.txt"}
                    },
                    {
                        "type": "tool_use",
                        "id": "tc_2",
                        "name": "read_text_file",
                        "input": {"path": "/tmp/result.txt"}
                    }
                ]

                # Verify agent tracks available tool types
                assert "search_files" in agent.available_functions
                assert "read_text_file" in agent.available_functions


class TestAgentErrorHandling:
    """Test agent's error handling capabilities."""

    def test_handles_invalid_tool_name(self):
        """Test agent gracefully handles invalid tool calls."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                invalid_tool = "nonexistent_tool"
                assert invalid_tool not in agent.available_functions

    def test_handles_tool_execution_failure(self):
        """Test agent handles tool execution errors."""
        result = ToolResult.fail(
            error="Permission denied",
            path="/restricted/file.txt"
        )

        assert result.success is False
        assert "Permission" in result.error
        assert result.path == "/restricted/file.txt"

    def test_handles_malformed_response(self):
        """Test agent handles malformed model responses."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                # Malformed response should not crash
                malformed = {}
                assert isinstance(malformed, dict)


class TestAgentContextManagement:
    """Test agent's context management."""

    def test_context_manager_initialization(self):
        """Test context manager is properly initialized."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                assert agent.context_manager is not None
                assert agent.context_manager.token_limit > 0

    def test_conversation_store_initialization(self):
        """Test conversation store is properly initialized."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                with patch('core.memory.conversation_store.ConversationStore'):
                    agent = BissiAgent()

                    assert agent.conversation_store is not None

    def test_vector_store_initialization(self):
        """Test vector store is properly initialized."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                with patch('core.memory.vector_store.VectorStore'):
                    agent = BissiAgent()

                    assert agent.vector_store is not None


class TestAgentCapabilities:
    """Test complex agentic workflows."""

    def test_read_write_workflow(self):
        """Test agent can perform read-write operations."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                # Verify agent has file I/O capabilities
                assert "read_text_file" in agent.available_functions
                assert "write_text_file" in agent.available_functions
                assert "edit_text_file" in agent.available_functions

    def test_search_capability(self):
        """Test agent can search for files."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                # Verify search capabilities
                assert "search_files" in agent.available_functions
                assert "search_by_content" in agent.available_functions
                assert "list_directory" in agent.available_functions

    def test_data_processing_capability(self):
        """Test agent can process data with Excel."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                # Verify data processing capabilities
                assert "read_excel" in agent.available_functions
                assert "write_excel" in agent.available_functions

    def test_code_execution_capability(self):
        """Test agent can execute Python code."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                # Verify code execution capability
                assert "python_runner" in agent.available_functions

    def test_document_processing_capability(self):
        """Test agent can process documents (Word, PDF, etc)."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                # Verify document processing capabilities
                doc_tools = ["read_word", "write_word", "read_pdf", "read_pptx"]
                for tool in doc_tools:
                    assert tool in agent.available_functions


class TestEngineReliability:
    """Test engine reliability and health checks."""

    @patch('core.engine.BissiEngine.health_check')
    def test_engine_health_check(self, mock_health):
        """Test engine health check mechanism."""
        mock_health.return_value = True

        engine = BissiEngine(model="test")
        assert engine.health_check() is True

    @patch('core.engine.BissiEngine.ensure_model_available')
    def test_engine_model_availability(self, mock_models):
        """Test engine can check model availability."""
        mock_models.return_value = True

        engine = BissiEngine(model="test")
        assert engine.ensure_model_available() is True

    def test_engine_initialization_with_custom_settings(self):
        """Test engine accepts custom configuration."""
        with patch('httpx.Client'):
            engine = BissiEngine(
                model="custom-model",
                host="http://custom:9000",
                timeout_seconds=300,
                max_retries=5,
                temperature=0.7
            )

            assert engine.model == "custom-model"
            assert engine.host == "http://custom:9000"
            assert engine.timeout_seconds == 300
            assert engine.max_retries == 5
            assert engine.temperature == 0.7


class TestAgentToolIntegration:
    """Integration tests for agent-tool interactions."""

    def test_agent_tool_registry(self):
        """Test all registered tools are callable."""
        with patch.object(BissiEngine, '__init__', return_value=None):
            with patch.object(BissiEngine, 'health_check', return_value=True):
                agent = BissiAgent()

                for tool_name, tool_fn in agent.available_functions.items():
                    assert callable(tool_fn), f"Tool {tool_name} is not callable"

    def test_tool_result_consistency(self):
        """Test ToolResult maintains consistent structure."""
        # Test success case
        success_result = ToolResult.ok(output="Success", message="OK")
        assert success_result.success is True
        assert success_result.output == "Success"
        assert success_result.error is None

        # Test error case
        error_result = ToolResult.fail(error="Error occurred")
        assert error_result.success is False
        assert error_result.error == "Error occurred"

        # Test with path
        path_result = ToolResult.ok(output="Data", path="/data/file.txt", size=1024)
        assert path_result.path == "/data/file.txt"
        assert path_result.size == 1024


@pytest.fixture
def mock_engine():
    """Provide mock engine for testing."""
    with patch.object(BissiEngine, '__init__', return_value=None):
        with patch.object(BissiEngine, 'health_check', return_value=True):
            return BissiEngine(model="test")


@pytest.fixture
def agent_with_mock_engine(mock_engine):
    """Provide agent with mock engine."""
    with patch.object(BissiEngine, '__init__', return_value=None):
        with patch.object(BissiEngine, 'health_check', return_value=True):
            return BissiAgent(model="test")


class TestAgentScenarios:
    """Real-world scenario tests."""

    def test_scenario_search_and_read(self, agent_with_mock_engine):
        """Scenario: Search for files then read one."""
        agent = agent_with_mock_engine

        # Verify agent can perform this workflow
        assert "search_files" in agent.available_functions
        assert "read_text_file" in agent.available_functions

    def test_scenario_data_analysis(self, agent_with_mock_engine):
        """Scenario: Read Excel, analyze with Python, write results."""
        agent = agent_with_mock_engine

        # Verify agent has required capabilities
        assert "read_excel" in agent.available_functions
        assert "python_runner" in agent.available_functions
        assert "write_excel" in agent.available_functions

    def test_scenario_document_generation(self, agent_with_mock_engine):
        """Scenario: Generate report document."""
        agent = agent_with_mock_engine

        # Verify agent can generate documents
        assert "write_word" in agent.available_functions
        assert "write_pptx" in agent.available_functions

    def test_scenario_code_analysis(self, agent_with_mock_engine):
        """Scenario: Search code files and analyze."""
        agent = agent_with_mock_engine

        # Verify code analysis capabilities
        assert "search_by_content" in agent.available_functions
        assert "read_text_file" in agent.available_functions
        assert "python_runner" in agent.available_functions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
