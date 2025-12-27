"""Embedding service for generating vector embeddings."""
from typing import List, Optional
import numpy as np
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class EmbeddingService:
    """Service for generating embeddings using OpenAI API."""
    
    def __init__(self):
        self.client = None
        self.model = settings.embedding_model
        self._current_api_key = None
        self._current_base_url = None
    
    def _ensure_client(self):
        """Ensure OpenAI client is initialized and up-to-date."""
        # Update model from settings
        self.model = settings.embedding_model
        
        # Reinitialize if settings have changed
        if (settings.openai_api_key and 
            (self._current_api_key != settings.openai_api_key or 
             self._current_base_url != settings.openai_base_url)):
            self.client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
            self._current_api_key = settings.openai_api_key
            self._current_base_url = settings.openai_base_url
        
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please configure API key.")
    
    def update_config(self, api_key: str = None, base_url: str = None, model: str = None):
        """Update embedding configuration."""
        if api_key:
            settings.openai_api_key = api_key
        if base_url:
            settings.openai_base_url = base_url
        if model:
            settings.embedding_model = model
            self.model = model
        # Force reinitialization on next use
        self._current_api_key = None
        self._current_base_url = None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        self._ensure_client()
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def embed_texts(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to embed in one API call
            
        Returns:
            List of embedding vectors
        """
        self._ensure_client()
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def embed_texts_as_numpy(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings and return as numpy array.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array of shape (n_texts, embedding_dim)
        """
        embeddings = self.embed_texts(texts)
        return np.array(embeddings, dtype=np.float32)


# Singleton instance
embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """Get the embedding service instance."""
    return embedding_service
