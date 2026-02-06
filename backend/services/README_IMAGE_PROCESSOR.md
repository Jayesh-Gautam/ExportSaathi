# ImageProcessor Service

## Overview

The ImageProcessor service provides comprehensive image processing and analysis capabilities using AWS Textract. It extracts text and visual features from product images to assist with HS code prediction and product identification.

**Requirements:** 1.2, 12.4

## Features

- **Text Extraction**: Extract text from product images (labels, packaging info, ingredients)
- **Visual Feature Analysis**: Extract key-value pairs, tables, and detected labels
- **Image Validation**: Validate image format, size, and quality
- **Image Preprocessing**: Optimize images for better text extraction
- **AWS Textract Integration**: Leverage AWS Textract for OCR and document analysis

## Installation

The ImageProcessor service requires the following dependencies:

```bash
pip install boto3 Pillow
```

Ensure AWS credentials are configured in your environment or `.env` file:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
TEXTRACT_ENABLED=True
MAX_IMAGE_SIZE_MB=10
```

## Usage

### Basic Text Extraction

```python
from services.image_processor import ImageProcessor

# Initialize processor
processor = ImageProcessor()

# Read image file
with open('product_image.jpg', 'rb') as f:
    image_bytes = f.read()

# Extract text
text = processor.extract_text(image_bytes)
print(f"Extracted text: {text}")
```

### Comprehensive Feature Extraction

```python
from services.image_processor import ImageProcessor

processor = ImageProcessor()

with open('product_image.jpg', 'rb') as f:
    image_bytes = f.read()

# Extract all features
features = processor.extract_features(image_bytes)

print(f"Text: {features.text}")
print(f"Confidence: {features.confidence}%")
print(f"Detected labels: {features.detected_labels}")
print(f"Key-value pairs: {features.key_value_pairs}")
print(f"Tables: {features.tables}")
```

### Image Validation

```python
from services.image_processor import ImageProcessor

processor = ImageProcessor()

with open('product_image.jpg', 'rb') as f:
    image_bytes = f.read()

# Validate image
validation = processor.validate_image(image_bytes)

if validation.is_valid:
    print(f"Image is valid: {validation.dimensions}, {validation.format}")
else:
    print(f"Validation errors: {validation.errors}")
    print(f"Warnings: {validation.warnings}")
```

### Image Preprocessing

```python
from services.image_processor import ImageProcessor

processor = ImageProcessor()

with open('product_image.png', 'rb') as f:
    image_bytes = f.read()

# Preprocess image (convert to JPEG, resize if needed, optimize)
processed_bytes = processor.preprocess_image(image_bytes)

# Save preprocessed image
with open('processed_image.jpg', 'wb') as f:
    f.write(processed_bytes)
```

### Convenience Functions

```python
from services.image_processor import (
    extract_text_from_image,
    extract_features_from_image
)

# Quick text extraction
with open('product_image.jpg', 'rb') as f:
    text = extract_text_from_image(f.read())

# Quick feature extraction
with open('product_image.jpg', 'rb') as f:
    features = extract_features_from_image(f.read())
```

## API Reference

### ImageProcessor Class

#### `__init__(region_name=None, max_image_size_mb=None)`

Initialize ImageProcessor with optional custom settings.

**Parameters:**
- `region_name` (str, optional): AWS region (defaults to settings)
- `max_image_size_mb` (int, optional): Maximum image size in MB (defaults to settings)

#### `validate_image(image_bytes: bytes) -> ValidationResult`

Validate image format, size, and quality.

**Parameters:**
- `image_bytes` (bytes): Raw image bytes

**Returns:**
- `ValidationResult`: Validation status with errors and warnings

**Example:**
```python
validation = processor.validate_image(image_bytes)
if not validation.is_valid:
    print(f"Errors: {validation.errors}")
```

#### `preprocess_image(image_bytes: bytes) -> bytes`

Preprocess image for better text extraction.

**Parameters:**
- `image_bytes` (bytes): Raw image bytes

**Returns:**
- `bytes`: Preprocessed image bytes

**Preprocessing steps:**
- Convert to RGB/JPEG format
- Resize if too large (max 4096px)
- Optimize compression

#### `extract_text(image_bytes: bytes) -> str`

Extract text from product image using AWS Textract.

**Parameters:**
- `image_bytes` (bytes): Raw image bytes

**Returns:**
- `str`: Extracted text as a single string

**Raises:**
- `ValueError`: If image is invalid
- `ClientError`: If AWS Textract API call fails

**Example:**
```python
try:
    text = processor.extract_text(image_bytes)
    print(f"Extracted: {text}")
