"""
Example usage of ImageProcessor service

This script demonstrates how to use the ImageProcessor service
for text extraction and feature analysis from product images.

Requirements: 1.2, 12.4
"""
import io
from PIL import Image, ImageDraw, ImageFont

from image_processor import ImageProcessor, extract_text_from_image, extract_features_from_image


def create_sample_product_image() -> bytes:
    """
    Create a sample product image with text for testing
    
    Returns:
        bytes: JPEG image bytes
    """
    # Create a white background image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to default if not available
    try:
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_medium = ImageFont.truetype("arial.ttf", 30)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Add product information
    y_position = 50
    
    # Product name
    draw.text((50, y_position), "ORGANIC GREEN TEA", fill='black', font=font_large)
    y_position += 60
    
    # Product details
    draw.text((50, y_position), "Premium Quality", fill='green', font=font_medium)
    y_position += 50
    
    draw.text((50, y_position), "Net Weight: 500g", fill='black', font=font_small)
    y_position += 40
    
    draw.text((50, y_position), "Made in India", fill='black', font=font_small)
    y_position += 40
    
    draw.text((50, y_position), "FDA Approved", fill='blue', font=font_small)
    y_position += 40
    
    draw.text((50, y_position), "Organic Certified", fill='green', font=font_small)
    y_position += 60
    
    # Ingredients section
    draw.text((50, y_position), "Ingredients:", fill='black', font=font_medium)
    y_position += 40
    draw.text((70, y_position), "- Green Tea Leaves (100%)", fill='black', font=font_small)
    y_position += 30
    draw.text((70, y_position), "- Natural Antioxidants", fill='black', font=font_small)
    y_position += 50
    
    # Warning
    draw.text((50, y_position), "CAUTION: Keep in cool, dry place", fill='red', font=font_small)
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    return buffer.getvalue()


def example_basic_text_extraction():
    """Example 1: Basic text extraction"""
    print("=" * 60)
    print("Example 1: Basic Text Extraction")
    print("=" * 60)
    
    # Create sample image
    image_bytes = create_sample_product_image()
    print(f"Created sample image: {len(image_bytes)} bytes")
    
    # Initialize processor
    processor = ImageProcessor()
    
    # Validate image
    print("\n1. Validating image...")
    validation = processor.validate_image(image_bytes)
    print(f"   Valid: {validation.is_valid}")
    print(f"   Format: {validation.format}")
    print(f"   Dimensions: {validation.dimensions}")
    print(f"   Size: {validation.file_size_mb:.2f} MB")
    
    if validation.warnings:
        print(f"   Warnings: {validation.warnings}")
    
    # Extract text (Note: This will fail without AWS credentials)
    print("\n2. Extracting text...")
    try:
        text = processor.extract_text(image_bytes)
        print(f"   Extracted text:\n{text}")
    except Exception as e:
        print(f"   Note: Text extraction requires AWS Textract credentials")
        print(f"   Error: {type(e).__name__}: {e}")
        print(f"   This is expected in local testing without AWS setup")


def example_feature_extraction():
    """Example 2: Comprehensive feature extraction"""
    print("\n" + "=" * 60)
    print("Example 2: Comprehensive Feature Extraction")
    print("=" * 60)
    
    # Create sample image
    image_bytes = create_sample_product_image()
    
    # Initialize processor
    processor = ImageProcessor()
    
    # Extract features (Note: This will fail without AWS credentials)
    print("\n1. Extracting features...")
    try:
        features = processor.extract_features(image_bytes)
        
        print(f"\n2. Results:")
        print(f"   Text: {features.text[:100]}..." if len(features.text) > 100 else f"   Text: {features.text}")
        print(f"   Confidence: {features.confidence:.2f}%")
        print(f"   Detected Labels: {features.detected_labels}")
        print(f"   Key-Value Pairs: {features.key_value_pairs}")
        print(f"   Tables: {len(features.tables)} table(s) found")
        
        if features.tables:
            print(f"\n3. First table:")
            for row in features.tables[0]:
                print(f"   {row}")
                
    except Exception as e:
        print(f"   Note: Feature extraction requires AWS Textract credentials")
        print(f"   Error: {type(e).__name__}: {e}")
        print(f"   This is expected in local testing without AWS setup")


