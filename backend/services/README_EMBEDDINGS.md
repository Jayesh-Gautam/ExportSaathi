# Embedding Service Documentation

## Overview

The `EmbeddingService` is a core component of the ExportSathi RAG (Retrieval-Augmented Generation) pipeline. It converts text into dense vector embeddings using the `sentence-transformers` library with the `all-mpnet-base-v2` model.

## Features

- **High-Quality Embeddings**: Uses `all-mpnet-base-v2` model (768 dimensions) for strong semantic similarity performance
- **Query Embedding**: Generate embeddings for single queries with LRU caching
- **Batch Processing**: Efficiently process multiple documents in batches
- **Caching**: LRU cache for repeated queries to improve performance
- **Normalized Vectors**: All embeddings are L2-normalized for cosine similarity
- **Edge Case Handling**: Gracefully handles empty strings, whitespace, and unicode text
- **Lazy Loading**: Model is loaded only when first needed
- **Singleton Pattern**: Global instance ensures only one model in memory

## Installation

The required dependencies are already in `requirements.txt`:

```bash
sentence-transformers==2.3.1
torch==2.5.1
```

## Usage

### Basic Usage

```python
from services import get_embedding_service

# Get the global service instance
service = get_embedding_service()

# Embed a single query
query = "What certifications do I need for exporting?"
embedding = service.embed_query(query)
print(embedding.shape)  # (768,)

# Embed multiple documents
documents = [
    "FDA certification for food products",
    "CE marking for electronics",
    "REACH compliance for chemicals"
]
embeddings = service.embed_documents(documents)
print(len(embeddings))  # 3
```

### Advanced Usage

```python
from services import EmbeddingService

# Create a custom instance with different settings
service = EmbeddingService(
    model_name="sentence-transformers/all-mpnet-base-v2",
    cache_size=256,  # Larger cache
    batch_size=64    # Larger batches
)

# Batch processing with custom batch size
texts = ["Text 1", "Text 2", ..., "Text 100"]
embeddings = service.embed_batch(texts, batch_size=16)

# Get embedding dimension
dim = service.get_embedding_dimension()  # 768

# Cache management
cache_info = service.get_cache_info()
print(f"Cache hits: {cache_info['hits']}")
print(f"Cache misses: {cache_info['misses']}")
print(f"Cache size: {cache_info['size']}/{cache_info['maxsize']}")

service.clear_cache()  # Clear the cache
```

### Semantic Similarity

```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

service = get_embedding_service()

# Embed query and documents
query_emb = service.embed_query("Export certifications for USA")
doc_embs = service.embed_documents([
    "FDA certification required for food exports to USA",
    "CE marking for European Union electronics",
    "BIS certification for India"
])

# Calculate similarities
for i, doc_emb in enumerate(doc_embs):
    similarity = cosine_similarity(query_emb, doc_emb)
    print(f"Document {i}: {similarity:.4f}")
```

## API Reference

### `EmbeddingService`

#### Constructor

```python
EmbeddingService(
    model_name: str = "sentence-transformers/all-mpnet-base-v2",
    cache_size: int = 128,
    batch_size: int = 32
)
```

**Parameters:**
- `model_name`: Sentence-transformers model to use
- `cache_size`: Maximum number of cached query embeddings (LRU)
- `batch_size`: Default batch size for document processing

#### Methods

##### `embed_query(text: str) -> np.ndarray`

Generate embedding for a single query text with caching.

**Parameters:**
- `text`: Query text to embed

**Returns:**
- Numpy array of shape `(768,)` containing the normalized embedding

**Example:**
```python
embedding = service.embed_query("What is HS code?")
```

##### `embed_documents(texts: List[str]) -> List[np.ndarray]`

Generate embeddings for multiple documents using batch processing.

**Parameters:**
- `texts`: List of document texts to embed

**Returns:**
- List of numpy arrays, each of shape `(768,)`

**Example:**
```python
docs = ["Doc 1", "Doc 2", "Doc 3"]
embeddings = service.embed_documents(docs)
```

##### `embed_batch(texts: List[str], batch_size: Optional[int] = None) -> List[np.ndarray]`

Generate embeddings with custom batch size.

**Parameters:**
- `texts`: List of texts to embed
- `batch_size`: Custom batch size (overrides default)