except ValueError as e:
    print(f"Invalid image: {e}")
```

#### `extract_features(image_bytes: bytes) -> ImageFeatures`

Extract comprehensive features from product image.

**Parameters:**
- `image_bytes` (bytes): Raw image bytes

**Returns:**
- `ImageFeatures`: Object containing:
  - `text`: Extracted text
  - `confidence`: Average confidence score (0-100)
  - `detected_labels`: List of detected labels
  - `text_blocks`: List of text blocks with positions
  - `key_value_pairs`: Dictionary of key-value pairs
  - `tables`: List of extracted tables
  - `raw_response`: Raw Textract response

**Raises:**
- `ValueError`: If image is invalid
- `ClientError`: If AWS Textract API call fails

**Example:**
```python
features = processor.extract_features(image_bytes)
print(f"Weight: {features.key_value_pairs.get('Weight', 'N/A')}")
print(f"Ingredients table: {features.tables[0] if features.tables else 'None'}")
```

### Data Classes

#### ValidationResult

```python
@dataclass
class ValidationResult:
    is_valid: bool              # Whether image passes validation
    errors: List[str]           # List of validation errors
    warnings: List[str]         # List of validation warnings
    file_size_mb: float         # Image file size in MB
    dimensions: Tuple[int, int] # Image dimensions (width, height)
    format: str                 # Image format (JPEG, PNG, etc.)
```

#### ImageFeatures

```python
@dataclass
class ImageFeatures:
    text: str                           # Extracted text
    confidence: float                   # Overall confidence (0-100)
    detected_labels: List[str]          # Detected labels/objects
    text_blocks: List[Dict[str, Any]]   # Text blocks with positions
    key_value_pairs: Dict[str, str]     # Key-value pairs
    tables: List[List[List[str]]]       # Extracted tables
    raw_response: Dict[str, Any]        # Raw Textract response
```

## Configuration

The ImageProcessor service uses the following configuration settings from `config.py`:

```python
# AWS Configuration
AWS_REGION: str = "us-east-1"
AWS_ACCESS_KEY_ID: str = ""
AWS_SECRET_ACCESS_KEY: str = ""

# AWS Textract
TEXTRACT_ENABLED: bool = True

# File Upload
MAX_IMAGE_SIZE_MB: int = 10
ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/jpg"]
```

## Supported Image Formats

- **JPEG** (.jpg, .jpeg)
- **PNG** (.png)

Images in other formats will be rejected during validation.

## Image Requirements

### Size Limits
- **Maximum file size**: 10 MB (configurable)
- **Minimum dimensions**: 50x50 pixels
- **Maximum dimensions**: 10,000x10,000 pixels (warning issued)
- **Recommended dimensions**: 300x300 pixels or larger for best accuracy

### Quality Recommendations
- Use high-resolution images for better text extraction
- Ensure good lighting and contrast
- Avoid blurry or distorted images
- Text should be clearly visible and legible

## AWS Textract Integration

The ImageProcessor uses two AWS Textract APIs:

### 1. DetectDocumentText
Used by `extract_text()` for simple text extraction.

**Features:**
- Fast text detection
- Line-by-line text extraction
- Confidence scores

### 2. AnalyzeDocument
Used by `extract_features()` for comprehensive analysis.

**Features:**
- Text extraction with positions
- Form data (key-value pairs)
- Table extraction
- Higher accuracy for structured data

## Error Handling

The service handles various error scenarios:

### Image Validation Errors
```python
try:
    text = processor.extract_text(image_bytes)
except ValueError as e:
    # Handle validation errors
    print(f"Invalid image: {e}")
```

### AWS API Errors
```python
from botocore.exceptions import ClientError

try:
    features = processor.extract_features(image_bytes)
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'InvalidParameterException':
        print("Invalid image format")
    elif error_code == 'ProvisionedThroughputExceededException':
        print("Rate limit exceeded, retry later")
