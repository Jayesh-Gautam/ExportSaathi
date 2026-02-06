# LLM Client Service

## Overview

The LLM Client Service provides a unified interface for interacting with Large Language Models (LLMs) through AWS Bedrock. It supports multiple models including Claude 3, Llama 3, and Mixtral with built-in retry logic, rate limiting, and structured output generation.

**Requirements:** 11.1, 11.2, 11.4

## Features

- **Multiple Model Support**: Claude 3 (Sonnet, Haiku, Opus), Llama 3 (70B, 8B), Mixtral 8x7B
- **Retry Logic**: Exponential backoff for transient failures
- **Rate Limiting**: Prevents API quota exhaustion
- **Structured Output**: JSON generation with schema validation
- **Error Handling**: Comprehensive error handling for AWS API errors
- **Model-Specific Formatting**: Automatic prompt formatting for each model type

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      LLMClient (Abstract)                    │
│  - generate(prompt, system_prompt, temperature, model)      │
│  - generate_structured(prompt, schema, system_prompt)       │
│  - generate_with_retry(prompt, max_retries)                 │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                ┌─────────────┴─────────────┐
                │                           │
    ┌───────────────────────┐   ┌──────────────────────┐
    │   BedrockClient       │   │   GroqClient         │
    │   (Implemented)       │   │   (TODO: Task 4.2)   │
    └───────────────────────┘   └──────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │   AWS Bedrock API     │
    │   - Claude 3          │
    │   - Llama 3           │
    │   - Mixtral           │
    └───────────────────────┘
```

## Usage

### Basic Text Generation

```python
from services.llm_client import BedrockClient, ModelType

# Initialize client
client = BedrockClient()

# Generate text
response = client.generate(
    prompt="What are the export requirements for LED lights to the USA?",
    system_prompt="You are an export compliance expert.",
    temperature=0.7
)

print(response)
```

### Structured JSON Output

```python
# Define expected schema
schema = {
    "type": "object",
    "properties": {
        "hs_code": {"type": "string"},
        "confidence": {"type": "number"},
        "description": {"type": "string"}
    },
    "required": ["hs_code", "confidence"]
}

# Generate structured response
result = client.generate_structured(
    prompt="Predict the HS code for LED light bulbs",
    schema=schema,
    system_prompt="You are an HS code prediction expert."
)

print(f"HS Code: {result['hs_code']}")
print(f"Confidence: {result['confidence']}")
```

### Generation with Retry

```python
# Automatically retry on transient failures
response = client.generate_with_retry(
    prompt="Analyze export compliance requirements",
    max_retries=3,
    temperature=0.5
)
```

### Custom Model Selection

```python
# Use specific model
response = client.generate(
    prompt="What certifications are needed?",
    model=ModelType.CLAUDE_3_OPUS,  # Use most capable Claude model
    temperature=0.3
)

# Or use Llama
response = client.generate(
    prompt="Calculate RoDTEP benefits",
    model=ModelType.LLAMA_3_70B
)

# Or use Mixtral
response = client.generate(
    prompt="Estimate freight costs",
    model=ModelType.MIXTRAL_8X7B
)
```

### Factory Pattern

```python
from services.llm_client import create_llm_client

# Create client based on configuration
client = create_llm_client()  # Returns BedrockClient or GroqClient

response = client.generate(prompt="Your prompt here")
```

## Supported Models

### Claude 3 Models (Anthropic)

- **Claude 3 Opus** (`anthropic.claude-3-opus-20240229-v1:0`)
  - Most capable model
  - Best for complex reasoning and analysis
  - Higher cost

- **Claude 3 Sonnet** (`anthropic.claude-3-sonnet-20240229-v1:0`)
  - Balanced performance and cost
  - Default model
  - Good for most use cases

- **Claude 3 Haiku** (`anthropic.claude-3-haiku-20240307-v1:0`)
  - Fastest and most cost-effective
  - Good for simple tasks

### Llama 3 Models (Meta)

- **Llama 3 70B** (`meta.llama3-70b-instruct-v1:0`)
  - Large model with strong performance
  - Open source

- **Llama 3 8B** (`meta.llama3-8b-instruct-v1:0`)
  - Smaller, faster model
  - Good for simpler tasks

### Mixtral Models (Mistral AI)

- **Mixtral 8x7B** (`mistral.mixtral-8x7b-instruct-v0:1`)
  - Mixture of Experts architecture
  - Good balance of performance and efficiency

## Configuration

Configure the client through environment variables in `.env`:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Bedrock Settings
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_TEMPERATURE=0.7
BEDROCK_MAX_TOKENS=4096

# Alternative: Use Groq API
USE_GROQ=False
GROQ_API_KEY=your_groq_key
GROQ_MODEL=mixtral-8x7b-32768
```

## Rate Limiting

The client implements automatic rate limiting to prevent API quota exhaustion:

- **Default Limit**: 50 requests per minute
- **Window**: 60 seconds rolling window
- **Behavior**: Raises exception when limit exceeded

```python
try:
    response = client.generate(prompt="Your prompt")
except Exception as e:
    if "rate limit" in str(e).lower():
        print("Rate limit exceeded. Please wait before retrying.")
```

## Retry Logic

The client implements exponential backoff for transient failures:

- **Default Retries**: 3 attempts
- **Backoff**: 1s, 2s, 4s, 8s, ...
- **No Retry**: Rate limit errors (fail immediately)

```python
# Customize retry behavior
response = client.generate_with_retry(
    prompt="Your prompt",
    max_retries=5  # Try up to 5 times
)
```

## Error Handling

The client handles various error scenarios:

