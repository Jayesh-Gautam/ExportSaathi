"""
Chat Service for ExportSathi

This service manages interactive Q&A conversations with context preservation.
It retrieves conversation history, maintains query context, uses RAG pipeline
for document retrieval, generates responses with source citations, and stores
messages in the database.

Requirements: 7.2, 7.3, 7.4, 7.7
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from backend.database.models import ChatSession, ChatMessage, Report
from backend.services.rag_pipeline import RAGPipeline, get_rag_pipeline
from backend.services.llm_client import create_llm_client
from backend.services.prompt_templates import EXPORTSATHI_MASTER_PROMPT

logger = logging.getLogger(__name__)


class ChatService:
    """
    Manages chat conversations with context preservation.
    
    Features:
    - Session-based conversation management
    - Context preservation (product, destination, report ID)
    - RAG-based document retrieval for questions
    - LLM response generation with source citations
    - Message storage in database
    
    Requirements: 7.2, 7.3, 7.4, 7.7
    """
    
    def __init__(
        self,
        rag_pipeline: Optional[RAGPipeline] = None,
        session_timeout_hours: int = 24
    ):
        """
        Initialize the chat service.
        
        Args:
            rag_pipeline: RAG pipeline for document retrieval (uses global if None)
            session_timeout_hours: Hours before session expires
        """
        self.rag_pipeline = rag_pipeline or get_rag_pipeline()
        self.llm_client = create_llm_client()
        self.session_timeout_hours = session_timeout_hours
        
        logger.info(
            f"ChatService initialized with session_timeout={session_timeout_hours}h"
        )
    
    def process_question(
        self,
        question: str,
        session_id: UUID,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process a chat question with context and generate response.
        
        This method:
        1. Retrieves conversation history from database
        2. Retrieves session context (product type, destination, report ID)
        3. Uses RAG pipeline to retrieve relevant documents
        4. Generates response with LLM using context and history
        5. Extracts source citations from retrieved documents
        6. Stores user question and assistant response in database
        
        Args:
            question: User's question
            session_id: Chat session ID
            db: Database session
            
        Returns:
            Dictionary containing:
                - response: Generated answer text
                - sources: List of source citations
                - session_id: Session ID
                - message_id: ID of the assistant's message
                
        Raises:
            ValueError: If session not found or question is empty
            
        Example:
            >>> chat_service = ChatService()
            >>> result = chat_service.process_question(
            ...     question="What are the FDA requirements?",
            ...     session_id=session_id,
            ...     db=db_session
            ... )
            >>> print(result['response'])
            >>> for source in result['sources']:
            ...     print(f"- {source['title']}")
        
        Requirements: 7.2, 7.3, 7.4, 7.7
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        logger.info(f"Processing question for session {session_id}: '{question[:100]}...'")
        
        try:
            # Step 1: Retrieve session and validate
            session = self._get_session(session_id, db)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Check if session has expired
            if session.expires_at and session.expires_at < datetime.utcnow():
                raise ValueError(f"Session {session_id} has expired")
            
            # Step 2: Retrieve conversation history
            history = self._get_history_messages(session_id, db)
            logger.info(f"Retrieved {len(history)} messages from history")
            
            # Step 3: Get session context
            context = self._get_session_context(session, db)
            logger.info(f"Session context: {context}")
            
            # Step 4: Build query with context for document retrieval
            contextual_query = self._build_contextual_query(question, context)
            
            # Step 5: Retrieve relevant documents using RAG pipeline
            filters = self._build_retrieval_filters(context)
            retrieved_docs = self.rag_pipeline.retrieve_documents(
                query=contextual_query,
                top_k=5,
                filters=filters,
                prioritize_government=True
            )
            
            logger.info(f"Retrieved {len(retrieved_docs)} documents for question")
            
            # Step 6: Build prompt with context, history, and retrieved documents
            prompt = self._build_chat_prompt(
                question=question,
                context=context,
                history=history,
                retrieved_docs=retrieved_docs
            )
            
            # Step 7: Generate response using LLM
            response_text = self.llm_client.generate(
                prompt=prompt,
                system_prompt=EXPORTSATHI_MASTER_PROMPT,
                temperature=0.7,
                max_tokens=2048
            )
            
            logger.info(f"Generated response with {len(response_text)} characters")
            
            # Step 8: Extract source citations
            sources = self.rag_pipeline.extract_sources(retrieved_docs)
            
            # Step 9: Store user question in database
            user_message = ChatMessage(
                id=uuid4(),
                session_id=session_id,
                role='user',
                content=question,
                sources=None,
                created_at=datetime.utcnow()
            )
            db.add(user_message)
            
            # Step 10: Store assistant response in database
            assistant_message = ChatMessage(
                id=uuid4(),
                session_id=session_id,
                role='assistant',
                content=response_text,
                sources=sources,
                created_at=datetime.utcnow()
            )
            db.add(assistant_message)
            
            # Step 11: Update session last activity
            session.last_activity = datetime.utcnow()
            
            # Commit all changes
            db.commit()
            
            logger.info(
                f"Successfully processed question and stored messages "
                f"(user: {user_message.id}, assistant: {assistant_message.id})"
            )
            
            return {
                'response': response_text,
                'sources': sources,
                'session_id': str(session_id),
                'message_id': str(assistant_message.id)
            }
        
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            db.rollback()
            raise
    
    def get_history(
        self,
        session_id: UUID,
        db: Session,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Chat session ID
            db: Database session
            limit: Maximum number of messages to retrieve (None for all)
            
        Returns:
            List of message dictionaries with role, content, sources, timestamp
            
        Example:
            >>> history = chat_service.get_history(session_id, db, limit=10)
            >>> for msg in history:
            ...     print(f"{msg['role']}: {msg['content'][:50]}...")
        
        Requirements: 7.3, 7.4
        """
        logger.info(f"Retrieving history for session {session_id}")
        
        try:
            messages = self._get_history_messages(session_id, db, limit)
            
            history = [
                {
                    'id': str(msg.id),
                    'role': msg.role,
                    'content': msg.content,
                    'sources': msg.sources,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
            
            logger.info(f"Retrieved {len(history)} messages")
            return history
        
        except Exception as e:
            logger.error(f"Error retrieving history: {e}", exc_info=True)
            raise
    
    def create_session(
        self,
        user_id: UUID,
        report_id: UUID,
        context: Dict[str, Any],
        db: Session
    ) -> UUID:
        """
        Create a new chat session with context.
        
        Args:
            user_id: User ID
            report_id: Associated report ID
            context: Session context (product, destination, etc.)
            db: Database session
            
        Returns:
            New session ID
            
        Example:
            >>> context = {
            ...     'product_type': 'LED Lights',
            ...     'destination': 'United States',
            ...     'hs_code': '8539.50.00'
            ... }
            >>> session_id = chat_service.create_session(
            ...     user_id=user_id,
            ...     report_id=report_id,
            ...     context=context,
            ...     db=db
            ... )
        
        Requirements: 7.2, 7.3
        """
        logger.info(f"Creating new chat session for user {user_id}, report {report_id}")
        
        try:
            session_id = uuid4()
            expires_at = datetime.utcnow() + timedelta(hours=self.session_timeout_hours)
            
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                report_id=report_id,
                context_data=context,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                expires_at=expires_at
            )
            
            db.add(session)
            db.commit()
            
            logger.info(f"Created session {session_id}, expires at {expires_at}")
            return session_id
        
        except Exception as e:
            logger.error(f"Error creating session: {e}", exc_info=True)
            db.rollback()
            raise
    
    def clear_session(
        self,
        session_id: UUID,
        db: Session
    ) -> None:
        """
        Clear conversation history for a session.
        
        This deletes all messages but keeps the session active.
        
        Args:
            session_id: Chat session ID
            db: Database session
            
        Example:
            >>> chat_service.clear_session(session_id, db)
        
        Requirements: 7.5
        """
        logger.info(f"Clearing history for session {session_id}")
        
        try:
            # Delete all messages for this session
            deleted_count = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleared {deleted_count} messages from session {session_id}")
        
        except Exception as e:
            logger.error(f"Error clearing session: {e}", exc_info=True)
            db.rollback()
            raise
    
    def delete_session(
        self,
        session_id: UUID,
        db: Session
    ) -> None:
        """
        Delete a chat session and all its messages.
        
        Args:
            session_id: Chat session ID
            db: Database session
            
        Example:
            >>> chat_service.delete_session(session_id, db)
        """
        logger.info(f"Deleting session {session_id}")
        
        try:
            # Delete session (messages will cascade delete)
            deleted_count = db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).delete()
            
            db.commit()
            
            if deleted_count > 0:
                logger.info(f"Deleted session {session_id}")
            else:
                logger.warning(f"Session {session_id} not found")
        
        except Exception as e:
            logger.error(f"Error deleting session: {e}", exc_info=True)
            db.rollback()
            raise
    
    # Private helper methods
    
    def _get_session(
        self,
        session_id: UUID,
        db: Session
    ) -> Optional[ChatSession]:
        """Retrieve session from database."""
        return db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
    
    def _get_history_messages(
        self,
        session_id: UUID,
        db: Session,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Retrieve message history from database."""
        query = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc())
        
        if limit:
            # Get the most recent N messages
            query = query.limit(limit)
        
        return query.all()
    
    def _get_session_context(
        self,
        session: ChatSession,
        db: Session
    ) -> Dict[str, Any]:
        """
        Extract session context including report details.
        
        Requirements: 7.2, 7.3
        """
        context = session.context_data or {}
        
        # Enrich context with report details if available
        if session.report_id:
            report = db.query(Report).filter(
                Report.id == session.report_id
            ).first()
            
            if report:
                context['product_type'] = report.product_name
                context['destination'] = report.destination_country
                context['business_type'] = report.business_type
                
                # Add HS code if available in report data
                if report.report_data and 'hs_code' in report.report_data:
                    context['hs_code'] = report.report_data['hs_code'].get('code')
        
        return context
    
    def _build_contextual_query(
        self,
        question: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Build a contextual query for document retrieval.
        
        Enhances the user's question with context information to improve
        document retrieval relevance.
        
        Requirements: 7.2, 7.3
        """
        # Extract key context elements
        product = context.get('product_type', '')
        destination = context.get('destination', '')
        hs_code = context.get('hs_code', '')
        
        # Build contextual query
        context_parts = []
        if product:
            context_parts.append(f"Product: {product}")
        if destination:
            context_parts.append(f"Destination: {destination}")
        if hs_code:
            context_parts.append(f"HS Code: {hs_code}")
        
        if context_parts:
            contextual_query = f"{' | '.join(context_parts)} | Question: {question}"
        else:
            contextual_query = question
        
        return contextual_query
    
    def _build_retrieval_filters(
        self,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Build metadata filters for document retrieval.
        
        Requirements: 7.2
        """
        filters = {}
        
        # Add destination country filter if available
        if 'destination' in context:
            filters['country'] = context['destination']
        
        # Add product category filter if available
        if 'product_category' in context:
            filters['product_category'] = context['product_category']
        
        return filters if filters else None
    
    def _build_chat_prompt(
        self,
        question: str,
        context: Dict[str, Any],
        history: List[ChatMessage],
        retrieved_docs: List[Any]
    ) -> str:
        """
        Build comprehensive prompt for chat response generation.
        
        Includes:
        - Session context (product, destination, etc.)
        - Conversation history
        - Retrieved regulatory documents
        - User's current question
        
        Requirements: 7.2, 7.3, 7.4, 7.7
        """
        # Build context section
        context_text = self._format_context(context)
        
        # Build history section (last 5 exchanges to keep prompt manageable)
        history_text = self._format_history(history[-10:] if len(history) > 10 else history)
        
        # Build retrieved documents section
        docs_text = self._format_retrieved_docs(retrieved_docs)
        
        # Construct full prompt
        prompt = f"""You are answering a follow-up question in an ongoing conversation about export requirements.

**Session Context:**
{context_text}

**Conversation History:**
{history_text}

**Relevant Regulatory Documents:**
{docs_text}

**Current Question:**
{question}

**Instructions:**
1. Answer the question based on the regulatory documents provided
2. Maintain context from the conversation history
3. Be specific and actionable
4. Cite sources when providing regulatory information
5. If the documents don't contain relevant information, say so clearly
6. Keep the response focused on the user's question

**Important:**
- Provide source citations from the regulatory documents
- Be concise but comprehensive
- Use the conversation context to provide relevant answers
- If clarification is needed, ask specific questions

Answer:"""
        
        return prompt
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format session context for prompt."""
        if not context:
            return "No specific context available."
        
        lines = []
        if 'product_type' in context:
            lines.append(f"- Product: {context['product_type']}")
        if 'destination' in context:
            lines.append(f"- Destination: {context['destination']}")
        if 'hs_code' in context:
            lines.append(f"- HS Code: {context['hs_code']}")
        if 'business_type' in context:
            lines.append(f"- Business Type: {context['business_type']}")
        
        return "\n".join(lines) if lines else "No specific context available."
    
    def _format_history(self, messages: List[ChatMessage]) -> str:
        """Format conversation history for prompt."""
        if not messages:
            return "No previous conversation."
        
        history_lines = []
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            # Truncate long messages
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            history_lines.append(f"{role}: {content}")
        
        return "\n".join(history_lines)
    
    def _format_retrieved_docs(self, docs: List[Any]) -> str:
        """Format retrieved documents for prompt."""
        if not docs:
            return "No relevant documents found."
        
        doc_lines = []
        for i, doc in enumerate(docs[:5], 1):  # Limit to top 5 documents
            source = doc.metadata.get('source', 'Unknown')
            # Truncate long content
            content = doc.content[:500] + "..." if len(doc.content) > 500 else doc.content
            doc_lines.append(f"[Document {i} - Source: {source}]\n{content}\n")
        
        return "\n".join(doc_lines)


# Global singleton instance
_chat_service: Optional[ChatService] = None


def get_chat_service(
    rag_pipeline: Optional[RAGPipeline] = None,
    session_timeout_hours: int = 24
) -> ChatService:
    """
    Get the global chat service instance.
    
    Returns:
        Global ChatService instance
    """
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(
            rag_pipeline=rag_pipeline,
            session_timeout_hours=session_timeout_hours
        )
    return _chat_service
