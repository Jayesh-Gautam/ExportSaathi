# ChatService Documentation

## Overview

The `ChatService` manages interactive Q&A conversations with context preservation for the ExportSathi platform. It enables users to ask follow-up questions about their export requirements while maintaining conversation history and session context.

**Requirements Implemented:** 7.2, 7.3, 7.4, 7.7

## Features

- **Session-based Conversation Management**: Create and manage chat sessions linked to export readiness reports
- **Context Preservation**: Maintain query context (product type, destination, report ID, HS code, business type)
- **RAG-based Document Retrieval**: Retrieve relevant regulatory documents for each question
- **LLM Response Generation**: Generate contextual responses with source citations
- **Message Storage**: Store all messages (user questions and assistant responses) in the database
- **Conversation History**: Retrieve and maintain conversation history across multiple questions
- **Session Expiration**: Automatic session timeout after configurable hours

## Architecture

```
ChatService
├── process_question()      # Main method to process user questions
├── get_history()           # Retrieve conversation history
├── create_session()        # Create new chat session
├── clear_session()         # Clear conversation history
└── delete_session()        # Delete session and messages
```

### Dependencies

- **RAGPipeline**: For document retrieval and context building
- **LLMClient**: For generating responses (Bedrock or Groq)
- **Database Models**: ChatSession, ChatMessage, Report
- **Prompt Templates**: EXPORTSATHI_MASTER_PROMPT

## Usage

### 1. Create a Chat Session

```python
from backend.services.chat_service import get_chat_service
from backend.database.connection import get_db

chat_service = get_chat_service()

# Create session with context
context = {
    'product_type': 'Organic Tea',
    'destination': 'United States',
    'hs_code': '0902.10.00',
    'business_type': 'Manufacturing'
}

session_id = chat_service.create_session(
    user_id=user_id,
    report_id=report_id,
    context=context,
    db=db_session
)
```

### 2. Process a Question

```python
# Ask a question
result = chat_service.process_question(
    question="What are the FDA requirements for my tea product?",
    session_id=session_id,
    db=db_session
)

# Access response and sources
print(result['response'])
for source in result['sources']:
    print(f"- {source['title']} ({source['source']})")
```

### 3. Retrieve Conversation History

```python
# Get full history
history = chat_service.get_history(
    session_id=session_id,
    db=db_session
)

# Get limited history (last 10 messages)
recent_history = chat_service.get_history(
    session_id=session_id,
    db=db_session,
    limit=10
)

for msg in history:
    print(f"{msg['role']}: {msg['content']}")
```

### 4. Clear or Delete Session

```python
# Clear conversation history (keeps session active)
chat_service.clear_session(session_id, db_session)

# Delete session and all messages
chat_service.delete_session(session_id, db_session)
```

## API Methods

### `process_question(question, session_id, db)`

Process a chat question with context and generate response.

**Parameters:**
- `question` (str): User's question
- `session_id` (UUID): Chat session ID
- `db` (Session): Database session

**Returns:**
```python
{
    'response': str,           # Generated answer text
    'sources': List[Dict],     # Source citations
    'session_id': str,         # Session ID
    'message_id': str          # Assistant message ID
}
```

**Process Flow:**
1. Retrieve session and validate (check expiration)
2. Retrieve conversation history from database
3. Get session context (product, destination, report details)
4. Build contextual query for document retrieval
5. Retrieve relevant documents using RAG pipeline
6. Build comprehensive prompt with context, history, and documents
7. Generate response using LLM
8. Extract source citations
9. Store user question and assistant response in database
10. Update session last activity timestamp

**Raises:**
- `ValueError`: If question is empty, session not found, or session expired

### `get_history(session_id, db, limit=None)`

Retrieve conversation history for a session.

**Parameters:**
- `session_id` (UUID): Chat session ID
- `db` (Session): Database session
- `limit` (int, optional): Maximum number of messages to retrieve

**Returns:**
```python
[
    {
        'id': str,
        'role': 'user' | 'assistant',
        'content': str,
        'sources': List[Dict] | None,
        'created_at': str  # ISO format
    }
]
```

### `create_session(user_id, report_id, context, db)`

Create a new chat session with context.

**Parameters:**
- `user_id` (UUID): User ID
- `report_id` (UUID): Associated report ID
- `context` (Dict): Session context (product, destination, etc.)
- `db` (Session): Database session

