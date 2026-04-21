"""Central orchestrator for BISSI.

Routes user requests to appropriate tools and manages the flow between
LLM, memory, and file operations.
"""
import json
import logging
import os
import shutil
import sys
from functools import wraps
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable

import ollama
import pandas as pd

from functions.office.word import DocxAgent
from functions.office import excel, pdf, ocr, powerpoint
from functions.filesystem import explorer, writer
from functions.operations import SafeOperator, get_operator
from functions.code import python_runner
from functions.system import clipboard
from core.memory.conversation_store import ConversationStore
from core.memory.vector_store import VectorStore
from core.router import route as _route
from core.user_profile import get_profile
from core.types import ToolResult

logger = logging.getLogger(__name__)


def tool_result(func: Callable) -> Callable:
    """Decorator that wraps tool methods with uniform error handling.

    Catches any exception and returns ToolResult.fail()
    so the LLM always gets a structured response.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception("Tool %s failed", func.__name__)
            return ToolResult.fail(str(e))
    return wrapper


def _raise_on_failure(result: Dict[str, Any]) -> Dict[str, Any]:
    """Raise on tool helper failure so SafeOperator can rollback cleanly."""
    if not result.get('success'):
        raise RuntimeError(result.get('error', 'Operation failed'))
    return result


class BissiAgent:
    """Central orchestrator connecting all BISSI components with native function calling."""

    # Default authoritative system prompt for BISSI
    DEFAULT_SYSTEM_PROMPT = """You are BISSI, an autonomous local AI agent.

CORE RULES (non-negotiable):
1. ACT, DON'T TALK: Call tools immediately. Never explain what you are about to do.
2. FILE OUTPUT IS MANDATORY: If the user asks for a .docx, .pptx, or .xlsx file, you MUST call the corresponding write tool. Never output the content as plain text in the chat.
3. PPTX RULE: Any request mentioning .pptx or "presentation" = call write_pptx immediately with structured slides.
4. FIND FILES YOURSELF: Never ask where a file is. Use list_directory or search_files first.
5. CALCULATE WITH CODE: Any sum, average, or count = use python_runner. Never calculate manually.
6. NO HALLUCINATION: Only report what tools return. Never invent data.
7. CONFIRM AFTER WRITING: After writing a file, confirm the path and size. Nothing else.

TOOL SELECTION GUIDE:
- User says "summarize in a .pptx" → write_pptx
- User says "write in a .docx" → write_word
- User says "analyse this Excel file" → read_excel + python_runner
- User says "read this document" → read_word or read_text_file
- User asks about current directory → safe_operator

