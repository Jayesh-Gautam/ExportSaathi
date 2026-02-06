# RAG Pipeline Service

## Overview

The RAG (Retrieval-Augmented Generation) Pipeline orchestrates document retrieval and context injection for LLM-based responses. It ensures that all AI-generated responses are grounded in retrieved regulatory documents from trusted sources.

**Requirements Implemented:** 10.2, 10.3, 10.4, 10.6

## Features

### 1. Semantic Document Retrieval
- Converts queries to embeddings using sentence-transformers
- Performs semantic search in the vector store
- Returns top-k most relevant documents
- Supports metadata filtering (country, source, product category)

### 2. Document Ranking
- Ranks documents by relevance score (cosine similarity)
- Filters documents below relevance threshold (default: 0.3)
- Prioritizes government sources with configurable boost (default: +0.1)

### 3. Context Injection
- Builds context from retrieved documents
- Injects context into LLM prompts
- Respects maximum context length limits
- Includes source citations in context

### 4. Government Source Prioritization
- Automatically boosts scores for official government sources:
  - DGFT (Directorate General of Foreign Trade)
  - FDA (Food and Drug Administration)
  - EU_RASFF (EU Rapid Alert System)
  - Customs_RMS (Risk Management System)
  - GSTN (GST Network)
  - RoDTEP (Remission of Duties and Taxes)
  - BIS, FSSAI, APEDA, EIC, Customs

### 5. Source Citation Extraction
- Extracts structured source information from documents
- Provides title, source, excerpt, relevance score
- Includes metadata (country, product category, last updated)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Query Embedding                                         │
│     ├─> EmbeddingService.embed_query()                     │
│     └─> Returns: np.ndarray (768-dim vector)               │
│                                                             │
│  2. Document Retrieval                                      │
│     ├─> VectorStore.search()                               │
│     ├─> Semantic similarity search                         │
│     └─> Returns: List[Document] with relevance scores      │
│                                                             │
│  3. Document Ranking                                        │
│     ├─> Sort by relevance score                            │
│     ├─> Apply government source boost                      │
│     ├─> Filter by relevance threshold                      │
│     └─> Returns: Ranked List[Document]                     │
│                                                             │
│  4. Context Building                                        │
│     ├─> Format documents with source citations             │
│     ├─> Respect max context length                         │
│     └─> Returns: Formatted context string                  │
│                                                             │
│  5. Prompt Enhancement                                      │
│     ├─> Inject context into user prompt                    │
│     └─> Returns: Enhanced prompt for LLM                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Basic Document Retrieval

```python
from services.rag_pipeline import RAGPipeline

# Initialize pipeline
pipeline = RAGPipeline()

# Retrieve relevant documents
documents = pipeline.retrieve_documents(
    query="What are FDA requirements for food exports?",
    top_k=5,
    prioritize_government=True
)

# Access results
for doc in documents:
    print(f"Source: {doc.metadata['source']}")
    print(f"Relevance: {doc.relevance_score:.3f}")
    print(f"Content: {doc.content[:200]}...")
```

### Filtered Retrieval

```python
# Retrieve documents with metadata filters
documents = pipeline.retrieve_documents(
    query="Agricultural export certifications",
    top_k=3,
    filters={
        "country": "India",
        "product_category": "agriculture"
    }
)
```

### Context Generation for LLM

```python
# Generate enhanced prompt with context
enhanced_prompt, source_docs = pipeline.generate_with_context(
    prompt="What documents do I need to export textiles?",
    top_k=3,
    include_sources=True,
    max_context_length=4000
)

# Now call LLM with enhanced prompt
# response = llm_client.generate(enhanced_prompt)
```

### Source Citation Extraction

```python
# Extract source citations for display
sources = pipeline.extract_sources(documents)

for source in sources:
    print(f"Title: {source['title']}")
    print(f"Source: {source['source']}")
    print(f"Relevance: {source['relevance_score']:.3f}")
    print(f"Excerpt: {source['excerpt']}")
```

