"""Core Ollama engine for BISSI.

Provides direct interface to Ollama LLM with streaming and tool support.
"""
import ollama
from typing import List, Dict, Any, Optional, Union, Iterator
import json


class BissiEngine:
    """Ollama LLM engine wrapper."""
    
    def __init__(self, 
                 model: str = 'gemma3:4b',
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.7,
                 context_window: int = 8192):
        """Initialize BISSI engine.
        
        Args:
            model: Ollama model name
            system_prompt: System prompt for all conversations
            temperature: Sampling temperature
            context_window: Maximum context length
        """
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.context_window = context_window
        
        # Pull model if not available
        self._ensure_model()
    
    def _ensure_model(self):
        """Ensure model is available locally."""
        try:
            ollama.show(self.model)
        except ollama.ResponseError:
            # Model not available, will be pulled on first use
            pass
    
    def chat(self, 
             messages: List[Dict[str, str]],
             stream: bool = False) -> Union[str, Iterator[str]]:
        """Send chat messages to LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream response
            
        Returns:
            Response text or iterator for streaming
        """
        # Prepend system prompt if set
        if self.system_prompt:
            if not messages or messages[0].get('role') != 'system':
                messages = [{'role': 'system', 'content': self.system_prompt}] + messages
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                stream=stream,
                options={
                    'temperature': self.temperature
                }
            )
            
            if stream:
                return (chunk.message.content for chunk in response)
            else:
                return response.message.content
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate(self, 
                 prompt: str,
                 context: Optional[str] = None,
                 stream: bool = False) -> Union[str, Iterator[str]]:
        """Generate text from prompt.
        
        Args:
            prompt: Input prompt
            context: Optional context to prepend
            stream: Whether to stream response
            
        Returns:
            Generated text or iterator
        """
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        try:
            response = ollama.generate(
                model=self.model,
                prompt=full_prompt,
                stream=stream,
                options={
                    'temperature': self.temperature
                }
            )
            
            if stream:
                return (chunk.response for chunk in response)
            else:
                return response.response
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = ollama.embeddings(
                model=self.model,
                prompt=text
            )
            return response.embedding
        except Exception as e:
            raise RuntimeError(f"Embedding failed: {e}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models.
        
        Returns:
            List of model information
        """
        try:
            models = ollama.list()
            return [
                {
                    'name': model.model,
                    'size': model.size,
                    'modified': model.modified_at
                }
                for model in models.models
            ]
        except Exception as e:
            return [{'error': str(e)}]
    
    def pull_model(self, model_name: str) -> Iterator[str]:
        """Pull model from Ollama registry.
        
        Args:
            model_name: Model to pull
            
        Returns:
            Iterator of progress messages
        """
        try:
            for progress in ollama.pull(model_name, stream=True):
                if 'status' in progress:
                    yield progress['status']
        except Exception as e:
            yield f"Error pulling model: {e}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model.
        
        Returns:
            Model details
        """
        try:
            info = ollama.show(self.model)
            return {
                'model': self.model,
                'license': info.license,
                'modelfile': info.modelfile,
                'parameters': info.parameters,
                'template': info.template,
                'details': info.details
            }
        except Exception as e:
            return {'error': str(e)}
    
    def set_model(self, model: str):
        """Change model.
        
        Args:
            model: New model name
        """
        self.model = model
        self._ensure_model()


# Convenience functions
def quick_chat(prompt: str, model: str = 'gemma3:4b') -> str:
    """Quick single-turn chat.
    
    Args:
        prompt: User message
        model: Model to use
        
    Returns:
        Assistant response
    """
    engine = BissiEngine(model=model)
    return engine.chat([{'role': 'user', 'content': prompt}])


def summarize_text(text: str, 
                   max_length: int = 200,
                   model: str = 'gemma3:4b') -> str:
    """Summarize long text.
    
    Args:
        text: Text to summarize
        max_length: Maximum summary length
        model: Model to use
        
    Returns:
        Summary text
    """
    engine = BissiEngine(model=model)
    
    prompt = f"""Please summarize the following text in {max_length} characters or less:

{text[:4000]}  # Limit input

Summary:"""
    
    return engine.generate(prompt)


def answer_question(context: str, 
                  question: str,
                  model: str = 'gemma3:4b') -> str:
    """Answer question based on context.
    
    Args:
        context: Background information
        question: Question to answer
        model: Model to use
        
    Returns:
        Answer text
    """
    engine = BissiEngine(model=model)
    
    prompt = f"""Based on the following context, answer the question:

Context:
{context[:4000]}

Question: {question}

Answer:"""
    
    return engine.generate(prompt)
