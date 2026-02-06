"""
Unit tests for RAG Pipeline Service.

Tests cover:
- Document retrieval with semantic search
- Document ranking by relevance
- Government source prioritization
- Context injection for LLM prompts
- Source citation extraction
"""

import pytest
import numpy as np
from typing import List
from unittest.mock import Mock, MagicMock, patch

from models.internal import Document
from services.rag_pipeline import RAGPipeline, get_rag_pipeline
from services.embeddings import EmbeddingService
from services.vector_store import VectorStore


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    service = Mock(spec=EmbeddingService)
    
    # Mock embed_query to return a fixed embedding
    service.embed_query.return_value = np.array([0.1] * 768, dtype=np.float32)
    
    # Mock embed_documents to return embeddings for multiple texts
    def mock_embed_documents(texts):
        return [np.array([0.1] * 768, dtype=np.float32) for _ in texts]
    
    service.embed_documents.side_effect = mock_embed_documents
    
    # Mock cache info
    service.get_cache_info.return_value = {
        'hits': 10,
        'misses': 5,
        'size': 5,
        'maxsize': 128
    }
    
    return service


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = Mock()
    
    # Mock search to return sample documents
    def mock_search(query_embedding, top_k, filters=None):
        # Create sample documents with different sources and scores
        docs = [
            Document(
                id="doc_dgft_001",
                content="DGFT regulations for agricultural exports...",
                metadata={
                    "source": "DGFT",
                    "country": "India",
                    "product_category": "agriculture"
                },
                embedding=[0.1] * 768,
                relevance_score=0.95
            ),
            Document(
                id="doc_fda_001",
                content="FDA requirements for food exports to US...",
                metadata={
                    "source": "FDA",
                    "country": "US",
                    "product_category": "food"
                },
                embedding=[0.1] * 768,
                relevance_score=0.85
            ),
            Document(
                id="doc_blog_001",
                content="Blog post about export tips...",
                metadata={
                    "source": "Blog",
                    "country": "India",
                    "product_category": "general"
                },
                embedding=[0.1] * 768,
                relevance_score=0.75
            ),
            Document(
                id="doc_customs_001",
                content="Customs RMS rules for shipment inspection...",
                metadata={
                    "source": "Customs_RMS",
                    "country": "India",
                    "product_category": "general"
                },
                embedding=[0.1] * 768,
                relevance_score=0.70
            ),
            Document(
                id="doc_low_score",
                content="Low relevance document...",
                metadata={
                    "source": "Unknown",
                    "country": "India",
                    "product_category": "general"
                },
                embedding=[0.1] * 768,
                relevance_score=0.25
            )
        ]
        
        # Apply filters if provided
        if filters:
            filtered_docs = []
            for doc in docs:
                matches = True
                for key, value in filters.items():
                    if doc.metadata.get(key) != value:
                        matches = False
                        break
                if matches:
                    filtered_docs.append(doc)
            docs = filtered_docs
        
        # Return top_k documents
        return docs[:top_k]
    
    store.search.side_effect = mock_search
    
    # Mock get_stats
    store.get_stats.return_value = {
        'total_documents': 100,
        'embedding_dimension': 768,
        'index_type': 'Flat'
    }
    
    return store


@pytest.fixture
def rag_pipeline(mock_embedding_service, mock_vector_store):
    """Create a RAG pipeline with mocked services."""
    return RAGPipeline(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        default_top_k=5,
        relevance_threshold=0.3,
        government_source_boost=0.1
    )


class TestRAGPipelineInitialization:
    """Test RAG pipeline initialization."""
    
    def test_initialization_with_defaults(self, mock_embedding_service, mock_vector_store):
        """Test pipeline initializes with default parameters."""
        pipeline = RAGPipeline(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store
        )
        
        assert pipeline.default_top_k == 5
        assert pipeline.relevance_threshold == 0.3
        assert pipeline.government_source_boost == 0.1
        assert 'DGFT' in pipeline.government_sources
        assert 'FDA' in pipeline.government_sources
    
    def test_initialization_with_custom_params(self, mock_embedding_service, mock_vector_store):
        """Test pipeline initializes with custom parameters."""
        pipeline = RAGPipeline(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            default_top_k=10,
            relevance_threshold=0.5,
            government_source_boost=0.2
        )
        
        assert pipeline.default_top_k == 10
        assert pipeline.relevance_threshold == 0.5
        assert pipeline.government_source_boost == 0.2


