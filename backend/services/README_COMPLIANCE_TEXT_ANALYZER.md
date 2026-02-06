# ComplianceTextAnalyzer Service

## Overview

The `ComplianceTextAnalyzer` service provides compliance text analysis capabilities using AWS Comprehend. It extracts entities, key phrases, and validates compliance-related content from regulatory documents and export documentation.

**Requirements:** 12.5

## Features

- **Entity Extraction**: Extract organizations, locations, dates, quantities, and other entities from compliance documents
- **Key Phrase Extraction**: Identify important phrases and terms in regulatory text
- **Compliance Term Extraction**: Automatically categorize certifications, regulations, standards, and restricted substances
- **Document Validation**: Validate export documents for compliance requirements with scoring
- **Sentiment Analysis**: Analyze sentiment in rejection reasons and feedback

## Installation

The service requires AWS Comprehend to be enabled and configured:

```python
# In .env file
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
COMPREHEND_ENABLED=True
```

## Usage

### Basic Entity Extraction

```python
from compliance_text_analyzer import ComplianceTextAnalyzer

analyzer = ComplianceTextAnalyzer()

text = "FDA approval required for United States export in January 2024"
entities = analyzer.extract_entities(text)

for entity in entities:
    print(f"{entity.text} ({entity.type}): {entity.score:.2f}")
# Output:
# FDA (ORGANIZATION): 0.95
# United States (LOCATION): 0.98
# January 2024 (DATE): 0.92
```

### Entity Extraction with Filtering

```python
# Extract only organizations and locations
entities = analyzer.extract_entities(
    text,
    filter_types=['ORGANIZATION', 'LOCATION']
)
```

### Key Phrase Extraction

```python
text = "FDA approval is required for export compliance with regulatory requirements"
key_phrases = analyzer.extract_key_phrases(text)

for phrase in key_phrases:
    print(f"{phrase.text}: {phrase.score:.2f}")
# Output:
# FDA approval: 0.95
# export compliance: 0.92
# regulatory requirements: 0.88
```

### Compliance Terms Extraction

```python
text = """
FDA approval and CE marking required for export to United States.
REACH regulation compliance needed. ISO 9001 standard applies.
Check lead content and mercury levels.
"""

compliance_terms = analyzer.extract_compliance_terms(text)

print("Certifications:", compliance_terms.certifications)
# ['FDA approval', 'CE marking']

print("Regulations:", compliance_terms.regulations)
# ['REACH regulation']

print("Standards:", compliance_terms.standards)
# ['ISO 9001 standard']

print("Restricted Substances:", compliance_terms.restricted_substances)
# ['lead content', 'mercury levels']

print("Countries:", compliance_terms.countries)
# ['United States']
```

### Document Validation

```python
# Validate a commercial invoice
invoice_text = """
Commercial Invoice
From: Acme Corp, Mumbai, India
To: Global Imports LLC, New York, USA
Date: January 15, 2024
Quantity: 1000 units
Total Value: $50,000
"""

validation = analyzer.validate_document(
    invoice_text,
    document_type='invoice'
)

print(f"Valid: {validation.is_valid}")
print(f"Compliance Score: {validation.compliance_score:.1f}/100")
print(f"Issues: {validation.detected_issues}")
print(f"Suggestions: {validation.suggestions}")
```

### Document Validation with Required Terms

```python
# Validate that specific terms are present
certificate_text = "This certifies that the product meets FDA standards"

validation = analyzer.validate_document(
    certificate_text,
    required_terms=['FDA', 'standards', 'certificate'],
    document_type='certificate'
)

if not validation.is_valid:
    print("Missing terms:", validation.missing_terms)
    # ['certificate']
```

### Sentiment Analysis

```python
# Analyze sentiment in rejection reasons
rejection_text = "Product rejected due to contamination and poor quality control"

sentiment = analyzer.detect_sentiment(rejection_text)

print(f"Sentiment: {sentiment['sentiment']}")
# NEGATIVE

print(f"Negative Score: {sentiment['scores']['negative']:.2f}")
# 0.88
```

## Convenience Functions

For quick one-off operations, use the convenience functions:

```python
from compliance_text_analyzer import (
    extract_entities_from_text,
    extract_key_phrases_from_text,
    extract_compliance_terms_from_text,
    validate_compliance_document
)

# Quick entity extraction
entities = extract_entities_from_text("FDA approval required")

# Quick key phrase extraction
key_phrases = extract_key_phrases_from_text("Export compliance needed")

# Quick compliance terms extraction
terms = extract_compliance_terms_from_text("CE marking and REACH compliance")

# Quick document validation
validation = validate_compliance_document(
    "Invoice text...",
    required_terms=['invoice', 'date', 'amount']
)
```

## Data Models

### Entity

```python
@dataclass
class Entity:
    text: str           # The entity text
    type: str          # Entity type (ORGANIZATION, LOCATION, DATE, etc.)
    score: float       # Confidence score (0-1)
    begin_offset: int  # Start position in text
    end_offset: int    # End position in text
```

### KeyPhrase

```python
@dataclass
class KeyPhrase:
    text: str           # The key phrase text
    score: float       # Confidence score (0-1)
    begin_offset: int  # Start position in text
    end_offset: int    # End position in text
```

### ComplianceTerms

```python
@dataclass
class ComplianceTerms:
    certifications: List[str]        # FDA, CE, REACH, etc.
    regulations: List[str]           # DGFT, customs rules, etc.
    standards: List[str]             # ISO, HACCP, etc.
    restricted_substances: List[str] # Lead, mercury, etc.
    countries: List[str]             # Country names
    organizations: List[str]         # Organization names
```