**Returns:**
- `UUID`: New session ID

**Context Structure:**
```python
{
    'product_type': str,
    'destination': str,
    'hs_code': str,
    'business_type': str,
    'product_category': str  # optional
}
```

### `clear_session(session_id, db)`

Clear conversation history for a session (keeps session active).

**Parameters:**
- `session_id` (UUID): Chat session ID
- `db` (Session): Database session

### `delete_session(session_id, db)`

Delete a chat session and all its messages.

**Parameters:**
- `session_id` (UUID): Chat session ID
- `db` (Session): Database session

## Context Preservation

The ChatService maintains context across multiple questions:

### Session Context
- Product type/name
- Destination country
- HS code
- Business type (Manufacturing/SaaS/Merchant)
- Report ID

### Conversation History
- Previous user questions
- Previous assistant responses
- Source citations from previous answers

### Contextual Query Building

Questions are enhanced with context for better document retrieval:

```python
# Original question
"What are the requirements?"

# Contextual query
"Product: Organic Tea | Destination: United States | HS Code: 0902.10.00 | Question: What are the requirements?"
```

### Retrieval Filters

Context is used to filter retrieved documents:

```python
filters = {
    'country': 'United States',
    'product_category': 'Food'
}
```

## Prompt Construction

The ChatService builds comprehensive prompts including:

1. **Session Context**: Product, destination, HS code, business type
2. **Conversation History**: Last 10 messages (5 exchanges)
3. **Retrieved Documents**: Top 5 relevant regulatory documents
4. **Current Question**: User's current question

**Prompt Structure:**
```
You are answering a follow-up question in an ongoing conversation about export requirements.

**Session Context:**
- Product: Organic Tea
- Destination: United States
- HS Code: 0902.10.00
- Business Type: Manufacturing

**Conversation History:**
User: What certifications do I need?
Assistant: You need FDA registration and FSSAI certification.

**Relevant Regulatory Documents:**
[Document 1 - Source: FDA]
FDA requires food products to be registered...

[Document 2 - Source: FSSAI]
All food exports must comply with FSSAI standards...

**Current Question:**
What are the specific steps for FDA registration?

**Instructions:**
1. Answer the question based on the regulatory documents provided
2. Maintain context from the conversation history
3. Be specific and actionable
4. Cite sources when providing regulatory information
5. If the documents don't contain relevant information, say so clearly

Answer:
```

## Database Schema

### ChatSession Table
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    report_id UUID REFERENCES reports(id),
    context_data JSONB,
    created_at TIMESTAMP,
    last_activity TIMESTAMP,
    expires_at TIMESTAMP
);
```

### ChatMessage Table
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id),
    role VARCHAR(20) CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB,
    created_at TIMESTAMP
);
```

## Configuration

### Session Timeout

Default: 24 hours

```python
chat_service = ChatService(session_timeout_hours=48)  # 48 hours
```

### RAG Pipeline Settings

The ChatService uses the global RAG pipeline with default settings:
- `top_k`: 5 documents
- `relevance_threshold`: 0.3
- `government_source_boost`: 0.1

### LLM Settings

- **Temperature**: 0.7 (balanced creativity and consistency)
- **Max Tokens**: 2048 (sufficient for detailed answers)
- **System Prompt**: EXPORTSATHI_MASTER_PROMPT with guardrails

## Error Handling

### Common Errors

1. **Empty Question**
   ```python
   ValueError: Question cannot be empty
   ```

2. **Session Not Found**
   ```python
   ValueError: Session {session_id} not found
   ```

3. **Session Expired**
   ```python
   ValueError: Session {session_id} has expired
   ```

4. **Database Errors**
   - Automatic rollback on errors
   - Logged with full stack trace

### Error Recovery

```python
try:
    result = chat_service.process_question(question, session_id, db)
except ValueError as e:
    # Handle validation errors
    print(f"Validation error: {e}")
except Exception as e:
    # Handle unexpected errors
    print(f"Unexpected error: {e}")
    # Session is automatically rolled back
```

## Testing

### Unit Tests

Run the test suite:

```bash
pytest backend/services/test_chat_service.py -v
```

### Test Coverage