class TestDocumentRetrieval:
    """Test document retrieval functionality."""
    
    def test_retrieve_documents_basic(self, rag_pipeline, mock_embedding_service, mock_vector_store):
        """Test basic document retrieval."""
        query = "What are FDA requirements for food exports?"
        
        docs = rag_pipeline.retrieve_documents(query, top_k=3)
        
        # Verify embedding service was called
        mock_embedding_service.embed_query.assert_called_once_with(query)
        
        # Verify vector store was called
        assert mock_vector_store.search.called
        
        # Verify results
        assert len(docs) <= 3
        assert all(isinstance(doc, Document) for doc in docs)
        assert all(doc.relevance_score >= rag_pipeline.relevance_threshold for doc in docs)
    
    def test_retrieve_documents_with_filters(self, rag_pipeline, mock_vector_store):
        """Test document retrieval with metadata filters."""
        query = "Export regulations"
        filters = {"country": "India"}
        
        docs = rag_pipeline.retrieve_documents(query, top_k=5, filters=filters)
        
        # Verify vector store was called with filters
        call_args = mock_vector_store.search.call_args
        assert call_args[1]['filters'] == filters
        
        # Verify all returned documents match filters
        for doc in docs:
            assert doc.metadata.get('country') == 'India'
    
    def test_retrieve_documents_empty_query(self, rag_pipeline):
        """Test retrieval with empty query returns empty list."""
        docs = rag_pipeline.retrieve_documents("")
        assert docs == []
        
        docs = rag_pipeline.retrieve_documents("   ")
        assert docs == []
    
    def test_retrieve_documents_filters_by_threshold(self, rag_pipeline):
        """Test that documents below relevance threshold are filtered out."""
        query = "Test query"
        
        docs = rag_pipeline.retrieve_documents(query, top_k=10)
        
        # All returned documents should be above threshold (0.3)
        assert all(doc.relevance_score >= 0.3 for doc in docs)
        
        # Low score document (0.25) should not be included
        assert not any(doc.id == "doc_low_score" for doc in docs)


class TestDocumentRanking:
    """Test document ranking functionality."""
    
    def test_rank_documents_by_score(self, rag_pipeline):
        """Test documents are ranked by relevance score."""
        docs = [
            Document(id="doc1", content="Content 1", metadata={}, relevance_score=0.5),
            Document(id="doc2", content="Content 2", metadata={}, relevance_score=0.9),
            Document(id="doc3", content="Content 3", metadata={}, relevance_score=0.7)
        ]
        
        ranked = rag_pipeline._rank_documents(docs, prioritize_government=False)
        
        # Should be sorted by score descending
        assert ranked[0].id == "doc2"  # 0.9
        assert ranked[1].id == "doc3"  # 0.7
        assert ranked[2].id == "doc1"  # 0.5
    
    def test_government_source_boost(self, rag_pipeline):
        """Test government sources receive score boost."""
        docs = [
            Document(
                id="doc_blog",
                content="Blog content",
                metadata={"source": "Blog"},
                relevance_score=0.8
            ),
            Document(
                id="doc_dgft",
                content="DGFT content",
                metadata={"source": "DGFT"},
                relevance_score=0.75
            )
        ]
        
        ranked = rag_pipeline._rank_documents(docs, prioritize_government=True)
        
        # DGFT should be boosted from 0.75 to 0.85 (0.75 + 0.1)
        # and should now rank higher than blog (0.8)
        assert ranked[0].id == "doc_dgft"
        assert ranked[0].relevance_score == 0.85
        assert ranked[1].id == "doc_blog"
        assert ranked[1].relevance_score == 0.8
    
    def test_government_source_boost_capped_at_one(self, rag_pipeline):
        """Test government source boost doesn't exceed 1.0."""
        docs = [
            Document(
                id="doc_fda",
                content="FDA content",
                metadata={"source": "FDA"},
                relevance_score=0.95
            )
        ]
        
        ranked = rag_pipeline._rank_documents(docs, prioritize_government=True)
        
        # Score should be capped at 1.0 (not 1.05)
        assert ranked[0].relevance_score == 1.0
    
    def test_rank_documents_without_government_boost(self, rag_pipeline):
        """Test ranking without government source boost."""
        docs = [
            Document(
                id="doc_blog",
                content="Blog content",
                metadata={"source": "Blog"},
                relevance_score=0.8
            ),
            Document(
                id="doc_dgft",
                content="DGFT content",
                metadata={"source": "DGFT"},
                relevance_score=0.75
            )
        ]
        
        ranked = rag_pipeline._rank_documents(docs, prioritize_government=False)
        
        # Without boost, blog should rank higher
        assert ranked[0].id == "doc_blog"
        assert ranked[0].relevance_score == 0.8
        assert ranked[1].id == "doc_dgft"
        assert ranked[1].relevance_score == 0.75


