"""
Example usage of the RAG Pipeline Service.

This script demonstrates how to use the RAG pipeline for:
1. Retrieving relevant documents from the knowledge base
2. Generating context-enhanced prompts for LLM
3. Extracting source citations

Prerequisites:
- Knowledge base must be loaded into the vector store
- Run load_knowledge_base.py first to build the FAISS index
"""

import logging
from pathlib import Path

from services.embeddings import get_embedding_service
from services.vector_store import get_vector_store
from services.rag_pipeline import RAGPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_document_retrieval():
    """Example: Retrieve relevant documents for a query."""
    logger.info("=" * 80)
    logger.info("Example 1: Document Retrieval")
    logger.info("=" * 80)
    
    # Initialize RAG pipeline
    pipeline = RAGPipeline()
    
    # Query for FDA requirements
    query = "What are the FDA requirements for exporting food products to the United States?"
    
    logger.info(f"\nQuery: {query}")
    logger.info("\nRetrieving documents...")
    
    # Retrieve top 5 relevant documents
    documents = pipeline.retrieve_documents(
        query=query,
        top_k=5,
        filters=None,  # No filters - search all documents
        prioritize_government=True  # Boost government sources
    )
    
    logger.info(f"\nRetrieved {len(documents)} documents:")
    for i, doc in enumerate(documents, 1):
        logger.info(f"\n{i}. Document ID: {doc.id}")
        logger.info(f"   Source: {doc.metadata.get('source', 'Unknown')}")
        logger.info(f"   Country: {doc.metadata.get('country', 'Unknown')}")
        logger.info(f"   Relevance Score: {doc.relevance_score:.3f}")
        logger.info(f"   Content Preview: {doc.content[:150]}...")


def example_filtered_retrieval():
    """Example: Retrieve documents with metadata filters."""
    logger.info("\n" + "=" * 80)
    logger.info("Example 2: Filtered Document Retrieval")
    logger.info("=" * 80)
    
    # Initialize RAG pipeline
    pipeline = RAGPipeline()
    
    # Query for certification requirements
    query = "What certifications are required for agricultural exports?"
    
    logger.info(f"\nQuery: {query}")
    logger.info("Filters: country=India, product_category=agriculture")
    logger.info("\nRetrieving documents...")
    
    # Retrieve documents with filters
    documents = pipeline.retrieve_documents(
        query=query,
        top_k=3,
        filters={
            "country": "India",
            "product_category": "agriculture"
        }
    )
    
    logger.info(f"\nRetrieved {len(documents)} documents:")
    for i, doc in enumerate(documents, 1):
        logger.info(f"\n{i}. {doc.id}")
        logger.info(f"   Source: {doc.metadata.get('source')}")
        logger.info(f"   Relevance: {doc.relevance_score:.3f}")


def example_context_generation():
    """Example: Generate context-enhanced prompt for LLM."""
    logger.info("\n" + "=" * 80)
    logger.info("Example 3: Context Generation for LLM")
    logger.info("=" * 80)
    
    # Initialize RAG pipeline
    pipeline = RAGPipeline()
    
    # User question
    prompt = "What documents do I need to export textiles to the EU?"
    
    logger.info(f"\nOriginal Prompt: {prompt}")
    logger.info("\nGenerating context-enhanced prompt...")
    
    # Generate enhanced prompt with context
    enhanced_prompt, source_docs = pipeline.generate_with_context(
        prompt=prompt,
        top_k=3,
        include_sources=True,
        max_context_length=2000
    )
    
    logger.info(f"\nEnhanced Prompt Length: {len(enhanced_prompt)} characters")
    logger.info(f"Source Documents: {len(source_docs)}")
    
    logger.info("\n--- Enhanced Prompt Preview ---")
    logger.info(enhanced_prompt[:500] + "...")
    
    logger.info("\n--- Source Documents ---")
    for i, doc in enumerate(source_docs, 1):
        logger.info(f"{i}. {doc.id} (score: {doc.relevance_score:.3f})")


