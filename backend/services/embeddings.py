"""
Embedding Service for generating vector embeddings from text.

This service uses sentence-transformers to generate embeddings for queries and documents.
It includes batch processing for efficiency and caching for repeated queries.
"""

import logging
from typing import List, Optional
from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using sentence-transformers.
    
    Uses the all-mpnet-base-v2 model which produces 768-dimensional embeddings
    with strong performance on semantic similarity tasks.
    
    Features:
    - Query and document embedding generation
    - Batch processing for efficient embedding generation
    - LRU caching for repeated queries
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        cache_size: int = 128,
        batch_size: int = 32
    ):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the sentence-transformers model to use
            cache_size: Maximum number of cached embeddings (LRU cache)
            batch_size: Default batch size for batch processing
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self._model: Optional[SentenceTransformer] = None
        self._cache_size = cache_size
        
        logger.info(f"Initializing EmbeddingService with model: {model_name}")
    
    @property
    def model(self) -> SentenceTransformer:
        """
        Lazy load the sentence transformer model.
        
        This allows the service to be instantiated without immediately
        loading the model, which can be expensive.
        """
        if self._model is None:
            logger.info(f"Loading sentence-transformers model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        return self._model
    
    @lru_cache(maxsize=128)
    def _cached_embed_query(self, text: str) -> tuple:
        """
        Internal cached method for embedding a single query.
        
        Returns tuple instead of ndarray because tuples are hashable
        and can be cached by lru_cache.
        
        Args:
            text: Query text to embed
            
        Returns:
            Tuple representation of the embedding vector
        """
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        return tuple(embedding.tolist())
    
    def embed_query(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single query text.
        
        This method uses caching to avoid re-computing embeddings
        for repeated queries.
        
        Args:
            text: Query text to embed
            
        Returns:
            Numpy array of shape (embedding_dim,) containing the embedding
            
        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.embed_query("What certifications do I need?")
            >>> embedding.shape
            (768,)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to embed_query")
            # Return zero vector for empty text
            return np.zeros(768, dtype=np.float32)
        
        # Use cached method and convert back to numpy array
        cached_tuple = self._cached_embed_query(text.strip())
        return np.array(cached_tuple, dtype=np.float32)
    
    def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple documents.
        
        This method processes documents in batches for efficiency.
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of numpy arrays, each of shape (embedding_dim,)
            
        Example:
            >>> service = EmbeddingService()
            >>> docs = ["Document 1", "Document 2", "Document 3"]
            >>> embeddings = service.embed_documents(docs)
            >>> len(embeddings)
            3
            >>> embeddings[0].shape
            (768,)
        """
        if not texts:
            logger.warning("Empty list provided to embed_documents")
            return []
        
        # Filter out empty texts and track their indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text.strip())
                valid_indices.append(i)
        
        if not valid_texts:
            logger.warning("All texts were empty in embed_documents")
            # Return zero vectors for all texts
            return [np.zeros(768, dtype=np.float32) for _ in texts]
        
        logger.info(f"Embedding {len(valid_texts)} documents in batches of {self.batch_size}")
        
        # Generate embeddings using batch processing
        embeddings = self.model.encode(
            valid_texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(valid_texts) > 100,  # Show progress for large batches
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        
        # Create result list with zero vectors for empty texts
        result = []
        valid_idx = 0
        for i in range(len(texts)):
            if i in valid_indices:
                result.append(embeddings[valid_idx].astype(np.float32))
                valid_idx += 1
            else:
                result.append(np.zeros(768, dtype=np.float32))
        
        logger.info(f"Successfully generated {len(result)} embeddings")
        return result
    
    def embed_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts with custom batch size.
        
        This is an alias for embed_documents with explicit batch size control.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing (overrides default)
            
        Returns:
            List of numpy arrays, each of shape (embedding_dim,)
        """
        if batch_size is not None:
            original_batch_size = self.batch_size
            self.batch_size = batch_size
            try:
                return self.embed_documents(texts)
            finally:
                self.batch_size = original_batch_size
        else:
            return self.embed_documents(texts)
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this service.
        
        Returns:
            Embedding dimension (768 for all-mpnet-base-v2)
        """
        return self.model.get_sentence_embedding_dimension()
    
    def clear_cache(self) -> None:
        """
        Clear the embedding cache.
        
        Useful for freeing memory or when you want to ensure fresh embeddings.
        """
        self._cached_embed_query.cache_clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_info(self) -> dict:
        """
        Get information about the cache state.
        
        Returns:
            Dictionary with cache statistics (hits, misses, size, maxsize)
        """
        cache_info = self._cached_embed_query.cache_info()
        return {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "size": cache_info.currsize,
            "maxsize": cache_info.maxsize
        }


# Global singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get the global embedding service instance.
    
    This ensures only one model is loaded in memory.
    
    Returns:
        Global EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