class TestContextGeneration:
    """Test context generation for LLM prompts."""
    
    def test_generate_with_context_basic(self, rag_pipeline):
        """Test basic context generation."""
        prompt = "What are FDA requirements?"
        
        enhanced_prompt, sources = rag_pipeline.generate_with_context(prompt, top_k=3)
        
        # Verify enhanced prompt contains context
        assert "Context:" in enhanced_prompt
        assert "Question:" in enhanced_prompt
        assert prompt in enhanced_prompt
        
        # Verify sources are returned
        assert len(sources) > 0
        assert all(isinstance(doc, Document) for doc in sources)
    
    def test_generate_with_context_with_provided_documents(self, rag_pipeline):
        """Test context generation with pre-retrieved documents."""
        prompt = "What are the requirements?"
        docs = [
            Document(
                id="doc1",
                content="Requirement 1: You must register...",
                metadata={"source": "FDA"},
                relevance_score=0.9
            ),
            Document(
                id="doc2",
                content="Requirement 2: You must obtain certification...",
                metadata={"source": "DGFT"},
                relevance_score=0.8
            )
        ]
        
        enhanced_prompt, sources = rag_pipeline.generate_with_context(
            prompt,
            documents=docs
        )
        
        # Verify context includes document content
        assert "Requirement 1" in enhanced_prompt
        assert "Requirement 2" in enhanced_prompt
        
        # Verify sources match provided documents
        assert sources == docs
    
    def test_generate_with_context_includes_sources(self, rag_pipeline):
        """Test context includes source citations."""
        prompt = "What are the requirements?"
        docs = [
            Document(
                id="doc1",
                content="Content from FDA",
                metadata={"source": "FDA"},
                relevance_score=0.9
            )
        ]
        
        enhanced_prompt, _ = rag_pipeline.generate_with_context(
            prompt,
            documents=docs,
            include_sources=True
        )
        
        # Verify source citation is included
        assert "FDA" in enhanced_prompt
        assert "Document 1" in enhanced_prompt
    
    def test_generate_with_context_respects_max_length(self, rag_pipeline):
        """Test context respects maximum length."""
        prompt = "What are the requirements?"
        
        # Create documents with long content
        long_content = "A" * 2000
        docs = [
            Document(
                id=f"doc{i}",
                content=long_content,
                metadata={"source": "FDA"},
                relevance_score=0.9
            )
            for i in range(5)
        ]
        
        enhanced_prompt, _ = rag_pipeline.generate_with_context(
            prompt,
            documents=docs,
            max_context_length=1000
        )
        
        # Extract context section
        context_start = enhanced_prompt.find("Context:")
        context_end = enhanced_prompt.find("Question:")
        context = enhanced_prompt[context_start:context_end]
        
        # Context should be within max length
        assert len(context) <= 1000 + 200  # Allow some buffer for headers
    
    def test_generate_with_context_empty_prompt(self, rag_pipeline):
        """Test context generation with empty prompt."""
        enhanced_prompt, sources = rag_pipeline.generate_with_context("")
        
        assert enhanced_prompt == ""
        assert sources == []


class TestContextBuilding:
    """Test context building from documents."""
    
    def test_build_context_basic(self, rag_pipeline):
        """Test basic context building."""
        docs = [
            Document(
                id="doc1",
                content="Content 1",
                metadata={"source": "FDA"},
                relevance_score=0.9
            ),
            Document(
                id="doc2",
                content="Content 2",
                metadata={"source": "DGFT"},
                relevance_score=0.8
            )
        ]
        
        context = rag_pipeline._build_context(docs, include_sources=True)
        
        # Verify both documents are included
        assert "Content 1" in context
        assert "Content 2" in context
        assert "FDA" in context
        assert "DGFT" in context
    
    def test_build_context_without_sources(self, rag_pipeline):
        """Test context building without source citations."""
        docs = [
            Document(
                id="doc1",
                content="Content 1",
                metadata={"source": "FDA"},
                relevance_score=0.9
            )
        ]
        
        context = rag_pipeline._build_context(docs, include_sources=False)
        
        # Content should be included but not source
        assert "Content 1" in context
        assert "FDA" not in context
    
    def test_build_context_truncates_long_content(self, rag_pipeline):
        """Test context truncates content to fit max length."""
        long_content = "A" * 5000
        docs = [
            Document(
                id="doc1",
                content=long_content,
                metadata={"source": "FDA"},
                relevance_score=0.9
            )
        ]
        
        context = rag_pipeline._build_context(docs, max_length=1000)
        
        # Context should be truncated
        assert len(context) <= 1000
        assert "..." in context  # Truncation indicator


