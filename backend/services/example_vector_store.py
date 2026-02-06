"""
Example usage of the vector store service.

This script demonstrates how to:
1. Initialize a vector store
2. Add documents with embeddings
3. Perform similarity search
4. Use metadata filtering
5. Save and load the index
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from services.vector_store import FAISSVectorStore, get_vector_store
from services.embeddings import EmbeddingService
from models.internal import Document


def main():
    print("=== Vector Store Example ===\n")
    
    # Initialize services
    print("1. Initializing embedding service and vector store...")
    embedding_service = EmbeddingService()
    vector_store = FAISSVectorStore(embedding_dimension=768)
    vector_store.initialize()
    print(f"   Vector store initialized with dimension {vector_store.embedding_dimension}\n")
    
    # Create sample documents
    print("2. Creating sample documents...")
    sample_texts = [
        "FDA certification is required for food exports to the United States",
        "CE marking is mandatory for products sold in the European Union",
        "DGFT regulates export policies in India",
        "RoDTEP provides duty refunds on exported products",
        "GST LUT allows exports without paying IGST"
    ]
    
    sample_metadata = [
        {"source": "FDA", "country": "USA", "category": "food"},
        {"source": "EU", "country": "EU", "category": "manufacturing"},
        {"source": "DGFT", "country": "India", "category": "policy"},
        {"source": "DGFT", "country": "India", "category": "finance"},
        {"source": "GSTN", "country": "India", "category": "tax"}
    ]
    
    # Generate embeddings and create documents
    print("   Generating embeddings...")
    embeddings = embedding_service.embed_documents(sample_texts)
    
    documents = []
    for i, (text, metadata, embedding) in enumerate(zip(sample_texts, sample_metadata, embeddings)):
        doc = Document(
            id=f"doc_{i}",
            content=text,
            metadata=metadata,
            embedding=embedding.tolist()
        )
        documents.append(doc)
    
    print(f"   Created {len(documents)} documents\n")
    
    # Add documents to vector store
    print("3. Adding documents to vector store...")
    vector_store.add_documents(documents)
    stats = vector_store.get_stats()
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Index size: {stats['index_size']}\n")
    
    # Perform similarity search
    print("4. Performing similarity search...")
    query = "What certifications do I need for food exports?"
    print(f"   Query: '{query}'")
    
    query_embedding = embedding_service.embed_query(query)
    results = vector_store.search(query_embedding, top_k=3)
    
    print(f"   Found {len(results)} results:")
    for i, doc in enumerate(results, 1):
        print(f"   {i}. [{doc.id}] Score: {doc.relevance_score:.4f}")
        print(f"      Content: {doc.content}")
        print(f"      Metadata: {doc.metadata}\n")
    
    # Search with metadata filters
    print("5. Searching with metadata filters...")
    print("   Filter: source='DGFT'")
    
    filtered_results = vector_store.search(
        query_embedding,
        top_k=5,
        filters={"source": "DGFT"}
    )
    
    print(f"   Found {len(filtered_results)} results:")
    for i, doc in enumerate(filtered_results, 1):
        print(f"   {i}. [{doc.id}] {doc.content[:50]}...")
        print(f"      Source: {doc.metadata['source']}\n")
    
    # Metadata-only search
    print("6. Performing metadata-only search...")
    print("   Filter: country='India'")
    
    metadata_results = vector_store.search_by_metadata({"country": "India"})
    
    print(f"   Found {len(metadata_results)} results:")
    for doc in metadata_results:
        print(f"   - [{doc.id}] {doc.content[:50]}...")
    print()
    
    # Save and load
    print("7. Saving vector store to disk...")
    save_path = "data/vector_store/example_index"
    vector_store.save(save_path)
    print(f"   Saved to {save_path}\n")
    
    print("8. Loading vector store from disk...")
    new_store = FAISSVectorStore(embedding_dimension=768)
    new_store.load(save_path)
    print(f"   Loaded {len(new_store.documents)} documents")
    
    # Verify loaded store works
    test_results = new_store.search(query_embedding, top_k=2)
    print(f"   Test search returned {len(test_results)} results\n")
    
    print("=== Example Complete ===")


if __name__ == "__main__":
    main()
