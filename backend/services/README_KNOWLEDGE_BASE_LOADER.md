# Knowledge Base Document Loader

## Overview

The Knowledge Base Document Loader is a complete pipeline for loading regulatory documents from S3, generating embeddings, and building a FAISS index for semantic search. This component is essential for the RAG (Retrieval-Augmented Generation) pipeline that powers ExportSathi's AI responses.

**Requirements Implemented:** 9.1, 9.2, 9.7

## Features

- **S3 Document Loading**: Downloads documents from S3 knowledge base bucket
- **Metadata Parsing**: Extracts and validates document metadata (source, country, product categories, certifications)
- **Embedding Generation**: Generates 768-dimensional embeddings using sentence-transformers
- **FAISS Index Building**: Creates searchable vector index for semantic similarity search
- **Index Persistence**: Saves index to local disk and optionally to S3
- **Batch Processing**: Efficient batch processing for large document collections

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Knowledge Base Loader                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. List Documents from S3                                   │
│     ├─ Paginate through S3 bucket                           │
│     └─ Filter out directories                               │
│                                                               │
│  2. Download & Parse Documents                               │
│     ├─ Download document content                            │
│     ├─ Get S3 metadata and tags                             │
│     ├─ Parse JSON/text files                                │
│     └─ Validate and set defaults                            │
│                                                               │
│  3. Generate Embeddings                                      │
│     ├─ Extract document content                             │
│     ├─ Batch process with EmbeddingService                  │
│     └─ Attach embeddings to documents                       │
│                                                               │
│  4. Build FAISS Index                                        │
│     ├─ Initialize FAISSVectorStore                          │
│     ├─ Add documents with embeddings                        │
│     ├─ Save index to disk                                   │
│     └─ Optionally upload to S3                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Document Format

### JSON Documents

JSON documents should have the following structure:

```json
{
  "content": "Document content text...",
  "metadata": {
    "source": "DGFT",
    "country": "IN",
    "product_category": "agriculture",
    "certifications": "APEDA,FSSAI,Phytosanitary",
    "last_updated": "2024-01-15"
  }
}
```

### Text Documents

Plain text documents (`.txt`, `.md`) use S3 metadata and tags for metadata:

- **S3 Object Metadata**: Set via `x-amz-meta-*` headers
- **S3 Object Tags**: Set via object tagging

### Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | No (default: "unknown") | Source type: DGFT, FDA, EU_RASFF, Customs_RMS, GSTN, RoDTEP |
| `country` | string | No (default: "unknown") | Country code: IN, US, EU, etc. |
| `product_category` | string | No (default: "general") | Product category: agriculture, food, manufacturing, etc. |
| `certifications` | string or list | No | Comma-separated list or array of related certifications |
| `last_updated` | string | No (auto-generated) | Last update date in ISO format |

## Usage

### Command Line

```bash
# Basic usage
python -m services.load_knowledge_base \
  --bucket exportsathi-knowledge-base \
  --output ./data/faiss_index

# With S3 prefix (folder)
python -m services.load_knowledge_base \
  --bucket exportsathi-knowledge-base \
  --prefix regulatory-docs/ \
  --output ./data/faiss_index

# With custom settings
python -m services.load_knowledge_base \
  --bucket exportsathi-knowledge-base \
  --output ./data/faiss_index \
  --embedding-dim 768 \
  --batch-size 32 \
  --verbose
```

### Python API

```python
from services.load_knowledge_base import KnowledgeBaseLoader

# Initialize loader
loader = KnowledgeBaseLoader(
    s3_bucket="exportsathi-knowledge-base",
    s3_prefix="regulatory-docs/",
    embedding_dimension=768,
    batch_size=32
)

# Run complete pipeline
loader.run(output_path="./data/faiss_index")

# Or run steps individually
documents = loader.load_documents()
documents = loader.generate_embeddings(documents)
loader.build_index(documents, "./data/faiss_index")
```

## Pipeline Steps

### 1. List Documents

Lists all documents in the S3 bucket, filtering out directories:

```python
documents = loader.list_documents()
# Returns: [{'key': 'doc1.json', 'size': 1024, 'last_modified': datetime}, ...]
```

### 2. Download Documents

Downloads document content from S3:

```python
content = loader.download_document("doc1.json")
# Returns: bytes
```

### 3. Get Metadata

Retrieves S3 object metadata and tags:

```python
metadata = loader.get_object_metadata("doc1.json")
# Returns: {'source': 'DGFT', 'country': 'IN', ...}
```

### 4. Parse Documents

Parses document content and metadata:

```python
document = loader.parse_document(s3_key, content, s3_metadata)
# Returns: Document(id=..., content=..., metadata=..., embedding=None)
```

Supported formats:
- **JSON** (`.json`): Parses `content` and `metadata` fields
- **Text** (`.txt`, `.md`): Uses content as-is with S3 metadata
- **Unsupported**: PDF, DOCX (returns None)

### 5. Generate Embeddings

Generates embeddings for all documents:

```python
documents = loader.generate_embeddings(documents)
# Adds 768-dimensional embedding to each document
```

Uses the `EmbeddingService` with `all-mpnet-base-v2` model.

### 6. Build Index

Builds FAISS index and saves to disk:

```python
loader.build_index(documents, "./data/faiss_index")
# Creates:
#   - ./data/faiss_index.index (FAISS index)
#   - ./data/faiss_index.metadata (document metadata)
```

## Testing

### Run Unit Tests

```bash
cd backend
python -m pytest services/test_load_knowledge_base.py -v
```

