"""
Chat API Router
Handles interactive Q&A with context

This router implements the chat endpoints for the ExportSathi platform:
1. POST /api/chat - Submit chat question with context
2. GET /api/chat/{session_id}/history - Retrieve conversation history
3. DELETE /api/chat/{session_id} - Clear conversation history

Requirements: 8.1
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
import logging
import uuid
from datetime import datetime

from models import ChatRequest, ChatResponse, ChatMessage, MessageRole
from models.common import Source
from services.chat_service import ChatService, get_chat_service
from database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


def get_chat_service_dependency() -> ChatService:
    """
    Dependency function to get ChatService instance.
    
    Returns:
        ChatService instance
    """
    return get_chat_service()


def parse_session_id(session_id: str) -> uuid.UUID:
    """
    Parse session ID string to UUID.
    
    Handles both UUID format and hex string format (with or without sess_ prefix).
    
    Args:
        session_id: Session ID string (e.g., "sess_abc123..." or "abc123...")
        
    Returns:
        UUID object
        
    Raises:
        HTTPException: If session ID format is invalid
    """
    # Remove sess_ prefix if present
    clean_id = session_id.replace("sess_", "")
    
    # Try to parse as UUID - if it fails, it might be a hex string without dashes
    try:
        # First try direct UUID parsing
        return uuid.UUID(clean_id)
    except ValueError:
        # Try adding dashes if it's a 32-character hex string
        if len(clean_id) == 32 and all(c in '0123456789abcdefABCDEF' for c in clean_id):
            try:
                # Format as UUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                formatted = f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"
                return uuid.UUID(formatted)
            except ValueError:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def submit_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    Submit chat question with context and receive AI-generated response.
    
    This endpoint processes user questions in the context of their export readiness
    report, retrieves relevant regulatory documents, and generates responses with
    source citations.
    
    **Request Body:**
    - session_id: Chat session identifier (format: sess_xxxxxxxxxxxx)
    - question: User's question (1-1000 characters)
    - context: Session context with report_id, product_type, destination_country
    
    **Returns:**
    - ChatResponse with message_id, answer, sources, and timestamp
    
    **Features:**
    - Maintains conversation history across multiple questions
    - Retrieves relevant regulatory documents using RAG pipeline
    - Generates responses grounded in retrieved documents
    - Provides source citations for regulatory information
    - Stores messages in database for history retrieval
    
    **Errors:**
    - 400: Invalid session ID format or empty question
    - 404: Session not found or expired
    - 422: Validation error
    - 500: Internal server error during processing
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Processing chat question for session: {request.session_id}")
        
        # Parse session ID
        session_uuid = parse_session_id(request.session_id)
        
        # Process question using ChatService
        result = chat_service.process_question(
            question=request.question,
            session_id=session_uuid,
            db=db
        )
        
        # Convert sources to Source model
        sources = []
        if result.get('sources'):
            for source in result['sources']:
                sources.append(Source(
                    title=source.get('title', 'Unknown'),
                    source=source.get('source', 'Unknown'),
                    url=source.get('url')
                ))
        
        # Create response
        response = ChatResponse(
            message_id=result['message_id'],
            answer=result['response'],
            sources=sources,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Chat question processed successfully: {response.message_id}")
        return response
    
    except ValueError as e:
        # Session not found or validation errors
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() or "expired" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error processing chat question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your question. Please try again later."
        )


@router.get("/{session_id}/history", response_model=List[ChatMessage])
async def get_chat_history(
    session_id: str,
    limit: int = None,
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    Retrieve conversation history for a chat session.
    
    This endpoint returns all messages (user questions and assistant responses)
    for a given chat session, ordered chronologically.
    
    **Path Parameters:**
    - session_id: Chat session identifier (format: sess_xxxxxxxxxxxx)
    
    **Query Parameters:**
    - limit: Maximum number of messages to retrieve (optional, default: all)
    
    **Returns:**
    - List of ChatMessage objects with message_id, role, content, sources, timestamp
    
    **Features:**
    - Returns complete conversation history
    - Includes source citations for assistant responses
    - Ordered chronologically (oldest to newest)
    - Supports pagination with limit parameter
    
    **Errors:**
    - 400: Invalid session ID format
    - 404: Session not found
    - 500: Internal server error
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Retrieving chat history for session: {session_id}")
        
        # Parse session ID
        session_uuid = parse_session_id(session_id)
        
        # Retrieve history using ChatService
        history = chat_service.get_history(
            session_id=session_uuid,
            db=db,
            limit=limit
        )
        
        # Convert to ChatMessage models
        messages = []
        for msg in history:
            # Convert sources to Source model
            sources = None
            if msg.get('sources'):
                sources = [
                    Source(
                        title=source.get('title', 'Unknown'),
                        source=source.get('source', 'Unknown'),
                        url=source.get('url')
                    )
                    for source in msg['sources']
                ]
            
            messages.append(ChatMessage(
                message_id=msg['id'],
                role=MessageRole(msg['role']),
                content=msg['content'],
                sources=sources,
                timestamp=datetime.fromisoformat(msg['created_at']) if msg.get('created_at') else datetime.utcnow()
            ))
        
        logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
        return messages
    
    except ValueError as e:
        # Session not found
        logger.error(f"Session not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error retrieving chat history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving chat history."
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_session(
    session_id: str,
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    Clear conversation history for a chat session.
    
    This endpoint deletes all messages in a chat session while keeping the
    session active. Users can continue asking questions after clearing history.
    
    **Path Parameters:**
    - session_id: Chat session identifier (format: sess_xxxxxxxxxxxx)
    
    **Returns:**
    - 204 No Content on success
    
    **Features:**
    - Deletes all messages in the session
    - Keeps session active for new questions
    - Preserves session context (product, destination, report)
    
    **Errors:**
    - 400: Invalid session ID format
    - 404: Session not found
    - 500: Internal server error
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Clearing history for session: {session_id}")
        
        # Parse session ID
        session_uuid = parse_session_id(session_id)
        
        # Clear session using ChatService
        chat_service.clear_session(
            session_id=session_uuid,
            db=db
        )
        
        logger.info(f"Session history cleared successfully: {session_id}")
        return None  # 204 No Content
    
    except ValueError as e:
        # Session not found
        logger.error(f"Session not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error clearing session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while clearing the session."
        )