FORBIDDEN:
- Never output slide content as plain text
- Never ask for clarification if you can find the answer with a tool
- Never say "I cannot create a file"
"""

    def __init__(self,
                 model: str = 'gemma4:e2b',
                 system_prompt: Optional[str] = None,
                 conversation_store: Optional[ConversationStore] = None,
                 vector_store: Optional[VectorStore] = None,
                 confirm_callback: Optional[Callable[[str, str], bool]] = None):
        """Initialize BISSI agent."""
        self.model = model
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.conversation_store = conversation_store or ConversationStore()
        self.vector_store = vector_store or VectorStore()
        self.safe_operator = get_operator(confirm_callback=confirm_callback)

        # Track current conversation
        self.current_conversation_id: Optional[int] = None

        # Active semantic memory
        self._profile = get_profile()

        # Available tools registry
        self.available_functions: Dict[str, Callable] = {
            'read_word': self._tool_read_word,
            'write_word': self._tool_write_word,
            'read_excel': self._tool_read_excel,
            'write_excel': self._tool_write_excel,
            'read_pptx': self._tool_read_pptx,
            'write_pptx': self._tool_write_pptx,
            'read_pdf': self._tool_read_pdf,
            'read_text_file': self._tool_read_text_file,
            'write_text_file': self._tool_write_text_file,
            'edit_text_file': self._tool_edit_text_file,
            'search_files': self._tool_search_files,
            'search_by_content': self._tool_search_by_content,
            'list_directory': self._tool_list_directory,
            'get_file_info': self._tool_file_info,
            'get_directory_tree': self._tool_get_directory_tree,
            'get_recent_files': self._tool_get_recent_files,
            'safe_operator': self._tool_safe_operator,
            'python_runner': self._tool_python_runner,
            'get_clipboard': self._tool_get_clipboard,
            'set_clipboard': self._tool_set_clipboard,
            # Vision tools
            'describe_image': self._tool_describe_image,
            'extract_text_from_image': self._tool_extract_text_from_image,
            'analyze_screenshot': self._tool_analyze_screenshot,
            'analyze_chart': self._tool_analyze_chart,
            'delete_file': self._tool_delete_file,
            'move_file': self._tool_move_file,
        }

        # Tool definitions for Gemma 4
        self.tools = self._build_tool_definitions()

    def start_conversation(self, title: Optional[str] = None) -> int:
        """Start new conversation thread."""
        self.current_conversation_id = self.conversation_store.create_conversation(title)
        return self.current_conversation_id

    def _generate_conversation_title(self, first_message: str) -> str:
        """Generate a concise title from the first user message.
        
        Takes first 5-7 meaningful words, max 40 chars.
        """
        # Clean up the message
        clean = first_message.strip().replace('\n', ' ')
        # Remove common prefixes
        prefixes = ['analyse ', 'analyser ', 'analysez ', 'explique ', 'expliquer ',
                    'résume ', 'résumer ', 'génère ', 'générer ', 'rédige ',
                    'crée ', 'créer ', 'écris ', 'écrire ', 'produis ',
                    'create ', 'generate ', 'summarize ', 'summarise ', 'explain ',
                    'list ', 'find ', 'search ', 'show ', 'read ', 'make ', 'write ', 'help ']
        lower = clean.lower()
        for p in prefixes:
            if lower.startswith(p):
                clean = clean[len(p):].strip()
                break
        # Take first words, max 40 chars
        words = clean.split()
        title_words = []
        length = 0
        for w in words[:7]:
            if length + len(w) + 1 <= 40:
                title_words.append(w)
                length += len(w) + 1
            else:
                break
        title = ' '.join(title_words)
        if len(title) > 40:
            title = title[:37] + '...'
        return title if title else 'Nouvelle conversation'

    def load_conversation(self, conversation_id: int) -> bool:
        """Load existing conversation."""
        history = self.conversation_store.get_history(conversation_id)
        if history:
            self.current_conversation_id = conversation_id
            return True
        return False

    # --- Core processing loop ---

    def process_request(
        self,
        user_input: str,
        max_iterations: int = 7,
        on_chunk: Optional[Callable[[str], None]] = None,
        on_tool_start: Optional[Callable[[str, Any], None]] = None,
        on_tool_done: Optional[Callable[[str, str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
    ) -> str:
        """Process user request with recursive multi-step reasoning loop.

        The loop runs until the model produces a final answer with no tool
        calls, max_iterations is reached, or should_stop() returns True.

        Args:
            user_input:      The user's request.
            max_iterations:  Maximum number of tool-call cycles (default 7).
            on_chunk:        Called with each streamed text token.
            on_tool_start:   Called before executing a tool (name, args).
            on_tool_done:    Called after executing a tool (name, result_str).
            on_thinking:     Called with status / thinking messages.
            should_stop:     Callable checked between iterations; return True
                             to abort and trigger the interrupted path.

        Returns:
            The final assistant response, or "" if interrupted.
        """
        def _stopped() -> bool:
            return should_stop is not None and should_stop()

        if _stopped():
            return ""

        if self.current_conversation_id is None:
            self.start_conversation()

        # ── Software MoE : routing adaptatif ──────────────────
        route_result = _route(
            user_input,
            threshold_adjustment=self._profile.threshold_adjustment()
        )
        self.model = route_result.model
        self._profile.record(route_result.model, route_result.domains)

        if on_thinking:
            on_thinking(
                f"→ {route_result.model} · score {route_result.score}"
            )

        self.conversation_store.save_message(
            self.current_conversation_id, 'user', user_input
        )

        # Auto-generate title on first user message
        history_check = self.conversation_store.get_history(self.current_conversation_id)
        if len(history_check) == 1:  # First message just saved
            auto_title = self._generate_conversation_title(user_input)
            self.conversation_store.update_conversation_title(
                self.current_conversation_id, auto_title
            )

        history = self.conversation_store.get_history(
            self.current_conversation_id, limit=15
        )
        messages = self._build_messages(history)

        if on_thinking:
            on_thinking("Connexion à Ollama…")

        for iteration in range(max_iterations):
            if _stopped():
                return ""

            if on_thinking:
                on_thinking(
                    f"Itération {iteration + 1} / {max_iterations}…"
                    if iteration > 0 else ""
                )

            full_content, tool_calls = self._stream_response(
                messages, on_chunk, should_stop
            )

            if _stopped():
                return ""

            if not tool_calls:
                # ── Final answer — no more tool calls ──────────────────
                self.conversation_store.save_message(
                    self.current_conversation_id, 'assistant', full_content
                )
                if on_thinking:
                    on_thinking("")
                return full_content

            # ── Tool-call round ────────────────────────────────────────
            calls_metadata = self._format_tool_calls(tool_calls, iteration)

            messages.append({
                'role': 'assistant',
                'content': full_content,
                'tool_calls': calls_metadata,
            })
            self.conversation_store.save_message(
                self.current_conversation_id, 'assistant', full_content,
                metadata={'tool_calls': calls_metadata},
            )

            for tool_call in tool_calls:
                if _stopped():
                    return ""

                func_name = tool_call.function.name
                raw_args  = tool_call.function.arguments
                tool_id   = (
                    tool_call.id if hasattr(tool_call, 'id')
                    else f'call_{iteration}'
                )

                # Notify UI: tool is starting
                if on_tool_start:
                    on_tool_start(func_name, raw_args)

                result_text = self._execute_tool(tool_call, iteration)

                # Notify UI: tool finished
                if on_tool_done:
                    on_tool_done(func_name, result_text)

                messages.append({
                    'role': 'tool',
                    'content': result_text,
                    'tool_call_id': tool_id,
                    'tool_name': func_name,
                })
                self.conversation_store.save_message(
                    self.current_conversation_id, 'tool',
                    f"[{func_name}] {result_text}",
                    metadata={'tool_name': func_name, 'tool_call_id': tool_id},
                )

        # Max iterations exhausted without a clean final answer
        limit_msg = (
            f"⚠ Limite de {max_iterations} itérations atteinte "
            "sans réponse finale."
        )
        if on_thinking:
            on_thinking("")
        return limit_msg

    def _stream_response(
        self,
        messages: List[Dict],
        on_chunk: Optional[Callable],
        should_stop: Optional[Callable[[], bool]] = None,
    ) -> tuple:
        """Stream a response from the LLM and collect content + tool calls.

        Returns:
            Tuple of (full_content: str, tool_calls: list)
        """
        full_content = ""
        tool_calls   = []

        response_stream = ollama.chat(
            model=self.model,
            messages=messages,
            tools=self.tools,
            stream=True,
        )

        for chunk in response_stream:
            if should_stop and should_stop():
                break
            if 'message' not in chunk:
                continue
            msg = chunk['message']
            if 'content' in msg and msg['content']:
                part = msg['content']
                full_content += part
                if on_chunk:
                    on_chunk(part)
            if 'tool_calls' in msg:
                tool_calls.extend(msg['tool_calls'])

        return full_content, tool_calls

    def _format_tool_calls(self, tool_calls: list, iteration: int) -> List[Dict]:
        """Format raw tool call objects into the dict format expected by the Ollama API."""
        calls_metadata = []
        for tc in tool_calls:
            calls_metadata.append({
                'id': tc.id if hasattr(tc, 'id') else f'call_{iteration}',
                'type': 'function',
                'function': {
                    'name': tc.function.name,
                    'arguments': tc.function.arguments,
                },
            })
        return calls_metadata

    def _execute_tool(self, tool_call, iteration: int) -> str:
        """Execute a single tool call and format the result as text for the LLM.

        Returns:
            String representation of the tool result, ready to feed back into messages.
        """
        tool_id   = tool_call.id if hasattr(tool_call, 'id') else f'call_{iteration}'
        func_name = tool_call.function.name
        args      = tool_call.function.arguments

        logger.info("Iter %d: Executing %s(%s)", iteration + 1, func_name, args)

        if func_name in self.available_functions:
            result = self.available_functions[func_name](**args)
        else:
            result = ToolResult.fail(f"Function {func_name} not found")

        # Keep a structured payload for the model instead of dropping metadata.
        if isinstance(result, ToolResult):
            result_text = json.dumps(result.to_dict(), ensure_ascii=False)
        elif isinstance(result, dict):
            result_text = json.dumps(result, ensure_ascii=False)
        else:
            result_text = str(result)

        return result_text

    def _build_messages(self, history: List[Dict]) -> List[Dict[str, str]]:
        """Build message list for LLM, prepending system_prompt if set."""
        messages = []

        if self.system_prompt and (not history or history[0].get('role') != 'system'):
            messages.append({'role': 'system', 'content': self.system_prompt})

        for msg in history:
            role = msg['role']
            if role not in ('user', 'assistant', 'system', 'tool'):
                continue

            msg_obj = {'role': role, 'content': msg['content']}

            if role == 'assistant':
                meta = msg.get('metadata') or {}
                if 'tool_calls' in meta:
                    msg_obj['tool_calls'] = meta['tool_calls']

            if role == 'tool':
                if 'name' in msg:
                    msg_obj['tool_name'] = msg['name']
                else:
                    meta = msg.get('metadata') or {}
                    if 'tool_name' in meta:
                        msg_obj['tool_name'] = meta['tool_name']

            messages.append(msg_obj)
        return messages

    # --- Tool definitions ---

    @staticmethod
    def _build_tool_definitions() -> List[Dict]:
        """Build the tool schema list for Ollama function calling."""
        return [
            {
                'type': 'function',
                'function': {
                    'name': 'python_runner',
                    'description': 'REQUIRED for all data analysis, calculations, and complex logic. Use pandas for CSV/Excel/JSON files, numpy for math, and matplotlib for charts. ALWAYS provide the complete python code to execute.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'code': {'type': 'string', 'description': 'The Python code to execute in the sandbox.'}
                        },
                        'required': ['code']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'write_word',
                    'description': 'Create a new Word document or update an existing one with text content.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'The absolute or relative path where to save the .docx file.'},
                            'content': {'type': 'string', 'description': 'The text content to write. Newlines will be treated as separate paragraphs.'},
                            'append': {'type': 'boolean', 'description': 'Whether to add to the existing document (True) or overwrite (False). Default: False'}
                        },
                        'required': ['file_path', 'content']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'read_word',
                    'description': 'Read content (paragraphs and tables) from a Microsoft Word (.docx) file.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'The absolute or relative path to the .docx file.'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'read_excel',
                    'description': 'Read Microsoft Excel (.xlsx, .xls) spreadsheets. Returns the column names and first 100 rows.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'The path to the Excel file.'},
                            'max_rows': {'type': 'integer', 'description': 'Max rows to read (default 100).'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'write_excel',
                    'description': 'Create or overwrite an Excel file with data.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to save the .xlsx file.'},
                            'data': {'type': 'array', 'items': {'type': 'object'}, 'description': 'List of objects representing rows (e.g., [{"col1": "val1"}, {"col1": "val2"}])'},
                            'sheet_name': {'type': 'string', 'description': 'Name of the worksheet.'}
                        },
                        'required': ['file_path', 'data']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'read_pptx',
                    'description': 'Extract text content from a PowerPoint (.pptx) presentation.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the PowerPoint file.'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'write_pptx',
                    'description': 'Create a new PowerPoint presentation with slides.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to save the .pptx file.'},
                            'title': {'type': 'string', 'description': 'Main title of the presentation.'},
                            'slides': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'title': {'type': 'string'},
                                        'content': {'type': 'string'}
                                    }
                                },
                                'description': 'List of slides with title and content.'
                            }
                        },
                        'required': ['file_path', 'title', 'slides']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'get_clipboard',
                    'description': 'Read the current text content of the system clipboard.',
                    'parameters': {
                        'type': 'object',
                        'properties': {}
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'set_clipboard',
                    'description': 'Copy text to the system clipboard.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'text': {'type': 'string', 'description': 'The text to copy.'}
                        },
                        'required': ['text']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'delete_file',
                    'description': 'Permanently delete a file from the disk.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the file to delete.'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'move_file',
                    'description': 'Move or rename a file.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'source': {'type': 'string', 'description': 'Current file path.'},
                            'destination': {'type': 'string', 'description': 'New file path.'}
                        },
                        'required': ['source', 'destination']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'read_pdf',
                    'description': 'Extract text from a PDF file, including scanned documents via OCR.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the PDF file.'},
                            'max_chars': {'type': 'integer', 'description': 'Maximum characters to return (default 2000).'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'read_text_file',
                    'description': 'Read a plain text file (.txt, .py, .md, .csv, etc.).',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the text file.'},
                            'max_lines': {'type': 'integer', 'description': 'Maximum lines to return (default: all).'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'write_text_file',
                    'description': 'Write or append content to a plain text file.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the file.'},
                            'content': {'type': 'string', 'description': 'Content to write.'},
                            'append': {'type': 'boolean', 'description': 'Append to existing content (True) or overwrite (False).'}
                        },
                        'required': ['file_path', 'content']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'edit_text_file',
                    'description': 'Replace specific text in a file (find & replace).',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the file.'},
                            'old_text': {'type': 'string', 'description': 'Text to find.'},
                            'new_text': {'type': 'string', 'description': 'Replacement text.'}
                        },
                        'required': ['file_path', 'old_text', 'new_text']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'search_files',
                    'description': 'Search for files by name pattern.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string', 'description': 'Filename pattern to search for.'},
                            'root_dir': {'type': 'string', 'description': 'Directory to search in (default: current directory).'}
                        },
                        'required': ['query']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'search_by_content',
                    'description': 'Search for files containing specific text.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'directory': {'type': 'string', 'description': 'Directory to search in.'},
                            'query': {'type': 'string', 'description': 'Text to search for inside files.'},
                            'extensions': {'type': 'array', 'items': {'type': 'string'}, 'description': 'List of file extensions to include (e.g., [".py", ".txt"]).'}
                        },
                        'required': ['directory', 'query']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'list_directory',
                    'description': 'List the contents of a directory.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'path': {'type': 'string', 'description': 'Path to the directory.'}
                        },
                        'required': ['path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'get_file_info',
                    'description': 'Get metadata about a file (size, modification date, etc.).',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the file.'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'get_directory_tree',
                    'description': 'Get a recursive tree view of a directory.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'path': {'type': 'string', 'description': 'Root directory path.'},
                            'max_depth': {'type': 'integer', 'description': 'Maximum depth (default 3).'}
                        },
                        'required': ['path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'get_recent_files',
                    'description': 'Get recently modified files in a directory.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'directory': {'type': 'string', 'description': 'Directory to search.'},
                            'limit': {'type': 'integer', 'description': 'Maximum files to return (default 10).'}
                        },
                        'required': ['directory']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'safe_operator',
                    'description': 'Run safe system introspection operations.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'operation': {
                                'type': 'string',
                                'enum': ['get_python_version', 'get_current_directory'],
                                'description': 'get_python_version returns Python version string, get_current_directory returns current working directory path'
                            }
                        },
                        'required': ['operation']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'describe_image',
                    'description': 'Describe or analyze an image using Gemma 4 vision model. Supports PNG, JPG, WEBP, GIF, BMP formats.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the image file'},
                            'prompt': {'type': 'string', 'description': 'Question or instruction about the image'},
                            'detail': {'type': 'string', 'enum': ['low', 'high', 'auto'], 'description': 'Detail level (default: high)'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'extract_text_from_image',
                    'description': 'Extract text from an image using vision model (OCR-like).',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the image'},
                            'language': {'type': 'string', 'description': 'Language code (default: eng)'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'analyze_screenshot',
                    'description': 'Analyze a screenshot, identify UI elements, text, and layout.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the screenshot'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'analyze_chart',
                    'description': 'Analyze a chart or graph, extract data points and trends.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'Path to the chart image'}
                        },
                        'required': ['file_path']
                    }
                }
            },
        ]

    # --- Tool implementation wrappers ---

    @staticmethod
    def _cancelled_result(operation: str, file_path: Union[str, Path]) -> ToolResult:
        path = str(Path(file_path).expanduser().resolve())
        return ToolResult.fail(
            f"{operation} cancelled by confirmation policy",
            path=path,
        )

    @staticmethod
    def _file_result(file_path: Union[str, Path], message: str) -> ToolResult:
        path = Path(file_path).expanduser().resolve()
        size = path.stat().st_size if path.exists() and path.is_file() else None
        return ToolResult.ok(message=message, path=str(path), size=size)

    @tool_result
    def _tool_read_word(self, file_path: str) -> ToolResult:
        agent = DocxAgent(file_path)
        return ToolResult.ok(
            output={
                'content': agent.read_paragraphs()[:500],
                'tables_count': len(agent.read_tables()),
            },
            path=str(Path(file_path).expanduser().resolve()),
        )

    @tool_result
    def _tool_write_word(self, file_path: str, content: str, append: bool = False) -> ToolResult:
        from functions.office import word
        target = Path(file_path).expanduser()
        description = "modify word document" if append and target.exists() else "create word document"
        operation = self.safe_operator.modify_document if append and target.exists() else self.safe_operator.write_new
        ok = operation(
            target,
            lambda path: word.write_document(str(path), content, append),
            description=description,
        )
        if not ok:
            return self._cancelled_result(description, target)
        return self._file_result(target, f'Document saved to {target}')

    @tool_result
    def _tool_read_excel(self, file_path: str, max_rows: int = 100) -> ToolResult:
        df = excel.read_excel(file_path)
        total_rows = len(df)
        data = df.head(max_rows).to_dict('records')
        all_rows_returned = len(data) >= total_rows
        return ToolResult.ok(
            output={
                'columns': list(df.columns),
                'data': data,
                'total_rows': total_rows,
                'returned_rows': len(data),
            },
            task_done=all_rows_returned,
        )

    @tool_result
    def _tool_write_excel(self, file_path: str, data: List[Dict[str, Any]], sheet_name: str = "Sheet1") -> ToolResult:
        df = pd.DataFrame(data)
        target = Path(file_path).expanduser()
        ok = self.safe_operator.write_new(
            target,
            lambda path: excel.write_excel(str(path), df, sheet_name=sheet_name),
            description="create excel file",
        )
        if not ok:
            return self._cancelled_result("create excel file", target)
        return self._file_result(target, f'Excel file saved to {target}')

    @tool_result
    def _tool_read_pptx(self, file_path: str) -> ToolResult:
        slides = powerpoint.read_presentation(file_path)
        return ToolResult.ok(
            output={'slides': slides},
            path=str(Path(file_path).expanduser().resolve()),
        )

    @tool_result
    def _tool_write_pptx(self, file_path: str, title: str, slides: List[Dict[str, str]]) -> ToolResult:
        target = Path(file_path).expanduser()

        def _write(path: Path) -> None:
            presentation = powerpoint.create_presentation(title)
            for slide_data in slides:
                presentation.add_slide(slide_data.get('title', ''), slide_data.get('content', ''))
            presentation.save(str(path))

        ok = self.safe_operator.write_new(
            target,
            _write,
            description="create powerpoint presentation",
        )
        if not ok:
            return self._cancelled_result("create powerpoint presentation", target)
        return self._file_result(target, f'Presentation saved to {target}')

    @tool_result
    def _tool_get_clipboard(self) -> ToolResult:
        return ToolResult.ok(output={'content': clipboard.get_clipboard()})

    @tool_result
    def _tool_set_clipboard(self, text: str) -> ToolResult:
        clipboard.set_clipboard(text)
        return ToolResult.ok(message='Text copied to clipboard')

    @tool_result
    def _tool_delete_file(self, file_path: str) -> ToolResult:
        ok = self.safe_operator.delete(file_path)
        if not ok:
            return self._cancelled_result("delete file", file_path)
        resolved = str(Path(file_path).expanduser().resolve())
        return ToolResult.ok(message=f'Deleted {resolved}', path=resolved)

    @tool_result
    def _tool_move_file(self, source: str, destination: str) -> ToolResult:
        ok = self.safe_operator.move(source, destination)
        if not ok:
            return self._cancelled_result("move file", source)
        return self._file_result(destination, f'Moved {source} to {destination}')

    @tool_result
    def _tool_read_pdf(self, file_path: str, max_chars: int = 2000) -> ToolResult:
        result = ocr.smart_pdf_extract(file_path)
        text = result['text']
        truncated = len(text) > max_chars
        content = text[:max_chars]
        if truncated:
            content += (
                f'\n\n... [TRUNCATED: {len(text) - max_chars} more characters remaining. '
                'Use max_chars to read more.]'
            )
        return ToolResult.ok(
            output={
                'content': content,
                'is_scanned': result['is_scanned'],
                'truncated': truncated,
                'total_length': len(text),
            },
            task_done=not truncated,
        )

    @tool_result
    def _tool_read_text_file(self, file_path: str, max_lines: int = None) -> ToolResult:
        result = explorer.read_text_file(file_path, max_lines)
        if result.get('success'):
            return ToolResult.ok(
                output={
                    'content': result.get('content'),
                    'lines': result.get('lines'),
                },
                path=result.get('path'),
                size=result.get('size'),
                task_done=not result.get('truncated', False),
            )
        return ToolResult.fail(result.get('error'), path=result.get('path'))

    @tool_result
    def _tool_write_text_file(
        self,
        file_path: Optional[str] = None,
        content: str = "",
        append: bool = False,
        path: Optional[str] = None,
    ) -> ToolResult:
        target_path = file_path or path
        if not target_path:
            return ToolResult.fail("Missing required argument: 'file_path'")
        target = Path(target_path).expanduser()
        description = "modify text file" if append and target.exists() else "create text file"
        operation = self.safe_operator.modify_document if append and target.exists() else self.safe_operator.write_new
        ok = operation(
            target,
            lambda resolved: _raise_on_failure(writer.write_text_file(resolved, content, append)),
            description=description,
        )
        if not ok:
            return self._cancelled_result(description, target)
        return self._file_result(target, f'Text file saved to {target}')

    @tool_result
    def _tool_edit_text_file(self, file_path: str, old_text: str, new_text: str) -> ToolResult:
        target = Path(file_path).expanduser()
        ok = self.safe_operator.modify_document(
            target,
            lambda resolved: _raise_on_failure(writer.replace_in_file(resolved, old_text, new_text)),
            description="modify text file",
        )
        if not ok:
            return self._cancelled_result("modify text file", target)
        return self._file_result(target, f'Text updated in {target}')

    @tool_result
    def _tool_search_files(self, query: str, root_dir: str = '.') -> ToolResult:
        results = explorer.search_files(root_dir, query)
        trimmed = results[:10]
        return ToolResult.ok(
            output={'results': trimmed},
            message=f'{len(trimmed)} file(s) found',
        )

    @tool_result
    def _tool_list_directory(self, path: str) -> ToolResult:
        items = explorer.list_directory(path)
        return ToolResult.ok(
            output={'items': items},
            path=str(Path(path).expanduser().resolve()),
            message=f'{len(items)} item(s)',
        )

    @tool_result
    def _tool_file_info(self, file_path: str) -> ToolResult:
        info = explorer.get_file_info(file_path)
        return ToolResult.ok(
            output={'info': info},
            path=info.get('path'),
            size=info.get('size'),
        )

    @tool_result
    def _tool_search_by_content(self, directory: str, query: str, extensions: Optional[List[str]] = None) -> ToolResult:
        results = explorer.search_by_content(directory, query, extensions)
        return ToolResult.ok(
            output={'results': results},
            message=f'{len(results)} file(s) matched content query',
        )

    @tool_result
    def _tool_get_directory_tree(self, path: str, max_depth: int = 3) -> ToolResult:
        return ToolResult.ok(
            output={'tree': explorer.get_directory_tree(path, max_depth)},
            path=str(Path(path).expanduser().resolve()),
        )

    @tool_result
    def _tool_get_recent_files(self, directory: str, limit: int = 10) -> ToolResult:
        files = explorer.get_recent_files(directory, limit=limit)
        return ToolResult.ok(
            output={'files': files},
            path=str(Path(directory).expanduser().resolve()),
            message=f'{len(files)} recent file(s)',
        )

    @tool_result
    def _tool_python_runner(self, code: str) -> ToolResult:
        return python_runner.run_code(code)

    @tool_result
    def _tool_safe_operator(self, operation: str) -> ToolResult:
        if operation == 'get_python_version':
            return ToolResult.ok(output=sys.version)
        elif operation == 'get_current_directory':
            return ToolResult.ok(output=os.getcwd())
        return ToolResult.fail(f'Unknown operation: {operation}')

    # --- Vision tools ---
    @tool_result
    def _tool_describe_image(self, file_path: str, prompt: str = "Describe this image in detail.", detail: str = "high") -> ToolResult:
        from functions.vision import describe_image
        return describe_image(file_path, prompt, detail)

    @tool_result
    def _tool_extract_text_from_image(self, file_path: str, language: str = "eng") -> ToolResult:
        from functions.vision import extract_text_from_image
        return extract_text_from_image(file_path, language)

    @tool_result
    def _tool_analyze_screenshot(self, file_path: str) -> ToolResult:
        from functions.vision import analyze_screenshot
        return analyze_screenshot(file_path)

    @tool_result
    def _tool_analyze_chart(self, file_path: str) -> ToolResult:
        from functions.vision import analyze_chart
        return analyze_chart(file_path)

    # --- RAG helpers ---

    def index_document_for_rag(self, file_path: Union[str, Path]) -> List[str]:
        """Index document into vector store for RAG."""
        return self.vector_store.index_file(file_path)

    def query_documents(self, query: str, n_results: int = 3) -> str:
        """Query indexed documents and generate response."""
        results = self.vector_store.query(query, n_results=n_results)

        if not results:
            return "No relevant documents found in the knowledge base."

        context = "Based on the following documents:\n\n"
        for i, result in enumerate(results, 1):
            context += f"Document {i}:\n{result['content'][:500]}...\n\n"

        context += f"\nQuestion: {query}"

        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant. Answer based only on the provided documents.'},
            {'role': 'user', 'content': context},
        ]

        return self._chat_with_llm(messages)

    # --- Public helpers ---

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.available_functions.keys())

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get current conversation history."""
        if self.current_conversation_id is None:
            return []
        return self.conversation_store.get_history(self.current_conversation_id)


# ── Singleton ──────────────────────────────────────────────────────────────────
_agent_instance: Optional[BissiAgent] = None


def get_agent(model: str = 'gemma4:e2b') -> BissiAgent:
    """Get or create the BissiAgent singleton."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = BissiAgent(model=model)
    return _agent_instance