**Returns:**
- List of numpy arrays, each of shape `(768,)`

##### `get_embedding_dimension() -> int`

Get the dimension of embeddings produced by this service.

**Returns:**
- Embedding dimension (768 for all-mpnet-base-v2)

##### `clear_cache() -> None`

Clear the embedding cache.

##### `get_cache_info() -> dict`

Get cache statistics.

**Returns:**
- Dictionary with keys: `hits`, `misses`, `size`, `maxsize`

### `get_embedding_service() -> EmbeddingService`

Get the global singleton embedding service instance.

**Returns:**
- Global `EmbeddingService` instance

## Model Information

### all-mpnet-base-v2

- **Dimensions**: 768
- **Max Sequence Length**: 384 tokens
- **Performance**: Strong performance on semantic similarity tasks
- **Normalization**: Embeddings are L2-normalized
- **Use Case**: General-purpose semantic search and similarity

**Model Card**: https://huggingface.co/sentence-transformers/all-mpnet-base-v2

## Performance Considerations

### Caching

The service uses LRU (Least Recently Used) caching for query embeddings:
- Default cache size: 128 queries
- Cache hits avoid re-computing embeddings
- Significant speedup for repeated queries

### Batch Processing

For multiple documents:
- Default batch size: 32
- Larger batches = better GPU utilization (if available)
- Progress bar shown for >100 documents

### Memory Usage

- Model size: ~420 MB
- Each embedding: 768 × 4 bytes = 3 KB
- Cache (128 queries): ~384 KB
- Use singleton pattern to avoid loading multiple models

## Edge Cases

### Empty Strings

Empty or whitespace-only strings return zero vectors:

```python
embedding = service.embed_query("")
# Returns: np.zeros(768, dtype=np.float32)
```

### Long Texts

Texts longer than 384 tokens are automatically truncated by the model.

### Unicode Text

Full unicode support for multilingual text:

```python
texts = [
    "Export to भारत (India)",
    "中国出口 (China export)",
    "Exportação para o Brasil"
]
embeddings = service.embed_documents(texts)
```

## Testing

Run the test suite:

```bash
cd backend/services
python -m pytest test_embeddings.py -v
```

Run the example demo:

```bash
cd backend/services
python example_embeddings.py
```

## Integration with RAG Pipeline

The embedding service is used by the RAG pipeline for:

1. **Query Embedding**: Convert user queries to vectors
2. **Document Embedding**: Convert knowledge base documents to vectors
3. **Semantic Search**: Find relevant documents using cosine similarity
4. **Context Retrieval**: Retrieve top-k most relevant documents for LLM

Example integration:

```python
from services import get_embedding_service

# In RAG pipeline
service = get_embedding_service()

# Embed user query
query = "What certifications do I need?"
query_embedding = service.embed_query(query)

# Search vector store
results = vector_store.search(query_embedding, top_k=5)

# Use retrieved documents as context for LLM
context = "\n\n".join([doc.content for doc in results])
```

## Troubleshooting

### Model Download Issues

If the model fails to download:
1. Check internet connection
2. Verify Hugging Face Hub access
3. Manually download model:
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')"
   ```

### Memory Issues

If running out of memory:
1. Reduce batch size: `service.batch_size = 16`
2. Clear cache periodically: `service.clear_cache()`
3. Use smaller model: `all-MiniLM-L6-v2` (384 dim)

### Performance Issues

For slow embedding generation:
1. Use batch processing for multiple documents
2. Enable GPU if available (PyTorch will auto-detect)
3. Increase batch size for better throughput

## Requirements Validation

This implementation satisfies **Requirement 10.1**:

> WHEN a query is processed, THE RAG_Pipeline SHALL convert the query into an embedding vector

✅ **Implemented Features:**
- Query embedding with `embed_query()` method
- Document embedding with `embed_documents()` method
- Batch processing for efficiency
- Caching mechanism for repeated queries
- Uses `all-mpnet-base-v2` model as specified
- Normalized embeddings for cosine similarity
- Comprehensive error handling

## Future Enhancements

Potential improvements:
- [ ] Support for multiple embedding models
- [ ] Async/await support for concurrent embedding
- [ ] Persistent cache (Redis/disk)
- [ ] GPU optimization hints
- [ ] Embedding quality metrics
- [ ] Model fine-tuning on export domain data
