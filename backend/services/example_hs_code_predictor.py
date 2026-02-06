"""
Example usage of HS Code Predictor Service

This script demonstrates how to use the HSCodePredictor to predict HS codes
for various products with different input combinations.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.hs_code_predictor import HSCodePredictor, predict_hs_code


def example_1_basic_prediction():
    """Example 1: Basic HS code prediction with product name only"""
    print("=" * 80)
    print("Example 1: Basic Prediction (Product Name Only)")
    print("=" * 80)
    
    predictor = HSCodePredictor()
    
    prediction = predictor.predict_hs_code(
        product_name="Organic Turmeric Powder"
    )
    
    print(f"\nProduct: Organic Turmeric Powder")
    print(f"Predicted HS Code: {prediction.code}")
    print(f"Confidence: {prediction.confidence}%")
    print(f"Description: {prediction.description}")
    
    if prediction.alternatives:
        print(f"\nAlternative HS Codes:")
        for i, alt in enumerate(prediction.alternatives, 1):
            print(f"  {i}. {alt.code} - {alt.description} ({alt.confidence}%)")
    
    print()


def example_2_with_ingredients():
    """Example 2: Prediction with product name and ingredients"""
    print("=" * 80)
    print("Example 2: Prediction with Ingredients")
    print("=" * 80)
    
    predictor = HSCodePredictor()
    
    prediction = predictor.predict_hs_code(
        product_name="Organic Turmeric Powder",
        ingredients="100% organic turmeric (Curcuma longa)",
        bom="Turmeric rhizomes, food-grade packaging material"
    )
    
    print(f"\nProduct: Organic Turmeric Powder")
    print(f"Ingredients: 100% organic turmeric (Curcuma longa)")
    print(f"BOM: Turmeric rhizomes, food-grade packaging material")
    print(f"\nPredicted HS Code: {prediction.code}")
    print(f"Confidence: {prediction.confidence}%")
    print(f"Description: {prediction.description}")
    
    if prediction.alternatives:
        print(f"\nAlternative HS Codes:")
        for i, alt in enumerate(prediction.alternatives, 1):
            print(f"  {i}. {alt.code} - {alt.description} ({alt.confidence}%)")
    
    print()


def example_3_with_destination():
    """Example 3: Prediction with destination country"""
    print("=" * 80)
    print("Example 3: Prediction with Destination Country")
    print("=" * 80)
    
    predictor = HSCodePredictor()
    
    prediction = predictor.predict_hs_code(
        product_name="LED Light Bulbs",
        ingredients="LED chips, aluminum housing, plastic diffuser",
        bom="LED components, heat sink, driver circuit, E27 base",
        destination_country="United States"
    )
    
    print(f"\nProduct: LED Light Bulbs")
    print(f"Destination: United States")
    print(f"Ingredients: LED chips, aluminum housing, plastic diffuser")
    print(f"\nPredicted HS Code: {prediction.code}")
    print(f"Confidence: {prediction.confidence}%")
    print(f"Description: {prediction.description}")
    
    if prediction.alternatives:
        print(f"\nAlternative HS Codes:")
        for i, alt in enumerate(prediction.alternatives, 1):
            print(f"  {i}. {alt.code} - {alt.description} ({alt.confidence}%)")
    
    print()


def example_4_convenience_function():
    """Example 4: Using the convenience function"""
    print("=" * 80)
    print("Example 4: Using Convenience Function")
    print("=" * 80)
    
    # Quick prediction without creating predictor instance
    prediction = predict_hs_code(
        product_name="Cotton T-Shirts",
        ingredients="100% cotton fabric, polyester thread",
        bom="Cotton fabric, thread, labels, packaging"
    )
    
    print(f"\nProduct: Cotton T-Shirts")
    print(f"Predicted HS Code: {prediction.code}")
    print(f"Confidence: {prediction.confidence}%")
    print(f"Description: {prediction.description}")
    
    print()


def example_5_multiple_products():
    """Example 5: Predicting HS codes for multiple products"""
    print("=" * 80)
    print("Example 5: Multiple Product Predictions")
    print("=" * 80)
    
    predictor = HSCodePredictor()
    
    products = [
        {
            "name": "Basmati Rice",
            "ingredients": "100% basmati rice",
            "bom": "Rice grains, packaging"
        },
        {
            "name": "Cashew Nuts",
            "ingredients": "100% cashew nuts, roasted and salted",
            "bom": "Cashew kernels, salt, packaging"
        },
        {
            "name": "Yoga Mats",
            "ingredients": "PVC foam, non-slip coating",
            "bom": "PVC material, coating, carrying strap"
        }
    ]
    
    print("\nPredicting HS codes for multiple products:\n")
    
    for product in products:
        prediction = predictor.predict_hs_code(
            product_name=product["name"],
            ingredients=product["ingredients"],
            bom=product["bom"]
        )
        
        print(f"Product: {product['name']}")
        print(f"  HS Code: {prediction.code}")
        print(f"  Confidence: {prediction.confidence}%")
        print(f"  Description: {prediction.description}")
        print()


def example_6_low_confidence_handling():
    """Example 6: Handling low confidence predictions"""
    print("=" * 80)
    print("Example 6: Handling Low Confidence Predictions")
    print("=" * 80)
    
    predictor = HSCodePredictor(confidence_threshold=70.0)
    
    prediction = predictor.predict_hs_code(
        product_name="Mixed Herbal Tea Blend",
        ingredients="Green tea, chamomile, mint, lemongrass",
        bom="Tea leaves, herbs, tea bags, packaging"
    )
    
    print(f"\nProduct: Mixed Herbal Tea Blend")
    print(f"Predicted HS Code: {prediction.code}")
    print(f"Confidence: {prediction.confidence}%")
    print(f"Description: {prediction.description}")
    
    # Check if confidence is below threshold
    if prediction.confidence < predictor.confidence_threshold:
        print(f"\n⚠️  Confidence is below {predictor.confidence_threshold}%")
        print("Consider reviewing these alternative HS codes:")
        
        if prediction.alternatives:
            for i, alt in enumerate(prediction.alternatives, 1):
                print(f"\n  Alternative {i}:")
                print(f"    Code: {alt.code}")
                print(f"    Confidence: {alt.confidence}%")
                print(f"    Description: {alt.description}")
        else:
            print("  No alternatives available. Manual verification recommended.")
    else:
        print(f"\n✓ High confidence prediction ({prediction.confidence}%)")
    
    print()


def example_7_custom_configuration():
    """Example 7: Custom predictor configuration"""
    print("=" * 80)
    print("Example 7: Custom Predictor Configuration")
    print("=" * 80)
    
    # Create predictor with custom settings
    predictor = HSCodePredictor(
        confidence_threshold=75.0,      # Higher threshold for alternatives
        num_similar_products=10         # Retrieve more similar products
    )
    
    print(f"\nCustom Configuration:")
    print(f"  Confidence Threshold: {predictor.confidence_threshold}%")
    print(f"  Similar Products: {predictor.num_similar_products}")
    
    prediction = predictor.predict_hs_code(
        product_name="Organic Honey",
        ingredients="100% pure organic honey",
        bom="Honey, glass jar, lid, label"
    )
    
    print(f"\nProduct: Organic Honey")
    print(f"Predicted HS Code: {prediction.code}")
    print(f"Confidence: {prediction.confidence}%")
    print(f"Description: {prediction.description}")
    
    print()


def example_8_error_handling():
    """Example 8: Error handling and edge cases"""
    print("=" * 80)
    print("Example 8: Error Handling")
    print("=" * 80)
    
    predictor = HSCodePredictor()
    
    # Test with minimal information
    print("\nTest 1: Minimal information (product name only)")
    prediction = predictor.predict_hs_code(
        product_name="Unknown Product"
    )
    print(f"  HS Code: {prediction.code}")
    print(f"  Confidence: {prediction.confidence}%")
    
    # Test with very specific product
    print("\nTest 2: Very specific product")
    prediction = predictor.predict_hs_code(
        product_name="Organic Fair Trade Single-Origin Ethiopian Coffee Beans",
        ingredients="100% Arabica coffee beans from Ethiopia",
        bom="Coffee beans, biodegradable packaging"
    )
    print(f"  HS Code: {prediction.code}")
    print(f"  Confidence: {prediction.confidence}%")
    
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "HS CODE PREDICTOR EXAMPLES" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    examples = [
        ("Basic Prediction", example_1_basic_prediction),
        ("With Ingredients", example_2_with_ingredients),
        ("With Destination", example_3_with_destination),
        ("Convenience Function", example_4_convenience_function),
        ("Multiple Products", example_5_multiple_products),
        ("Low Confidence Handling", example_6_low_confidence_handling),
        ("Custom Configuration", example_7_custom_configuration),
        ("Error Handling", example_8_error_handling),
    ]
    
    for i, (name, example_func) in enumerate(examples, 1):
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ Example {i} ({name}) failed with error: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("=" * 80)
    print("All examples completed!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    # Note: These examples will only work if:
    # 1. AWS credentials are configured
    # 2. Vector store is initialized with product data
    # 3. LLM client (Bedrock/Groq) is properly configured
    
    print("\n⚠️  Note: These examples require:")
    print("  - AWS credentials configured")
    print("  - Vector store initialized with product data")
    print("  - LLM client (Bedrock/Groq) properly configured")
    print()
    
    response = input("Do you want to run the examples? (y/n): ")
    if response.lower() == 'y':
        main()
    else:
        print("\nExamples not run. Configure the required services first.")
        print("See README_HS_CODE_PREDICTOR.md for setup instructions.")
