"""
Chat and conversation data models.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from .enums import MessageRole
from .common import Source


class QueryContext(BaseModel):
    """Context for chat conversation."""
    report_id: str = Field(..., description="Associated report ID")
    product_type: str = Field(..., description="Product type")
    destination_country: str = Field(..., description="Destination country")

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "rpt_123e4567",
                "product_type": "Turmeric powder",
                "destination_country": "United States"
            }
        }


class ChatMessage(BaseModel):
    """Chat message in a conversation."""
    message_id: str = Field(..., description="Unique message identifier")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., min_length=1, description="Message content")
    sources: Optional[List[Source]] = Field(None, description="Source citations")
    timestamp: datetime = Field(..., description="Message timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_123e4567",
                "role": "assistant",
                "content": "FDA registration is required for food facilities...",
                "sources": [
                    {
                        "title": "FDA Food Facility Registration",
                        "source": "FDA",
                        "url": "https://fda.gov/registration"
                    }
                ],
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    session_id: str = Field(..., description="Chat session ID")
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    context: QueryContext = Field(..., description="Conversation context")

    @field_validator('question')
    @classmethod
    def validate_question_not_empty(cls, v: str) -> str:
        """Validate question is not empty after stripping."""
        if not v.strip():
            raise ValueError('Question cannot be empty or whitespace only')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_123e4567",
                "question": "What documents do I need for FDA registration?",
                "context": {
                    "report_id": "rpt_123e4567",
                    "product_type": "Turmeric powder",
                    "destination_country": "United States"
                }
            }
        }


class ChatResponse(BaseModel):
    """Response to a chat message."""
    message_id: str = Field(..., description="Unique message identifier")
    answer: str = Field(..., description="Assistant's answer")
    sources: List[Source] = Field(default_factory=list, description="Source citations")
    timestamp: datetime = Field(..., description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_123e4567",
                "answer": "For FDA registration, you need: 1) Company registration certificate...",
                "sources": [
                    {
                        "title": "FDA Registration Requirements",
                        "source": "FDA",
                        "url": "https://fda.gov/requirements"
                    }
                ],
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class ChatSession(BaseModel):
    """Chat session with conversation history."""
    session_id: str = Field(..., description="Unique session identifier")
    messages: List[ChatMessage] = Field(default_factory=list, description="Conversation messages")
    context: QueryContext = Field(..., description="Session context")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_123e4567",
                "messages": [],
                "context": {
                    "report_id": "rpt_123e4567",
                    "product_type": "Turmeric powder",
                    "destination_country": "United States"
                },
                "created_at": "2024-01-15T10:00:00Z",
                "last_activity": "2024-01-15T10:30:00Z"
            }
        }