### AWS ClientError
```python
try:
    response = client.generate(prompt="Test")
except Exception as e:
    # Handles: ValidationException, ThrottlingException, etc.
    print(f"AWS API Error: {e}")
```

### BotoCoreError
```python
try:
    response = client.generate(prompt="Test")
except Exception as e:
    # Handles: Connection errors, timeout, etc.
    print(f"Connection Error: {e}")
```

### Invalid JSON (Structured Output)
```python
try:
    result = client.generate_structured(prompt="Test", schema={})
except Exception as e:
    # Handles: Invalid JSON response
    print(f"JSON Parsing Error: {e}")
```

## Model-Specific Prompt Formatting

The client automatically formats prompts according to each model's requirements:

### Claude 3 (Messages API)
```json
{
  "messages": [
    {"role": "user", "content": "Your prompt"}
  ],
  "system": "System prompt",
  "max_tokens": 4096,
  "temperature": 0.7,
  "anthropic_version": "bedrock-2023-05-31"
}
```

### Llama 3 (Instruction Format)
```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
System prompt<|eot_id|><|start_header_id|>user<|end_header_id|>
Your prompt<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

### Mixtral (Instruction Format)
```
<s>[INST] System prompt

Your prompt [/INST]
```

## Testing

Run the test suite:

```bash
cd backend/services
python -m pytest test_llm_client.py -v
```

### Test Coverage

- ✅ Client initialization
- ✅ Prompt formatting for all models
- ✅ Response parsing for all models
- ✅ Basic text generation
- ✅ Custom model selection
- ✅ Error handling (ClientError, BotoCoreError)
- ✅ Rate limiting enforcement
- ✅ Rate limit window expiry
- ✅ Structured JSON generation
- ✅ JSON extraction from wrapped text
- ✅ Invalid JSON handling
- ✅ Retry logic (success on first attempt)
- ✅ Retry logic (success after failures)
- ✅ Retry logic (all attempts fail)
- ✅ Rate limit errors not retried
- ✅ Exponential backoff timing
- ✅ Unsupported model errors
- ✅ Factory pattern

**Total Tests**: 25 tests, all passing ✅

## Integration with Other Services

### RAG Pipeline Integration

```python
from services.llm_client import create_llm_client
from services.rag_pipeline import RAGPipeline

llm_client = create_llm_client()
rag_pipeline = RAGPipeline(llm_client=llm_client)

# Use in RAG pipeline
response = rag_pipeline.generate_with_context(
    query="What certifications are needed?",
    context_documents=retrieved_docs
)
```

### Report Generator Integration

```python
from services.llm_client import BedrockClient, ModelType
from services.report_generator import ReportGenerator

llm_client = BedrockClient()
report_generator = ReportGenerator(llm_client=llm_client)

# Generate export readiness report
report = report_generator.generate_report(
    product_details=product_data,
    hs_code=predicted_hs_code
)
```

## Performance Considerations

### Model Selection

- **Complex Analysis**: Use Claude 3 Opus or Llama 3 70B
- **Balanced Tasks**: Use Claude 3 Sonnet (default)
- **Simple Tasks**: Use Claude 3 Haiku or Llama 3 8B
- **Cost-Effective**: Use Mixtral 8x7B

### Temperature Settings

- **Factual/Structured**: 0.0 - 0.3 (more deterministic)
- **Balanced**: 0.5 - 0.7 (default)
- **Creative**: 0.8 - 1.0 (more varied)

### Token Limits

- **Short Responses**: 512 - 1024 tokens
- **Medium Responses**: 2048 tokens
- **Long Responses**: 4096 tokens (default)
- **Very Long**: 8192+ tokens (check model limits)

## Best Practices

1. **Use Retry Logic**: Always use `generate_with_retry()` for production
2. **Handle Rate Limits**: Implement backoff in your application
3. **Choose Right Model**: Balance cost, speed, and quality
4. **Set Appropriate Temperature**: Lower for factual, higher for creative
5. **Validate Structured Output**: Always validate JSON against schema
6. **Log Errors**: Use logging for debugging and monitoring
7. **Monitor Costs**: Track API usage and costs
8. **Cache Results**: Cache responses when appropriate

## Future Enhancements

- [ ] Implement GroqClient (Task 4.2)
- [ ] Add streaming support for long responses
- [ ] Implement token counting and cost estimation
- [ ] Add response caching layer
- [ ] Support for function calling
- [ ] Add prompt templates library
- [ ] Implement A/B testing for model comparison
- [ ] Add metrics and monitoring integration

## Troubleshooting

### Issue: Rate Limit Exceeded
**Solution**: Wait for the rate limit window to expire or increase the limit

### Issue: Invalid Model ID
**Solution**: Check that the model ID is correct and available in your AWS region

### Issue: Connection Timeout
**Solution**: Check network connectivity and AWS credentials

### Issue: Invalid JSON Response
**Solution**: Adjust prompt to be more explicit about JSON format requirements

### Issue: High Latency
**Solution**: Use a faster model (Haiku, Llama 3 8B) or reduce max_tokens

## References

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude 3 Model Card](https://www.anthropic.com/claude)
- [Llama 3 Documentation](https://llama.meta.com/)
- [Mixtral Documentation](https://mistral.ai/)

## Task Completion

✅ **Task 4.1: Implement AWS Bedrock client**
- ✅ Created BedrockClient class using Boto3
- ✅ Implemented generate method with model selection (Claude 3, Llama 3, Mixtral)
- ✅ Added generate_structured method for JSON responses
- ✅ Implemented retry logic with exponential backoff
- ✅ Added rate limiting and error handling
- ✅ All 25 unit tests passing
- ✅ Requirements 11.1, 11.2, 11.4 satisfied
