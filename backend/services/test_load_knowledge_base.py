"""
Unit tests for knowledge base document loader.

Tests the complete pipeline for loading documents from S3 (or local),
generating embeddings, and building FAISS index.

Requirements: 9.1, 9.2, 9.7
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from models.internal import Document
from services.load_knowledge_base import KnowledgeBaseLoader


class TestKnowledgeBaseLoader:
    """Test suite for KnowledgeBaseLoader."""
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            {
                "key": "dgft_export_policy.json",
                "content": json.dumps({
                    "content": "DGFT export policy for agricultural products...",
                    "metadata": {
                        "source": "DGFT",
                        "country": "IN",
                        "product_category": "agriculture",
                        "certifications": "APEDA,FSSAI"
                    }
                }),
                "metadata": {}
            },
            {
                "key": "fda_requirements.txt",
                "content": "FDA requirements for food exports to US...",
                "metadata": {
                    "source": "FDA",
                    "country": "US",
                    "product_category": "food"
                }
            }
        ]
    
    @pytest.fixture
    def mock_s3_client(self, sample_documents):
        """Mock S3 client for testing."""
        mock_client = Mock()
        
        # Mock list_objects_v2
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {
                        "Key": doc["key"],
                        "Size": len(doc["content"]),
                        "LastModified": datetime.now()
                    }
                    for doc in sample_documents
                ]
            }
        ]
        mock_client.get_paginator.return_value = mock_paginator
        
        # Mock get_object
        def mock_get_object(Bucket, Key):
            for doc in sample_documents:
                if doc["key"] == Key:
                    return {
                        "Body": Mock(read=lambda: doc["content"].encode('utf-8'))
                    }
            raise Exception(f"Key not found: {Key}")
        
        mock_client.get_object.side_effect = mock_get_object
        
        # Mock head_object
        def mock_head_object(Bucket, Key):
            for doc in sample_documents:
                if doc["key"] == Key:
                    return {"Metadata": doc["metadata"]}
            raise Exception(f"Key not found: {Key}")
        
        mock_client.head_object.side_effect = mock_head_object
        
        # Mock get_object_tagging
        mock_client.get_object_tagging.return_value = {"TagSet": []}
        
        return mock_client
    
    def test_initialization(self):
        """Test KnowledgeBaseLoader initialization."""
        with patch('services.load_knowledge_base.boto3.client'):
            loader = KnowledgeBaseLoader(
                s3_bucket="test-bucket",
                s3_prefix="docs/",
                embedding_dimension=768,
                batch_size=32
            )
            
            assert loader.s3_bucket == "test-bucket"
            assert loader.s3_prefix == "docs/"
            assert loader.embedding_dimension == 768
            assert loader.batch_size == 32
    
    def test_list_documents(self, mock_s3_client):
        """Test listing documents from S3."""
        with patch('services.load_knowledge_base.boto3.client', return_value=mock_s3_client):
            loader = KnowledgeBaseLoader(s3_bucket="test-bucket")
            documents = loader.list_documents()
            
            assert len(documents) == 2
            assert documents[0]["key"] == "dgft_export_policy.json"
            assert documents[1]["key"] == "fda_requirements.txt"
    
    def test_parse_json_document(self, mock_s3_client):
        """Test parsing JSON document with metadata."""
        with patch('services.load_knowledge_base.boto3.client', return_value=mock_s3_client):
            loader = KnowledgeBaseLoader(s3_bucket="test-bucket")
            
            content = json.dumps({
                "content": "Test content",
                "metadata": {
                    "source": "DGFT",
                    "country": "IN"
                }
            }).encode('utf-8')
            
            doc = loader.parse_document(
                "test.json",
                content,
                {"extra": "metadata"}
            )
            
            assert doc is not None
            assert doc.content == "Test content"
            assert doc.metadata["source"] == "DGFT"
            assert doc.metadata["country"] == "IN"
            assert doc.metadata["extra"] == "metadata"  # S3 metadata merged
    
    def test_parse_text_document(self, mock_s3_client):
        """Test parsing plain text document."""
        with patch('services.load_knowledge_base.boto3.client', return_value=mock_s3_client):
            loader = KnowledgeBaseLoader(s3_bucket="test-bucket")
            
            content = b"Plain text content"
            metadata = {
                "source": "FDA",
                "country": "US"
            }
            
            doc = loader.parse_document("test.txt", content, metadata)
            
            assert doc is not None
            assert doc.content == "Plain text content"
            assert doc.metadata["source"] == "FDA"
            assert doc.metadata["country"] == "US"
    
    def test_parse_document_with_certifications(self, mock_s3_client):
        """Test parsing certifications from comma-separated string."""
        with patch('services.load_knowledge_base.boto3.client', return_value=mock_s3_client):
            loader = KnowledgeBaseLoader(s3_bucket="test-bucket")
            
            content = json.dumps({
                "content": "Test content",
                "metadata": {
                    "certifications": "FDA,CE,REACH"
                }
            }).encode('utf-8')
            
            doc = loader.parse_document("test.json", content, {})
            
            assert doc is not None
            assert isinstance(doc.metadata["certifications"], list)
            assert doc.metadata["certifications"] == ["FDA", "CE", "REACH"]
    
    def test_parse_empty_document(self, mock_s3_client):
        """Test that empty documents are rejected."""
        with patch('services.load_knowledge_base.boto3.client', return_value=mock_s3_client):
            loader = KnowledgeBaseLoader(s3_bucket="test-bucket")
            
            content = json.dumps({
                "content": "",
                "metadata": {}
            }).encode('utf-8')
            
            doc = loader.parse_document("test.json", content, {})
            
            assert doc is None
    
    def test_parse_unsupported_file_type(self, mock_s3_client):
        """Test that unsupported file types are rejected."""
        with patch('services.load_knowledge_base.boto3.client', return_value=mock_s3_client):
            loader = KnowledgeBaseLoader(s3_bucket="test-bucket")
            
            content = b"PDF content"
            
            doc = loader.parse_document("test.pdf", content, {})
            
            assert doc is None
    
    def test_metadata_defaults(self, mock_s3_client):
        """Test that default metadata values are set."""
        with patch('services.load_knowledge_base.boto3.client', return_value=mock_s3_client):
            loader = KnowledgeBaseLoader(s3_bucket="test-bucket")
            
            content = b"Test content"
            
            doc = loader.parse_document("test.txt", content, {})
            
            assert doc is not None
            assert doc.metadata["source"] == "unknown"
            assert doc.metadata["country"] == "unknown"
            assert doc.metadata["product_category"] == "general"
            assert "last_updated" in doc.metadata
            assert "s3_key" in doc.metadata
    
    @patch('services.load_knowledge_base.get_embedding_service')
    def test_generate_embeddings(self, mock_get_embedding_service, mock_s3_client):
        """Test embedding generation for documents."""
        import numpy as np
        
        # Mock embedding service
        mock_embedding_service = Mock()
        mock_embedding_service.embed_documents.return_value = [
            np.array([0.1] * 768, dtype=np.float32),
            np.array([0.2] * 768, dtype=np.float32)
        ]
        mock_get_embedding_service.return_value = mock_embedding_service
        
        with patch('services.load_knowledge_base.boto3.client', return_value=mock_s3_client):
            loader = KnowledgeBaseLoader(s3_bucket="test-bucket")
            
            documents = [
                Document(id="doc1", content="Content 1", metadata={}, embedding=None),
                Document(id="doc2", content="Content 2", metadata={}, embedding=None)
            ]
            
            result = loader.generate_embeddings(documents)
            
            assert len(result) == 2
            assert result[0].embedding is not None
            assert len(result[0].embedding) == 768
            assert result[1].embedding is not None
            assert len(result[1].embedding) == 768
    
    @patch('services.load_knowledge_base.FAISSVectorStore')
    @patch('services.load_knowledge_base.get_embedding_service')
    def test_build_index(self, mock_get_embedding_service, mock_vector_store_class, mock_s3_client):
        """Test building FAISS index."""
        # Mock vector store
        mock_vector_store = Mock()
        mock_vector_store.get_stats.return_value = {
            "total_documents": 2,
            "embedding_dimension": 768
        }
        mock_vector_store_class.return_value = mock_vector_store
        
        with patch('services.load_knowledge_base.boto3.client', return_value=mock_s3_client):
            loader = KnowledgeBaseLoader(s3_bucket="test-bucket")
            
            documents = [
                Document(id="doc1", content="Content 1", metadata={}, embedding=[0.1] * 768),
                Document(id="doc2", content="Content 2", metadata={}, embedding=[0.2] * 768)
            ]
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = str(Path(temp_dir) / "test_index")
                loader.build_index(documents, output_path)
                
                # Verify vector store was initialized and used
                mock_vector_store.initialize.assert_called_once()
                mock_vector_store.add_documents.assert_called_once_with(documents)
                mock_vector_store.save.assert_called_once_with(output_path)
    
    @patch('services.load_knowledge_base.FAISSVectorStore')
    @patch('services.load_knowledge_base.get_embedding_service')
    def test_complete_pipeline(self, mock_get_embedding_service, mock_vector_store_class, mock_s3_client):
        """Test the complete knowledge base loading pipeline."""
        import numpy as np
        
        # Mock embedding service
        mock_embedding_service = Mock()
        mock_embedding_service.embed_documents.return_value = [
            np.array([0.1] * 768, dtype=np.float32),
            np.array([0.2] * 768, dtype=np.float32)
        ]
        mock_get_embedding_service.return_value = mock_embedding_service
        
        # Mock vector store
        mock_vector_store = Mock()
        mock_vector_store.get_stats.return_value = {
            "total_documents": 2,
            "embedding_dimension": 768
        }
        mock_vector_store_class.return_value = mock_vector_store
        
        with patch('services.load_knowledge_base.boto3.client', return_value=mock_s3_client):
            loader = KnowledgeBaseLoader(s3_bucket="test-bucket")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = str(Path(temp_dir) / "test_index")
                loader.run(output_path)
                
                # Verify all steps were executed
                mock_embedding_service.embed_documents.assert_called_once()
                mock_vector_store.initialize.assert_called_once()
                mock_vector_store.add_documents.assert_called_once()
                mock_vector_store.save.assert_called_once()


class TestKnowledgeBaseLoaderIntegration:
    """Integration tests using real services (no mocks)."""
    
    def test_load_and_search_documents(self):
        """Test loading documents and performing semantic search."""
        from services.embeddings import get_embedding_service
        from services.vector_store import FAISSVectorStore
        
        # Create sample documents
        documents = [
            Document(
                id="doc1",
                content="FDA requirements for food exports to United States",
                metadata={
                    "source": "FDA",
                    "country": "US",
                    "product_category": "food"
                },
                embedding=None
            ),
            Document(
                id="doc2",
                content="DGFT export policy for agricultural products from India",
                metadata={
                    "source": "DGFT",
                    "country": "IN",
                    "product_category": "agriculture"
                },
                embedding=None
            )
        ]
        
        # Generate embeddings
        embedding_service = get_embedding_service()
        texts = [doc.content for doc in documents]
        embeddings = embedding_service.embed_documents(texts)
        
        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding.tolist()
        
        # Build index
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "test_index")
            
            vector_store = FAISSVectorStore(embedding_dimension=768)
            vector_store.initialize()
            vector_store.add_documents(documents)
            vector_store.save(output_path)
            
            # Test search
            query = "What are FDA food export requirements?"
            query_embedding = embedding_service.embed_query(query)
            results = vector_store.search(query_embedding, top_k=2)
            
            assert len(results) > 0
            assert results[0].id == "doc1"  # FDA document should be most relevant
            assert results[0].relevance_score > 0.5
    
    def test_metadata_filtering(self):
        """Test metadata filtering in search."""
        from services.embeddings import get_embedding_service
        from services.vector_store import FAISSVectorStore
        
        # Create sample documents with different sources
        documents = [
            Document(
                id="dgft1",
                content="DGFT export regulations",
                metadata={"source": "DGFT", "country": "IN"},
                embedding=None
            ),
            Document(
                id="fda1",
                content="FDA import regulations",
                metadata={"source": "FDA", "country": "US"},
                embedding=None
            ),
            Document(
                id="dgft2",
                content="DGFT certification requirements",
                metadata={"source": "DGFT", "country": "IN"},
                embedding=None
            )
        ]
        
        # Generate embeddings
        embedding_service = get_embedding_service()
        texts = [doc.content for doc in documents]
        embeddings = embedding_service.embed_documents(texts)
        
        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding.tolist()
        
        # Build index
        vector_store = FAISSVectorStore(embedding_dimension=768)
        vector_store.initialize()
        vector_store.add_documents(documents)
        
        # Test search with filter
        query_embedding = embedding_service.embed_query("export regulations")
        results = vector_store.search(
            query_embedding,
            top_k=5,
            filters={"source": "DGFT"}
        )
        
        assert len(results) == 2
        assert all(doc.metadata["source"] == "DGFT" for doc in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
