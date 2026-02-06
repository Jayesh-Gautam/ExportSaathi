# Groq API Client Implementation

## Overview

The `GroqClient` class provides an alternative LLM inference backend to AWS Bedrock, using Groq's fast LPU (Language Processing Unit) architecture. It implements the same `LLMClient` interface as `BedrockClient`, making it a drop-in replacement.

## Features

- **Same Interface**: Implements the same `LLMClient` abstract interface as `BedrockClient`
- **Fast Inference**: Leverages Groq's LPU architecture for rapid response times
- **Retry Logic**: Exponential backoff retry mechanism for transient failures
- **Rate Limiting**: Built-in rate limiting to prevent API quota exhaustion
- **Error Handling**: Comprehensive error handling with specific error types
- **Structured Output**: Support for JSON schema-based structured responses

## Supported Models

The GroqClient supports the following models:
- `mixtral-8x7b-32768` (default)
- `llama3-70b-8192`
- `llama3-8b-8192`
- `gemma-7b-it`

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=mixtral-8x7b-32768
USE_GROQ=true  # Set to true to use Groq instead of Bedrock
```

### Installation

Install the Groq library:

```bash
pip install groq==0.4.2
```

## Usage

### Using the Factory Function

The recommended way to create an LLM client is using the factory function, which automatically selects the appropriate client based on configuration:

```python
from services.llm_client import create_llm_client

# Creates GroqClient if USE_GROQ=true, otherwise BedrockClient
client = create_llm_client()

# Generate text
response = client.generate(
    prompt="What is export compliance?",
    system_prompt="You are an export compliance expert.",
    temperature=0.7,
    max_tokens=1000
)
print(response)
```

### Direct Instantiation

You can also create a GroqClient directly:

```python
from services.llm_client import GroqClient

client = GroqClient(
    api_key="your_api_key",
    model="mixtral-8x7b-32768",
    temperature=0.7,
    max_tokens=4096
)

# Generate text
response = client.generate(
    prompt="Explain HS codes",
    system_prompt="You are a customs expert."
)
```

### Structured Output

Generate JSON responses that match a specific schema:

```python
schema = {
    "type": "object",
    "properties": {
        "hs_code": {"type": "string"},
        "confidence": {"type": "number"},
        "description": {"type": "string"}
    }
}

result = client.generate_structured(
    prompt="Predict the HS code for LED lights",
    schema=schema
)

print(result["hs_code"])  # e.g., "8541.10"
print(result["confidence"])  # e.g., 0.95
```

### Retry Logic

Use automatic retry with exponential backoff:

```python
response = client.generate_with_retry(
    prompt="What are the FDA requirements for food exports?",
    max_retries=3,
    system_prompt="You are an FDA compliance expert."
)
```

## Error Handling

The GroqClient provides specific error handling for common issues:

### Rate Limit Errors

```python
try:
    response = client.generate("Test prompt")
except Exception as e:
    if "rate limit" in str(e).lower():
        print("Rate limit exceeded. Please wait before retrying.")
```

### Authentication Errors

```python
try:
    client = GroqClient(api_key="invalid_key")
except ValueError as e:
    print(f"Configuration error: {e}")
```

### Model Not Found

```python
try:
    response = client.generate("Test", model="invalid-model")
except Exception as e:
    if "model not found" in str(e).lower():
        print("Invalid model specified")
```

## Rate Limiting

The GroqClient implements client-side rate limiting:
- **Window**: 60 seconds
- **Max Requests**: 30 per window (Groq free tier limit)

When the rate limit is exceeded, an exception is raised with the wait time:

```
Exception: Rate limit exceeded. Please wait 15.3 seconds
```

## Comparison with BedrockClient

| Feature | BedrockClient | GroqClient |
|---------|--------------|------------|
| Interface | LLMClient | LLMClient (same) |
| Models | Claude 3, Llama 3, Mixtral | Mixtral, Llama 3, Gemma |
| Rate Limit | 50 req/min | 30 req/min |
| Retry Logic | ✅ | ✅ |
| Structured Output | ✅ | ✅ |
| Cost | AWS Bedrock pricing | Groq pricing |
| Speed | Standard | Fast (LPU) |

## Testing

Run the GroqClient tests:

```bash
# All GroqClient tests
python -m pytest services/test_llm_client.py::TestGroqClient -v

# Specific test
python -m pytest services/test_llm_client.py::TestGroqClient::test_generate_success -v

# All LLM client tests (Bedrock + Groq + Factory)
python -m pytest services/test_llm_client.py -v
```

## Implementation Details

### Methods

The GroqClient implements three required methods from the `LLMClient` interface:

1. **`generate()`**: Generate text response with optional system prompt
2. **`generate_structured()`**: Generate JSON response matching a schema
3. **`generate_with_retry()`**: Generate with automatic retry on failure

### Internal Methods

- **`_check_rate_limit()`**: Enforces rate limiting
- **Error handling**: Categorizes errors (rate limit, auth, model not found)

### Retry Behavior

- **Retries**: Transient errors (network, temporary API issues)
- **No Retry**: Rate limit errors, authentication errors
- **Backoff**: Exponential (1s, 2s, 4s, ...)

## Requirements

This implementation satisfies:
- **Requirement 11.1**: LLM Integration and Structured Outputs

## Related Files

- `backend/services/llm_client.py` - Main implementation
- `backend/services/test_llm_client.py` - Unit tests
- `backend/config.py` - Configuration settings
- `backend/requirements.txt` - Dependencies

## Future Enhancements

Potential improvements:
- Support for streaming responses
- Token usage tracking and reporting
- Custom timeout configuration
- Response caching
- Batch request support