def example_source_extraction():
    """Example: Extract source citations from documents."""
    logger.info("\n" + "=" * 80)
    logger.info("Example 4: Source Citation Extraction")
    logger.info("=" * 80)
    
    # Initialize RAG pipeline
    pipeline = RAGPipeline()
    
    # Retrieve documents
    query = "What are the RoDTEP benefits for exporters?"
    documents = pipeline.retrieve_documents(query, top_k=3)
    
    logger.info(f"\nQuery: {query}")
    logger.info(f"Retrieved {len(documents)} documents")
    
    # Extract source citations
    sources = pipeline.extract_sources(documents)
    
    logger.info("\n--- Source Citations ---")
    for source in sources:
        logger.info(f"\nTitle: {source['title']}")
        logger.info(f"Source: {source['source']}")
        logger.info(f"Relevance: {source['relevance_score']:.3f}")
        logger.info(f"Excerpt: {source['excerpt'][:100]}...")
        if 'url' in source:
            logger.info(f"URL: {source['url']}")


def example_government_source_prioritization():
    """Example: Demonstrate government source prioritization."""
    logger.info("\n" + "=" * 80)
    logger.info("Example 5: Government Source Prioritization")
    logger.info("=" * 80)
    
    # Initialize RAG pipeline
    pipeline = RAGPipeline()
    
    query = "Export regulations for India"
    
    # Retrieve without government boost
    logger.info("\n--- Without Government Source Boost ---")
    docs_no_boost = pipeline.retrieve_documents(
        query=query,
        top_k=5,
        prioritize_government=False
    )
    
    for i, doc in enumerate(docs_no_boost[:3], 1):
        logger.info(f"{i}. {doc.metadata.get('source')} - Score: {doc.relevance_score:.3f}")
    
    # Retrieve with government boost
    logger.info("\n--- With Government Source Boost ---")
    docs_with_boost = pipeline.retrieve_documents(
        query=query,
        top_k=5,
        prioritize_government=True
    )
    
    for i, doc in enumerate(docs_with_boost[:3], 1):
        logger.info(f"{i}. {doc.metadata.get('source')} - Score: {doc.relevance_score:.3f}")


def example_pipeline_stats():
    """Example: Get pipeline statistics."""
    logger.info("\n" + "=" * 80)
    logger.info("Example 6: Pipeline Statistics")
    logger.info("=" * 80)
    
    # Initialize RAG pipeline
    pipeline = RAGPipeline()
    
    # Get statistics
    stats = pipeline.get_stats()
    
    logger.info("\n--- Pipeline Configuration ---")
    logger.info(f"Default top_k: {stats['default_top_k']}")
    logger.info(f"Relevance threshold: {stats['relevance_threshold']}")
    logger.info(f"Government source boost: {stats['government_source_boost']}")
    
    logger.info("\n--- Government Sources ---")
    for source in sorted(stats['government_sources']):
        logger.info(f"  - {source}")
    
    if 'vector_store' in stats:
        logger.info("\n--- Vector Store Stats ---")
        for key, value in stats['vector_store'].items():
            logger.info(f"  {key}: {value}")
    
    if 'embedding_cache' in stats:
        logger.info("\n--- Embedding Cache Stats ---")
        for key, value in stats['embedding_cache'].items():
            logger.info(f"  {key}: {value}")


def main():
    """Run all examples."""
    logger.info("RAG Pipeline Examples")
    logger.info("=" * 80)
    
    # Check if vector store index exists
    index_path = Path("./data/faiss_index.index")
    if not index_path.exists():
        logger.error(
            "\nError: Vector store index not found at ./data/faiss_index.index"
        )
        logger.error(
            "Please run load_knowledge_base.py first to build the index."
        )
        logger.error(
            "\nExample command:"
        )
        logger.error(
            "  python -m services.load_knowledge_base --bucket your-bucket --output ./data/faiss_index"
        )
        return
    
    try:
        # Load vector store
        logger.info("\nLoading vector store...")
        vector_store = get_vector_store()
        vector_store.load("./data/faiss_index")
        logger.info("Vector store loaded successfully!")
        
        # Run examples
        example_document_retrieval()
        example_filtered_retrieval()
        example_context_generation()
        example_source_extraction()
        example_government_source_prioritization()
        example_pipeline_stats()
        
        logger.info("\n" + "=" * 80)
        logger.info("All examples completed successfully!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"\nError running examples: {e}", exc_info=True)


if __name__ == '__main__':
    main()
