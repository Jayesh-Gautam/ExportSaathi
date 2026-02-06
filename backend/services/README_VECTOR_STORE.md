# Vector Store Service

## Overview

The Vector Store Service provides semantic document search capabilities using FAISS (Facebook AI Similarity Search). It enables the ExportSathi platform to retrieve relevant regulatory documents based on semantic similarity, supporting the RAG (Retrieval-Augmented Generation) pipeline.

**Requirements Implemented:** 9.2, 9.3, 9.4

## Features

- **Fast Similarity Search**: Uses FAISS for efficient vector similarity search
- **Metadata Filtering**: Filter search results by document metadata (source, country, category, etc.)
- **Index Persistence**: Save and load indexes from local disk or AWS S3
- **Cosine Similarity**: Normalized vectors for accurate semantic matching
- **Flexible Architecture**: Abstract interface supports multiple vector store implementations

## Architecture

### Abstract Interface

The `VectorStore` abstract class defines the interface that all vector store implementations must follow:

```python
class VectorStore(ABC):
    def add_documents(documents: List[Document]) -> None
    def search(query_embedding, top_k, filters) -> List[Document]
    def search_by_metadata(metadata_filters) -> List[Document]
    def initialize() -> None
    def rebuild_index() -> None
    def save(path: str) -> None
    def load(path: str) -> None
```

### FAISS Implementation

The `FAISSVectorStore` class implements the interface using FAISS:

- **Index Type**: IndexFlatIP (inner product) for exact cosine similarity search
- **Embedding Dimension**: 768 (for all-mpnet-base-v2 model)
- **Metadata Storage**: Separate JSON file for document metadata
- **S3 Integration**: Optional upload/download to AWS S3

## Usage

### Basic Usage

```python
from services.vector_store import FAISSVectorStore
from services.embeddings import EmbeddingService
from models.internal import Document

# Initialize services
embedding_service = EmbeddingService()
vector_store = FAISSVectorStore(embedding_dimension=768)
vector_store.initialize()

# Create documents with embeddings
texts = ["FDA certification required for food exports", ...]
embeddings = embedding_service.embed_documents(texts)

documents = [
    Document(
        id=f"doc_{i}",
        content=text,
        metadata={"source": "FDA", "country": "USA"},
        embedding=embedding.tolist()
    )
    for i, (text, embedding) in enumerate(zip(texts, embeddings))
]

# Add documents to vector store
vector_store.add_documents(documents)

# Search for similar documents
query = "What certifications do I need?"
query_embedding = embedding_service.embed_query(query)
results = vector_store.search(query_embedding, top_k=5)

for doc in results:
    print(f"Score: {doc.relevance_score:.4f}")
    print(f"Content: {doc.content}")
```

### Search with Metadata Filters

```python
# Search only DGFT documents
results = vector_store.search(
    query_embedding,
    top_k=5,
    filters={"source": "DGFT"}
)

# Search documents for specific country
results = vector_store.search(
    query_embedding,
    top_k=5,
    filters={"country": "India"}
)

# Multiple filters
results = vector_store.search(
    query_embedding,
    top_k=5,
    filters={"source": "DGFT", "category": "agriculture"}
)
```

### Metadata-Only Search

```python
# Find all documents from a specific source
results = vector_store.search_by_metadata({"source": "FDA"})

# Find documents by multiple criteria
results = vector_store.search_by_metadata({
    "country": "India",
    "category": "finance"
})
```

### Save and Load Index

```python
# Save to local disk
vector_store.save("data/vector_store/index")

# Load from local disk
new_store = FAISSVectorStore(embedding_dimension=768)
new_store.load("data/vector_store/index")

# With S3 persistence
vector_store = FAISSVectorStore(
    embedding_dimension=768,
    s3_bucket="my-bucket",
    s3_prefix="vector_store/"
)
vector_store.save("data/vector_store/index")  # Automatically uploads to S3
```

### Global Singleton

```python
from services.vector_store import get_vector_store

# Get global instance (recommended for production)
vector_store = get_vector_store(
    embedding_dimension=768,
    s3_bucket="my-bucket"
)
```

## Document Metadata Structure

Documents should include metadata for filtering and source attribution:

```python
metadata = {
    "source": str,          # Source organization (DGFT, FDA, EU, GSTN, etc.)
    "country": str,         # Country code (India, USA, EU, etc.)
    "category": str,        # Document category (agriculture, manufacturing, finance, etc.)
    "last_updated": str,    # ISO date string
    "certification": str,   # Related certification (FDA, CE, BIS, etc.) - optional
    "product_type": str,    # Product category - optional
}
```