def example_image_preprocessing():
    """Example 3: Image preprocessing"""
    print("\n" + "=" * 60)
    print("Example 3: Image Preprocessing")
    print("=" * 60)
    
    # Create sample PNG image with transparency
    print("\n1. Creating PNG image with transparency...")
    img = Image.new('RGBA', (800, 600), color=(255, 255, 255, 200))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Product Label", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    png_bytes = buffer.getvalue()
    
    print(f"   Original PNG size: {len(png_bytes)} bytes")
    print(f"   Format: PNG")
    print(f"   Mode: RGBA")
    
    # Preprocess
    print("\n2. Preprocessing image...")
    processor = ImageProcessor()
    processed_bytes = processor.preprocess_image(png_bytes)
    
    print(f"   Processed size: {len(processed_bytes)} bytes")
    
    # Verify processed image
    processed_img = Image.open(io.BytesIO(processed_bytes))
    print(f"   Format: {processed_img.format}")
    print(f"   Mode: {processed_img.mode}")
    print(f"   Dimensions: {processed_img.size}")
    
    print("\n   ✓ PNG with transparency converted to JPEG RGB")


def example_convenience_functions():
    """Example 4: Using convenience functions"""
    print("\n" + "=" * 60)
    print("Example 4: Convenience Functions")
    print("=" * 60)
    
    # Create sample image
    image_bytes = create_sample_product_image()
    
    print("\n1. Using extract_text_from_image()...")
    try:
        text = extract_text_from_image(image_bytes)
        print(f"   Extracted: {text[:100]}..." if len(text) > 100 else f"   Extracted: {text}")
    except Exception as e:
        print(f"   Note: Requires AWS Textract credentials")
        print(f"   Error: {type(e).__name__}")
    
    print("\n2. Using extract_features_from_image()...")
    try:
        features = extract_features_from_image(image_bytes)
        print(f"   Confidence: {features.confidence:.2f}%")
        print(f"   Labels: {features.detected_labels}")
    except Exception as e:
        print(f"   Note: Requires AWS Textract credentials")
        print(f"   Error: {type(e).__name__}")


def example_error_handling():
    """Example 5: Error handling"""
    print("\n" + "=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)
    
    processor = ImageProcessor()
    
    # Test 1: Invalid image data
    print("\n1. Testing with invalid image data...")
    invalid_bytes = b'not an image'
    validation = processor.validate_image(invalid_bytes)
    print(f"   Valid: {validation.is_valid}")
    print(f"   Errors: {validation.errors}")
    
    # Test 2: Too small image
    print("\n2. Testing with too small image...")
    tiny_img = Image.new('RGB', (30, 30), color='white')
    buffer = io.BytesIO()
    tiny_img.save(buffer, format='JPEG')
    tiny_bytes = buffer.getvalue()
    
    validation = processor.validate_image(tiny_bytes)
    print(f"   Valid: {validation.is_valid}")
    print(f"   Errors: {validation.errors}")
    
    # Test 3: Graceful handling when Textract disabled
    print("\n3. Testing with Textract disabled...")
    processor.textract_enabled = False
    processor.textract_client = None
    
    sample_bytes = create_sample_product_image()
    text = processor.extract_text(sample_bytes)
    print(f"   Returned empty text: '{text}'")
    print(f"   ✓ Graceful degradation working")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("ImageProcessor Service - Usage Examples")
    print("=" * 60)
    print("\nThese examples demonstrate the ImageProcessor service capabilities.")
    print("Note: AWS Textract features require valid AWS credentials.")
    print("=" * 60)
    
    # Run examples
    example_basic_text_extraction()
    example_feature_extraction()
    example_image_preprocessing()
    example_convenience_functions()
    example_error_handling()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nFor production use:")
    print("1. Configure AWS credentials in .env file")
    print("2. Set TEXTRACT_ENABLED=True")
    print("3. Ensure AWS Textract is available in your region")
    print("4. Implement retry logic for production workloads")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
