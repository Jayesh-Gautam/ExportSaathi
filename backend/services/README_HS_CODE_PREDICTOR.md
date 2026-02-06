# HS Code Predictor Service

## Overview

The HS Code Predictor Service provides intelligent prediction of Harmonized System (HS) codes for products using multi-modal analysis. It combines image processing, text analysis, semantic search, and LLM inference to predict the most appropriate HS code with confidence scoring.

**Requirements:** 2.1, 2.8

## Features

- **Multi-modal Product Analysis**: Combines image features with text descriptions
- **Image Feature Extraction**: Uses AWS Textract to extract text, labels, and visual features from product images
- **Semantic Search**: Finds similar products with known HS codes using vector similarity
- **LLM-based Prediction**: Uses large language models to predict HS codes with confidence scores
- **Confidence-based Alternatives**: Returns alternative HS codes when confidence is below 70%
- **Robust Error Handling**: Falls back to similar product HS codes when LLM fails
- **Flexible Input**: Works with or without product images

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HSCodePredictor                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Extract Image Features (if image provided)             │
│     └─> ImageProcessor (AWS Textract)                      │
│         ├─> Text extraction                                │
│         ├─> Label detection                                │
│         └─> Key-value pairs                                │
│                                                             │
│  2. Combine Product Features                               │
│     ├─> Product name                                       │
│     ├─> Ingredients/BOM                                    │
│     ├─> Image text & labels                                │
│     └─> Combined text representation                       │
│                                                             │
│  3. Find Similar Products                                  │
│     └─> Vector Store (semantic search)                     │
│         ├─> Generate query embedding                       │
│         ├─> Search for similar products                    │
│         └─> Filter by has_hs_code=True                     │
│                                                             │
│  4. Predict with LLM                                       │
│     └─> LLM Client (Bedrock/Groq)                          │
│         ├─> Build context from similar products            │
│         ├─> Generate structured prediction                 │
│         └─> Return HS code + confidence + alternatives     │
│                                                             │
│  5. Fallback (if LLM fails)                                │
│     └─> Use most similar product's HS code                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from services.hs_code_predictor import HSCodePredictor

# Initialize predictor
predictor = HSCodePredictor()

# Predict HS code with all inputs
prediction = predictor.predict_hs_code(
    product_name="Organic Turmeric Powder",
    image=image_bytes,  # Optional
    bom="Turmeric rhizomes, packaging material",
    ingredients="100% organic turmeric",
    destination_country="United States"
)

print(f"HS Code: {prediction.code}")
print(f"Confidence: {prediction.confidence}%")
print(f"Description: {prediction.description}")

# Check for alternatives if confidence is low
if prediction.confidence < 70:
    print("\nAlternative HS codes:")
    for alt in prediction.alternatives:
        print(f"  - {alt.code}: {alt.description} ({alt.confidence}%)")
```

### Convenience Function

```python
from services.hs_code_predictor import predict_hs_code

# Quick prediction without creating predictor instance
prediction = predict_hs_code(
    product_name="Turmeric Powder",
    ingredients="100% turmeric"
)
```

### Without Image

```python
# Prediction works without image (text-only)
prediction = predictor.predict_hs_code(
    product_name="Turmeric Powder",
    bom="Turmeric rhizomes",
    ingredients="100% organic turmeric"
)
```

## API Reference

### HSCodePredictor

Main class for HS code prediction.

#### Constructor

```python
HSCodePredictor(
    image_processor: Optional[ImageProcessor] = None,
    embedding_service: Optional[EmbeddingService] = None,
    vector_store: Optional[VectorStore] = None,
    llm_client: Optional[LLMClient] = None,
    confidence_threshold: float = 70.0,
    num_similar_products: int = 5
)
```

**Parameters:**
- `image_processor`: Service for image processing (creates new if None)
- `embedding_service`: Service for embeddings (uses global if None)
- `vector_store`: Vector store for product search (uses global if None)
- `llm_client`: LLM client for prediction (creates new if None)
- `confidence_threshold`: Threshold for returning alternatives (default 70%)
- `num_similar_products`: Number of similar products to retrieve (default 5)

#### Methods

##### predict_hs_code()

Predict HS code from product information.

```python
def predict_hs_code(
    product_name: str,
    image: Optional[bytes] = None,
    bom: Optional[str] = None,
    ingredients: Optional[str] = None,
    destination_country: Optional[str] = None
) -> HSCodePrediction
```

**Parameters:**
- `product_name`: Name of the product (required)
- `image`: Product image bytes (optional)
- `bom`: Bill of Materials (optional)
- `ingredients`: Product ingredients (optional)
- `destination_country`: Destination country for context (optional)

**Returns:** `HSCodePrediction` with:
- `code`: Predicted HS code (format: XXXX.XX)
- `confidence`: Confidence percentage (0-100)
- `description`: Description of what the HS code covers
- `alternatives`: List of alternative HS codes (if confidence < threshold)

**Example:**
```python
prediction = predictor.predict_hs_code(
    product_name="Organic Turmeric Powder",
    ingredients="100% organic turmeric",
    bom="Turmeric rhizomes, packaging material"
)
```

##### extract_image_features()

Extract features from product image using Textract.

```python
def extract_image_features(image: bytes) -> ImageFeatures
```

**Parameters:**
- `image`: Product image bytes

**Returns:** `ImageFeatures` with:
- `text`: Extracted text from image
- `confidence`: Extraction confidence (0-1)
- `detected_labels`: List of detected labels
- `text_blocks`: List of text blocks with positions
- `key_value_pairs`: Extracted key-value pairs
- `tables`: Extracted table data

**Raises:**
- `ValueError`: If image is invalid
- Returns empty features on error instead of raising

##### find_similar_products()

Find similar products with known HS codes using semantic search.

```python
def find_similar_products(
    features: ProductFeatures,
    destination_country: Optional[str] = None
) -> List[Document]
```

**Parameters:**
- `features`: Combined product features
- `destination_country`: Optional country filter

**Returns:** List of similar product documents with HS codes

## Data Models

### HSCodePrediction

```python
class HSCodePrediction(BaseModel):
    code: str                              # HS code (format: XXXX.XX)
    confidence: float                      # Confidence percentage (0-100)
    description: str                       # HS code description
    alternatives: List[HSCodeAlternative]  # Alternative HS codes
