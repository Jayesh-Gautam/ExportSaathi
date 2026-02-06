"""
Unit tests for LLM Client Service

Tests the BedrockClient and GroqClient implementations including:
- Basic text generation
- Structured JSON output
- Retry logic with exponential backoff
- Rate limiting
- Error handling
- Model-specific prompt formatting

Requirements: 11.1, 11.2, 11.4
"""
import json
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError

from services.llm_client import (
    BedrockClient, 
    GroqClient, 
    ModelType, 
    create_llm_client,
    GROQ_AVAILABLE
)


class TestBedrockClient:
    """Test suite for BedrockClient"""
    
    @pytest.fixture
    def mock_boto_client(self):
        """Create a mock boto3 client"""
        with patch('boto3.client') as mock_client:
            yield mock_client
    
    @pytest.fixture
    def bedrock_client(self, mock_boto_client):
        """Create BedrockClient instance with mocked boto3"""
        client = BedrockClient(
            region_name="us-east-1",
            model_id=ModelType.CLAUDE_3_SONNET,
            temperature=0.7,
            max_tokens=1000
        )
        return client
    
    def test_initialization(self, bedrock_client):
        """Test BedrockClient initialization"""
        assert bedrock_client.region_name == "us-east-1"
        assert bedrock_client.default_model_id == ModelType.CLAUDE_3_SONNET
        assert bedrock_client.default_temperature == 0.7
        assert bedrock_client.default_max_tokens == 1000
        assert bedrock_client.client is not None
    
    def test_format_prompt_claude(self, bedrock_client):
        """Test prompt formatting for Claude models"""
        prompt = "What is export compliance?"
        system_prompt = "You are an export compliance expert."
        model_id = ModelType.CLAUDE_3_SONNET
        
        body = bedrock_client._format_prompt_for_model(prompt, system_prompt, model_id)
        
        assert "messages" in body
        assert body["messages"][0]["role"] == "user"
        assert body["messages"][0]["content"] == prompt
        assert body["system"] == system_prompt
        assert "max_tokens" in body
        assert "temperature" in body
        assert body["anthropic_version"] == "bedrock-2023-05-31"
    
    def test_format_prompt_llama(self, bedrock_client):
        """Test prompt formatting for Llama models"""
        prompt = "What is export compliance?"
        system_prompt = "You are an export compliance expert."
        model_id = ModelType.LLAMA_3_70B
        
        body = bedrock_client._format_prompt_for_model(prompt, system_prompt, model_id)
        
        assert "prompt" in body
        assert "system" in body["prompt"]
        assert "user" in body["prompt"]
        assert prompt in body["prompt"]
        assert "max_gen_len" in body
        assert "temperature" in body
    
    def test_format_prompt_mixtral(self, bedrock_client):
        """Test prompt formatting for Mixtral models"""
        prompt = "What is export compliance?"
        system_prompt = "You are an export compliance expert."
        model_id = ModelType.MIXTRAL_8X7B
        
        body = bedrock_client._format_prompt_for_model(prompt, system_prompt, model_id)
        
        assert "prompt" in body
        assert "[INST]" in body["prompt"]
        assert "[/INST]" in body["prompt"]
        assert prompt in body["prompt"]
        assert "max_tokens" in body
        assert "temperature" in body
    
    def test_parse_response_claude(self, bedrock_client):
        """Test response parsing for Claude models"""
        response_body = {
            "content": [
                {"text": "Export compliance refers to..."}
            ]
        }
        model_id = ModelType.CLAUDE_3_SONNET
        
        text = bedrock_client._parse_response(response_body, model_id)
        
        assert text == "Export compliance refers to..."
    
    def test_parse_response_llama(self, bedrock_client):
        """Test response parsing for Llama models"""
        response_body = {
            "generation": "Export compliance refers to..."
        }
        model_id = ModelType.LLAMA_3_70B
        
        text = bedrock_client._parse_response(response_body, model_id)
        
        assert text == "Export compliance refers to..."
    
    def test_parse_response_mixtral(self, bedrock_client):
        """Test response parsing for Mixtral models"""
        response_body = {
            "outputs": [
                {"text": "Export compliance refers to..."}
            ]
        }
        model_id = ModelType.MIXTRAL_8X7B
        
        text = bedrock_client._parse_response(response_body, model_id)
        
        assert text == "Export compliance refers to..."
    
    def test_generate_success(self, bedrock_client):
        """Test successful text generation"""
        # Mock the boto3 client response
        mock_response = {
            'body': MagicMock()
        }
        response_body = {
            "content": [
                {"text": "This is a test response"}
            ]
        }
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        bedrock_client.client.invoke_model = Mock(return_value=mock_response)
        
        result = bedrock_client.generate(
            prompt="Test prompt",
            system_prompt="Test system",
            temperature=0.5
        )
        
        assert result == "This is a test response"
        assert bedrock_client.client.invoke_model.called
    
    def test_generate_with_custom_model(self, bedrock_client):
        """Test generation with custom model selection"""
        mock_response = {
            'body': MagicMock()
        }
        response_body = {
            "generation": "Llama response"
        }
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        bedrock_client.client.invoke_model = Mock(return_value=mock_response)
        
        result = bedrock_client.generate(
            prompt="Test prompt",
            model=ModelType.LLAMA_3_70B
        )
        
        assert result == "Llama response"
        call_args = bedrock_client.client.invoke_model.call_args
        assert call_args[1]['modelId'] == ModelType.LLAMA_3_70B
    
    def test_generate_client_error(self, bedrock_client):
        """Test handling of AWS ClientError"""
        error_response = {
            'Error': {
                'Code': 'ValidationException',
                'Message': 'Invalid model ID'
            }
        }
        bedrock_client.client.invoke_model = Mock(
            side_effect=ClientError(error_response, 'InvokeModel')
        )
        
        with pytest.raises(Exception) as exc_info:
            bedrock_client.generate(prompt="Test prompt")
        
        assert "Bedrock API error" in str(exc_info.value)
        assert "Invalid model ID" in str(exc_info.value)
    
    def test_generate_botocore_error(self, bedrock_client):
        """Test handling of BotoCoreError"""
        bedrock_client.client.invoke_model = Mock(
            side_effect=BotoCoreError()
        )
        
        with pytest.raises(Exception) as exc_info:
            bedrock_client.generate(prompt="Test prompt")
        
        assert "Bedrock connection error" in str(exc_info.value)
    
    def test_rate_limiting(self, bedrock_client):
        """Test rate limiting enforcement"""
        # Set a low rate limit for testing
        bedrock_client._max_requests_per_window = 3
        bedrock_client._rate_limit_window = 1.0
        
        # Mock successful responses
        mock_response = {
            'body': MagicMock()
        }
        response_body = {"content": [{"text": "Response"}]}
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        bedrock_client.client.invoke_model = Mock(return_value=mock_response)
        
        # Make requests up to the limit
        for i in range(3):
            bedrock_client.generate(prompt=f"Test {i}")
        
        # Next request should fail with rate limit error
        with pytest.raises(Exception) as exc_info:
            bedrock_client.generate(prompt="Test 4")
        
        assert "rate limit" in str(exc_info.value).lower()
    
    def test_rate_limit_window_expiry(self, bedrock_client):
        """Test that rate limit window expires correctly"""
        bedrock_client._max_requests_per_window = 2
        bedrock_client._rate_limit_window = 0.5  # 500ms window
        
        mock_response = {
            'body': MagicMock()
        }
        response_body = {"content": [{"text": "Response"}]}
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        bedrock_client.client.invoke_model = Mock(return_value=mock_response)
        
        # Make 2 requests
        bedrock_client.generate(prompt="Test 1")
        bedrock_client.generate(prompt="Test 2")
        
        # Wait for window to expire
        time.sleep(0.6)
        
        # Should be able to make another request
        result = bedrock_client.generate(prompt="Test 3")
        assert result == "Response"
    
    def test_generate_structured_success(self, bedrock_client):
        """Test structured JSON generation"""
        schema = {
            "type": "object",
            "properties": {
                "hs_code": {"type": "string"},
                "confidence": {"type": "number"}
            }
        }
        
        mock_response = {
            'body': MagicMock()
        }
        json_response = {"hs_code": "1234.56", "confidence": 0.95}
        response_body = {
            "content": [
                {"text": json.dumps(json_response)}
            ]
        }
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        bedrock_client.client.invoke_model = Mock(return_value=mock_response)
        
        result = bedrock_client.generate_structured(
            prompt="Predict HS code",
            schema=schema
        )
        
        assert result == json_response
        assert result["hs_code"] == "1234.56"
        assert result["confidence"] == 0.95
    
    def test_generate_structured_with_text_wrapper(self, bedrock_client):
        """Test structured generation when JSON is wrapped in text"""
        schema = {"type": "object"}
        
        mock_response = {
            'body': MagicMock()
        }
        json_response = {"result": "success"}
        # Wrap JSON in extra text
        wrapped_text = f"Here is the JSON:\n{json.dumps(json_response)}\nThat's the result."
        response_body = {
            "content": [
                {"text": wrapped_text}
            ]
        }
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        bedrock_client.client.invoke_model = Mock(return_value=mock_response)
        
        result = bedrock_client.generate_structured(
            prompt="Generate JSON",
            schema=schema
        )
        
        assert result == json_response
    
    def test_generate_structured_invalid_json(self, bedrock_client):
        """Test structured generation with invalid JSON response"""
        schema = {"type": "object"}
        
        mock_response = {
            'body': MagicMock()
        }
        response_body = {
            "content": [
                {"text": "This is not valid JSON"}
            ]
        }
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        bedrock_client.client.invoke_model = Mock(return_value=mock_response)
        
        with pytest.raises(Exception) as exc_info:
            bedrock_client.generate_structured(
                prompt="Generate JSON",
                schema=schema
            )
        
        assert "valid JSON" in str(exc_info.value)
    
    def test_generate_with_retry_success_first_attempt(self, bedrock_client):
        """Test retry logic when first attempt succeeds"""
        mock_response = {
            'body': MagicMock()
        }
        response_body = {"content": [{"text": "Success"}]}
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        bedrock_client.client.invoke_model = Mock(return_value=mock_response)
        
        result = bedrock_client.generate_with_retry(
            prompt="Test prompt",
            max_retries=3
        )
        
        assert result == "Success"
        assert bedrock_client.client.invoke_model.call_count == 1
    
    def test_generate_with_retry_success_after_failures(self, bedrock_client):
        """Test retry logic with transient failures"""
        mock_response = {
            'body': MagicMock()
        }
        response_body = {"content": [{"text": "Success"}]}
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        
        # Fail twice, then succeed
        bedrock_client.client.invoke_model = Mock(
            side_effect=[
                BotoCoreError(),
                BotoCoreError(),
                mock_response
            ]
        )
        
        result = bedrock_client.generate_with_retry(
            prompt="Test prompt",
            max_retries=3
        )
        
        assert result == "Success"
        assert bedrock_client.client.invoke_model.call_count == 3
    
    def test_generate_with_retry_all_attempts_fail(self, bedrock_client):
        """Test retry logic when all attempts fail"""
        bedrock_client.client.invoke_model = Mock(
            side_effect=BotoCoreError()
        )
        
        with pytest.raises(Exception) as exc_info:
            bedrock_client.generate_with_retry(
                prompt="Test prompt",
                max_retries=3
            )
        
        assert "Failed after 3 attempts" in str(exc_info.value)
        assert bedrock_client.client.invoke_model.call_count == 3
    
    def test_generate_with_retry_rate_limit_no_retry(self, bedrock_client):
        """Test that rate limit errors are not retried"""
        bedrock_client.client.invoke_model = Mock(
            side_effect=Exception("Rate limit exceeded")
        )
        
        with pytest.raises(Exception) as exc_info:
            bedrock_client.generate_with_retry(
                prompt="Test prompt",
                max_retries=3
            )
        
        assert "rate limit" in str(exc_info.value).lower()
        # Should not retry on rate limit
        assert bedrock_client.client.invoke_model.call_count == 1
    
    def test_exponential_backoff_timing(self, bedrock_client):
        """Test that exponential backoff delays are correct"""
        bedrock_client.client.invoke_model = Mock(
            side_effect=BotoCoreError()
        )
        
        start_time = time.time()
        
        with pytest.raises(Exception):
            bedrock_client.generate_with_retry(
                prompt="Test prompt",
                max_retries=3
            )
        
        elapsed_time = time.time() - start_time
        
        # Expected delays: 1s + 2s = 3s (plus some overhead)
        # We allow some tolerance for test execution time
        assert elapsed_time >= 3.0
        assert elapsed_time < 4.0
    
    def test_unsupported_model_format_prompt(self, bedrock_client):
        """Test error handling for unsupported model in format_prompt"""
        with pytest.raises(ValueError) as exc_info:
            bedrock_client._format_prompt_for_model(
                "Test prompt",
                None,
                "unsupported.model-v1:0"
            )
        
        assert "Unsupported model" in str(exc_info.value)
    
    def test_unsupported_model_parse_response(self, bedrock_client):
        """Test error handling for unsupported model in parse_response"""
        with pytest.raises(ValueError) as exc_info:
            bedrock_client._parse_response(
                {"text": "response"},
                "unsupported.model-v1:0"
            )
        
        assert "Unsupported model" in str(exc_info.value)


