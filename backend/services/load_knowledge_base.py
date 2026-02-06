"""
Knowledge Base Document Loader

This script loads documents from the S3 knowledge base bucket, parses metadata,
generates embeddings, and builds a FAISS index for semantic search.

Requirements: 9.1, 9.2, 9.7

Usage:
    python -m services.load_knowledge_base --bucket exportsathi-knowledge-base --output ./data/faiss_index

The script expects documents in S3 to be organized with metadata in the filename or
as S3 object metadata. Supported formats:
- JSON files with 'content' and 'metadata' fields
- Text files with metadata in S3 object tags
- PDF files (text extraction not yet implemented)

Metadata fields:
- source: Source type (DGFT, FDA, EU_RASFF, Customs_RMS, GSTN, RoDTEP)
- country: Country code (IN, US, EU, etc.)
- product_category: Product category (agriculture, textiles, electronics, etc.)
- certifications: Comma-separated list of related certifications
- last_updated: Last update date (ISO format)
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from models.internal import Document
from services.embeddings import get_embedding_service
from services.vector_store import FAISSVectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeBaseLoader:
    """
    Loads documents from S3, generates embeddings, and builds FAISS index.
    
    This class handles the complete pipeline for building the knowledge base:
    1. Download documents from S3
    2. Parse document content and metadata
    3. Generate embeddings using the embedding service
    4. Build FAISS index for semantic search
    5. Save index to local disk and optionally back to S3
    """
    
    def __init__(
        self,
        s3_bucket: str,
        s3_prefix: str = "",
        embedding_dimension: int = 768,
        batch_size: int = 32
    ):
        """
        Initialize the knowledge base loader.
        
        Args:
            s3_bucket: S3 bucket name containing knowledge base documents
            s3_prefix: Optional prefix for S3 keys (folder path)
            embedding_dimension: Dimension of embeddings (768 for all-mpnet-base-v2)
            batch_size: Batch size for embedding generation
        """
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.embedding_dimension = embedding_dimension
        self.batch_size = batch_size
        
        # Initialize services
        try:
            self.s3_client = boto3.client('s3')
            logger.info(f"S3 client initialized for bucket: {s3_bucket}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
        
        self.embedding_service = get_embedding_service()
        logger.info("Embedding service initialized")
        
        self.vector_store: Optional[FAISSVectorStore] = None
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the S3 bucket.
        
        Returns:
            List of dictionaries with 'key', 'size', and 'last_modified' fields
        """
        logger.info(f"Listing documents in s3://{self.s3_bucket}/{self.s3_prefix}")
        
        documents = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        
        try:
            for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=self.s3_prefix):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    # Skip directories
                    if obj['Key'].endswith('/'):
                        continue
                    
                    documents.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
            
            logger.info(f"Found {len(documents)} documents in S3")
            return documents
        
        except ClientError as e:
            logger.error(f"Error listing S3 objects: {e}")
            raise
    
    def download_document(self, s3_key: str) -> Optional[bytes]:
        """
        Download a document from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Document content as bytes, or None if download fails
        """
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            content = response['Body'].read()
            logger.debug(f"Downloaded {len(content)} bytes from {s3_key}")
            return content
        
        except ClientError as e:
            logger.error(f"Error downloading {s3_key}: {e}")
            return None
    
    def get_object_metadata(self, s3_key: str) -> Dict[str, Any]:
        """
        Get S3 object metadata and tags.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dictionary with metadata fields
        """
        metadata = {}
        
        try:
            # Get object metadata
            response = self.s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
            metadata.update(response.get('Metadata', {}))
            
            # Get object tags
            try:
                tags_response = self.s3_client.get_object_tagging(
                    Bucket=self.s3_bucket,
                    Key=s3_key
                )
                for tag in tags_response.get('TagSet', []):
                    metadata[tag['Key']] = tag['Value']
            except ClientError:
                # Tags might not be available
                pass
            
            logger.debug(f"Retrieved metadata for {s3_key}: {metadata}")
            return metadata
        
        except ClientError as e:
            logger.warning(f"Error getting metadata for {s3_key}: {e}")
            return {}
    
    def parse_document(
        self,
        s3_key: str,
        content: bytes,
        s3_metadata: Dict[str, Any]
    ) -> Optional[Document]:
        """
        Parse document content and metadata.
        
        Supports:
        - JSON files with 'content' and 'metadata' fields
        - Text files with metadata from S3 tags
        
        Args:
            s3_key: S3 object key
            content: Document content as bytes
            s3_metadata: S3 object metadata and tags
            
        Returns:
            Document object or None if parsing fails
        """
        try:
            # Determine file type from extension
            file_ext = Path(s3_key).suffix.lower()
            
            if file_ext == '.json':
                # Parse JSON document
                doc_data = json.loads(content.decode('utf-8'))
                
                doc_content = doc_data.get('content', '')
                doc_metadata = doc_data.get('metadata', {})
                
                # Merge with S3 metadata (S3 metadata takes precedence)
                doc_metadata.update(s3_metadata)
                
            elif file_ext in ['.txt', '.md']:
                # Plain text document
                doc_content = content.decode('utf-8')
                doc_metadata = s3_metadata.copy()
                
            else:
                logger.warning(f"Unsupported file type: {file_ext} for {s3_key}")
                return None
            
            # Validate required fields
            if not doc_content or not doc_content.strip():
                logger.warning(f"Empty content for {s3_key}")
                return None
            
            # Generate document ID from S3 key
            doc_id = Path(s3_key).stem.replace(' ', '_').replace('/', '_')
            
            # Ensure metadata has required fields with defaults
            doc_metadata.setdefault('source', 'unknown')
            doc_metadata.setdefault('country', 'unknown')
            doc_metadata.setdefault('product_category', 'general')
            doc_metadata.setdefault('last_updated', datetime.now().isoformat())
            doc_metadata['s3_key'] = s3_key
            
            # Parse certifications if present
            if 'certifications' in doc_metadata and isinstance(doc_metadata['certifications'], str):
                doc_metadata['certifications'] = [
                    cert.strip() for cert in doc_metadata['certifications'].split(',')
                ]
            
            return Document(
                id=doc_id,
                content=doc_content,
                metadata=doc_metadata,
                embedding=None  # Will be generated later
            )
        
        except Exception as e:
            logger.error(f"Error parsing document {s3_key}: {e}")
            return None
    
    def load_documents(self) -> List[Document]:
        """
        Load all documents from S3 with metadata.
        
        Returns:
            List of Document objects
        """
        logger.info("Loading documents from S3...")
        
        # List all documents
        s3_objects = self.list_documents()
        
        if not s3_objects:
            logger.warning("No documents found in S3 bucket")
            return []
        
        documents = []
        
        for obj in s3_objects:
            s3_key = obj['key']
            logger.info(f"Processing {s3_key}...")
            
            # Download document
            content = self.download_document(s3_key)
            if content is None:
                continue
            
            # Get metadata
            s3_metadata = self.get_object_metadata(s3_key)
            
            # Parse document
            document = self.parse_document(s3_key, content, s3_metadata)
            if document is not None:
                documents.append(document)
                logger.info(f"Loaded document: {document.id}")
        
        logger.info(f"Successfully loaded {len(documents)} documents")
        return documents
    
    def generate_embeddings(self, documents: List[Document]) -> List[Document]:
        """
        Generate embeddings for all documents.
        
        Args:
            documents: List of Document objects without embeddings
            
        Returns:
            List of Document objects with embeddings
        """
        logger.info(f"Generating embeddings for {len(documents)} documents...")
        
        # Extract content for embedding
        texts = [doc.content for doc in documents]
        
        # Generate embeddings in batches
        embeddings = self.embedding_service.embed_documents(texts)
        
        # Attach embeddings to documents
        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding.tolist()
        
        logger.info("Embeddings generated successfully")
        return documents
    
    def build_index(self, documents: List[Document], output_path: str) -> None:
        """
        Build FAISS index and save to disk.
        
        Args:
            documents: List of Document objects with embeddings
            output_path: Path to save the index
        """
        logger.info("Building FAISS index...")
        
        # Initialize vector store
        self.vector_store = FAISSVectorStore(
            embedding_dimension=self.embedding_dimension,
            index_type="Flat",
            s3_bucket=self.s3_bucket,
            s3_prefix="vector_store/"
        )
        self.vector_store.initialize()
        
        # Add documents to vector store
        self.vector_store.add_documents(documents)
        
        # Save index
        logger.info(f"Saving index to {output_path}...")
        self.vector_store.save(output_path)
        
        # Print statistics
        stats = self.vector_store.get_stats()
        logger.info(f"Index statistics: {stats}")
        
        logger.info("FAISS index built and saved successfully")
    
    def run(self, output_path: str) -> None:
        """
        Run the complete knowledge base loading pipeline.
        
        Args:
            output_path: Path to save the FAISS index
        """
        logger.info("Starting knowledge base loading pipeline...")
        start_time = datetime.now()
        
        try:
            # Step 1: Load documents from S3
            documents = self.load_documents()
            
            if not documents:
                logger.error("No documents loaded. Exiting.")
                return
            
            # Step 2: Generate embeddings
            documents = self.generate_embeddings(documents)
            
            # Step 3: Build and save FAISS index
            self.build_index(documents, output_path)
            
            # Calculate elapsed time
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Knowledge base loading completed in {elapsed:.2f} seconds")
            logger.info(f"Total documents indexed: {len(documents)}")
            
        except Exception as e:
            logger.error(f"Error in knowledge base loading pipeline: {e}")
            raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Load knowledge base documents from S3 and build FAISS index"
    )
    parser.add_argument(
        '--bucket',
        type=str,
        required=True,
        help='S3 bucket name containing knowledge base documents'
    )
    parser.add_argument(
        '--prefix',
        type=str,
        default='',
        help='S3 prefix (folder path) for documents'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='./data/faiss_index',
        help='Output path for FAISS index'
    )
    parser.add_argument(
        '--embedding-dim',
        type=int,
        default=768,
        help='Embedding dimension (default: 768 for all-mpnet-base-v2)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for embedding generation'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create loader
    loader = KnowledgeBaseLoader(
        s3_bucket=args.bucket,
        s3_prefix=args.prefix,
        embedding_dimension=args.embedding_dim,
        batch_size=args.batch_size
    )
    
    # Run pipeline
    try:
        loader.run(args.output)
        logger.info("Knowledge base loading completed successfully!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Knowledge base loading failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
