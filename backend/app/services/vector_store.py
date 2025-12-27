"""FAISS-based vector store for semantic search."""
import os
import json
import pickle
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
import faiss

from app.config import settings
from app.models.document import DocumentChunk, RetrievedContext
from app.services.embedding_service import get_embedding_service


class VectorStore:
    """FAISS-based vector store for document chunks."""
    
    def __init__(self, store_path: str = None):
        self.store_path = store_path or settings.vector_store_path
        self.embedding_service = get_embedding_service()
        
        # FAISS index
        self.index: Optional[faiss.IndexFlatIP] = None
        self.dimension: int = 1536  # OpenAI ada-002 dimension
        
        # Metadata storage
        self.chunk_metadata: Dict[int, Dict] = {}  # faiss_id -> metadata
        self.chunk_contents: Dict[int, str] = {}   # faiss_id -> content
        self.document_chunks: Dict[str, List[int]] = {}  # doc_id -> [faiss_ids]
        
        # Ensure store directory exists
        Path(self.store_path).mkdir(parents=True, exist_ok=True)
        
        # Try to load existing index
        self._load_index()
    
    def _load_index(self):
        """Load existing index from disk if available."""
        index_path = os.path.join(self.store_path, "faiss.index")
        metadata_path = os.path.join(self.store_path, "metadata.pkl")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            self.index = faiss.read_index(index_path)
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.chunk_metadata = data.get('metadata', {})
                self.chunk_contents = data.get('contents', {})
                self.document_chunks = data.get('doc_chunks', {})
        else:
            # Create new index with inner product (for cosine similarity with normalized vectors)
            self.index = faiss.IndexFlatIP(self.dimension)
    
    def _save_index(self):
        """Save index and metadata to disk."""
        index_path = os.path.join(self.store_path, "faiss.index")
        metadata_path = os.path.join(self.store_path, "metadata.pkl")
        
        faiss.write_index(self.index, index_path)
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'metadata': self.chunk_metadata,
                'contents': self.chunk_contents,
                'doc_chunks': self.document_chunks
            }, f)
    
    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of DocumentChunk objects
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        # Get embeddings for all chunks
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.embed_texts_as_numpy(texts)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Get current index size (will be the starting ID for new chunks)
        start_id = self.index.ntotal
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Store metadata
        for i, chunk in enumerate(chunks):
            faiss_id = start_id + i
            self.chunk_metadata[faiss_id] = {
                'chunk_id': chunk.id,
                'document_id': chunk.document_id,
                'chunk_index': chunk.chunk_index,
                'metadata': chunk.metadata
            }
            self.chunk_contents[faiss_id] = chunk.content
            
            # Track chunks by document
            if chunk.document_id not in self.document_chunks:
                self.document_chunks[chunk.document_id] = []
            self.document_chunks[chunk.document_id].append(faiss_id)
        
        # Save to disk
        self._save_index()
        
        return len(chunks)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None
    ) -> List[RetrievedContext]:
        """
        Search for similar chunks.
        
        Args:
            query: Query text
            top_k: Number of results to return
            document_ids: Optional filter by document IDs
            
        Returns:
            List of RetrievedContext objects
        """
        if self.index.ntotal == 0:
            return []
        
        # Get query embedding
        query_embedding = self.embedding_service.embed_texts_as_numpy([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        # If filtering by documents, we need to search more and filter
        search_k = top_k * 3 if document_ids else top_k
        scores, indices = self.index.search(query_embedding, min(search_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            metadata = self.chunk_metadata.get(idx, {})
            
            # Filter by document IDs if specified
            if document_ids and metadata.get('document_id') not in document_ids:
                continue
            
            results.append(RetrievedContext(
                chunk_id=metadata.get('chunk_id', ''),
                document_id=metadata.get('document_id', ''),
                content=self.chunk_contents.get(idx, ''),
                score=float(score),
                metadata=metadata.get('metadata', {})
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a document.
        
        Note: FAISS doesn't support deletion well, so we rebuild the index.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            Number of chunks deleted
        """
        if document_id not in self.document_chunks:
            return 0
        
        faiss_ids_to_delete = set(self.document_chunks[document_id])
        deleted_count = len(faiss_ids_to_delete)
        
        # Collect remaining data
        remaining_embeddings = []
        new_metadata = {}
        new_contents = {}
        new_doc_chunks = {}
        
        for old_id in range(self.index.ntotal):
            if old_id in faiss_ids_to_delete:
                continue
            
            # Get the embedding
            embedding = self.index.reconstruct(old_id)
            remaining_embeddings.append(embedding)
            
            new_id = len(remaining_embeddings) - 1
            new_metadata[new_id] = self.chunk_metadata[old_id]
            new_contents[new_id] = self.chunk_contents[old_id]
            
            doc_id = self.chunk_metadata[old_id]['document_id']
            if doc_id not in new_doc_chunks:
                new_doc_chunks[doc_id] = []
            new_doc_chunks[doc_id].append(new_id)
        
        # Rebuild index
        self.index = faiss.IndexFlatIP(self.dimension)
        if remaining_embeddings:
            embeddings_array = np.array(remaining_embeddings, dtype=np.float32)
            self.index.add(embeddings_array)
        
        self.chunk_metadata = new_metadata
        self.chunk_contents = new_contents
        self.document_chunks = new_doc_chunks
        
        # Save
        self._save_index()
        
        return deleted_count
    
    def clear(self):
        """Clear all data from the vector store."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunk_metadata = {}
        self.chunk_contents = {}
        self.document_chunks = {}
        self._save_index()
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store."""
        return {
            "total_chunks": self.index.ntotal,
            "total_documents": len(self.document_chunks),
            "dimension": self.dimension
        }


# Singleton instance
vector_store = VectorStore()


def get_vector_store() -> VectorStore:
    """Get the vector store instance."""
    return vector_store