class TestGroqClient:
    """Test suite for GroqClient"""
    
    @pytest.fixture
    def mock_groq_client(self):
        """Create a mock Groq client"""
        # Mock the Groq class at the module level if it doesn't exist
        with patch('services.llm_client.GROQ_AVAILABLE', True):
            with patch('groq.Groq') as mock_groq:
                yield mock_groq
    
    @pytest.fixture
    def groq_client(self, mock_groq_client):
        """Create GroqClient instance with mocked Groq"""
        with patch('services.llm_client.settings') as mock_settings:
            mock_settings.GROQ_API_KEY = "test-api-key"
            mock_settings.GROQ_MODEL = "mixtral-8x7b-32768"
            
            # Patch the Groq import in the module
            with patch('services.llm_client.Groq', mock_groq_client):
                client = GroqClient(
                    api_key="test-api-key",
                    model="mixtral-8x7b-32768",
                    temperature=0.7,
                    max_tokens=1000
                )
                return client
    
    def test_initialization(self, groq_client):
        """Test GroqClient initialization"""
        assert groq_client.api_key == "test-api-key"
        assert groq_client.default_model == "mixtral-8x7b-32768"
        assert groq_client.default_temperature == 0.7
        assert groq_client.default_max_tokens == 1000
        assert groq_client.client is not None
    
    def test_initialization_without_api_key(self):
        """Test GroqClient initialization fails without API key"""
        with patch('services.llm_client.GROQ_AVAILABLE', True):
            with patch('services.llm_client.settings') as mock_settings:
                mock_settings.GROQ_API_KEY = ""
                
                with patch('services.llm_client.Groq'):
                    with pytest.raises(ValueError) as exc_info:
                        GroqClient()
                    
                    assert "API key is required" in str(exc_info.value)
    
    def test_generate_success(self, groq_client):
        """Test successful text generation"""
        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Export compliance refers to..."
        
        groq_client.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = groq_client.generate(
            prompt="What is export compliance?",
            system_prompt="You are an expert.",
            temperature=0.7,
            max_tokens=500
        )
        
        assert result == "Export compliance refers to..."
        assert groq_client.client.chat.completions.create.called
        
        # Verify call arguments
        call_args = groq_client.client.chat.completions.create.call_args
        assert call_args[1]["model"] == "mixtral-8x7b-32768"
        assert call_args[1]["temperature"] == 0.7
        assert call_args[1]["max_tokens"] == 500
        assert len(call_args[1]["messages"]) == 2
        assert call_args[1]["messages"][0]["role"] == "system"
        assert call_args[1]["messages"][1]["role"] == "user"
    
    def test_generate_without_system_prompt(self, groq_client):
        """Test generation without system prompt"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response text"
        
        groq_client.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = groq_client.generate(prompt="Test prompt")
        
        assert result == "Response text"
        
        # Verify only user message is sent
        call_args = groq_client.client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
    
    def test_generate_structured_success(self, groq_client):
        """Test successful structured JSON generation"""
        expected_json = {"hs_code": "8541.10", "confidence": 0.95}
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(expected_json)
        
        groq_client.client.chat.completions.create = Mock(return_value=mock_response)
        
        schema = {
            "type": "object",
            "properties": {
                "hs_code": {"type": "string"},
                "confidence": {"type": "number"}
            }
        }
        
        result = groq_client.generate_structured(
            prompt="Predict HS code for LED lights",
            schema=schema
        )
        
        assert result == expected_json
        assert result["hs_code"] == "8541.10"
        assert result["confidence"] == 0.95
    
    def test_generate_structured_extracts_json(self, groq_client):
        """Test JSON extraction from text response"""
        expected_json = {"status": "success", "value": 42}
        response_text = f"Here is the JSON:\n{json.dumps(expected_json)}\nThat's it!"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = response_text
        
        groq_client.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = groq_client.generate_structured(
            prompt="Test",
            schema={"type": "object"}
        )
        
        assert result == expected_json
    
    def test_generate_structured_invalid_json(self, groq_client):
        """Test error handling for invalid JSON response"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not JSON"
        
        groq_client.client.chat.completions.create = Mock(return_value=mock_response)
        
        with pytest.raises(Exception) as exc_info:
            groq_client.generate_structured(
                prompt="Test",
                schema={"type": "object"}
            )
        
        assert "not return valid JSON" in str(exc_info.value)
    
    def test_rate_limiting(self, groq_client):
        """Test rate limiting enforcement"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"
        
        groq_client.client.chat.completions.create = Mock(return_value=mock_response)
        
        # Make requests up to the limit
        for _ in range(groq_client._max_requests_per_window):
            groq_client.generate("Test prompt")
        
        # Next request should fail
        with pytest.raises(Exception) as exc_info:
            groq_client.generate("Test prompt")
        
        assert "rate limit" in str(exc_info.value).lower()
    
    def test_generate_with_retry_success(self, groq_client):
        """Test retry logic with eventual success"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Success"
        
        # Fail twice, then succeed
        groq_client.client.chat.completions.create = Mock(
            side_effect=[
                Exception("Temporary error"),
                Exception("Another error"),
                mock_response
            ]
        )
        
        result = groq_client.generate_with_retry(
            prompt="Test prompt",
            max_retries=3
        )
        
        assert result == "Success"
        assert groq_client.client.chat.completions.create.call_count == 3
    
    def test_generate_with_retry_all_fail(self, groq_client):
        """Test retry logic when all attempts fail"""
        groq_client.client.chat.completions.create = Mock(
            side_effect=Exception("Persistent error")
        )
        
        with pytest.raises(Exception) as exc_info:
            groq_client.generate_with_retry(
                prompt="Test prompt",
                max_retries=3
            )
        
        assert "Failed after 3 attempts" in str(exc_info.value)
        assert groq_client.client.chat.completions.create.call_count == 3
    
    def test_generate_with_retry_no_retry_on_rate_limit(self, groq_client):
        """Test that rate limit errors are not retried"""
        groq_client.client.chat.completions.create = Mock(
            side_effect=Exception("Rate limit exceeded")
        )
        
        with pytest.raises(Exception) as exc_info:
            groq_client.generate_with_retry(
                prompt="Test prompt",
                max_retries=3
            )
        
        assert "rate limit" in str(exc_info.value).lower()
        # Should not retry on rate limit
        assert groq_client.client.chat.completions.create.call_count == 1
    
    def test_generate_with_retry_no_retry_on_auth_error(self, groq_client):
        """Test that authentication errors are not retried"""
        groq_client.client.chat.completions.create = Mock(
            side_effect=Exception("Authentication failed")
        )
        
        with pytest.raises(Exception) as exc_info:
            groq_client.generate_with_retry(
                prompt="Test prompt",
                max_retries=3
            )
        
        assert "authentication" in str(exc_info.value).lower()
        # Should not retry on auth error
        assert groq_client.client.chat.completions.create.call_count == 1
    
    def test_error_handling_rate_limit(self, groq_client):
        """Test specific error handling for rate limit"""
        groq_client.client.chat.completions.create = Mock(
            side_effect=Exception("rate_limit_exceeded")
        )
        
        with pytest.raises(Exception) as exc_info:
            groq_client.generate("Test prompt")
        
        assert "rate limit" in str(exc_info.value).lower()
    
    def test_error_handling_authentication(self, groq_client):
        """Test specific error handling for authentication"""
        groq_client.client.chat.completions.create = Mock(
            side_effect=Exception("Invalid API key")
        )
        
        with pytest.raises(Exception) as exc_info:
            groq_client.generate("Test prompt")
        
        assert "authentication" in str(exc_info.value).lower()
    
    def test_error_handling_model_not_found(self, groq_client):
        """Test specific error handling for model not found"""
        groq_client.client.chat.completions.create = Mock(
            side_effect=Exception("Model not found: invalid-model")
        )
        
        with pytest.raises(Exception) as exc_info:
            groq_client.generate("Test prompt")
        
        assert "model not found" in str(exc_info.value).lower()