### Run Integration Test

```bash
cd backend
python -m services.test_knowledge_base_loader
```

The integration test:
1. Creates 5 sample documents
2. Generates embeddings
3. Builds FAISS index
4. Tests semantic search
5. Tests metadata filtering
6. Tests index persistence

## Example Output

```
2024-01-15 10:00:00 - INFO - Starting knowledge base loading pipeline...
2024-01-15 10:00:01 - INFO - Listing documents in s3://exportsathi-knowledge-base/
2024-01-15 10:00:02 - INFO - Found 50 documents in S3
2024-01-15 10:00:03 - INFO - Processing dgft_export_policy.json...
2024-01-15 10:00:03 - INFO - Loaded document: dgft_export_policy
...
2024-01-15 10:00:10 - INFO - Successfully loaded 50 documents
2024-01-15 10:00:11 - INFO - Generating embeddings for 50 documents...
2024-01-15 10:00:25 - INFO - Embeddings generated successfully
2024-01-15 10:00:26 - INFO - Building FAISS index...
2024-01-15 10:00:27 - INFO - Added 50 documents to vector store
2024-01-15 10:00:27 - INFO - Saving index to ./data/faiss_index...
2024-01-15 10:00:28 - INFO - Index statistics: {'total_documents': 50, 'embedding_dimension': 768, 'index_type': 'Flat', 'index_size': 50}
2024-01-15 10:00:28 - INFO - Knowledge base loading completed in 28.45 seconds
```

## Performance

- **Embedding Generation**: ~100-200 documents/minute (CPU)
- **Index Building**: Near-instant for <10K documents
- **Search Latency**: <10ms for exact search, <2ms for approximate search

## Error Handling

The loader handles various error conditions:

- **S3 Access Errors**: Logs error and raises exception
- **Invalid Documents**: Skips and logs warning
- **Empty Content**: Skips and logs warning
- **Unsupported Formats**: Skips and logs warning
- **Missing Metadata**: Uses default values

## S3 Bucket Structure

Recommended S3 bucket structure:

```
exportsathi-knowledge-base/
├── dgft/
│   ├── export_policy_agriculture.json
│   ├── export_policy_textiles.json
│   └── rodtep_schedules.json
├── fda/
│   ├── food_requirements.json
│   ├── refusal_database.json
│   └── labeling_requirements.json
├── eu/
│   ├── ce_marking.json
│   ├── reach_regulations.json
│   └── rasff_alerts.json
└── customs/
    ├── rms_rules.json
    └── hs_code_classification.json
```

## Integration with RAG Pipeline

The knowledge base loader creates the foundation for the RAG pipeline:

```python
from services.embeddings import get_embedding_service
from services.vector_store import FAISSVectorStore

# Load pre-built index
vector_store = FAISSVectorStore(embedding_dimension=768)
vector_store.load("./data/faiss_index")

# Generate query embedding
embedding_service = get_embedding_service()
query_embedding = embedding_service.embed_query("What are FDA requirements?")

# Search for relevant documents
results = vector_store.search(query_embedding, top_k=5)

# Use results as context for LLM
for doc in results:
    print(f"Document: {doc.id}")
    print(f"Relevance: {doc.relevance_score:.4f}")
    print(f"Content: {doc.content[:200]}...")
```

## Maintenance

### Updating the Knowledge Base

To update the knowledge base with new documents:

1. Upload new documents to S3 bucket
2. Re-run the loader to rebuild the index
3. Deploy updated index to production

```bash
# Upload new documents
aws s3 cp new_documents/ s3://exportsathi-knowledge-base/ --recursive

# Rebuild index
python -m services.load_knowledge_base \
  --bucket exportsathi-knowledge-base \
  --output ./data/faiss_index

# Deploy to production
aws s3 cp ./data/faiss_index.index s3://exportsathi-production/vector_store/
aws s3 cp ./data/faiss_index.metadata s3://exportsathi-production/vector_store/
```

### Monitoring

Key metrics to monitor:

- **Document Count**: Total documents in index
- **Index Size**: Disk space used by index
- **Search Latency**: Time to retrieve documents
- **Embedding Quality**: Relevance scores for test queries

## Troubleshooting

### Issue: "No documents found in S3 bucket"

**Solution**: Check S3 bucket name and prefix, verify AWS credentials

### Issue: "Unsupported file type"

**Solution**: Convert documents to JSON or TXT format

### Issue: "Empty content for document"

**Solution**: Verify document has non-empty content field

### Issue: "Embedding dimension mismatch"

**Solution**: Ensure all embeddings use the same model (all-mpnet-base-v2 = 768 dim)

## Requirements Validation

✅ **Requirement 9.1**: Documents loaded from S3 with metadata parsing  
✅ **Requirement 9.2**: Embeddings generated and stored in vector store  
✅ **Requirement 9.7**: Documents tagged with metadata (source, country, product category, certifications)

## Related Components

- **EmbeddingService** (`services/embeddings.py`): Generates embeddings
- **FAISSVectorStore** (`services/vector_store.py`): Stores and searches embeddings
- **RAGPipeline** (`services/rag_pipeline.py`): Uses knowledge base for retrieval
- **Document Model** (`models/internal.py`): Document data structure

## Future Enhancements

- [ ] Support for PDF document parsing
- [ ] Incremental index updates (add new documents without full rebuild)
- [ ] Document versioning and change tracking
- [ ] Automatic metadata extraction from document content
- [ ] Multi-language support
- [ ] Document deduplication