### DocumentValidation

```python
@dataclass
class DocumentValidation:
    is_valid: bool                  # Whether document passes validation
    compliance_score: float         # Overall score (0-100)
    detected_issues: List[str]      # List of issues found
    missing_terms: List[str]        # Required terms not found
    suggestions: List[str]          # Improvement suggestions
    entities: List[Entity]          # Extracted entities
    key_phrases: List[KeyPhrase]    # Extracted key phrases
```

## Document Type Validation Rules

### Invoice Validation

When `document_type='invoice'`, the validator checks for:
- Organization/company names (buyer and seller)
- Dates (invoice date, shipment date)
- Quantities and values

### Certificate Validation

When `document_type='certificate'`, the validator checks for:
- Certification terms (FDA, CE, ISO, etc.)
- Standards and compliance references

## Compliance Score Calculation

The compliance score (0-100) is calculated based on:

1. **Required Terms** (30 points): Deducted if required terms are missing
2. **Detected Issues** (40 points): Deducted for validation issues (10 points each, max 40)
3. **Entity Coverage** (+10 points): Bonus for good entity coverage (≥5 entities)
4. **Key Phrase Coverage** (+10 points): Bonus for good key phrase coverage (≥10 phrases)

A document is considered valid if:
- Compliance score ≥ 70
- All required terms are present

## Text Length Limits

AWS Comprehend has a 5000 byte limit for text analysis. The service automatically:
- Truncates text longer than 5000 bytes to ~4000 characters
- Logs a warning when truncation occurs
- Continues processing with truncated text

## Error Handling

The service handles errors gracefully:

- **Comprehend Disabled**: Returns empty results instead of raising errors
- **Empty Text**: Raises `ValueError` with clear message
- **API Errors**: Logs error and re-raises `ClientError` for proper handling
- **Unexpected Errors**: Logs error and returns safe default values

## Compliance Keywords

The service recognizes these compliance-related keywords:

### Certifications
- FDA, CE, REACH, BIS, ZED, SOFTEX
- ISO, HACCP, GMP, FSSAI
- Halal, Kosher, Organic
- EPA, RoHS

### Regulations
- DGFT, Customs, GST, IGST
- RoDTEP, MEIS, SEIS
- Regulation, Directive, Act, Rule, Policy, Schedule

### Restricted Substances
- Lead, Mercury, Cadmium, Arsenic
- Pesticide, Antibiotic, Hormone
- Preservative, Additive, Colorant
- Banned, Prohibited

## Integration with Other Services

### With DocumentValidator

```python
from compliance_text_analyzer import ComplianceTextAnalyzer
from document_validator import DocumentValidator

analyzer = ComplianceTextAnalyzer()
validator = DocumentValidator()

# Extract compliance terms from document
compliance_terms = analyzer.extract_compliance_terms(document_text)

# Use terms for validation
validation_result = validator.validate_with_compliance_terms(
    document_text,
    compliance_terms
)
```

### With RAG Pipeline

```python
from compliance_text_analyzer import ComplianceTextAnalyzer
from rag_pipeline import RAGPipeline

analyzer = ComplianceTextAnalyzer()
rag = RAGPipeline()

# Extract key phrases from regulatory document
key_phrases = analyzer.extract_key_phrases(regulatory_text)

# Use key phrases to enhance RAG queries
enhanced_query = " ".join([phrase.text for phrase in key_phrases[:5]])
relevant_docs = rag.retrieve_documents(enhanced_query)
```

## Testing

Run the test suite:

```bash
pytest test_compliance_text_analyzer.py -v
```

The test suite includes:
- Unit tests for all methods
- Mock AWS Comprehend responses
- Edge case handling
- Error scenario testing
- Convenience function testing

## Performance Considerations

- **API Calls**: Each method makes 1 AWS Comprehend API call
- **Text Truncation**: Automatic for texts >5000 bytes
- **Batch Processing**: Not currently supported (process texts individually)
- **Caching**: Consider caching results for repeated analysis of same text

## Cost Estimation

AWS Comprehend pricing (as of 2024):
- **Entity Detection**: $0.0001 per unit (100 characters)
- **Key Phrase Detection**: $0.0001 per unit (100 characters)
- **Sentiment Analysis**: $0.0001 per unit (100 characters)

Example: Analyzing a 1000-character document with all features:
- 3 API calls × 10 units = 30 units
- Cost: 30 × $0.0001 = $0.003 (less than 1 cent)

## Limitations

1. **Language Support**: Currently configured for English only
2. **Text Length**: 5000 byte limit per API call
3. **Batch Processing**: Not supported (process one text at a time)
4. **Custom Entities**: Uses AWS Comprehend's built-in entity types only

## Future Enhancements

- [ ] Support for multiple languages
- [ ] Batch processing for multiple documents
- [ ] Custom entity recognition training
- [ ] Result caching for performance
- [ ] Async API support
- [ ] Integration with AWS Comprehend Medical for healthcare products

## Related Services

- **ImageProcessor**: Extract text from images for analysis
- **DocumentValidator**: Validate export documents
- **RAGPipeline**: Retrieve regulatory documents
- **DocumentGenerator**: Generate compliant documents

## References

- [AWS Comprehend Documentation](https://docs.aws.amazon.com/comprehend/)
- [AWS Comprehend API Reference](https://docs.aws.amazon.com/comprehend/latest/APIReference/)
- [ExportSathi Requirements](../../.kiro/specs/export-readiness-platform/requirements.md)
- [ExportSathi Design](../../.kiro/specs/export-readiness-platform/design.md)