class TestLLMClientFactory:
    """Test suite for LLM client factory"""
    
    @patch('services.llm_client.settings')
    @patch('boto3.client')
    def test_create_bedrock_client(self, mock_boto_client, mock_settings):
        """Test factory creates BedrockClient when USE_GROQ is False"""
        mock_settings.USE_GROQ = False
        
        client = create_llm_client()
        
        assert isinstance(client, BedrockClient)
    
    @patch('services.llm_client.settings')
    @patch('services.llm_client.GROQ_AVAILABLE', True)
    @patch('services.llm_client.Groq')
    def test_create_groq_client(self, mock_groq, mock_settings):
        """Test factory creates GroqClient when USE_GROQ is True"""
        mock_settings.USE_GROQ = True
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.GROQ_MODEL = "mixtral-8x7b-32768"
        
        client = create_llm_client()
        
        assert isinstance(client, GroqClient)
    
    @patch('services.llm_client.settings')
    @patch('services.llm_client.GROQ_AVAILABLE', False)
    def test_create_groq_client_not_available(self, mock_settings):
        """Test factory raises error when Groq library not installed"""
        mock_settings.USE_GROQ = True
        
        with pytest.raises(ImportError) as exc_info:
            create_llm_client()
        
        assert "Groq library not installed" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
