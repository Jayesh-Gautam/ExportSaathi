"""
Unit tests for the EmbeddingService.

Tests cover:
- Query embedding generation
- Document batch embedding
- Caching mechanism
- Edge cases (empty strings, large batches)
"""

import pytest
import numpy as np
from embeddings import EmbeddingService, get_embedding_service


class TestEmbeddingService:
    """Test suite for EmbeddingService."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh embedding service for each test."""
        service = EmbeddingService()
        service.clear_cache()  # Ensure clean cache
        return service
    
    def test_embed_query_returns_correct_shape(self, service):
        """Test that embed_query returns the correct embedding dimension."""
        text = "What certifications do I need for exporting LED lights to USA?"
        embedding = service.embed_query(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)  # all-mpnet-base-v2 produces 768-dim embeddings
        assert embedding.dtype == np.float32
    
    def test_embed_query_produces_normalized_vectors(self, service):
        """Test that embeddings are normalized (for cosine similarity)."""
        text = "Export compliance requirements"
        embedding = service.embed_query(text)
        
        # Check that the vector is normalized (L2 norm ≈ 1)
        norm = np.linalg.norm(embedding)
        assert np.isclose(norm, 1.0, atol=1e-5)
    
    def test_embed_query_caching(self, service):
        """Test that repeated queries use the cache."""
        text = "HS code prediction"
        
        # First call - cache miss
        embedding1 = service.embed_query(text)
        cache_info1 = service.get_cache_info()
        
        # Second call - cache hit
        embedding2 = service.embed_query(text)
        cache_info2 = service.get_cache_info()
        
        # Embeddings should be identical
        np.testing.assert_array_equal(embedding1, embedding2)
        
        # Cache hits should increase
        assert cache_info2["hits"] > cache_info1["hits"]
    
    def test_embed_query_empty_string(self, service):
        """Test that empty strings return zero vectors."""
        embedding = service.embed_query("")
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)
        assert np.all(embedding == 0)
    
    def test_embed_query_whitespace_only(self, service):
        """Test that whitespace-only strings return zero vectors."""
        embedding = service.embed_query("   \n\t  ")
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)
        assert np.all(embedding == 0)
    
    def test_embed_documents_returns_correct_shape(self, service):
        """Test that embed_documents returns correct number and shape of embeddings."""
        texts = [
            "FDA certification requirements",
            "CE marking for electronics",
            "REACH compliance for chemicals"
        ]
        embeddings = service.embed_documents(texts)
        
        assert len(embeddings) == 3
        for embedding in embeddings:
            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (768,)
            assert embedding.dtype == np.float32
    
    def test_embed_documents_empty_list(self, service):
        """Test that empty list returns empty list."""
        embeddings = service.embed_documents([])
        assert embeddings == []
    
    def test_embed_documents_with_empty_strings(self, service):
        """Test that empty strings in list are handled correctly."""
        texts = [
            "Valid text",
            "",
            "Another valid text",
            "   ",  # Whitespace only
            "Final text"
        ]
        embeddings = service.embed_documents(texts)
        
        assert len(embeddings) == 5
        
        # Valid texts should have non-zero embeddings
        assert not np.all(embeddings[0] == 0)
        assert not np.all(embeddings[2] == 0)
        assert not np.all(embeddings[4] == 0)
        
        # Empty texts should have zero embeddings
        assert np.all(embeddings[1] == 0)
        assert np.all(embeddings[3] == 0)
    
    def test_embed_documents_batch_processing(self, service):
        """Test that batch processing works correctly with many documents."""
        # Create 100 documents to test batch processing
        texts = [f"Document number {i} about export compliance" for i in range(100)]
        embeddings = service.embed_documents(texts)
        
        assert len(embeddings) == 100
        for embedding in embeddings:
            assert embedding.shape == (768,)
            # Each document should have a unique embedding
            assert not np.all(embedding == 0)
    
    def test_embed_batch_custom_batch_size(self, service):
        """Test that custom batch size works correctly."""
        texts = [f"Text {i}" for i in range(10)]
        
        # Use custom batch size
        embeddings = service.embed_batch(texts, batch_size=2)
        
        assert len(embeddings) == 10
        for embedding in embeddings:
            assert embedding.shape == (768,)
    
    def test_embed_documents_produces_different_embeddings(self, service):
        """Test that different texts produce different embeddings."""
        texts = [
            "Export to United States",
            "Export to European Union",
            "Export to China"
        ]
        embeddings = service.embed_documents(texts)
        
        # Embeddings should be different
        assert not np.array_equal(embeddings[0], embeddings[1])
        assert not np.array_equal(embeddings[1], embeddings[2])
        assert not np.array_equal(embeddings[0], embeddings[2])
    
    def test_embed_documents_similar_texts_have_similar_embeddings(self, service):
        """Test that semantically similar texts have similar embeddings."""
        texts = [
            "FDA certification for food products",
            "Food and Drug Administration approval for food items",
            "Exporting electronics to Japan"
        ]
        embeddings = service.embed_documents(texts)
        
        # Calculate cosine similarity
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        # Similar texts (0 and 1) should have higher similarity
        sim_01 = cosine_similarity(embeddings[0], embeddings[1])
        sim_02 = cosine_similarity(embeddings[0], embeddings[2])
        
        assert sim_01 > sim_02  # Similar texts more similar than dissimilar
        assert sim_01 > 0.7  # High similarity for semantically similar texts
    
    def test_get_embedding_dimension(self, service):
        """Test that get_embedding_dimension returns correct value."""
        dim = service.get_embedding_dimension()
        assert dim == 768
    
    def test_clear_cache(self, service):
        """Test that cache clearing works."""
        # Generate some embeddings to populate cache
        service.embed_query("Test query 1")
        service.embed_query("Test query 2")
        
        cache_info_before = service.get_cache_info()
        assert cache_info_before["size"] > 0
        
        # Clear cache
        service.clear_cache()
        
        cache_info_after = service.get_cache_info()
        assert cache_info_after["size"] == 0
        assert cache_info_after["hits"] == 0
        assert cache_info_after["misses"] == 0
    
    def test_get_cache_info(self, service):
        """Test that cache info returns correct statistics."""
        service.clear_cache()
        
        # First query - cache miss
        service.embed_query("Query 1")
        info1 = service.get_cache_info()
        assert info1["misses"] == 1
        assert info1["hits"] == 0
        assert info1["size"] == 1
        
        # Repeat query - cache hit
        service.embed_query("Query 1")
        info2 = service.get_cache_info()
        assert info2["hits"] == 1
        assert info2["misses"] == 1
        assert info2["size"] == 1
        
        # New query - another cache miss
        service.embed_query("Query 2")
        info3 = service.get_cache_info()
        assert info3["misses"] == 2
        assert info3["hits"] == 1
        assert info3["size"] == 2
    
    def test_singleton_get_embedding_service(self):
        """Test that get_embedding_service returns the same instance."""
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        
        assert service1 is service2  # Same object instance
    
    def test_model_lazy_loading(self):
        """Test that model is loaded lazily."""
        service = EmbeddingService()
        
        # Model should not be loaded yet
        assert service._model is None
        
        # First embedding triggers model loading
        service.embed_query("Test")
        
        # Model should now be loaded
        assert service._model is not None
    
    def test_unicode_text_handling(self, service):
        """Test that service handles unicode text correctly."""
        texts = [
            "Export to भारत (India)",
            "中国出口 (China export)",
            "Exportação para o Brasil",
            "Экспорт в Россию"
        ]
        embeddings = service.embed_documents(texts)
        
        assert len(embeddings) == 4
        for embedding in embeddings:
            assert embedding.shape == (768,)
            assert not np.all(embedding == 0)
    
    def test_long_text_handling(self, service):
        """Test that service handles long texts correctly."""
        # Create a very long text (sentence-transformers has a max length)
        long_text = " ".join(["export compliance certification"] * 200)
        
        embedding = service.embed_query(long_text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)
        assert not np.all(embedding == 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