- ✅ Service initialization
- ✅ Session creation and management
- ✅ Question processing with context
- ✅ Conversation history retrieval
- ✅ Context preservation
- ✅ Prompt formatting
- ✅ Error handling (empty questions, missing sessions, expired sessions)
- ✅ Message storage
- ✅ Source citation extraction

### Example Test

```python
def test_process_question_success(chat_service, mock_db, sample_session):
    """Test successfully processing a question."""
    question = "What are the FDA requirements?"
    
    result = chat_service.process_question(
        question=question,
        session_id=sample_session.id,
        db=mock_db
    )
    
    assert 'response' in result
    assert 'sources' in result
    assert len(result['response']) > 0
```

## Performance Considerations

### Response Time

- **Target**: < 10 seconds per question (Requirement 16.3)
- **Typical**: 3-7 seconds depending on document retrieval and LLM latency

### Optimization Strategies

1. **Document Retrieval**: Limit to top 5 documents
2. **History Truncation**: Use last 10 messages only
3. **Content Truncation**: Limit document content to 500 chars in prompt
4. **Caching**: RAG pipeline uses embedding cache
5. **Connection Pooling**: Database connection pooling enabled

### Scalability

- **Session Storage**: PostgreSQL with indexes on session_id and created_at
- **Message Storage**: Cascade delete for efficient cleanup
- **Concurrent Sessions**: Thread-safe with database transactions

## Integration with API Router

The ChatService is used by the chat API router:

```python
# backend/routers/chat.py
from backend.services.chat_service import get_chat_service
from backend.database.connection import get_db

@router.post("/")
async def submit_question(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    chat_service = get_chat_service()
    
    result = chat_service.process_question(
        question=request.question,
        session_id=request.session_id,
        db=db
    )
    
    return result
```

## Best Practices

### 1. Session Management

- Create one session per report
- Clear history when starting a new topic
- Delete sessions after user completes export process

### 2. Context Enrichment

- Always provide complete context when creating sessions
- Include HS code if available
- Specify business type for persona-specific responses

### 3. Question Formulation

- Encourage specific questions
- Reference previous conversation when relevant
- Ask follow-up questions for clarification

### 4. Error Handling

- Validate session before processing questions
- Handle expired sessions gracefully
- Provide clear error messages to users

### 5. Performance

- Limit conversation history to recent messages
- Use pagination for long histories
- Monitor LLM response times

## Future Enhancements

### Planned Features

1. **Multi-language Support**: Translate questions and responses
2. **Voice Input**: Speech-to-text for questions
3. **Suggested Questions**: AI-generated follow-up questions
4. **Export Conversation**: Download chat history as PDF
5. **Smart Summaries**: Summarize long conversations
6. **Feedback Loop**: User ratings for response quality

### Potential Optimizations

1. **Response Streaming**: Stream LLM responses for faster perceived performance
2. **Predictive Caching**: Pre-fetch common questions
3. **Context Compression**: Compress long conversation histories
4. **Hybrid Search**: Combine semantic and keyword search

## Troubleshooting

### Issue: Slow Response Times

**Possible Causes:**
- Large number of retrieved documents
- Long conversation history
- LLM service latency

**Solutions:**
- Reduce `top_k` in RAG pipeline
- Limit history to last 5 exchanges
- Check LLM service status

### Issue: Irrelevant Responses

**Possible Causes:**
- Poor document retrieval
- Missing context
- Insufficient conversation history

**Solutions:**
- Verify context is properly set
- Check retrieved document relevance scores
- Ensure conversation history is preserved

### Issue: Session Expired Errors

**Possible Causes:**
- Session timeout too short
- User inactive for extended period

**Solutions:**
- Increase session timeout
- Implement session refresh on activity
- Provide clear expiration warnings to users

## References

- **Requirements**: `.kiro/specs/export-readiness-platform/requirements.md` (Requirement 7)
- **Design**: `.kiro/specs/export-readiness-platform/design.md` (Component 24)
- **Database Models**: `backend/database/models.py`
- **RAG Pipeline**: `backend/services/rag_pipeline.py`
- **LLM Client**: `backend/services/llm_client.py`
- **Prompt Templates**: `backend/services/prompt_templates.py`

## Support

For issues or questions about the ChatService:
1. Check the test suite for usage examples
2. Review the design document for architecture details
3. Consult the RAG pipeline documentation for retrieval issues
4. Check LLM client documentation for generation issues
