"""
Tests for ChatService

Tests the chat service functionality including:
- Session creation and management
- Question processing with context
- Conversation history retrieval
- Message storage
- Context preservation
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from backend.services.chat_service import ChatService, get_chat_service
from backend.database.models import ChatSession, ChatMessage, Report
from models.internal import Document


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def mock_rag_pipeline():
    """Create a mock RAG pipeline."""
    pipeline = Mock()
    
    # Mock retrieve_documents to return sample documents
    doc1 = Document(
        id="doc1",
        content="FDA requires food products to be registered with the FDA.",
        metadata={
            'source': 'FDA',
            'country': 'US',
            'title': 'FDA Food Registration Requirements'
        },
        relevance_score=0.9
    )
    doc2 = Document(
        id="doc2",
        content="All food exports must comply with FSSAI standards.",
        metadata={
            'source': 'FSSAI',
            'country': 'India',
            'title': 'FSSAI Export Standards'
        },
        relevance_score=0.85
    )
    
    pipeline.retrieve_documents = Mock(return_value=[doc1, doc2])
    pipeline.extract_sources = Mock(return_value=[
        {
            'id': 'doc1',
            'title': 'FDA Food Registration Requirements',
            'source': 'FDA',
            'excerpt': 'FDA requires food products to be registered...',
            'relevance_score': 0.9,
            'metadata': {'country': 'US'}
        },
        {
            'id': 'doc2',
            'title': 'FSSAI Export Standards',
            'source': 'FSSAI',
            'excerpt': 'All food exports must comply with FSSAI...',
            'relevance_score': 0.85,
            'metadata': {'country': 'India'}
        }
    ])
    
    return pipeline


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = Mock()
    client.generate = Mock(return_value="Based on FDA regulations, you need to register your food product with the FDA before exporting to the United States. This involves submitting Form FDA 2541 and paying the registration fee.")
    return client


@pytest.fixture
def chat_service(mock_rag_pipeline, mock_llm_client):
    """Create a ChatService instance with mocked dependencies."""
    with patch('backend.services.chat_service.create_llm_client', return_value=mock_llm_client):
        service = ChatService(rag_pipeline=mock_rag_pipeline)
        return service


@pytest.fixture
def sample_session():
    """Create a sample chat session."""
    session_id = uuid4()
    user_id = uuid4()
    report_id = uuid4()
    
    session = ChatSession(
        id=session_id,
        user_id=user_id,
        report_id=report_id,
        context_data={
            'product_type': 'Organic Tea',
            'destination': 'United States',
            'hs_code': '0902.10.00',
            'business_type': 'Manufacturing'
        },
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    return session


@pytest.fixture
def sample_report():
    """Create a sample report."""
    report_id = uuid4()
    
    report = Report(
        id=report_id,
        product_name='Organic Tea',
        destination_country='United States',
        business_type='Manufacturing',
        report_data={
            'hs_code': {
                'code': '0902.10.00',
                'confidence': 95
            }
        }
    )
    
    return report


class TestChatServiceCreation:
    """Test chat service initialization."""
    
    def test_chat_service_initialization(self, mock_rag_pipeline):
        """Test that ChatService initializes correctly."""
        with patch('backend.services.chat_service.create_llm_client'):
            service = ChatService(rag_pipeline=mock_rag_pipeline)
            
            assert service.rag_pipeline == mock_rag_pipeline
            assert service.session_timeout_hours == 24
    
    def test_get_chat_service_singleton(self):
        """Test that get_chat_service returns a singleton instance."""
        with patch('backend.services.chat_service.create_llm_client'):
            service1 = get_chat_service()
            service2 = get_chat_service()
            
            assert service1 is service2


class TestSessionManagement:
    """Test session creation and management."""
    
    def test_create_session(self, chat_service, mock_db):
        """Test creating a new chat session."""
        user_id = uuid4()
        report_id = uuid4()
        context = {
            'product_type': 'LED Lights',
            'destination': 'Germany',
            'hs_code': '8539.50.00'
        }
        
        session_id = chat_service.create_session(
            user_id=user_id,
            report_id=report_id,
            context=context,
            db=mock_db
        )
        
        # Verify session was created
        assert session_id is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the session object
        added_session = mock_db.add.call_args[0][0]
        assert isinstance(added_session, ChatSession)
        assert added_session.user_id == user_id
        assert added_session.report_id == report_id
        assert added_session.context_data == context
    
    def test_clear_session(self, chat_service, mock_db):
        """Test clearing conversation history."""
        session_id = uuid4()
        
        # Mock the query to return a delete count
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.delete = Mock(return_value=3)
        mock_db.query = Mock(return_value=mock_query)
        
        chat_service.clear_session(session_id, mock_db)
        
        # Verify messages were deleted
        mock_db.query.assert_called_once_with(ChatMessage)
        mock_query.delete.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_delete_session(self, chat_service, mock_db):
        """Test deleting a chat session."""
        session_id = uuid4()
        
        # Mock the query to return a delete count
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.delete = Mock(return_value=1)
        mock_db.query = Mock(return_value=mock_query)
        
        chat_service.delete_session(session_id, mock_db)
        
        # Verify session was deleted
        mock_db.query.assert_called_once_with(ChatSession)
        mock_query.delete.assert_called_once()
        mock_db.commit.assert_called_once()


class TestQuestionProcessing:
    """Test question processing with context."""
    
    def test_process_question_success(
        self,
        chat_service,
        mock_db,
        sample_session,
        sample_report
    ):
        """Test successfully processing a question."""
        question = "What are the FDA requirements for my product?"
        
        # Mock database queries
        def mock_query_side_effect(model):
            mock_query = Mock()
            if model == ChatSession:
                mock_query.filter = Mock(return_value=mock_query)
                mock_query.first = Mock(return_value=sample_session)
            elif model == ChatMessage:
                mock_query.filter = Mock(return_value=mock_query)
                mock_query.order_by = Mock(return_value=mock_query)
                mock_query.all = Mock(return_value=[])
            elif model == Report:
                mock_query.filter = Mock(return_value=mock_query)
                mock_query.first = Mock(return_value=sample_report)
            return mock_query
        
        mock_db.query = Mock(side_effect=mock_query_side_effect)
        
        # Process question
        result = chat_service.process_question(
            question=question,
            session_id=sample_session.id,
            db=mock_db
        )
        
        # Verify result structure
        assert 'response' in result
        assert 'sources' in result
        assert 'session_id' in result
        assert 'message_id' in result
        
        # Verify response content
        assert len(result['response']) > 0
        assert len(result['sources']) > 0
        
        # Verify messages were stored
        assert mock_db.add.call_count == 2  # User message + assistant message
        mock_db.commit.assert_called_once()
    
    def test_process_question_empty_question(self, chat_service, mock_db):
        """Test that empty questions raise ValueError."""
        session_id = uuid4()
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            chat_service.process_question(
                question="",
                session_id=session_id,
                db=mock_db
            )
    
    def test_process_question_session_not_found(self, chat_service, mock_db):
        """Test that missing session raises ValueError."""
        session_id = uuid4()
        question = "What are the requirements?"
        
        # Mock query to return None (session not found)
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        mock_db.query = Mock(return_value=mock_query)
        
        with pytest.raises(ValueError, match="not found"):
            chat_service.process_question(
                question=question,
                session_id=session_id,
                db=mock_db
            )
    
    def test_process_question_expired_session(self, chat_service, mock_db, sample_session):
        """Test that expired session raises ValueError."""
        question = "What are the requirements?"
        
        # Set session as expired
        sample_session.expires_at = datetime.utcnow() - timedelta(hours=1)
        
        # Mock query to return expired session
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_session)
        mock_db.query = Mock(return_value=mock_query)
        
        with pytest.raises(ValueError, match="expired"):
            chat_service.process_question(
                question=question,
                session_id=sample_session.id,
                db=mock_db
            )
    
    def test_process_question_with_history(
        self,
        chat_service,
        mock_db,
        sample_session,
        sample_report
    ):
        """Test processing question with conversation history."""
        question = "What about CE marking?"
        
        # Create sample history messages
        history_messages = [
            ChatMessage(
                id=uuid4(),
                session_id=sample_session.id,
                role='user',
                content='What certifications do I need?',
                created_at=datetime.utcnow() - timedelta(minutes=5)
            ),
            ChatMessage(
                id=uuid4(),
                session_id=sample_session.id,
                role='assistant',
                content='You need FDA registration and FSSAI certification.',
                created_at=datetime.utcnow() - timedelta(minutes=4)
            )
        ]
        
        # Mock database queries
        def mock_query_side_effect(model):
            mock_query = Mock()
            if model == ChatSession:
                mock_query.filter = Mock(return_value=mock_query)
                mock_query.first = Mock(return_value=sample_session)
            elif model == ChatMessage:
                mock_query.filter = Mock(return_value=mock_query)
                mock_query.order_by = Mock(return_value=mock_query)
                mock_query.all = Mock(return_value=history_messages)
            elif model == Report:
                mock_query.filter = Mock(return_value=mock_query)
                mock_query.first = Mock(return_value=sample_report)
            return mock_query
        
        mock_db.query = Mock(side_effect=mock_query_side_effect)
        
        # Process question
        result = chat_service.process_question(
            question=question,
            session_id=sample_session.id,
            db=mock_db
        )
        
        # Verify result
        assert 'response' in result
        assert len(result['response']) > 0
        
        # Verify LLM was called with history in prompt
        chat_service.llm_client.generate.assert_called_once()
        call_args = chat_service.llm_client.generate.call_args
        prompt = call_args[1]['prompt']
        
        # Verify history is included in prompt
        assert 'Conversation History' in prompt


class TestHistoryRetrieval:
    """Test conversation history retrieval."""
    
    def test_get_history(self, chat_service, mock_db):
        """Test retrieving conversation history."""
        session_id = uuid4()
        
        # Create sample messages
        messages = [
            ChatMessage(
                id=uuid4(),
                session_id=session_id,
                role='user',
                content='Question 1',
                sources=None,
                created_at=datetime.utcnow() - timedelta(minutes=10)
            ),
            ChatMessage(
                id=uuid4(),
                session_id=session_id,
                role='assistant',
                content='Answer 1',
                sources=[{'source': 'FDA'}],
                created_at=datetime.utcnow() - timedelta(minutes=9)
            ),
            ChatMessage(
                id=uuid4(),
                session_id=session_id,
                role='user',
                content='Question 2',
                sources=None,
                created_at=datetime.utcnow() - timedelta(minutes=5)
            )
        ]
        
        # Mock query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=messages)
        mock_db.query = Mock(return_value=mock_query)
        
        # Get history
        history = chat_service.get_history(session_id, mock_db)
        
        # Verify history
        assert len(history) == 3
        assert history[0]['role'] == 'user'
        assert history[0]['content'] == 'Question 1'
        assert history[1]['role'] == 'assistant'
        assert history[1]['sources'] == [{'source': 'FDA'}]
    
    def test_get_history_with_limit(self, chat_service, mock_db):
        """Test retrieving limited conversation history."""
        session_id = uuid4()
        
        # Create sample messages
        messages = [
            ChatMessage(
                id=uuid4(),
                session_id=session_id,
                role='user',
                content=f'Question {i}',
                created_at=datetime.utcnow() - timedelta(minutes=10-i)
            )
            for i in range(5)
        ]
        
        # Mock query with limit
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=messages[:3])
        mock_db.query = Mock(return_value=mock_query)
        
        # Get history with limit
        history = chat_service.get_history(session_id, mock_db, limit=3)
        
        # Verify limit was applied
        mock_query.limit.assert_called_once_with(3)
        assert len(history) == 3


class TestContextPreservation:
    """Test context preservation across questions."""
    
    def test_contextual_query_building(self, chat_service):
        """Test building contextual queries."""
        question = "What are the requirements?"
        context = {
            'product_type': 'LED Lights',
            'destination': 'Germany',
            'hs_code': '8539.50.00'
        }
        
        contextual_query = chat_service._build_contextual_query(question, context)
        
        # Verify context is included
        assert 'LED Lights' in contextual_query
        assert 'Germany' in contextual_query
        assert '8539.50.00' in contextual_query
        assert question in contextual_query
    
    def test_retrieval_filters_building(self, chat_service):
        """Test building retrieval filters from context."""
        context = {
            'destination': 'United States',
            'product_category': 'Electronics'
        }
        
        filters = chat_service._build_retrieval_filters(context)
        
        # Verify filters
        assert filters is not None
        assert filters['country'] == 'United States'
        assert filters['product_category'] == 'Electronics'
    
    def test_session_context_extraction(self, chat_service, mock_db, sample_session, sample_report):
        """Test extracting context from session and report."""
        # Mock report query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_report)
        mock_db.query = Mock(return_value=mock_query)
        
        context = chat_service._get_session_context(sample_session, mock_db)
        
        # Verify context includes session and report data
        assert context['product_type'] == 'Organic Tea'
        assert context['destination'] == 'United States'
        assert context['hs_code'] == '0902.10.00'
        assert context['business_type'] == 'Manufacturing'


class TestPromptFormatting:
    """Test prompt formatting for chat."""
    
    def test_format_context(self, chat_service):
        """Test formatting session context."""
        context = {
            'product_type': 'Organic Tea',
            'destination': 'United States',
            'hs_code': '0902.10.00',
            'business_type': 'Manufacturing'
        }
        
        formatted = chat_service._format_context(context)
        
        assert 'Organic Tea' in formatted
        assert 'United States' in formatted
        assert '0902.10.00' in formatted
        assert 'Manufacturing' in formatted
    
    def test_format_history(self, chat_service):
        """Test formatting conversation history."""
        messages = [
            ChatMessage(
                id=uuid4(),
                session_id=uuid4(),
                role='user',
                content='What certifications do I need?',
                created_at=datetime.utcnow()
            ),
            ChatMessage(
                id=uuid4(),
                session_id=uuid4(),
                role='assistant',
                content='You need FDA and FSSAI certifications.',
                created_at=datetime.utcnow()
            )
        ]
        
        formatted = chat_service._format_history(messages)
        
        assert 'User:' in formatted
        assert 'Assistant:' in formatted
        assert 'certifications' in formatted
    
    def test_format_retrieved_docs(self, chat_service):
        """Test formatting retrieved documents."""
        docs = [
            Document(
                id="doc1",
                content="FDA requires food registration.",
                metadata={'source': 'FDA'},
                relevance_score=0.9
            ),
            Document(
                id="doc2",
                content="FSSAI standards must be met.",
                metadata={'source': 'FSSAI'},
                relevance_score=0.85
            )
        ]
        
        formatted = chat_service._format_retrieved_docs(docs)
        
        assert 'Document 1' in formatted
        assert 'FDA' in formatted
        assert 'FSSAI' in formatted
        assert 'food registration' in formatted


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