## Performance Considerations

### Index Types

- **Flat (IndexFlatIP)**: Exact search, best for < 1M documents
- **IVF (IndexIVFFlat)**: Approximate search, faster for large datasets

```python
# For large datasets (> 100K documents)
vector_store = FAISSVectorStore(
    embedding_dimension=768,
    index_type="IVF"
)
```

### Search Performance

- **Flat index**: O(n) search time, exact results
- **IVF index**: O(log n) search time, approximate results
- **Metadata filtering**: Applied post-search, may require larger top_k

### Memory Usage

- **Embeddings**: ~3 KB per document (768 dimensions × 4 bytes)
- **Metadata**: ~1 KB per document (JSON)
- **Total**: ~4 KB per document

For 100K documents: ~400 MB memory

## Testing

Run the test suite:

```bash
cd backend/services
python -m pytest test_vector_store.py -v
```

Run the example:

```bash
cd backend/services
python example_vector_store.py
```

## Integration with RAG Pipeline

The vector store integrates with the RAG pipeline for document retrieval:

```python
from services.vector_store import get_vector_store
from services.embeddings import get_embedding_service

# Initialize services
embedding_service = get_embedding_service()
vector_store = get_vector_store()

# RAG retrieval
def retrieve_documents(query: str, top_k: int = 5, filters: dict = None):
    # Convert query to embedding
    query_embedding = embedding_service.embed_query(query)
    
    # Search vector store
    documents = vector_store.search(
        query_embedding,
        top_k=top_k,
        filters=filters
    )
    
    return documents

# Example: Retrieve documents for certification query
query = "What certifications do I need for food exports to USA?"
documents = retrieve_documents(
    query,
    top_k=5,
    filters={"country": "USA"}
)
```

## S3 Persistence

### Configuration

Set environment variables:

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=your-bucket-name
```

### Usage

```python
import os

vector_store = FAISSVectorStore(
    embedding_dimension=768,
    s3_bucket=os.getenv("S3_BUCKET"),
    s3_prefix="vector_store/"
)

# Save (automatically uploads to S3)
vector_store.save("data/vector_store/index")

# Load (automatically downloads from S3 if not found locally)
vector_store.load("data/vector_store/index")
```

### S3 Structure

```
s3://your-bucket/
└── vector_store/
    ├── index.index      # FAISS index file
    └── index.metadata   # Document metadata JSON
```

## Error Handling

The vector store handles common errors gracefully:

- **Empty documents**: Skipped with warning
- **Invalid embeddings**: Skipped with warning
- **Dimension mismatch**: Raises ValueError
- **S3 errors**: Logged, falls back to local storage
- **Missing files**: Raises FileNotFoundError

## Statistics

Get vector store statistics:

```python
stats = vector_store.get_stats()
print(stats)
# {
#     "total_documents": 1000,
#     "embedding_dimension": 768,
#     "index_type": "Flat",
#     "index_size": 1000,
#     "s3_enabled": True
# }
```

## Best Practices

1. **Initialize once**: Use the global singleton `get_vector_store()`
2. **Batch additions**: Add documents in batches for efficiency
3. **Normalize embeddings**: Always normalize for cosine similarity
4. **Filter strategically**: Use metadata filters to reduce search space
5. **Save regularly**: Persist index after significant updates
6. **Monitor memory**: Track document count and memory usage
7. **Use S3**: Enable S3 persistence for production deployments

## Troubleshooting

### Issue: Search returns no results

- Check that documents have been added: `vector_store.get_stats()`
- Verify embedding dimensions match
- Check metadata filters aren't too restrictive

### Issue: Low relevance scores

- Ensure embeddings are normalized
- Check that the same embedding model is used for queries and documents
- Verify document content is relevant to queries

### Issue: S3 upload/download fails

- Check AWS credentials are configured
- Verify S3 bucket exists and has correct permissions
- Check network connectivity

### Issue: High memory usage

- Consider using IVF index for large datasets
- Reduce embedding dimension (use all-MiniLM-L6-v2 with 384 dims)
- Implement document pagination

## Future Enhancements

- [ ] Support for ChromaDB implementation
- [ ] Hybrid search (vector + keyword)
- [ ] Document versioning
- [ ] Incremental index updates
- [ ] Distributed index sharding
- [ ] Query caching
- [ ] Relevance feedback
- [ ] Multi-vector search

## References

- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [Requirements 9.2, 9.3, 9.4](../../.kiro/specs/export-readiness-platform/requirements.md)
