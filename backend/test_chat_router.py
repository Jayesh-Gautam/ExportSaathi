"""
Test suite for Chat API Router

Tests the chat API endpoints to ensure they work correctly with:
1. POST /api/chat - Submit chat question
2. GET /api/chat/{session_id}/history - Retrieve conversation history
3. DELETE /api/chat/{session_id} - Clear conversation history

This is a comprehensive test suite for the chat router implementation.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime

from main import app
from models import ChatRequest, ChatResponse, ChatMessage, MessageRole, QueryContext
from models.common import Source


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_session_id():
    """Create a mock session ID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_chat_request(mock_session_id):
    """Create a mock chat request."""
    return ChatRequest(
        session_id=mock_session_id,
        question="What are the FDA requirements for turmeric powder?",
        context=QueryContext(
            report_id="rpt_test123456",
            product_type="Turmeric powder",
            destination_country="United States"
        )
    )


@pytest.fixture
def mock_chat_service_response():
    """Create a mock chat service response."""
    return {
        'response': 'FDA registration is required for food facilities. You need to register your facility and renew annually.',
        'sources': [
            {
                'title': 'FDA Food Facility Registration',
                'source': 'FDA',
                'url': 'https://fda.gov/registration'
            },
            {
                'title': 'FDA Requirements for Spices',
                'source': 'FDA',
                'url': 'https://fda.gov/spices'
            }
        ],
        'session_id': str(uuid.uuid4()),
        'message_id': str(uuid.uuid4())
    }


@pytest.fixture
def mock_chat_history():
    """Create mock chat history."""
    return [
        {
            'id': str(uuid.uuid4()),
            'role': 'user',
            'content': 'What certifications do I need?',
            'sources': None,
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'role': 'assistant',
            'content': 'You need FDA registration and FSSAI certification.',
            'sources': [
                {
                    'title': 'FDA Registration',
                    'source': 'FDA',
                    'url': 'https://fda.gov'
                }
            ],
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'role': 'user',
            'content': 'How long does FDA registration take?',
            'sources': None,
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'role': 'assistant',
            'content': 'FDA registration typically takes 2-3 weeks.',
            'sources': [],
            'created_at': datetime.utcnow().isoformat()
        }
    ]


# Test POST /api/chat

def test_submit_question_success(client, mock_chat_request, mock_chat_service_response):
    """Test successful chat question submission."""
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service
        mock_service = Mock()
        mock_service.process_question.return_value = mock_chat_service_response
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/chat/",
            json=mock_chat_request.model_dump()
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert 'message_id' in data
        assert 'answer' in data
        assert 'sources' in data
        assert 'timestamp' in data
        assert data['answer'] == mock_chat_service_response['response']
        assert len(data['sources']) == 2
        assert data['sources'][0]['title'] == 'FDA Food Facility Registration'
        
        # Verify service was called correctly
        mock_service.process_question.assert_called_once()
        call_args = mock_service.process_question.call_args
        assert call_args.kwargs['question'] == mock_chat_request.question


def test_submit_question_empty_question(client, mock_session_id):
    """Test chat question submission with empty question."""
    request_data = {
        'session_id': mock_session_id,
        'question': '',
        'context': {
            'report_id': 'rpt_test123456',
            'product_type': 'Turmeric powder',
            'destination_country': 'United States'
        }
    }
    
    response = client.post("/api/chat/", json=request_data)
    
    # Should fail validation
    assert response.status_code == 422


def test_submit_question_whitespace_only(client, mock_session_id):
    """Test chat question submission with whitespace-only question."""
    request_data = {
        'session_id': mock_session_id,
        'question': '   ',
        'context': {
            'report_id': 'rpt_test123456',
            'product_type': 'Turmeric powder',
            'destination_country': 'United States'
        }
    }
    
    response = client.post("/api/chat/", json=request_data)
    
    # Should fail validation
    assert response.status_code == 422


def test_submit_question_session_not_found(client, mock_chat_request):
    """Test chat question submission with non-existent session."""
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service to raise ValueError
        mock_service = Mock()
        mock_service.process_question.side_effect = ValueError("Session not found")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/chat/",
            json=mock_chat_request.model_dump()
        )
        
        # Should return 404
        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()


def test_submit_question_session_expired(client, mock_chat_request):
    """Test chat question submission with expired session."""
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service to raise ValueError for expired session
        mock_service = Mock()
        mock_service.process_question.side_effect = ValueError("Session has expired")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/chat/",
            json=mock_chat_request.model_dump()
        )
        
        # Should return 404
        assert response.status_code == 404
        assert 'expired' in response.json()['detail'].lower()


