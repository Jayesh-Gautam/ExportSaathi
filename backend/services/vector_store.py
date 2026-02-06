"""
Vector Store Service for semantic document search.

This service provides an abstract interface for vector stores and implements
FAISS-based vector storage with metadata filtering and S3 persistence.

Requirements: 9.2, 9.3, 9.4
"""

import logging
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
import faiss
import boto3

from models.internal import Document

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """
    Abstract interface for vector store implementations.
    
    Provides methods for adding documents, searching by embedding similarity,
    and searching by metadata filters.
    """
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents with embeddings to the vector store."""
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents using embedding similarity."""
        pass
    
    @abstractmethod
    def search_by_metadata(self, metadata_filters: Dict[str, Any]) -> List[Document]:
        """Search for documents matching metadata filters."""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the vector store."""
        pass
    
    @abstractmethod
    def rebuild_index(self) -> None:
        """Rebuild the vector store index from scratch."""
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """Save the vector store to disk or cloud storage."""
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        """Load the vector store from disk or cloud storage."""
        pass



class FAISSVectorStore(VectorStore):
    """
    FAISS-based vector store implementation.
    
    Features:
    - Fast similarity search using FAISS
    - Metadata filtering capabilities
    - Index persistence to local disk and S3
    - Support for cosine similarity (normalized vectors)
    
    Requirements: 9.2, 9.3, 9.4
    """
    
    def __init__(
        self,
        embedding_dimension: int = 768,
        index_type: str = "Flat",
        s3_bucket: Optional[str] = None,
        s3_prefix: str = "vector_store/"
    ):
        """Initialize FAISS vector store."""
        self.embedding_dimension = embedding_dimension
        self.index_type = index_type
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        
        # FAISS index for similarity search
        self.index: Optional[faiss.Index] = None
        
        # Store documents and metadata separately (FAISS only stores vectors)
        self.documents: List[Document] = []
        self.document_ids: List[str] = []
        
        # S3 client for persistence
        self.s3_client = None
        if s3_bucket:
            try:
                self.s3_client = boto3.client('s3')
                logger.info(f"S3 client initialized for bucket: {s3_bucket}")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
        
        logger.info(
            f"FAISSVectorStore initialized with dimension={embedding_dimension}, "
            f"index_type={index_type}"
        )
    
    def initialize(self) -> None:
        """Initialize the FAISS index."""
        if self.index_type == "Flat":
            # Flat index for exact search with inner product (cosine similarity for normalized vectors)
            self.index = faiss.IndexFlatIP(self.embedding_dimension)
            logger.info("Created FAISS IndexFlatIP for exact cosine similarity search")
        elif self.index_type == "IVF":
            # IVF index for approximate search (faster for large datasets)
            quantizer = faiss.IndexFlatIP(self.embedding_dimension)
            nlist = 100  # Number of clusters
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dimension, nlist)
            logger.info(f"Created FAISS IndexIVFFlat with {nlist} clusters")
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        
        logger.info("FAISS index initialized successfully")

    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents with embeddings to the vector store."""
        if not documents:
            logger.warning("No documents provided to add_documents")
            return
        
        if self.index is None:
            self.initialize()
        
        # Validate and extract embeddings
        embeddings = []
        valid_documents = []
        
        for doc in documents:
            if doc.embedding is None:
                logger.warning(f"Document {doc.id} has no embedding, skipping")
                continue
            
            embedding = np.array(doc.embedding, dtype=np.float32)
            
            if embedding.shape[0] != self.embedding_dimension:
                logger.warning(
                    f"Document {doc.id} has invalid embedding dimension "
                    f"{embedding.shape[0]}, expected {self.embedding_dimension}, skipping"
                )
                continue
            
            embeddings.append(embedding)
            valid_documents.append(doc)
        
        if not embeddings:
            logger.warning("No valid documents with embeddings to add")
            return
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_array)
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store documents and IDs
        self.documents.extend(valid_documents)
        self.document_ids.extend([doc.id for doc in valid_documents])
        
        logger.info(f"Added {len(valid_documents)} documents to vector store")
        logger.info(f"Total documents in store: {len(self.documents)}")

    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents using embedding similarity."""
        if self.index is None or len(self.documents) == 0:
            logger.warning("Vector store is empty or not initialized")
            return []
        
        # Validate query embedding
        if query_embedding.shape[0] != self.embedding_dimension:
            raise ValueError(
                f"Query embedding dimension {query_embedding.shape[0]} "
                f"does not match index dimension {self.embedding_dimension}"
            )
        
        # Normalize query embedding for cosine similarity
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search in FAISS index
        # For IVF index, we need to search more candidates if we have filters
        search_k = top_k * 10 if filters else top_k
        search_k = min(search_k, len(self.documents))
        
        distances, indices = self.index.search(query_embedding, search_k)
        
        # Convert results to Document objects with relevance scores
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            doc = self.documents[idx]
            
            # Apply metadata filters if provided
            if filters and not self._matches_filters(doc.metadata, filters):
                continue
            
            # Create a copy of the document with relevance score
            result_doc = doc.model_copy(deep=True)
            result_doc.relevance_score = float(distance)  # Inner product score (higher is better)
            results.append(result_doc)
            
            # Stop if we have enough results after filtering
            if len(results) >= top_k:
                break
        
        logger.info(f"Search returned {len(results)} documents")
        return results
    
    def search_by_metadata(self, metadata_filters: Dict[str, Any]) -> List[Document]:
        """Search for documents matching metadata filters."""
        if not metadata_filters:
            logger.warning("No metadata filters provided")
            return []
        
        results = []
        for doc in self.documents:
            if self._matches_filters(doc.metadata, metadata_filters):
                results.append(doc.model_copy(deep=True))
        
        logger.info(f"Metadata search returned {len(results)} documents")
        return results
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document metadata matches all filters."""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            # Support list values (match if any value matches)
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True

    
    def rebuild_index(self) -> None:
        """Rebuild the vector store index from scratch."""
        logger.info("Rebuilding FAISS index from documents")
        
        # Store current documents
        current_documents = self.documents.copy()
        
        # Reset index and documents
        self.initialize()
        self.documents = []
        self.document_ids = []
        
        # Re-add all documents
        if current_documents:
            self.add_documents(current_documents)
        
        logger.info("Index rebuild complete")
    
    def save(self, path: str) -> None:
        """Save the vector store to disk and optionally to S3."""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        # Create directory if it doesn't exist
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_path = f"{path}.index"
        faiss.write_index(self.index, index_path)
        logger.info(f"Saved FAISS index to {index_path}")
        
        # Save documents and metadata
        metadata_path = f"{path}.metadata"
        metadata = {
            "documents": [doc.model_dump() for doc in self.documents],
            "document_ids": self.document_ids,
            "embedding_dimension": self.embedding_dimension,
            "index_type": self.index_type
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        logger.info(f"Saved metadata to {metadata_path}")
        
        # Upload to S3 if configured
        if self.s3_client and self.s3_bucket:
            try:
                self._upload_to_s3(index_path, metadata_path)
            except Exception as e:
                logger.error(f"Failed to upload to S3: {e}")
    
    def load(self, path: str) -> None:
        """Load the vector store from disk or S3."""
        index_path = f"{path}.index"
        metadata_path = f"{path}.metadata"
        
        # Try to download from S3 if configured and local files don't exist
        if self.s3_client and self.s3_bucket:
            if not Path(index_path).exists() or not Path(metadata_path).exists():
                try:
                    self._download_from_s3(index_path, metadata_path)
                except Exception as e:
                    logger.error(f"Failed to download from S3: {e}")
        
        # Load FAISS index
        if not Path(index_path).exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        
        self.index = faiss.read_index(index_path)
        logger.info(f"Loaded FAISS index from {index_path}")
        
        # Load documents and metadata
        if not Path(metadata_path).exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self.documents = [Document(**doc) for doc in metadata["documents"]]
        self.document_ids = metadata["document_ids"]
        self.embedding_dimension = metadata["embedding_dimension"]
        self.index_type = metadata["index_type"]
        
        logger.info(f"Loaded {len(self.documents)} documents from {metadata_path}")

    
    def _upload_to_s3(self, index_path: str, metadata_path: str) -> None:
        """Upload index and metadata files to S3."""
        # Upload index file
        index_key = f"{self.s3_prefix}{Path(index_path).name}"
        self.s3_client.upload_file(index_path, self.s3_bucket, index_key)
        logger.info(f"Uploaded index to s3://{self.s3_bucket}/{index_key}")
        
        # Upload metadata file
        metadata_key = f"{self.s3_prefix}{Path(metadata_path).name}"
        self.s3_client.upload_file(metadata_path, self.s3_bucket, metadata_key)
        logger.info(f"Uploaded metadata to s3://{self.s3_bucket}/{metadata_key}")
    
    def _download_from_s3(self, index_path: str, metadata_path: str) -> None:
        """Download index and metadata files from S3."""
        # Create directory if it doesn't exist
        Path(index_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Download index file
        index_key = f"{self.s3_prefix}{Path(index_path).name}"
        self.s3_client.download_file(self.s3_bucket, index_key, index_path)
        logger.info(f"Downloaded index from s3://{self.s3_bucket}/{index_key}")
        
        # Download metadata file
        metadata_key = f"{self.s3_prefix}{Path(metadata_path).name}"
        self.s3_client.download_file(self.s3_bucket, metadata_key, metadata_path)
        logger.info(f"Downloaded metadata from s3://{self.s3_bucket}/{metadata_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            "total_documents": len(self.documents),
            "embedding_dimension": self.embedding_dimension,
            "index_type": self.index_type,
            "index_size": self.index.ntotal if self.index else 0,
            "s3_enabled": self.s3_bucket is not None
        }


# Global singleton instance
_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store(
    embedding_dimension: int = 768,
    index_type: str = "Flat",
    s3_bucket: Optional[str] = None,
    s3_prefix: str = "vector_store/"
) -> FAISSVectorStore:
    """
    Get the global vector store instance.
    
    This ensures only one vector store is loaded in memory.
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore(
            embedding_dimension=embedding_dimension,
            index_type=index_type,
            s3_bucket=s3_bucket,
            s3_prefix=s3_prefix
        )
        _vector_store.initialize()
    return _vector_store
