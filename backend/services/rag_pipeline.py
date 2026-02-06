"""
RAG Pipeline Service for document retrieval and LLM generation.

This service orchestrates the Retrieval-Augmented Generation pipeline:
1. Convert queries to embeddings
2. Retrieve relevant documents from vector store
3. Rank documents by relevance
4. Inject context into LLM prompts
5. Generate responses with source citations

Requirements: 10.2, 10.3, 10.4, 10.6
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from models.internal import Document
from services.embeddings import EmbeddingService, get_embedding_service
from services.vector_store import VectorStore, FAISSVectorStore, get_vector_store

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Orchestrates document retrieval and LLM generation with context.
    
    The RAG pipeline provides two main capabilities:
    1. retrieve_documents: Semantic search for relevant documents
    2. generate_with_context: LLM generation with retrieved context
    
    Features:
    - Query embedding and semantic search
    - Document ranking by relevance score
    - Context injection for LLM prompts
    - Government source prioritization
    - Source citation extraction
    
    Requirements: 10.2, 10.3, 10.4, 10.6
    """
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
        default_top_k: int = 5,
        relevance_threshold: float = 0.3,
        government_source_boost: float = 0.1
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            embedding_service: Service for generating embeddings (uses global if None)
            vector_store: Vector store for document retrieval (uses global if None)
            default_top_k: Default number of documents to retrieve
            relevance_threshold: Minimum relevance score for documents (0-1)
            government_source_boost: Score boost for government sources
        """
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or get_vector_store()
        self.default_top_k = default_top_k
        self.relevance_threshold = relevance_threshold
        self.government_source_boost = government_source_boost
        
        # Government sources that should be prioritized
        self.government_sources = {
            'DGFT', 'Customs_RMS', 'FDA', 'EU_RASFF', 'GSTN', 'RoDTEP',
            'BIS', 'FSSAI', 'APEDA', 'EIC', 'Customs'
        }
        
        logger.info(
            f"RAGPipeline initialized with top_k={default_top_k}, "
            f"relevance_threshold={relevance_threshold}"
        )
    
    def retrieve_documents(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        prioritize_government: bool = True
    ) -> List[Document]:
        """
        Retrieve relevant documents for a query using semantic search.
        
        This method:
        1. Converts the query to an embedding vector
        2. Performs semantic search in the vector store
        3. Ranks documents by relevance score
        4. Optionally boosts government sources
        5. Filters by relevance threshold
        
        Args:
            query: Query text to search for
            top_k: Number of documents to retrieve (uses default if None)
            filters: Metadata filters to apply (e.g., {"country": "US", "source": "FDA"})
            prioritize_government: Whether to boost government source rankings
            
        Returns:
            List of Document objects ranked by relevance score
            
        Example:
            >>> pipeline = RAGPipeline()
            >>> docs = pipeline.retrieve_documents(
            ...     "What are FDA requirements for food exports?",
            ...     top_k=5,
            ...     filters={"country": "US"}
            ... )
            >>> for doc in docs:
            ...     print(f"{doc.metadata['source']}: {doc.relevance_score:.3f}")
        
        Requirements: 10.2, 10.3, 10.6
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to retrieve_documents")
            return []
        
        top_k = top_k or self.default_top_k
        
        logger.info(f"Retrieving documents for query: '{query[:100]}...'")
        logger.info(f"Parameters: top_k={top_k}, filters={filters}, prioritize_government={prioritize_government}")
        
        start_time = datetime.now()
        
        try:
            # Step 1: Convert query to embedding
            query_embedding = self.embedding_service.embed_query(query)
            logger.debug(f"Generated query embedding with shape {query_embedding.shape}")
            
            # Step 2: Retrieve documents from vector store
            # Request more documents than needed to allow for filtering and re-ranking
            search_k = top_k * 3 if filters or prioritize_government else top_k
            
            retrieved_docs = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=search_k,
                filters=filters
            )
            
            logger.info(f"Retrieved {len(retrieved_docs)} documents from vector store")
            
            if not retrieved_docs:
                logger.warning("No documents retrieved from vector store")
                return []
            
            # Step 3: Rank documents by relevance score
            ranked_docs = self._rank_documents(
                documents=retrieved_docs,
                prioritize_government=prioritize_government
            )
            
            # Step 4: Filter by relevance threshold
            filtered_docs = [
                doc for doc in ranked_docs
                if doc.relevance_score is not None and doc.relevance_score >= self.relevance_threshold
            ]
            
            logger.info(
                f"Filtered to {len(filtered_docs)} documents above threshold "
                f"{self.relevance_threshold}"
            )
            
            # Step 5: Return top_k documents
            result_docs = filtered_docs[:top_k]
            
            # Calculate elapsed time
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(
                f"Document retrieval completed in {elapsed_ms:.2f}ms, "
                f"returning {len(result_docs)} documents"
            )
            
            # Log top results for debugging
            for i, doc in enumerate(result_docs[:3], 1):
                logger.debug(
                    f"  {i}. {doc.metadata.get('source', 'unknown')} - "
                    f"{doc.id} (score: {doc.relevance_score:.3f})"
                )
            
            return result_docs
        
        except Exception as e:
            logger.error(f"Error in retrieve_documents: {e}", exc_info=True)
            raise
    
    def _rank_documents(
        self,
        documents: List[Document],
        prioritize_government: bool = True
    ) -> List[Document]:
        """
        Rank documents by relevance score with optional government source boost.
        
        Args:
            documents: List of documents to rank
            prioritize_government: Whether to boost government sources
            
        Returns:
            List of documents sorted by adjusted relevance score (descending)
            
        Requirements: 10.6
        """
        if not documents:
            return []
        
        # Apply government source boost if enabled
        if prioritize_government:
            for doc in documents:
                source = doc.metadata.get('source', '')
                
                # Check if source is a government source
                if any(gov_source in source for gov_source in self.government_sources):
                    if doc.relevance_score is not None:
                        original_score = doc.relevance_score
                        doc.relevance_score = min(1.0, doc.relevance_score + self.government_source_boost)
                        
                        logger.debug(
                            f"Boosted government source {source}: "
                            f"{original_score:.3f} -> {doc.relevance_score:.3f}"
                        )
        
        # Sort by relevance score (descending)
        ranked_docs = sorted(
            documents,
            key=lambda doc: doc.relevance_score if doc.relevance_score is not None else 0.0,
            reverse=True
        )
        
        return ranked_docs
    
    def generate_with_context(
        self,
        prompt: str,
        query: Optional[str] = None,
        documents: Optional[List[Document]] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        include_sources: bool = True,
        max_context_length: int = 4000
    ) -> Tuple[str, List[Document]]:
        """
        Generate LLM response with retrieved document context.
        
        This method:
        1. Retrieves relevant documents (if not provided)
        2. Constructs context from document content
        3. Injects context into the prompt
        4. Returns the enhanced prompt and source documents
        
        Note: This method prepares the prompt with context but does not call the LLM.
        The actual LLM call should be made by the caller using an LLM client.
        
        Args:
            prompt: User prompt or question
            query: Query for document retrieval (uses prompt if None)
            documents: Pre-retrieved documents (retrieves if None)
            top_k: Number of documents to retrieve
            filters: Metadata filters for retrieval
            include_sources: Whether to include source citations in context
            max_context_length: Maximum character length for context
            
        Returns:
            Tuple of (enhanced_prompt, source_documents)
            - enhanced_prompt: Prompt with injected context
            - source_documents: List of documents used as context
            
        Example:
            >>> pipeline = RAGPipeline()
            >>> enhanced_prompt, sources = pipeline.generate_with_context(
            ...     prompt="What are the FDA requirements?",
            ...     top_k=3
            ... )
            >>> # Now call LLM with enhanced_prompt
            >>> # response = llm_client.generate(enhanced_prompt)
        
        Requirements: 10.4
        """
        if not prompt or not prompt.strip():
            logger.warning("Empty prompt provided to generate_with_context")
            return prompt, []
        
        logger.info(f"Generating context for prompt: '{prompt[:100]}...'")
        
        try:
            # Step 1: Retrieve documents if not provided
            if documents is None:
                retrieval_query = query or prompt
                documents = self.retrieve_documents(
                    query=retrieval_query,
                    top_k=top_k,
                    filters=filters
                )
            
            if not documents:
                logger.warning("No documents available for context")
                return prompt, []
            
            logger.info(f"Using {len(documents)} documents for context")
            
            # Step 2: Construct context from documents
            context = self._build_context(
                documents=documents,
                include_sources=include_sources,
                max_length=max_context_length
            )
            
            # Step 3: Inject context into prompt
            enhanced_prompt = self._inject_context(prompt, context)
            
            logger.info(
                f"Generated enhanced prompt with {len(context)} chars of context "
                f"from {len(documents)} documents"
            )
            
            return enhanced_prompt, documents
        
        except Exception as e:
            logger.error(f"Error in generate_with_context: {e}", exc_info=True)
            # Return original prompt on error
            return prompt, []
    
    def _build_context(
        self,
        documents: List[Document],
        include_sources: bool = True,
        max_length: int = 4000
    ) -> str:
        """
        Build context string from retrieved documents.
        
        Args:
            documents: List of documents to include in context
            include_sources: Whether to include source citations
            max_length: Maximum character length for context
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(documents, 1):
            # Format document content with optional source citation
            if include_sources:
                source = doc.metadata.get('source', 'Unknown')
                doc_header = f"[Document {i} - Source: {source}]\n"
            else:
                doc_header = f"[Document {i}]\n"
            
            doc_content = doc.content.strip()
            
            # Calculate space needed for this document
            doc_text = f"{doc_header}{doc_content}\n\n"
            doc_length = len(doc_text)
            
            # Check if adding this document would exceed max length
            if current_length + doc_length > max_length:
                # Try to include partial content
                remaining_space = max_length - current_length - len(doc_header) - 10
                if remaining_space > 100:  # Only include if we have reasonable space
                    truncated_content = doc_content[:remaining_space] + "..."
                    doc_text = f"{doc_header}{truncated_content}\n\n"
                    context_parts.append(doc_text)
                    logger.debug(f"Truncated document {i} to fit max_length")
                break
            
            context_parts.append(doc_text)
            current_length += doc_length
        
        context = "".join(context_parts)
        
        logger.debug(f"Built context with {len(context)} characters from {len(context_parts)} documents")
        
        return context
    
    def _inject_context(self, prompt: str, context: str) -> str:
        """
        Inject retrieved context into the user prompt.
        
        Args:
            prompt: Original user prompt
            context: Context string from retrieved documents
            
        Returns:
            Enhanced prompt with context
        """
        if not context:
            return prompt
        
        # Format: Context first, then user question
        enhanced_prompt = f"""Use the following context from regulatory documents to answer the question. If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {prompt}