class TestSourceExtraction:
    """Test source citation extraction."""
    
    def test_extract_sources(self, rag_pipeline):
        """Test extracting source citations from documents."""
        docs = [
            Document(
                id="doc_fda_001",
                content="FDA requirements for food exports to US. This is a long document with detailed requirements...",
                metadata={
                    "source": "FDA",
                    "country": "US",
                    "product_category": "food",
                    "title": "FDA Food Export Requirements",
                    "url": "https://fda.gov/exports"
                },
                relevance_score=0.95
            ),
            Document(
                id="doc_dgft_001",
                content="DGFT regulations for agricultural exports...",
                metadata={
                    "source": "DGFT",
                    "country": "India",
                    "product_category": "agriculture"
                },
                relevance_score=0.85
            )
        ]
        
        sources = rag_pipeline.extract_sources(docs)
        
        # Verify source structure
        assert len(sources) == 2
        
        # Check first source
        assert sources[0]['id'] == "doc_fda_001"
        assert sources[0]['title'] == "FDA Food Export Requirements"
        assert sources[0]['source'] == "FDA"
        assert sources[0]['relevance_score'] == 0.95
        assert sources[0]['url'] == "https://fda.gov/exports"
        assert len(sources[0]['excerpt']) <= 203  # 200 + "..."
        
        # Check second source (no title or URL)
        assert sources[1]['id'] == "doc_dgft_001"
        assert sources[1]['title'] == "doc_dgft_001"  # Falls back to ID
        assert sources[1]['source'] == "DGFT"
        assert 'url' not in sources[1]


class TestPipelineStats:
    """Test pipeline statistics."""
    
    def test_get_stats(self, rag_pipeline):
        """Test getting pipeline statistics."""
        stats = rag_pipeline.get_stats()
        
        # Verify stats structure
        assert 'default_top_k' in stats
        assert 'relevance_threshold' in stats
        assert 'government_source_boost' in stats
        assert 'government_sources' in stats
        assert 'vector_store' in stats
        assert 'embedding_cache' in stats
        
        # Verify values
        assert stats['default_top_k'] == 5
        assert stats['relevance_threshold'] == 0.3
        assert stats['government_source_boost'] == 0.1
        assert 'DGFT' in stats['government_sources']


class TestGlobalInstance:
    """Test global pipeline instance."""
    
    def test_get_rag_pipeline_singleton(self):
        """Test get_rag_pipeline returns singleton instance."""
        with patch('services.rag_pipeline.get_embedding_service'), \
             patch('services.rag_pipeline.get_vector_store'):
            
            pipeline1 = get_rag_pipeline()
            pipeline2 = get_rag_pipeline()
            
            # Should return same instance
            assert pipeline1 is pipeline2


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_retrieve_documents_no_results(self, mock_embedding_service):
        """Test retrieval when no documents match."""
        # Create a new mock vector store that returns empty list
        empty_vector_store = Mock()
        empty_vector_store.search.return_value = []
        empty_vector_store.get_stats.return_value = {}
        
        # Create pipeline with empty vector store
        pipeline = RAGPipeline(
            embedding_service=mock_embedding_service,
            vector_store=empty_vector_store
        )
        
        docs = pipeline.retrieve_documents("query", top_k=5)
        
        assert docs == []
    
    def test_retrieve_documents_all_below_threshold(self, mock_embedding_service):
        """Test retrieval when all documents are below threshold."""
        # Create a mock vector store that returns low-score documents
        low_score_vector_store = Mock()
        low_score_docs = [
            Document(
                id=f"doc{i}",
                content=f"Content {i}",
                metadata={"source": "Test"},
                relevance_score=0.1
            )
            for i in range(5)
        ]
        low_score_vector_store.search.return_value = low_score_docs
        low_score_vector_store.get_stats.return_value = {}
        
        # Create pipeline with low-score vector store
        pipeline = RAGPipeline(
            embedding_service=mock_embedding_service,
            vector_store=low_score_vector_store
        )
        
        docs = pipeline.retrieve_documents("query", top_k=5)
        
        # All documents below threshold (0.3) should be filtered out
        assert docs == []
    
    def test_rank_documents_empty_list(self, rag_pipeline):
        """Test ranking empty document list."""
        ranked = rag_pipeline._rank_documents([])
        assert ranked == []
    
    def test_rank_documents_with_none_scores(self, rag_pipeline):
        """Test ranking documents with None relevance scores."""
        docs = [
            Document(id="doc1", content="Content 1", metadata={}, relevance_score=0.8),
            Document(id="doc2", content="Content 2", metadata={}, relevance_score=None),
            Document(id="doc3", content="Content 3", metadata={}, relevance_score=0.6)
        ]
        
        ranked = rag_pipeline._rank_documents(docs)
        
        # Documents with None scores should be ranked last (treated as 0.0)
        assert ranked[0].id == "doc1"
        assert ranked[1].id == "doc3"
        assert ranked[2].id == "doc2"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
