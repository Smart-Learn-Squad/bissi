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
    """Central orchestrator connecting all BISSI components."""
    
    def __init__(self, 
                 model: str = 'gemma3:4b',
                 conversation_store: Optional[ConversationStore] = None,
                 vector_store: Optional[VectorStore] = None):
        """Initialize BISSI manager.
        
        Args:
            model: Ollama model name
            conversation_store: Conversation persistence instance
            vector_store: RAG vector store instance
        """
        self.model = model
        self.conversation_store = conversation_store or ConversationStore()
        self.vector_store = vector_store or VectorStore()
        self.safe_operator = get_operator()
        
        # Track current conversation
        self.current_conversation_id: Optional[int] = None
        
        # Available tools registry
        self.tools: Dict[str, Callable] = {
            'read_word': self._tool_read_word,
            'read_excel': self._tool_read_excel,
            'read_pdf': self._tool_read_pdf,
            'search_files': self._tool_search_files,
            'list_directory': self._tool_list_directory,
            'file_info': self._tool_file_info,
        }
    
    def start_conversation(self, title: Optional[str] = None) -> int:
        """Start new conversation thread.
        
        Args:
            title: Optional conversation title
            
        Returns:
            Conversation ID
        """
        self.current_conversation_id = self.conversation_store.create_conversation(title)
        return self.current_conversation_id
    
    def load_conversation(self, conversation_id: int) -> bool:
        """Load existing conversation.
        
        Args:
            conversation_id: Conversation to load
            
        Returns:
            True if loaded successfully
        """
        history = self.conversation_store.get_history(conversation_id)
        if history:
            self.current_conversation_id = conversation_id
            return True
        return False
    
    def process_request(self, user_input: str) -> str:
        """Process user request and return response.
        
        Args:
            user_input: User's message
            
        Returns:
            Assistant's response
        """
        # Ensure we have a conversation
        if self.current_conversation_id is None:
            self.start_conversation()
        
        # Save user message
        self.conversation_store.save_message(
            self.current_conversation_id,
            'user',
            user_input
        )
        
        # Build message history for context
        history = self.conversation_store.get_history(
            self.current_conversation_id,
            limit=10
        )
        
        messages = self._build_messages(history)
        
        # Check if this is a tool request
        tool_result = self._try_execute_tool(user_input)
        if tool_result:
            # Tool was executed, include result in response
            response = self._generate_tool_response(user_input, tool_result, messages)
        else:
            # Regular chat
            response = self._chat_with_llm(messages)
        
        # Save assistant response
        self.conversation_store.save_message(
            self.current_conversation_id,
            'assistant',
            response
        )
        
        return response
    
    def _build_messages(self, history: List[Dict]) -> List[Dict[str, str]]:
        """Build message list for LLM from conversation history."""
        messages = []
        
        for msg in history:
            role = msg['role']
            if role in ('user', 'assistant', 'system'):
                messages.append({
                    'role': role,
                    'content': msg['content']
                })
        
        return messages
    
    def _chat_with_llm(self, messages: List[Dict[str, str]]) -> str:
        """Send messages to Ollama and get response."""
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            return response.message.content
        except Exception as e:
            return f"Error communicating with LLM: {str(e)}"
    
    def _try_execute_tool(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Check if user input matches a tool pattern and execute."""
        # Simple keyword-based routing (can be improved with LLM classification)
        input_lower = user_input.lower()
        
        # Extract file path if present
        file_path = self._extract_file_path(user_input)
        
        if not file_path:
            return None
        
        # Route based on file extension and keywords
        path = Path(file_path)
        
        if path.suffix.lower() == '.docx':
            return self._tool_read_word(file_path)
        
        elif path.suffix.lower() in ('.xlsx', '.xls'):
            return self._tool_read_excel(file_path)
        
        elif path.suffix.lower() == '.pdf':
            return self._tool_read_pdf(file_path)
        
        elif 'search' in input_lower or 'find' in input_lower:
            return self._tool_search_files(file_path)
        
        return None
    
    def _extract_file_path(self, text: str) -> Optional[str]:
        """Try to extract file path from text."""
        # Simple extraction - look for common path patterns
        words = text.split()
        for word in words:
            # Check if word looks like a file path
            if '/' in word or '\\' in word or word.startswith('~'):
                # Clean up punctuation
                path = word.strip('"\',.!?;:')
                return path
        return None
    
    def _generate_tool_response(self, 
                                user_input: str, 
                                tool_result: Dict[str, Any],
                                messages: List[Dict[str, str]]) -> str:
        """Generate response incorporating tool results."""
        # Add tool result as system message
        tool_message = {
            'role': 'system',
            'content': f"Tool execution result:\n{json.dumps(tool_result, indent=2)}"
        }
        messages.append(tool_message)
        
        return self._chat_with_llm(messages)
    
    # Tool implementations
    def _tool_read_word(self, file_path: str) -> Dict[str, Any]:
        """Read Word document."""
        try:
            agent = DocxAgent(file_path)
            paragraphs = agent.read_paragraphs()
            tables = agent.read_tables()
            
            return {
                'success': True,
                'file_type': 'docx',
                'paragraphs': paragraphs[:20],  # Limit output
                'paragraph_count': len(paragraphs),
                'table_count': len(tables)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tool_read_excel(self, file_path: str) -> Dict[str, Any]:
        """Read Excel file."""
        try:
            df = excel.read_excel(file_path)
            
            return {
                'success': True,
                'file_type': 'excel',
                'shape': df.shape,
                'columns': list(df.columns),
                'preview': df.head(10).to_dict('records'),
                'summary': excel.summarize_sheet(file_path)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tool_read_pdf(self, file_path: str) -> Dict[str, Any]:
        """Read PDF file with OCR fallback."""
        try:
            # Try direct extraction first
            result = ocr.smart_pdf_extract(file_path)
            
            return {
                'success': True,
                'file_type': 'pdf',
                'method': result['method'],
                'is_scanned': result['is_scanned'],
                'content_preview': result['text'][:2000],
                'info': pdf.get_pdf_info(file_path)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tool_search_files(self, query: str) -> Dict[str, Any]:
        """Search files."""
        try:
            # Default to current directory
            results = explorer.search_files('.', query)
            
            return {
                'success': True,
                'query': query,
                'results_count': len(results),
                'results': results[:10]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tool_list_directory(self, path: str = '.') -> Dict[str, Any]:
        """List directory contents."""
        try:
            items = explorer.list_directory(path)
            
            return {
                'success': True,
                'path': str(Path(path).absolute()),
                'items_count': len(items),
                'items': items
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tool_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information."""
        try:
            info = explorer.get_file_info(file_path)
            return {'success': True, 'info': info}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
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