## Configuration

### Pipeline Parameters

```python
pipeline = RAGPipeline(
    embedding_service=None,           # Uses global instance if None
    vector_store=None,                # Uses global instance if None
    default_top_k=5,                  # Default number of documents to retrieve
    relevance_threshold=0.3,          # Minimum relevance score (0-1)
    government_source_boost=0.1       # Score boost for government sources
)
```

### Retrieval Parameters

```python
documents = pipeline.retrieve_documents(
    query="Your query here",
    top_k=5,                          # Number of documents to retrieve
    filters={                         # Optional metadata filters
        "country": "US",
        "source": "FDA",
        "product_category": "food"
    },
    prioritize_government=True        # Enable government source boost
)
```

### Context Generation Parameters

```python
enhanced_prompt, sources = pipeline.generate_with_context(
    prompt="Your question here",
    query=None,                       # Optional separate query (uses prompt if None)
    documents=None,                   # Optional pre-retrieved documents
    top_k=5,                          # Number of documents to retrieve
    filters=None,                     # Optional metadata filters
    include_sources=True,             # Include source citations in context
    max_context_length=4000           # Maximum characters for context
)
```

## Government Source Prioritization

The pipeline automatically identifies and boosts government sources to ensure regulatory accuracy:

```python
# Government sources receive +0.1 boost to relevance score
# Example: Document with 0.75 score becomes 0.85 if from DGFT

# Without boost:
# 1. Blog (0.80)
# 2. DGFT (0.75)

# With boost:
# 1. DGFT (0.85)  <- Boosted from 0.75
# 2. Blog (0.80)
```

Recognized government sources:
- **DGFT**: Directorate General of Foreign Trade
- **FDA**: Food and Drug Administration
- **EU_RASFF**: EU Rapid Alert System for Food and Feed
- **Customs_RMS**: Customs Risk Management System
- **GSTN**: GST Network
- **RoDTEP**: Remission of Duties and Taxes on Exported Products
- **BIS**: Bureau of Indian Standards
- **FSSAI**: Food Safety and Standards Authority of India
- **APEDA**: Agricultural and Processed Food Products Export Development Authority
- **EIC**: Export Inspection Council
- **Customs**: Indian Customs

## Context Injection Format

The pipeline formats context for LLM prompts as follows:

```
Use the following context from regulatory documents to answer the question. 
If the context doesn't contain relevant information, say so.

Context:
[Document 1 - Source: DGFT]
DGFT regulations for agricultural exports...

[Document 2 - Source: FDA]
FDA requirements for food exports to US...

Question: What are the FDA requirements for food exports?

Answer based on the context provided above:
```

## Performance Considerations

### Retrieval Speed
- Query embedding: ~10-50ms
- Vector search: ~10-100ms (depends on index size)
- Total retrieval: ~50-200ms for typical queries

### Context Length Management
- Default max context: 4000 characters
- Automatically truncates documents to fit limit
- Prioritizes earlier documents (higher relevance)

### Caching
- Query embeddings are cached (LRU cache, size: 128)
- Repeated queries benefit from cache hits
- Clear cache with `embedding_service.clear_cache()`

## Error Handling

The pipeline handles various error conditions gracefully:

```python
# Empty query
docs = pipeline.retrieve_documents("")
# Returns: []

# No documents found
docs = pipeline.retrieve_documents("very specific query")
# Returns: [] if no documents above threshold

# All documents below threshold
docs = pipeline.retrieve_documents("irrelevant query")
# Returns: [] (filters out low-relevance documents)
```

## Integration with Other Services

### With Embedding Service
```python
from services.embeddings import get_embedding_service

embedding_service = get_embedding_service()
pipeline = RAGPipeline(embedding_service=embedding_service)
```

