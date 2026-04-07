"""Vector store for BISSI RAG (Retrieval-Augmented Generation).

Provides document embedding and similarity search using ChromaDB.
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import hashlib


class VectorStore:
    """Document vector store for semantic search."""
    
    def __init__(self, 
                 persist_directory: Union[str, Path] = "~/.bissi/vector_store",
                 collection_name: str = "documents"):
        """Initialize vector store.
        
        Args:
            persist_directory: Where to store ChromaDB data
            collection_name: Name of the collection
        """
        self.persist_directory = Path(persist_directory).expanduser()
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_document(self, 
                     content: str,
                     document_id: Optional[str] = None,
                     metadata: Optional[Dict] = None,
                     source: Optional[str] = None) -> str:
        """Add document to vector store.
        
        Args:
            content: Document text content
            document_id: Unique ID (auto-generated if None)
            metadata: Additional metadata (title, author, etc.)
            source: Document source path or URL
            
        Returns:
            Document ID
        """
        # Generate ID from content hash if not provided
        if document_id is None:
            document_id = hashlib.md5(content.encode()).hexdigest()[:16]
        
        # Prepare metadata
        doc_metadata = metadata or {}
        if source:
            doc_metadata['source'] = source
        doc_metadata['char_count'] = len(content)
        
        # Add to collection (ChromaDB handles embedding)
        self.collection.add(
            documents=[content],
            ids=[document_id],
            metadatas=[doc_metadata]
        )
        
        return document_id
    
    def add_documents(self, 
                      documents: List[Dict[str, Any]]) -> List[str]:
        """Add multiple documents at once.
        
        Args:
            documents: List of dicts with 'content', 'id', 'metadata', 'source'
            
        Returns:
            List of document IDs
        """
        ids = []
        contents = []
        metadatas = []
        
        for doc in documents:
            content = doc['content']
            doc_id = doc.get('id') or hashlib.md5(content.encode()).hexdigest()[:16]
            
            metadata = doc.get('metadata', {})
            if doc.get('source'):
                metadata['source'] = doc['source']
            metadata['char_count'] = len(content)
            
            ids.append(doc_id)
            contents.append(content)
            metadatas.append(metadata)
        
        self.collection.add(
            documents=contents,
            ids=ids,
            metadatas=metadatas
        )
        
        return ids
    
    def query(self, 
              query_text: str,
              n_results: int = 5,
              filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar documents.
        
        Args:
            query_text: Search query
            n_results: Number of results to return
            filter_metadata: Optional filter on metadata
            
        Returns:
            List of matching documents with scores
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_metadata
        )
        
        # Format results
        matches = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                matches.append({
                    'id': doc_id,
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
        
        return matches
    
    def similarity_search(self, 
                          content: str,
                          threshold: float = 0.7,
                          n_results: int = 10) -> List[Dict[str, Any]]:
        """Find documents similar to provided content.
        
        Args:
            content: Content to find similar documents for
            threshold: Minimum similarity score (0-1)
            n_results: Maximum results to check
            
        Returns:
            Documents above threshold, sorted by similarity
        """
        all_results = self.query(content, n_results=n_results)
        
        # Filter by threshold (distance < 1-threshold, since lower is better)
        cutoff = 1 - threshold
        filtered = [r for r in all_results if r['distance'] < cutoff]
        
        return filtered
    
    def delete_document(self, document_id: str) -> bool:
        """Remove document from store.
        
        Args:
            document_id: Document to delete
            
        Returns:
            True if deleted
        """
        try:
            self.collection.delete(ids=[document_id])
            return True
        except Exception:
            return False
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get specific document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document data or None
        """
        try:
            result = self.collection.get(ids=[document_id])
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
        except Exception:
            pass
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics.
        
        Returns:
            Document count and collection info
        """
        count = self.collection.count()
        return {
            'documents': count,
            'collection': self.collection.name
        }
    
    def clear(self) -> None:
        """Remove all documents from collection."""
        self.collection.delete(where={})
    
    def index_file(self, 
                   file_path: Union[str, Path],
                   chunk_size: int = 1000,
                   overlap: int = 100) -> List[str]:
        """Index a file by splitting into chunks and adding to store.
        
        Args:
            file_path: Path to text file
            chunk_size: Characters per chunk
            overlap: Overlap between chunks
            
        Returns:
            List of chunk IDs
        """
        file_path = Path(file_path)
        
        # Read file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        # Split into chunks
        chunks = self._chunk_text(text, chunk_size, overlap)
        
        # Add chunks as documents
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{file_path.stem}_chunk_{i}"
            documents.append({
                'content': chunk,
                'id': doc_id,
                'metadata': {
                    'source': str(file_path),
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
            })
        
        return self.add_documents(documents)
    
    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence or word boundary
            if end < len(text):
                # Look for sentence break
                for char in ['. ', '! ', '? ', '\n']:
                    idx = chunk.rfind(char)
                    if idx > chunk_size * 0.5:  # Found reasonable break point
                        end = start + idx + len(char)
                        chunk = text[start:end]
                        break
                else:
                    # Break at word boundary
                    last_space = chunk.rfind(' ')
                    if last_space > 0:
                        end = start + last_space
                        chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