```

### HSCodeAlternative

```python
class HSCodeAlternative(BaseModel):
    code: str          # Alternative HS code
    confidence: float  # Confidence percentage
    description: str   # Description
```

### ProductFeatures

```python
@dataclass
class ProductFeatures:
    product_name: str
    description: str
    bom: Optional[str]
    ingredients: Optional[str]
    image_text: Optional[str]
    image_labels: Optional[List[str]]
    visual_features: Optional[Dict[str, Any]]
    combined_text: str
```

## Prediction Algorithm

The HS code prediction follows this algorithm:

1. **Image Feature Extraction** (if image provided):
   - Extract text using AWS Textract
   - Detect labels and objects
   - Extract key-value pairs (e.g., "Weight: 500g")
   - Extract tables (ingredient lists, nutrition facts)

2. **Feature Combination**:
   - Combine product name, ingredients, BOM
   - Add image-extracted text and labels
   - Create unified text representation

3. **Similar Product Search**:
   - Generate embedding from combined features
   - Search vector store for similar products
   - Filter for products with known HS codes
   - Retrieve top N similar products

4. **LLM Prediction**:
   - Build context from similar products
   - Construct prompt with product features and similar products
   - Call LLM with structured output schema
   - Parse HS code, confidence, description, alternatives

5. **Confidence-based Alternatives**:
   - If confidence < 70%, include alternative HS codes
   - Sort alternatives by confidence (descending)

6. **Fallback Mechanism** (if LLM fails):
   - Use most similar product's HS code
   - Cap confidence at 60% for fallback
   - Include alternatives from other similar products

## Error Handling

The predictor implements robust error handling:

1. **Image Processing Errors**:
   - Returns empty features instead of failing
   - Continues with text-only prediction

2. **Vector Store Errors**:
   - Returns empty similar products list
   - LLM still attempts prediction without context

3. **LLM Errors**:
   - Falls back to similar product HS codes
   - Returns low-confidence prediction if no similar products

4. **Complete Failure**:
   - Returns HS code "0000.00" with 0% confidence
   - Includes error description

## Configuration

The predictor can be configured through constructor parameters:

```python
predictor = HSCodePredictor(
    confidence_threshold=75.0,      # Raise threshold for alternatives
    num_similar_products=10         # Retrieve more similar products
)
```

## Dependencies

- **ImageProcessor**: AWS Textract integration for image analysis
- **EmbeddingService**: Sentence transformers for text embeddings
- **VectorStore**: FAISS for semantic similarity search
- **LLMClient**: AWS Bedrock or Groq for LLM inference

## Testing

Run the test suite:

```bash
pytest backend/services/test_hs_code_predictor.py -v
```

### Test Coverage

- ✅ Initialization
- ✅ Prediction with all inputs
- ✅ Prediction without image
- ✅ Low confidence with alternatives
- ✅ Image feature extraction
- ✅ Error handling for image processing
- ✅ Similar product search
- ✅ Metadata filtering
- ✅ Feature combination
- ✅ LLM prompt construction
- ✅ Fallback prediction
- ✅ Complete error handling
- ✅ Convenience function

## Performance Considerations

1. **Image Processing**: AWS Textract calls can take 1-3 seconds
2. **Vector Search**: FAISS search is fast (<100ms for typical datasets)
3. **LLM Inference**: Bedrock/Groq calls take 2-5 seconds
4. **Total Time**: Expect 3-8 seconds for complete prediction with image

## Best Practices

1. **Always provide product name**: This is the minimum required input
2. **Include ingredients/BOM when available**: Improves prediction accuracy
3. **Use high-quality images**: Better image quality = better text extraction
4. **Check confidence scores**: Confidence < 70% indicates uncertainty
5. **Review alternatives**: When confidence is low, consider alternative HS codes
6. **Verify predictions**: Always verify HS codes with official sources

## Future Enhancements

- [ ] Cache predictions for identical products
- [ ] Support for country-specific HS code variations
- [ ] Confidence calibration based on historical accuracy
- [ ] Multi-language support for product descriptions
- [ ] Integration with official HS code databases
- [ ] Batch prediction for multiple products

## Related Services

- **ImageProcessor**: Extracts features from product images
- **EmbeddingService**: Generates embeddings for semantic search
- **VectorStore**: Stores and retrieves similar products
- **LLMClient**: Provides LLM inference capabilities
- **RAGPipeline**: May use HSCodePredictor for HS code queries

## References

- [Harmonized System (HS) Codes](https://www.wcoomd.org/en/topics/nomenclature/overview/what-is-the-harmonized-system.aspx)
- [AWS Textract Documentation](https://docs.aws.amazon.com/textract/)
- [DGFT HS Code Classification](https://www.dgft.gov.in/)
