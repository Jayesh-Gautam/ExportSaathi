"""
Example usage of LLM Client Service

This script demonstrates how to use the BedrockClient for various tasks
in the ExportSathi platform.

Requirements: 11.1, 11.2, 11.4
"""
import json
from llm_client import BedrockClient, ModelType, create_llm_client


def example_basic_generation():
    """Example: Basic text generation"""
    print("\n" + "="*60)
    print("Example 1: Basic Text Generation")
    print("="*60)
    
    client = BedrockClient()
    
    prompt = "What are the key export compliance requirements for LED lights to the USA?"
    system_prompt = "You are an expert in Indian export compliance and international trade regulations."
    
    print(f"\nPrompt: {prompt}")
    print("\nGenerating response...")
    
    try:
        response = client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        print(f"\nResponse:\n{response}")
    except Exception as e:
        print(f"\nError: {e}")


def example_structured_output():
    """Example: Structured JSON generation"""
    print("\n" + "="*60)
    print("Example 2: Structured JSON Output")
    print("="*60)
    
    client = BedrockClient()
    
    # Define schema for HS code prediction
    schema = {
        "type": "object",
        "properties": {
            "hs_code": {
                "type": "string",
                "description": "The predicted HS code"
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score between 0 and 1"
            },
            "description": {
                "type": "string",
                "description": "Description of the product category"
            },
            "alternatives": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "hs_code": {"type": "string"},
                        "confidence": {"type": "number"}
                    }
                }
            }
        },
        "required": ["hs_code", "confidence", "description"]
    }
    
    prompt = """Predict the HS code for the following product:
    
Product: LED Light Bulbs (9W, E27 base, warm white, 220V)
Destination: United States

Provide the most likely HS code with confidence score and up to 2 alternatives."""
    
    system_prompt = "You are an HS code classification expert with deep knowledge of international trade nomenclature."
    
    print(f"\nPrompt: {prompt}")
    print("\nGenerating structured response...")
    
    try:
        result = client.generate_structured(
            prompt=prompt,
            schema=schema,
            system_prompt=system_prompt
        )
        print(f"\nStructured Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\nError: {e}")


def example_model_comparison():
    """Example: Compare different models"""
    print("\n" + "="*60)
    print("Example 3: Model Comparison")
    print("="*60)
    
    client = BedrockClient()
    
    prompt = "List the top 3 certifications needed for exporting food products to the EU."
    system_prompt = "You are a certification expert."
    
    models = [
        (ModelType.CLAUDE_3_HAIKU, "Claude 3 Haiku (Fast)"),
        (ModelType.CLAUDE_3_SONNET, "Claude 3 Sonnet (Balanced)"),
        (ModelType.LLAMA_3_8B, "Llama 3 8B (Open Source)")
    ]
    
    print(f"\nPrompt: {prompt}\n")
    
    for model_id, model_name in models:
        print(f"\n--- {model_name} ---")
        try:
            response = client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model_id,
                temperature=0.5
            )
            print(f"Response: {response[:200]}...")  # First 200 chars
        except Exception as e:
            print(f"Error: {e}")


def example_retry_logic():
    """Example: Generation with retry"""
    print("\n" + "="*60)
    print("Example 4: Generation with Retry Logic")
    print("="*60)
    
    client = BedrockClient()
    
    prompt = "What is the RoDTEP benefit rate for HS code 8539.50 exported to USA?"
    system_prompt = "You are an expert in Indian export incentive schemes."
    
    print(f"\nPrompt: {prompt}")
    print("\nGenerating with automatic retry (up to 3 attempts)...")
    
    try:
        response = client.generate_with_retry(
            prompt=prompt,
            system_prompt=system_prompt,
            max_retries=3,
            temperature=0.5
        )
        print(f"\nResponse:\n{response}")
    except Exception as e:
        print(f"\nError after all retries: {e}")


def example_certification_guidance():
    """Example: Generate certification guidance"""
    print("\n" + "="*60)
    print("Example 5: Certification Guidance Generation")
    print("="*60)
    
    client = BedrockClient()
    
    schema = {
        "type": "object",
        "properties": {
            "certification_name": {"type": "string"},
            "why_required": {"type": "string"},
            "steps": {
                "type": "array",
                "items": {"type": "string"}
            },
            "required_documents": {
                "type": "array",
                "items": {"type": "string"}
            },
            "estimated_cost_inr": {
                "type": "object",
                "properties": {
                    "min": {"type": "number"},
                    "max": {"type": "number"}
                }
            },
            "estimated_timeline_days": {"type": "number"},
            "common_rejection_reasons": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
    
    prompt = """Generate detailed guidance for obtaining FDA registration for exporting 
LED lights to the USA. Include steps, documents, costs, timeline, and common issues."""
    
    system_prompt = "You are a certification consultant specializing in US FDA requirements."
    
    print(f"\nPrompt: {prompt}")
    print("\nGenerating certification guidance...")
    
    try:
        result = client.generate_structured(
            prompt=prompt,
            schema=schema,
            system_prompt=system_prompt
        )
        print(f"\nCertification Guidance:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\nError: {e}")


def example_factory_pattern():
    """Example: Using factory pattern"""
    print("\n" + "="*60)
    print("Example 6: Factory Pattern Usage")
    print("="*60)
    
    # Create client using factory (respects USE_GROQ setting)
    client = create_llm_client()
    
    prompt = "What is the difference between LCL and FCL shipments?"
    
    print(f"\nPrompt: {prompt}")
    print("\nGenerating response using factory-created client...")
    
    try:
        response = client.generate(
            prompt=prompt,
            temperature=0.6
        )
        print(f"\nResponse:\n{response}")
    except Exception as e:
        print(f"\nError: {e}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("LLM Client Service - Usage Examples")
    print("="*60)
    print("\nNote: These examples require valid AWS credentials and Bedrock access.")
    print("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file.")
    
    examples = [
        ("Basic Generation", example_basic_generation),
        ("Structured Output", example_structured_output),
        ("Model Comparison", example_model_comparison),
        ("Retry Logic", example_retry_logic),
        ("Certification Guidance", example_certification_guidance),
        ("Factory Pattern", example_factory_pattern)
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    print("\nEnter example number to run (1-6), 'all' to run all, or 'q' to quit:")
    choice = input("> ").strip().lower()
    
    if choice == 'q':
        print("\nExiting...")
        return
    
    if choice == 'all':
        for name, func in examples:
            try:
                func()
            except Exception as e:
                print(f"\nExample '{name}' failed: {e}")
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                examples[idx][1]()
            else:
                print("\nInvalid choice!")
        except ValueError:
            print("\nInvalid input!")
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
