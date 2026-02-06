"""
LLM Client Service for ExportSathi

This module provides a unified interface for interacting with Large Language Models (LLMs)
through AWS Bedrock. It supports multiple models (Claude 3, Llama 3, Mixtral) with
retry logic, rate limiting, and structured output generation.

Requirements: 11.1, 11.2, 11.4
"""
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from config import settings


logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Supported LLM models"""
    CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
    CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
    LLAMA_3_70B = "meta.llama3-70b-instruct-v1:0"
    LLAMA_3_8B = "meta.llama3-8b-instruct-v1:0"
    MIXTRAL_8X7B = "mistral.mixtral-8x7b-instruct-v0:1"


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        model: Optional[str] = None,
        max_tokens: int = 4096
    ) -> str:
        """
        Generate text response from LLM
        
        Args:
            prompt: User prompt/query
            system_prompt: System instructions for the LLM
            temperature: Sampling temperature (0.0 to 1.0)
            model: Model identifier (uses default if not specified)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response from LLM
        
        Args:
            prompt: User prompt/query
            schema: JSON schema for expected response structure
            system_prompt: System instructions for the LLM
            model: Model identifier (uses default if not specified)
            
        Returns:
            Parsed JSON response matching schema
        """
        pass
    
    @abstractmethod
    def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text with automatic retry on failure
        
        Args:
            prompt: User prompt/query
            max_retries: Maximum number of retry attempts
            system_prompt: System instructions for the LLM
            temperature: Sampling temperature
            model: Model identifier
            
        Returns:
            Generated text response
        """
        pass


