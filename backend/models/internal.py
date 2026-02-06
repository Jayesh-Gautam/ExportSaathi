"""
Internal data models for backend services.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Document(BaseModel):
    """Internal model for retrieved documents from vector store."""
    id: str = Field(..., description="Document identifier")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    embedding: Optional[List[float]] = Field(None, description="Document embedding vector")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_dgft_001",
                "content": "Export policy for agricultural products...",
                "metadata": {
                    "source": "DGFT",
                    "country": "India",
                    "category": "agriculture",
                    "last_updated": "2024-01-01"
                },
                "embedding": None,
                "relevance_score": 0.95
            }
        }


class EmbeddingRequest(BaseModel):
    """Request to generate embeddings."""
    texts: List[str] = Field(..., min_items=1, description="Texts to embed")
    batch_size: int = Field(default=32, gt=0, description="Batch size for processing")

    class Config:
        json_schema_extra = {
            "example": {
                "texts": [
                    "What are the FDA requirements for food exports?",
                    "How to obtain CE certification?"
                ],
                "batch_size": 32
            }
        }


class EmbeddingResponse(BaseModel):
    """Response with generated embeddings."""
    embeddings: List[List[float]] = Field(..., description="Generated embedding vectors")
    model: str = Field(..., description="Model used for embedding")
    dimension: int = Field(..., gt=0, description="Embedding dimension")

    class Config:
        json_schema_extra = {
            "example": {
                "embeddings": [[0.1, 0.2, 0.3]],
                "model": "all-mpnet-base-v2",
                "dimension": 768
            }
        }


class VectorSearchRequest(BaseModel):
    """Request for vector similarity search."""
    query_embedding: List[float] = Field(..., description="Query embedding vector")
    top_k: int = Field(default=5, gt=0, le=50, description="Number of results to return")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Metadata filters")

    class Config:
        json_schema_extra = {
            "example": {
                "query_embedding": [0.1, 0.2, 0.3],
                "top_k": 5,
                "filters": {
                    "source": "DGFT",
                    "country": "India"
                }
            }
        }


class VectorSearchResponse(BaseModel):
    """Response from vector similarity search."""
    documents: List[Document] = Field(..., description="Retrieved documents")
    query_time_ms: float = Field(..., ge=0, description="Query execution time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "documents": [],
                "query_time_ms": 45.2
            }
        }


class LLMRequest(BaseModel):
    """Request to LLM service."""
    prompt: str = Field(..., min_length=1, description="Prompt for LLM")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
    model: str = Field(default="claude-3-sonnet", description="Model to use")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "What are the FDA requirements for food exports?",
                "system_prompt": "You are an export compliance expert.",
                "temperature": 0.7,
                "max_tokens": 1000,
                "model": "claude-3-sonnet"
            }
        }


class LLMResponse(BaseModel):
    """Response from LLM service."""
    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., ge=0, description="Tokens used")
    finish_reason: str = Field(..., description="Reason for completion")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "FDA requires food facility registration...",
                "model": "claude-3-sonnet",
                "tokens_used": 250,
                "finish_reason": "stop"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    code: str = Field(..., description="Error code")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "detail": "Product name is required",
                "code": "INVALID_INPUT"
            }
        }
