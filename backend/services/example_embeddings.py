"""
Example usage of the EmbeddingService.

This script demonstrates how to use the embedding service for:
1. Single query embedding
2. Batch document embedding
3. Cache usage
4. Semantic similarity comparison
"""

import numpy as np
from embeddings import get_embedding_service


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def main():
    # Get the global embedding service instance
    service = get_embedding_service()
    
    print("=" * 80)
    print("ExportSathi Embedding Service Demo")
    print("=" * 80)
    print()
    
    # Example 1: Single query embedding
    print("1. Single Query Embedding")
    print("-" * 80)
    query = "What certifications do I need to export LED lights to USA?"
    print(f"Query: {query}")
    
    embedding = service.embed_query(query)
    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding dimension: {service.get_embedding_dimension()}")
    print(f"First 5 values: {embedding[:5]}")
    print(f"L2 norm (should be ~1.0): {np.linalg.norm(embedding):.6f}")
    print()
    
    # Example 2: Batch document embedding
    print("2. Batch Document Embedding")
    print("-" * 80)
    documents = [
        "FDA certification is required for food products exported to USA",
        "CE marking is mandatory for electronics sold in European Union",
        "REACH compliance ensures chemical safety in EU markets",
        "BIS certification is needed for certain products in India",
        "SOFTEX declaration is required for software service exports"
    ]
    
    print(f"Embedding {len(documents)} documents...")
    doc_embeddings = service.embed_documents(documents)
    print(f"Generated {len(doc_embeddings)} embeddings")
    print(f"Each embedding shape: {doc_embeddings[0].shape}")
    print()
    
    # Example 3: Cache demonstration
    print("3. Cache Performance")
    print("-" * 80)
    service.clear_cache()
    print("Cache cleared")
    
    # First query - cache miss
    _ = service.embed_query(query)
    cache_info = service.get_cache_info()
    print(f"After first query - Hits: {cache_info['hits']}, Misses: {cache_info['misses']}")
    
    # Second query (same) - cache hit
    _ = service.embed_query(query)
    cache_info = service.get_cache_info()
    print(f"After second query - Hits: {cache_info['hits']}, Misses: {cache_info['misses']}")
    print(f"Cache size: {cache_info['size']}/{cache_info['maxsize']}")
    print()
    
    # Example 4: Semantic similarity
    print("4. Semantic Similarity Comparison")
    print("-" * 80)
    
    # Compare query with each document
    query_embedding = service.embed_query(query)
    
    print(f"Query: {query}")
    print()
    print("Similarity scores with documents:")
    
    similarities = []
    for i, doc in enumerate(documents):
        similarity = cosine_similarity(query_embedding, doc_embeddings[i])
        similarities.append((similarity, doc))
        print(f"  {similarity:.4f} - {doc[:60]}...")
    
    print()
    print("Most relevant document:")
    best_similarity, best_doc = max(similarities, key=lambda x: x[0])
    print(f"  Score: {best_similarity:.4f}")
    print(f"  Document: {best_doc}")
    print()
    
    # Example 5: Semantic search simulation
    print("5. Semantic Search Simulation")
    print("-" * 80)
    
    # Knowledge base documents
    knowledge_base = [
        "FDA requires pre-market approval for medical devices",
        "LED lights are classified under HS code 8539",
        "UL certification ensures electrical safety standards",
        "Energy Star certification for energy-efficient products",
        "FCC certification required for electronic devices in USA",
        "RoHS compliance restricts hazardous substances",
        "Export documentation includes commercial invoice and packing list",
        "GST LUT allows exports without paying IGST",
    ]
    
    search_query = "electrical safety certification for USA"
    print(f"Search query: {search_query}")
    print()
    
    # Embed query and knowledge base
    search_embedding = service.embed_query(search_query)
    kb_embeddings = service.embed_documents(knowledge_base)
    
    # Calculate similarities and rank
    results = []
    for i, kb_doc in enumerate(knowledge_base):
        similarity = cosine_similarity(search_embedding, kb_embeddings[i])
        results.append((similarity, kb_doc))
    
    # Sort by similarity (descending)
    results.sort(reverse=True, key=lambda x: x[0])
    
    print("Top 3 most relevant documents:")
    for i, (score, doc) in enumerate(results[:3], 1):
        print(f"  {i}. Score: {score:.4f}")
        print(f"     {doc}")
        print()
    
    print("=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