class BedrockClient(LLMClient):
    """
    AWS Bedrock client for LLM inference
    
    Supports Claude 3, Llama 3, and Mixtral models with:
    - Exponential backoff retry logic
    - Rate limiting
    - Structured output generation
    - Error handling
    
    Requirements: 11.1, 11.2, 11.4
    """
    
    def __init__(
        self,
        region_name: Optional[str] = None,
        model_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """
        Initialize Bedrock client
        
        Args:
            region_name: AWS region (defaults to settings)
            model_id: Default model ID (defaults to settings)
            temperature: Default temperature
            max_tokens: Default max tokens
        """
        self.region_name = region_name or settings.AWS_REGION
        self.default_model_id = model_id or settings.BEDROCK_MODEL_ID
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        
        # Configure boto3 with retry settings
        config = Config(
            region_name=self.region_name,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            connect_timeout=10,
            read_timeout=60
        )
        
        # Initialize Bedrock runtime client
        self.client = boto3.client(
            'bedrock-runtime',
            config=config,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None
        )
        
        # Rate limiting state
        self._request_times: List[float] = []
        self._rate_limit_window = 60.0  # 1 minute window
        self._max_requests_per_window = 50  # Conservative limit
        
        logger.info(f"Initialized BedrockClient with model {self.default_model_id}")
    
    def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting
        
        Raises:
            Exception: If rate limit is exceeded
        """
        current_time = time.time()
        
        # Remove requests outside the time window
        self._request_times = [
            t for t in self._request_times
            if current_time - t < self._rate_limit_window
        ]
        
        # Check if we've exceeded the limit
        if len(self._request_times) >= self._max_requests_per_window:
            wait_time = self._rate_limit_window - (current_time - self._request_times[0])
            logger.warning(f"Rate limit reached. Need to wait {wait_time:.2f} seconds")
            raise Exception(f"Rate limit exceeded. Please wait {wait_time:.2f} seconds")
        
        # Record this request
        self._request_times.append(current_time)
    
    def _format_prompt_for_model(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model_id: str
    ) -> Dict[str, Any]:
        """
        Format prompt according to model requirements
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            model_id: Model identifier
            
        Returns:
            Formatted request body for the model
        """
        # Claude models use Messages API
        if model_id.startswith("anthropic.claude"):
            messages = [{"role": "user", "content": prompt}]
            body = {
                "messages": messages,
                "max_tokens": self.default_max_tokens,
                "temperature": self.default_temperature,
                "anthropic_version": "bedrock-2023-05-31"
            }
            if system_prompt:
                body["system"] = system_prompt
            return body
        
        # Llama models use different format
        elif model_id.startswith("meta.llama"):
            full_prompt = ""
            if system_prompt:
                full_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_prompt}<|eot_id|>"
            full_prompt += f"<|start_header_id|>user<|end_header_id|>\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
            
            return {
                "prompt": full_prompt,
                "max_gen_len": self.default_max_tokens,
                "temperature": self.default_temperature,
                "top_p": 0.9
            }
        
        # Mixtral models
        elif model_id.startswith("mistral.mixtral"):
            full_prompt = ""
            if system_prompt:
                full_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
            else:
                full_prompt = f"<s>[INST] {prompt} [/INST]"
            
            return {
                "prompt": full_prompt,
                "max_tokens": self.default_max_tokens,
                "temperature": self.default_temperature,
                "top_p": 0.9,
                "top_k": 50
            }
        
        else:
            raise ValueError(f"Unsupported model: {model_id}")
    
    def _parse_response(self, response_body: Dict[str, Any], model_id: str) -> str:
        """
        Parse response based on model type
        
        Args:
            response_body: Raw response from Bedrock
            model_id: Model identifier
            
        Returns:
            Extracted text response
        """
        if model_id.startswith("anthropic.claude"):
            # Claude returns content in messages format
            content = response_body.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
            return ""
        
        elif model_id.startswith("meta.llama"):
            # Llama returns generation
            return response_body.get("generation", "")
        
        elif model_id.startswith("mistral.mixtral"):
            # Mixtral returns outputs
            outputs = response_body.get("outputs", [])
            if outputs and len(outputs) > 0:
                return outputs[0].get("text", "")
            return ""
        
        else:
            raise ValueError(f"Unsupported model: {model_id}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        model: Optional[str] = None,
        max_tokens: int = 4096
    ) -> str:
        """
        Generate text response from Bedrock
        
        Args:
            prompt: User prompt/query
            system_prompt: System instructions for the LLM
            temperature: Sampling temperature (0.0 to 1.0)
            model: Model identifier (uses default if not specified)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If API call fails or rate limit exceeded
        """
        # Check rate limit
        self._check_rate_limit()
        
        model_id = model or self.default_model_id
        
        # Temporarily override defaults for this call
        original_temp = self.default_temperature
        original_max_tokens = self.default_max_tokens
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        
        try:
            # Format prompt for the specific model
            body = self._format_prompt_for_model(prompt, system_prompt, model_id)
            
            logger.debug(f"Calling Bedrock with model {model_id}")
            
            # Call Bedrock API
            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            text_response = self._parse_response(response_body, model_id)
            
            logger.debug(f"Received response of length {len(text_response)}")
            return text_response
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock ClientError: {error_code} - {error_message}")
            raise Exception(f"Bedrock API error: {error_message}")
        
        except BotoCoreError as e:
            logger.error(f"Bedrock BotoCoreError: {str(e)}")
            raise Exception(f"Bedrock connection error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in Bedrock generate: {str(e)}")
            raise
        
        finally:
            # Restore defaults
            self.default_temperature = original_temp
            self.default_max_tokens = original_max_tokens
    
    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response from Bedrock
        
        Args:
            prompt: User prompt/query
            schema: JSON schema for expected response structure
            system_prompt: System instructions for the LLM
            model: Model identifier (uses default if not specified)
            
        Returns:
            Parsed JSON response matching schema
            
        Raises:
            Exception: If response is not valid JSON or doesn't match schema
        """
        # Enhance prompt to request JSON output
        json_prompt = f"""{prompt}

Please respond with valid JSON that matches this schema:
{json.dumps(schema, indent=2)}

Return ONLY the JSON object, no additional text or explanation."""
        
        # Enhance system prompt to emphasize JSON output
        json_system_prompt = system_prompt or ""
        json_system_prompt += "\n\nYou must respond with valid JSON only. Do not include any text outside the JSON object."
        
        # Generate response
        response_text = self.generate(
            prompt=json_prompt,
            system_prompt=json_system_prompt,
            temperature=0.3,  # Lower temperature for more consistent structured output
            model=model
        )
        
        # Try to extract JSON from response
        try:
            # Try direct parsing first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            logger.error(f"Failed to parse JSON from response: {response_text[:200]}")
            raise Exception("LLM did not return valid JSON")
    
    def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text with exponential backoff retry on failure
        
        Args:
            prompt: User prompt/query
            max_retries: Maximum number of retry attempts
            system_prompt: System instructions for the LLM
            temperature: Sampling temperature
            model: Model identifier
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    model=model
                )
            
            except Exception as e:
                last_exception = e
                
                # Don't retry on rate limit errors
                if "rate limit" in str(e).lower():
                    raise
                
                # Calculate exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1.0  # 1s, 2s, 4s, ...
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed")
        
        # All retries exhausted
        raise Exception(f"Failed after {max_retries} attempts: {str(last_exception)}")


