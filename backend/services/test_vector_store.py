"""
Unit tests for the vector store service.

Tests the FAISSVectorStore implementation including:
- Document addition
- Similarity search
- Metadata filtering
- Index persistence
"""

import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path

from services.vector_store import FAISSVectorStore
from models.internal import Document


@pytest.fixture
def vector_store():
    """Create a fresh vector store for each test."""
    store = FAISSVectorStore(embedding_dimension=768)
    store.initialize()
    return store


@pytest.fixture
def sample_documents():
    """Create sample documents with embeddings."""
    docs = []
    for i in range(5):
        # Create random embeddings
        embedding = np.random.randn(768).astype(np.float32)
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        
        doc = Document(
            id=f"doc_{i}",
            content=f"This is document {i} about export regulations",
            metadata={
                "source": "DGFT" if i < 3 else "FDA",
                "country": "India" if i % 2 == 0 else "USA",
                "category": "agriculture"
            },
            embedding=embedding.tolist()
        )
        docs.append(doc)
    
    return docs


def test_initialize(vector_store):
    """Test that vector store initializes correctly."""
    assert vector_store.index is not None
    assert vector_store.embedding_dimension == 768
    assert len(vector_store.documents) == 0


def test_add_documents(vector_store, sample_documents):
    """Test adding documents to the vector store."""
    vector_store.add_documents(sample_documents)
    
    assert len(vector_store.documents) == 5
    assert len(vector_store.document_ids) == 5
    assert vector_store.index.ntotal == 5


def test_add_documents_without_embeddings(vector_store):
    """Test that documents without embeddings are skipped."""
    docs = [
        Document(
            id="doc_no_embedding",
            content="Document without embedding",
            metadata={"source": "DGFT"}
        )
    ]
    
    vector_store.add_documents(docs)
    assert len(vector_store.documents) == 0


def test_search(vector_store, sample_documents):
    """Test similarity search."""
    vector_store.add_documents(sample_documents)
    
    # Use the first document's embedding as query
    query_embedding = np.array(sample_documents[0].embedding, dtype=np.float32)
    
    results = vector_store.search(query_embedding, top_k=3)
    
    assert len(results) <= 3
    assert all(doc.relevance_score is not None for doc in results)
    # First result should be the same document (highest similarity)
    assert results[0].id == "doc_0"


def test_search_with_filters(vector_store, sample_documents):
    """Test similarity search with metadata filters."""
    vector_store.add_documents(sample_documents)
    
    query_embedding = np.array(sample_documents[0].embedding, dtype=np.float32)
    
    # Search only for DGFT documents
    results = vector_store.search(
        query_embedding,
        top_k=5,
        filters={"source": "DGFT"}
    )
    
    assert len(results) <= 3  # Only 3 DGFT documents
    assert all(doc.metadata["source"] == "DGFT" for doc in results)


def test_search_by_metadata(vector_store, sample_documents):
    """Test metadata-only search."""
    vector_store.add_documents(sample_documents)
    
    results = vector_store.search_by_metadata({"source": "FDA"})
    
    assert len(results) == 2  # 2 FDA documents
    assert all(doc.metadata["source"] == "FDA" for doc in results)


def test_search_empty_store(vector_store):
    """Test search on empty vector store."""
    query_embedding = np.random.randn(768).astype(np.float32)
    results = vector_store.search(query_embedding, top_k=5)
    
    assert len(results) == 0


def test_rebuild_index(vector_store, sample_documents):
    """Test rebuilding the index."""
    vector_store.add_documents(sample_documents)
    
    original_count = len(vector_store.documents)
    
    vector_store.rebuild_index()
    
    assert len(vector_store.documents) == original_count
    assert vector_store.index.ntotal == original_count


def test_save_and_load(vector_store, sample_documents):
    """Test saving and loading the vector store."""
    vector_store.add_documents(sample_documents)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "test_index"
        
        # Save
        vector_store.save(str(save_path))
        
        # Create new store and load
        new_store = FAISSVectorStore(embedding_dimension=768)
        new_store.load(str(save_path))
        
        # Verify loaded data
        assert len(new_store.documents) == 5
        assert new_store.index.ntotal == 5
        assert new_store.embedding_dimension == 768
        
        # Test search on loaded store
        query_embedding = np.array(sample_documents[0].embedding, dtype=np.float32)
        results = new_store.search(query_embedding, top_k=3)
        assert len(results) > 0


def test_get_stats(vector_store, sample_documents):
    """Test getting vector store statistics."""
    vector_store.add_documents(sample_documents)
    
    stats = vector_store.get_stats()
    
    assert stats["total_documents"] == 5
    assert stats["embedding_dimension"] == 768
    assert stats["index_type"] == "Flat"
    assert stats["index_size"] == 5
    assert stats["s3_enabled"] is False


def test_invalid_embedding_dimension(vector_store):
    """Test that documents with invalid embedding dimensions are rejected."""
    doc = Document(
        id="doc_invalid",
        content="Document with wrong dimension",
        metadata={"source": "DGFT"},
        embedding=np.random.randn(384).tolist()  # Wrong dimension
    )
    
    vector_store.add_documents([doc])
    assert len(vector_store.documents) == 0


def test_search_with_invalid_query_dimension(vector_store, sample_documents):
    """Test that search with invalid query dimension raises error."""
    vector_store.add_documents(sample_documents)
    
    query_embedding = np.random.randn(384).astype(np.float32)  # Wrong dimension
    
    with pytest.raises(ValueError):
        vector_store.search(query_embedding, top_k=3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