def test_submit_question_invalid_session_id_format(client):
    """Test chat question submission with invalid session ID format."""
    request_data = {
        'session_id': 'invalid-session-id',
        'question': 'What are the requirements?',
        'context': {
            'report_id': 'rpt_test123456',
            'product_type': 'Turmeric powder',
            'destination_country': 'United States'
        }
    }
    
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post("/api/chat/", json=request_data)
        
        # Should return 400 for invalid format
        assert response.status_code == 400
        assert 'Invalid session ID format' in response.json()['detail']


def test_submit_question_with_sources(client, mock_chat_request):
    """Test chat question submission returns sources correctly."""
    mock_response = {
        'response': 'Test answer',
        'sources': [
            {
                'title': 'DGFT Handbook',
                'source': 'DGFT',
                'url': 'https://dgft.gov.in/handbook'
            }
        ],
        'session_id': str(uuid.uuid4()),
        'message_id': str(uuid.uuid4())
    }
    
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service
        mock_service = Mock()
        mock_service.process_question.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/chat/",
            json=mock_chat_request.model_dump()
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data['sources']) == 1
        assert data['sources'][0]['title'] == 'DGFT Handbook'
        assert data['sources'][0]['source'] == 'DGFT'


def test_submit_question_no_sources(client, mock_chat_request):
    """Test chat question submission with no sources."""
    mock_response = {
        'response': 'Test answer without sources',
        'sources': [],
        'session_id': str(uuid.uuid4()),
        'message_id': str(uuid.uuid4())
    }
    
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service
        mock_service = Mock()
        mock_service.process_question.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/chat/",
            json=mock_chat_request.model_dump()
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['sources'] == []


# Test GET /api/chat/{session_id}/history

def test_get_chat_history_success(client, mock_session_id, mock_chat_history):
    """Test successful chat history retrieval."""
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service
        mock_service = Mock()
        mock_service.get_history.return_value = mock_chat_history
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(f"/api/chat/{mock_session_id}/history")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4
        assert data[0]['role'] == 'user'
        assert data[1]['role'] == 'assistant'
        assert 'message_id' in data[0]
        assert 'content' in data[0]
        assert 'timestamp' in data[0]
        
        # Verify service was called correctly
        mock_service.get_history.assert_called_once()
        call_args = mock_service.get_history.call_args
        assert call_args.kwargs['limit'] is None


def test_get_chat_history_with_limit(client, mock_session_id, mock_chat_history):
    """Test chat history retrieval with limit parameter."""
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service - return only first 2 messages
        mock_service = Mock()
        mock_service.get_history.return_value = mock_chat_history[:2]
        mock_get_service.return_value = mock_service
        
        # Make request with limit
        response = client.get(f"/api/chat/{mock_session_id}/history?limit=2")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify service was called with limit
        mock_service.get_history.assert_called_once()
        call_args = mock_service.get_history.call_args
        assert call_args.kwargs['limit'] == 2


def test_get_chat_history_empty(client, mock_session_id):
    """Test chat history retrieval for session with no messages."""
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service - return empty history
        mock_service = Mock()
        mock_service.get_history.return_value = []
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(f"/api/chat/{mock_session_id}/history")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data == []


def test_get_chat_history_session_not_found(client):
    """Test chat history retrieval for non-existent session."""
    non_existent_session = str(uuid.uuid4())
    
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service to raise ValueError
        mock_service = Mock()
        mock_service.get_history.side_effect = ValueError("Session not found")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(f"/api/chat/{non_existent_session}/history")
        
        # Should return 404
        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()


def test_get_chat_history_invalid_session_id(client):
    """Test chat history retrieval with invalid session ID format."""
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Make request with invalid session ID
        response = client.get("/api/chat/invalid-id/history")
        
        # Should return 400
        assert response.status_code == 400
        assert 'Invalid session ID format' in response.json()['detail']


def test_get_chat_history_with_sources(client, mock_session_id):
    """Test chat history retrieval includes sources correctly."""
    history_with_sources = [
        {
            'id': str(uuid.uuid4()),
            'role': 'user',
            'content': 'What are the requirements?',
            'sources': None,
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'role': 'assistant',
            'content': 'You need FDA registration.',
            'sources': [
                {
                    'title': 'FDA Guide',
                    'source': 'FDA',
                    'url': 'https://fda.gov'
                }
            ],
            'created_at': datetime.utcnow().isoformat()
        }
    ]
    
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service
        mock_service = Mock()
        mock_service.get_history.return_value = history_with_sources
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(f"/api/chat/{mock_session_id}/history")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['sources'] is None
        assert data[1]['sources'] is not None
        assert len(data[1]['sources']) == 1
        assert data[1]['sources'][0]['title'] == 'FDA Guide'


