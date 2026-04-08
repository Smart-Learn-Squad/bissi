"""Central orchestrator for BISSI.

Routes user requests to appropriate tools and manages the flow between
LLM, memory, and file operations.
"""
import ollama
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable
import json

# Import modules
from functions.office.word import DocxAgent
from functions.office import excel, pdf, ocr
from functions.filesystem import explorer
from functions.operations import SafeOperator, get_operator
from core.memory.conversation_store import ConversationStore
from core.memory.vector_store import VectorStore


class BissiManager:
    """Central orchestrator connecting all BISSI components with native function calling."""
    
    # Default authoritative system prompt for BISSI
    DEFAULT_SYSTEM_PROMPT = """You are BISSI, an autonomous AI agent with direct tool access.

WORK PROTOCOL - FOLLOW THESE PHASES FOR EVERY TASK:

**Phase 1: AUDIT**
For any file-related request, ALWAYS start with list_directory('.') to see what's actually on disk.

**Phase 2: ACTION**
If a file exists in the listing, you MUST read it with the appropriate tool (read_excel, read_word, read_text_file, etc.). 
NEVER say "I cannot access" - you HAVE the tools, USE them immediately without asking permission.

**Phase 3: CALCULATION**
For data analysis, use the python_runner tool to execute code and guarantee accuracy. Don't guess - calculate.

**Phase 4: LANGUAGE**
ALWAYS respond in the SAME LANGUAGE as the user's query (French -> French, English -> English). 
Never switch languages, even if reading documents in other languages.

RULES:
- You have tools. Use them proactively.
- If a tool fails, try an alternative approach in the next iteration.
- Never ask the user for information you can discover yourself with tools.

You are an agent with tool access. ACT like one."""

    def __init__(self, 
                 model: str = 'gemma4:e2b',
                 system_prompt: Optional[str] = None,
                 conversation_store: Optional[ConversationStore] = None,
                 vector_store: Optional[VectorStore] = None):
        """Initialize BISSI manager."""
        self.model = model
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.conversation_store = conversation_store or ConversationStore()
        self.vector_store = vector_store or VectorStore()
        self.safe_operator = get_operator()
        
        # Track current conversation
        self.current_conversation_id: Optional[int] = None
        
        # Available tools registry
        self.available_functions: Dict[str, Callable] = {
            'read_word': self._tool_read_word,
            'read_excel': self._tool_read_excel,
            'read_pdf': self._tool_read_pdf,
            'read_text_file': self._tool_read_text_file,
            'search_files': self._tool_search_files,
            'search_by_content': self._tool_search_by_content,
            'list_directory': self._tool_list_directory,
            'get_file_info': self._tool_file_info,
            'get_directory_tree': self._tool_get_directory_tree,
            'get_recent_files': self._tool_get_recent_files,
            'safe_operator': self._tool_safe_operator,
        }

        # Tool definitions for Gemma 4
        self.tools = [
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
                    'description': 'MUST USE: Read and analyze Microsoft Excel (.xlsx, .xls) spreadsheets. When asked about Excel data, IMMEDIATELY use this tool to read the file. NEVER ask the user about column names - read the file first to discover the structure yourself.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'The path to the Excel file.'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'read_pdf',
                    'description': 'Extract text from a PDF file using direct extraction or OCR if necessary.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'The path to the PDF file.'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'read_text_file',
                    'description': 'Read the content of any text-based file (Python .py, Markdown .md, TXT .txt, JSON .json, YAML .yaml, etc.). Use this for source code, documentation, config files.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'The path to the text file to read.'},
                            'max_lines': {'type': 'integer', 'description': 'Maximum number of lines to read (optional, reads all if not specified).'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'search_files',
                    'description': 'Search for files matching a pattern (e.g., "*.py", "*.md", "*.txt"). REQUIRED FIRST STEP when asked to find/count files of a specific type.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string', 'description': 'File pattern to search for, e.g., "*.py" for Python files, "*.md" for markdown files.'},
                            'root_dir': {'type': 'string', 'description': 'Directory to search in (use "." for current directory)'}
                        },
                        'required': ['query']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'list_directory',
                    'description': 'List all files and subdirectories in a given path.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'path': {'type': 'string', 'description': 'The directory path to list.'}
                        },
                        'required': ['path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'get_file_info',
                    'description': 'Get file size and metadata. REQUIRED to compare file sizes or get detailed info about specific files.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'file_path': {'type': 'string', 'description': 'The path to the file to analyze.'}
                        },
                        'required': ['file_path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'search_by_content',
                    'description': 'Search for files containing specific text content within their body.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'directory': {'type': 'string', 'description': 'Directory to search in'},
                            'query': {'type': 'string', 'description': 'Text to search for within files'},
                            'extensions': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Optional file extensions to limit search (e.g., [".py", ".txt"])'}
                        },
                        'required': ['directory', 'query']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'get_directory_tree',
                    'description': 'Get a hierarchical tree structure of a directory and all its subdirectories.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'path': {'type': 'string', 'description': 'Root directory path'},
                            'max_depth': {'type': 'integer', 'description': 'Maximum depth to traverse (default: 3)'}
                        },
                        'required': ['path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'get_recent_files',
                    'description': 'Get files sorted by modification time, most recent first.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'directory': {'type': 'string', 'description': 'Directory to search in'},
                            'limit': {'type': 'integer', 'description': 'Number of recent files to return (default: 10)'}
                        },
                        'required': ['directory']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'safe_operator',
                    'description': 'Get Python version or current working directory. MUST USE when asked about Python version or working directory.',
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
            }
        ]
    
    def start_conversation(self, title: Optional[str] = None) -> int:
        """Start new conversation thread."""
        self.current_conversation_id = self.conversation_store.create_conversation(title)
        return self.current_conversation_id
    
    def load_conversation(self, conversation_id: int) -> bool:
        """Load existing conversation."""
        history = self.conversation_store.get_history(conversation_id)
        if history:
            self.current_conversation_id = conversation_id
            return True
        return False
    
    def process_request(self, user_input: str, max_iterations: int = 7) -> str:
        """Process user request with recursive multi-step reasoning loop.
        
        Accumulates the full reasoning chain (assistant reflection + tool results)
        in a local messages list to maintain context across iterations.
        
        Args:
            user_input: The user's request
            max_iterations: Maximum number of tool call cycles (default 7)
            
        Returns:
            The final assistant response after all tool iterations
        """
        if self.current_conversation_id is None:
            self.start_conversation()
        
        # Save user message to history
        self.conversation_store.save_message(self.current_conversation_id, 'user', user_input)
        
        # Initialize messages list with history + user input
        history = self.conversation_store.get_history(self.current_conversation_id, limit=15)
        messages = self._build_messages(history)
        
        iteration = 0
        done = False
        
        while iteration < max_iterations and not done:
            # Call model with accumulated conversation context
            response = ollama.chat(
                model=self.model,
                messages=messages,
                tools=self.tools
            )
            
            message = response['message']
            tool_calls = message.get('tool_calls')
            
            if not tool_calls:
                # No tool calls - we have the final answer
                done = True
                # Add final assistant message to history
                messages.append({
                    'role': 'assistant',
                    'content': message.get('content', '')
                })
                self.conversation_store.save_message(
                    self.current_conversation_id, 
                    'assistant', 
                    message.get('content', '')
                )
                break
            
            # Model wants to use tools - add its reasoning to the chain
            # Convert tool calls to proper format
            tool_calls_list = []
            for tc in tool_calls:
                tool_calls_list.append({
                    'id': tc.id if hasattr(tc, 'id') else f'call_{iteration}',
                    'type': 'function',
                    'function': {
                        'name': tc.function.name,
                        'arguments': tc.function.arguments
                    }
                })
            
            # Add assistant's tool call request to messages (its "reflection")
            assistant_msg = {
                'role': 'assistant',
                'content': message.get('content', ''),
                'tool_calls': tool_calls_list
            }
            messages.append(assistant_msg)
            
            # Persist assistant's reasoning
            self.conversation_store.save_message(
                self.current_conversation_id,
                'assistant',
                message.get('content', ''),
                metadata={'tool_calls': tool_calls_list}
            )
            
            # Execute all requested tools and add results to chain
            for tool_call in tool_calls:
                tool_id = tool_call.id if hasattr(tool_call, 'id') else f'call_{iteration}'
                func_name = tool_call.function.name
                args = tool_call.function.arguments
                
                print(f"[Core] Iter {iteration+1}: Executing {func_name}({args})")
                
                # Execute the tool
                if func_name in self.available_functions:
                    result = self.available_functions[func_name](**args)
                else:
                    result = {'error': f"Function {func_name} not found"}
                
                # Format result as text
                if isinstance(result, dict) and 'output' in result:
                    result_text = result['output']
                elif isinstance(result, dict) and 'error' in result:
                    result_text = f"Error: {result['error']}"
                elif isinstance(result, dict):
                    result_text = '\n'.join(f"{k}: {v}" for k, v in result.items())
                else:
                    result_text = str(result)
                
                # Add tool result to messages (feeds next iteration)
                tool_msg = {
                    'role': 'tool',
                    'content': result_text,
                    'tool_call_id': tool_id,
                    'tool_name': func_name
                }
                messages.append(tool_msg)
                
                # Persist tool result
                self.conversation_store.save_message(
                    self.current_conversation_id,
                    'tool',
                    f"[{func_name}] {result_text}",
                    metadata={'tool_name': func_name, 'tool_call_id': tool_id}
                )
            
            iteration += 1
        
        # Return final assistant content
        return message.get('content', '')

    def _build_messages(self, history: List[Dict]) -> List[Dict[str, str]]:
        """Build message list for LLM, prepending system_prompt if set."""
        messages = []
        
        # Prepend system prompt if it exists and history doesn't start with one
        if self.system_prompt and (not history or history[0].get('role') != 'system'):
            messages.append({'role': 'system', 'content': self.system_prompt})
            
        for msg in history:
            role = msg['role']
            if role in ('user', 'assistant', 'system', 'tool'):
                msg_obj = {'role': role, 'content': msg['content']}
                
                # Restore tool_calls from metadata for assistant messages
                if role == 'assistant':
                    meta = msg.get('metadata') or {}
                    if 'tool_calls' in meta:
                        msg_obj['tool_calls'] = meta['tool_calls']
                
                # Add tool_name for tool messages (from name field or metadata)
                if role == 'tool':
                    if 'name' in msg:
                        msg_obj['tool_name'] = msg['name']
                    else:
                        # Try to extract from metadata if available
                        meta = msg.get('metadata') or {}
                        if 'tool_name' in meta:
                            msg_obj['tool_name'] = meta['tool_name']
                
                messages.append(msg_obj)
        return messages

    # --- Tool implementation wrappers (internal) ---
    def _tool_read_word(self, file_path: str) -> Dict[str, Any]:
        try:
            agent = DocxAgent(file_path)
            return {'success': True, 'content': agent.read_paragraphs()[:30], 'tables_count': len(agent.read_tables())}
        except Exception as e: return {'success': False, 'error': str(e)}

    def _tool_read_excel(self, file_path: str, max_rows: int = 100) -> Dict[str, Any]:
        try:
            df = excel.read_excel(file_path)
            total_rows = len(df)
            # Return all data or up to max_rows
            data = df.head(max_rows).to_dict('records')
            return {
                'success': True, 
                'columns': list(df.columns), 
                'data': data,
                'total_rows': total_rows,
                'returned_rows': len(data)
            }
        except Exception as e: return {'success': False, 'error': str(e)}

    def _tool_read_pdf(self, file_path: str) -> Dict[str, Any]:
        try:
            result = ocr.smart_pdf_extract(file_path)
            return {'success': True, 'content': result['text'][:2000], 'is_scanned': result['is_scanned']}
        except Exception as e: return {'success': False, 'error': str(e)}

    def _tool_read_text_file(self, file_path: str, max_lines: int = None) -> Dict[str, Any]:
        """Read any text file (Python, Markdown, TXT, JSON, etc.)."""
        try:
            return explorer.read_text_file(file_path, max_lines)
        except Exception as e: return {'success': False, 'error': str(e)}

    def _tool_search_files(self, query: str, root_dir: str = '.') -> Dict[str, Any]:
        try:
            results = explorer.search_files(root_dir, query)
            return {'success': True, 'results': results[:10]}
        except Exception as e: return {'success': False, 'error': str(e)}

    def _tool_list_directory(self, path: str) -> Dict[str, Any]:
        try:
            return {'success': True, 'items': explorer.list_directory(path)}
        except Exception as e: return {'success': False, 'error': str(e)}

    def _tool_file_info(self, file_path: str) -> Dict[str, Any]:
        try:
            return {'success': True, 'info': explorer.get_file_info(file_path)}
        except Exception as e: return {'success': False, 'error': str(e)}

    def _tool_search_by_content(self, directory: str, query: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search for files containing specific text content."""
        try:
            return {'success': True, 'results': explorer.search_by_content(directory, query, extensions)}
        except Exception as e: return {'success': False, 'error': str(e)}

    def _tool_get_directory_tree(self, path: str, max_depth: int = 3) -> Dict[str, Any]:
        """Get hierarchical tree structure of directory."""
        try:
            return {'success': True, 'tree': explorer.get_directory_tree(path, max_depth)}
        except Exception as e: return {'success': False, 'error': str(e)}

    def _tool_get_recent_files(self, directory: str, limit: int = 10) -> Dict[str, Any]:
        """Get recently modified files."""
        try:
            return {'success': True, 'files': explorer.get_recent_files(directory, limit)}
        except Exception as e: return {'success': False, 'error': str(e)}

    def _tool_safe_operator(self, operation: str) -> Dict[str, Any]:
        """Execute safe system operations."""
        try:
            if operation == 'get_python_version':
                import sys
                return {'success': True, 'output': sys.version}
            elif operation == 'get_current_directory':
                import os
                return {'success': True, 'output': os.getcwd()}
            else:
                return {'success': False, 'error': f'Unknown operation: {operation}'}
        except Exception as e: return {'success': False, 'error': str(e)}
    
    def index_document_for_rag(self, file_path: Union[str, Path]) -> List[str]:
        """Index document into vector store for RAG.
        
        Args:
            file_path: Document to index
            
        Returns:
            List of chunk IDs
        """
        return self.vector_store.index_file(file_path)
    
    def query_documents(self, query: str, n_results: int = 3) -> str:
        """Query indexed documents and generate response.
        
        Args:
            query: Search query
            n_results: Number of documents to retrieve
            
        Returns:
            Generated response based on retrieved documents
        """
        # Retrieve relevant documents
        results = self.vector_store.query(query, n_results=n_results)
        
        if not results:
            return "No relevant documents found in the knowledge base."
        
        # Build context
        context = "Based on the following documents:\n\n"
        for i, result in enumerate(results, 1):
            context += f"Document {i}:\n{result['content'][:500]}...\n\n"
        
        context += f"\nQuestion: {query}"
        
        # Generate response
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant. Answer based only on the provided documents.'},
            {'role': 'user', 'content': context}
        ]
        
        return self._chat_with_llm(messages)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get current conversation history."""
        if self.current_conversation_id is None:
            return []
        return self.conversation_store.get_history(self.current_conversation_id)


# Singleton instance
_manager_instance: Optional[BissiManager] = None


def get_manager() -> BissiManager:
    """Get or create BISSI manager singleton."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = BissiManager()
    return _manager_instance