```

### Textract Disabled
When Textract is disabled in configuration, the service returns empty results instead of raising errors:

```python
# With TEXTRACT_ENABLED=False
text = processor.extract_text(image_bytes)  # Returns ""
features = processor.extract_features(image_bytes)  # Returns empty ImageFeatures
```

## Testing

Run the comprehensive test suite:

```bash
cd backend/services
python -m pytest test_image_processor.py -v
```

**Test Coverage:**
- Image validation (format, size, quality)
- Image preprocessing (conversion, resizing, optimization)
- Text extraction (success, errors, edge cases)
- Feature extraction (key-value pairs, tables, labels)
- Error handling (invalid images, API errors)
- Integration workflows

## Performance Considerations

### Image Preprocessing
- Large images (>4096px) are automatically resized
- PNG images are converted to JPEG for better compatibility
- Compression is applied to reduce file size

### API Calls
- `extract_text()` uses DetectDocumentText (faster, simpler)
- `extract_features()` uses AnalyzeDocument (slower, more comprehensive)
- Choose the appropriate method based on your needs

### Rate Limiting
AWS Textract has rate limits:
- DetectDocumentText: 5 TPS (transactions per second)
- AnalyzeDocument: 1 TPS

Implement retry logic with exponential backoff for production use.

## Use Cases

### 1. HS Code Prediction
Extract product information from packaging images:
```python
features = processor.extract_features(product_image)
product_name = features.text
ingredients = features.key_value_pairs.get('Ingredients', '')
```

### 2. Compliance Checking
Extract certification labels and warnings:
```python
features = processor.extract_features(product_image)
certifications = [label for label in features.detected_labels 
                  if any(cert in label.lower() 
                         for cert in ['fda', 'ce', 'organic', 'halal'])]
```

### 3. Document Processing
Extract data from invoices, packing lists, certificates:
```python
features = processor.extract_features(document_image)
invoice_data = features.key_value_pairs
line_items = features.tables[0] if features.tables else []
```

### 4. Product Catalog
Build searchable product database from images:
```python
text = processor.extract_text(product_image)
# Index text for search
# Store in database with product metadata
```

## Troubleshooting

### Issue: "Textract is disabled"
**Solution:** Set `TEXTRACT_ENABLED=True` in your `.env` file and ensure AWS credentials are configured.

### Issue: "Invalid image" error
**Solution:** Check image format (JPEG/PNG only), size (<10MB), and dimensions (>50px).

### Issue: Low confidence scores
**Solution:** Use higher resolution images with better lighting and contrast.

### Issue: Missing text in extraction
**Solution:** 
- Ensure text is clearly visible in the image
- Try preprocessing the image first
- Use `extract_features()` instead of `extract_text()` for better accuracy

### Issue: AWS ClientError
**Solution:** 
- Verify AWS credentials are correct
- Check AWS region configuration
- Ensure Textract service is available in your region
- Check for rate limiting (implement retry logic)

## Best Practices

1. **Always validate images** before processing
2. **Preprocess images** for better results
3. **Handle errors gracefully** with try-except blocks
4. **Use appropriate method**: `extract_text()` for simple text, `extract_features()` for structured data
5. **Cache results** to avoid redundant API calls
6. **Implement retry logic** for production use
7. **Monitor costs** - AWS Textract charges per page/image processed
8. **Log errors** for debugging and monitoring

## Cost Optimization

AWS Textract pricing (as of 2024):
- DetectDocumentText: $1.50 per 1,000 pages
- AnalyzeDocument: $50 per 1,000 pages (with FORMS and TABLES)

**Tips to reduce costs:**
1. Use `extract_text()` when you only need text
2. Cache results to avoid reprocessing
3. Validate images before sending to Textract
4. Preprocess images to improve accuracy (fewer retries)
5. Consider batch processing for large volumes

## Future Enhancements

Potential improvements for future versions:

- [ ] Support for additional image formats (TIFF, BMP)
- [ ] Batch processing for multiple images
- [ ] Custom label detection using AWS Rekognition
- [ ] OCR quality assessment and recommendations
- [ ] Automatic image enhancement (contrast, brightness)
- [ ] Multi-language text extraction
- [ ] Barcode and QR code detection
- [ ] Handwriting recognition
- [ ] Result caching with Redis
- [ ] Async processing for large images

## Related Services

- **HSCodePredictor**: Uses ImageProcessor for product image analysis
- **DocumentGenerator**: May use ImageProcessor for document scanning
- **ComplianceTextAnalyzer**: Works with extracted text for compliance checking

## References

- [AWS Textract Documentation](https://docs.aws.amazon.com/textract/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [ExportSathi Design Document](../../.kiro/specs/export-readiness-platform/design.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test cases in `test_image_processor.py`
3. Consult AWS Textract documentation
4. Contact the development team

---

**Last Updated:** 2024
**Version:** 1.0.0
**Status:** Production Ready ✅