# Test DELETE /api/chat/{session_id}

def test_clear_session_success(client, mock_session_id):
    """Test successful session clearing."""
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service
        mock_service = Mock()
        mock_service.clear_session.return_value = None
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.delete(f"/api/chat/{mock_session_id}")
        
        # Assertions
        assert response.status_code == 204
        assert response.content == b''
        
        # Verify service was called correctly
        mock_service.clear_session.assert_called_once()


def test_clear_session_not_found(client):
    """Test session clearing for non-existent session."""
    non_existent_session = str(uuid.uuid4())
    
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service to raise ValueError
        mock_service = Mock()
        mock_service.clear_session.side_effect = ValueError("Session not found")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.delete(f"/api/chat/{non_existent_session}")
        
        # Should return 404
        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()


def test_clear_session_invalid_session_id(client):
    """Test session clearing with invalid session ID format."""
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Make request with invalid session ID
        response = client.delete("/api/chat/invalid-id")
        
        # Should return 400
        assert response.status_code == 400
        assert 'Invalid session ID format' in response.json()['detail']


# Test parse_session_id helper function

def test_parse_session_id_valid_uuid():
    """Test parsing valid UUID session ID."""
    from routers.chat import parse_session_id
    
    session_uuid = uuid.uuid4()
    result = parse_session_id(str(session_uuid))
    assert result == session_uuid


def test_parse_session_id_with_prefix():
    """Test parsing session ID with sess_ prefix."""
    from routers.chat import parse_session_id
    
    session_uuid = uuid.uuid4()
    result = parse_session_id(f"sess_{session_uuid}")
    assert result == session_uuid


def test_parse_session_id_hex_string():
    """Test parsing session ID as hex string without dashes."""
    from routers.chat import parse_session_id
    
    session_uuid = uuid.uuid4()
    hex_string = str(session_uuid).replace('-', '')
    result = parse_session_id(hex_string)
    assert result == session_uuid


def test_parse_session_id_hex_string_with_prefix():
    """Test parsing session ID as hex string with sess_ prefix."""
    from routers.chat import parse_session_id
    
    session_uuid = uuid.uuid4()
    hex_string = f"sess_{str(session_uuid).replace('-', '')}"
    result = parse_session_id(hex_string)
    assert result == session_uuid


def test_parse_session_id_invalid():
    """Test parsing invalid session ID raises HTTPException."""
    from routers.chat import parse_session_id
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        parse_session_id("invalid-session-id")
    
    assert exc_info.value.status_code == 400
    assert 'Invalid session ID format' in exc_info.value.detail


# Integration-style tests

def test_chat_flow_integration(client, mock_session_id):
    """Test complete chat flow: submit question -> get history -> clear."""
    mock_response = {
        'response': 'Test answer',
        'sources': [],
        'session_id': mock_session_id,
        'message_id': str(uuid.uuid4())
    }
    
    mock_history = [
        {
            'id': str(uuid.uuid4()),
            'role': 'user',
            'content': 'Test question',
            'sources': None,
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'id': mock_response['message_id'],
            'role': 'assistant',
            'content': mock_response['response'],
            'sources': [],
            'created_at': datetime.utcnow().isoformat()
        }
    ]
    
    with patch('routers.chat.get_db') as mock_db, \
         patch('routers.chat.get_chat_service') as mock_get_service:
        
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock chat service
        mock_service = Mock()
        mock_service.process_question.return_value = mock_response
        mock_service.get_history.return_value = mock_history
        mock_service.clear_session.return_value = None
        mock_get_service.return_value = mock_service
        
        # Step 1: Submit question
        request_data = {
            'session_id': mock_session_id,
            'question': 'Test question',
            'context': {
                'report_id': 'rpt_test123456',
                'product_type': 'Test product',
                'destination_country': 'United States'
            }
        }
        response1 = client.post("/api/chat/", json=request_data)
        assert response1.status_code == 200
        
        # Step 2: Get history
        response2 = client.get(f"/api/chat/{mock_session_id}/history")
        assert response2.status_code == 200
        assert len(response2.json()) == 2
        
        # Step 3: Clear session
        response3 = client.delete(f"/api/chat/{mock_session_id}")
        assert response3.status_code == 204


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