Answer based on the context provided above:"""
        
        return enhanced_prompt
    
    def extract_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Extract source citations from documents for display.
        
        Args:
            documents: List of documents to extract sources from
            
        Returns:
            List of source citation dictionaries with title, source, excerpt, relevance
            
        Example:
            >>> sources = pipeline.extract_sources(documents)
            >>> for source in sources:
            ...     print(f"{source['title']} ({source['source']}): {source['relevance_score']:.2f}")
        """
        sources = []
        
        for doc in documents:
            # Extract key metadata
            source_info = {
                'id': doc.id,
                'title': doc.metadata.get('title', doc.id),
                'source': doc.metadata.get('source', 'Unknown'),
                'excerpt': doc.content[:200] + '...' if len(doc.content) > 200 else doc.content,
                'relevance_score': doc.relevance_score,
                'metadata': {
                    'country': doc.metadata.get('country'),
                    'product_category': doc.metadata.get('product_category'),
                    'last_updated': doc.metadata.get('last_updated')
                }
            }
            
            # Add URL if available
            if 'url' in doc.metadata:
                source_info['url'] = doc.metadata['url']
            
            sources.append(source_info)
        
        return sources
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG pipeline.
        
        Returns:
            Dictionary with pipeline statistics
        """
        vector_store_stats = self.vector_store.get_stats() if hasattr(self.vector_store, 'get_stats') else {}
        embedding_cache_info = self.embedding_service.get_cache_info()
        
        return {
            'default_top_k': self.default_top_k,
            'relevance_threshold': self.relevance_threshold,
            'government_source_boost': self.government_source_boost,
            'government_sources': list(self.government_sources),
            'vector_store': vector_store_stats,
            'embedding_cache': embedding_cache_info
        }


# Global singleton instance
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline(
    embedding_service: Optional[EmbeddingService] = None,
    vector_store: Optional[VectorStore] = None,
    default_top_k: int = 5,
    relevance_threshold: float = 0.3,
    government_source_boost: float = 0.1
) -> RAGPipeline:
    """
    Get the global RAG pipeline instance.
    
    This ensures only one pipeline is created with shared services.
    
    Returns:
        Global RAGPipeline instance
    """
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline(
            embedding_service=embedding_service,
            vector_store=vector_store,
            default_top_k=default_top_k,
            relevance_threshold=relevance_threshold,
            government_source_boost=government_source_boost
        )
    return _rag_pipeline