### With Vector Store
```python
from services.vector_store import get_vector_store

vector_store = get_vector_store()
vector_store.load("./data/faiss_index")
pipeline = RAGPipeline(vector_store=vector_store)
```

### With LLM Client (Future)
```python
# Generate context-enhanced prompt
enhanced_prompt, sources = pipeline.generate_with_context(
    prompt="What are FDA requirements?"
)

# Call LLM with enhanced prompt
response = llm_client.generate(
    prompt=enhanced_prompt,
    temperature=0.7,
    max_tokens=1000
)

# Display response with sources
print(response)
print("\nSources:")
for source in pipeline.extract_sources(sources):
    print(f"- {source['title']} ({source['source']})")
```

## Statistics and Monitoring

```python
# Get pipeline statistics
stats = pipeline.get_stats()

print(f"Configuration:")
print(f"  Default top_k: {stats['default_top_k']}")
print(f"  Relevance threshold: {stats['relevance_threshold']}")
print(f"  Government boost: {stats['government_source_boost']}")

print(f"\nVector Store:")
print(f"  Total documents: {stats['vector_store']['total_documents']}")
print(f"  Embedding dimension: {stats['vector_store']['embedding_dimension']}")

print(f"\nEmbedding Cache:")
print(f"  Hits: {stats['embedding_cache']['hits']}")
print(f"  Misses: {stats['embedding_cache']['misses']}")
print(f"  Hit rate: {stats['embedding_cache']['hits'] / (stats['embedding_cache']['hits'] + stats['embedding_cache']['misses']):.2%}")
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest backend/services/test_rag_pipeline.py -v

# Run specific test class
python -m pytest backend/services/test_rag_pipeline.py::TestDocumentRetrieval -v

# Run with coverage
python -m pytest backend/services/test_rag_pipeline.py --cov=services.rag_pipeline
```

Test coverage includes:
- Pipeline initialization
- Document retrieval with various parameters
- Document ranking and government source boost
- Context generation and injection
- Source citation extraction
- Edge cases and error handling

## Examples

See `example_rag_pipeline.py` for complete working examples:

```bash
# Run examples (requires loaded vector store)
python -m services.example_rag_pipeline
```

Examples demonstrate:
1. Basic document retrieval
2. Filtered retrieval with metadata
3. Context generation for LLM
4. Source citation extraction
5. Government source prioritization
6. Pipeline statistics

## Requirements Mapping

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| 10.2 | Query embedding and semantic search | `retrieve_documents()` with `embed_query()` and `vector_store.search()` |
| 10.3 | Document ranking by relevance | `_rank_documents()` with score-based sorting |
| 10.4 | Context injection for LLM prompts | `generate_with_context()` and `_inject_context()` |
| 10.6 | Government source prioritization | `_rank_documents()` with government source boost |

## Future Enhancements

Potential improvements for future iterations:

1. **Hybrid Search**: Combine semantic search with keyword search
2. **Re-ranking**: Use cross-encoder models for better ranking
3. **Query Expansion**: Automatically expand queries with synonyms
4. **Caching**: Cache retrieved documents for repeated queries
5. **Analytics**: Track query patterns and document usage
6. **A/B Testing**: Compare different retrieval strategies
7. **Feedback Loop**: Learn from user feedback on relevance

## Troubleshooting

### No documents retrieved
- Check if vector store is loaded: `vector_store.get_stats()`
- Verify query is not empty
- Lower relevance threshold: `relevance_threshold=0.1`
- Check metadata filters are correct

### Low relevance scores
- Verify embeddings are normalized
- Check if documents are properly indexed
- Try different query phrasing
- Increase `top_k` to see more results

### Context too long
- Reduce `max_context_length`
- Reduce `top_k` to retrieve fewer documents
- Documents will be automatically truncated

### Government sources not prioritized
- Verify `prioritize_government=True`
- Check document metadata has correct `source` field
- Verify source name matches government source list

## License

Part of the ExportSathi platform. See main project LICENSE for details.