class GroqClient(LLMClient):
    """
    Groq API client for LLM inference
    
    Provides an alternative to AWS Bedrock with:
    - Fast inference using Groq's LPU architecture
    - Exponential backoff retry logic
    - Rate limiting
    - Structured output generation
    - Error handling
    
    Supports models: mixtral-8x7b-32768, llama3-70b-8192, llama3-8b-8192, gemma-7b-it
    
    Requirements: 11.1
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key (defaults to settings)
            model: Default model name (defaults to settings)
            temperature: Default temperature
            max_tokens: Default max tokens
            
        Raises:
            ImportError: If groq library is not installed
        """
        if not GROQ_AVAILABLE:
            raise ImportError(
                "Groq library not installed. Install with: pip install groq"
            )
        
        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY in environment.")
        
        self.default_model = model or settings.GROQ_MODEL
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        
        # Rate limiting state
        self._request_times: List[float] = []
        self._rate_limit_window = 60.0  # 1 minute window
        self._max_requests_per_window = 30  # Groq free tier limit
        
        logger.info(f"Initialized GroqClient with model {self.default_model}")
    
    def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting
        
        Raises:
            Exception: If rate limit is exceeded
        """
        current_time = time.time()
        
        # Remove requests outside the time window
        self._request_times = [
            t for t in self._request_times
            if current_time - t < self._rate_limit_window
        ]
        
        # Check if we've exceeded the limit
        if len(self._request_times) >= self._max_requests_per_window:
            wait_time = self._rate_limit_window - (current_time - self._request_times[0])
            logger.warning(f"Rate limit reached. Need to wait {wait_time:.2f} seconds")
            raise Exception(f"Rate limit exceeded. Please wait {wait_time:.2f} seconds")
        
        # Record this request
        self._request_times.append(current_time)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        model: Optional[str] = None,
        max_tokens: int = 4096
    ) -> str:
        """
        Generate text response from Groq
        
        Args:
            prompt: User prompt/query
            system_prompt: System instructions for the LLM
            temperature: Sampling temperature (0.0 to 1.0)
            model: Model identifier (uses default if not specified)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If API call fails or rate limit exceeded
        """
        # Check rate limit
        self._check_rate_limit()
        
        model_name = model or self.default_model
        
        try:
            # Build messages array
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            logger.debug(f"Calling Groq with model {model_name}")
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=False
            )
            
            # Extract response text
            text_response = response.choices[0].message.content
            
            logger.debug(f"Received response of length {len(text_response)}")
            return text_response
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Groq API error: {error_msg}")
            
            # Handle specific error types
            if "rate_limit" in error_msg.lower():
                raise Exception(f"Groq rate limit exceeded: {error_msg}")
            elif "authentication" in error_msg.lower() or "api key" in error_msg.lower() or "api_key" in error_msg.lower():
                raise Exception(f"Groq authentication error: {error_msg}")
            elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                raise Exception(f"Groq model not found: {model_name}")
            else:
                raise Exception(f"Groq API error: {error_msg}")
    
    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response from Groq
        
        Args:
            prompt: User prompt/query
            schema: JSON schema for expected response structure
            system_prompt: System instructions for the LLM
            model: Model identifier (uses default if not specified)
            
        Returns:
            Parsed JSON response matching schema
            
        Raises:
            Exception: If response is not valid JSON or doesn't match schema
        """
        # Enhance prompt to request JSON output
        json_prompt = f"""{prompt}

Please respond with valid JSON that matches this schema:
{json.dumps(schema, indent=2)}

Return ONLY the JSON object, no additional text or explanation."""
        
        # Enhance system prompt to emphasize JSON output
        json_system_prompt = system_prompt or ""
        json_system_prompt += "\n\nYou must respond with valid JSON only. Do not include any text outside the JSON object."
        
        # Generate response with lower temperature for consistency
        response_text = self.generate(
            prompt=json_prompt,
            system_prompt=json_system_prompt,
            temperature=0.3,
            model=model
        )
        
        # Try to extract JSON from response
        try:
            # Try direct parsing first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            logger.error(f"Failed to parse JSON from response: {response_text[:200]}")
            raise Exception("LLM did not return valid JSON")
    
    def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text with exponential backoff retry on failure
        
        Args:
            prompt: User prompt/query
            max_retries: Maximum number of retry attempts
            system_prompt: System instructions for the LLM
            temperature: Sampling temperature
            model: Model identifier
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    model=model
                )
            
            except Exception as e:
                last_exception = e
                
                # Don't retry on rate limit or authentication errors
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "authentication" in error_msg:
                    raise
                
                # Calculate exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1.0  # 1s, 2s, 4s, ...
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed")
        
        # All retries exhausted
        raise Exception(f"Failed after {max_retries} attempts: {str(last_exception)}")


def create_llm_client() -> LLMClient:
    """
    Factory function to create appropriate LLM client based on configuration
    
    Returns:
        LLMClient instance (BedrockClient or GroqClient)
        
    Raises:
        ValueError: If USE_GROQ is True but Groq is not properly configured
    """
    if settings.USE_GROQ:
        if not GROQ_AVAILABLE:
            raise ImportError(
                "Groq library not installed. Install with: pip install groq"
            )
        return GroqClient()
    else:
        return BedrockClient()
