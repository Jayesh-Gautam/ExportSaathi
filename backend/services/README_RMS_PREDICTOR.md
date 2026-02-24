# RMS Predictor Service

## Overview

The RMS Predictor service estimates the probability of customs inspection under India's Risk Management System (RMS). RMS is the automated customs screening system that flags shipments for physical inspection based on various risk factors.

This service helps exporters:
- Understand their inspection risk level
- Identify specific risk factors in their shipment
- Receive actionable mitigation strategies
- Avoid common triggers that lead to delays

## Features

### 1. Probability Estimation
- Calculates RMS check probability (0-100%)
- Considers multiple risk factors:
  - Product type and category
  - HS code classification
  - Product description keywords
  - Export history
  - Shipment value
- Returns risk level (LOW, MEDIUM, HIGH)

### 2. Risk Factor Identification
- Detects high-risk product categories
- Identifies red flag keywords in descriptions
- Assesses HS code risk levels
- Evaluates export history impact
- Considers first-time exporter status

### 3. Red Flag Keyword Detection
- Comprehensive database of 50+ keywords
- Categories include:
  - Chemical and hazardous materials
  - Pharmaceuticals and drugs
  - Herbal and natural products
  - Weapons and controlled items
  - Dual-use technology
  - High-value items

### 4. Mitigation Strategies
- Provides 5-15 actionable tips per assessment
- Tailored to specific risk factors
- Includes documentation requirements
- Suggests certification needs
- Recommends customs broker assistance

## Usage

### Basic Usage

```python
from services.rms_predictor import RMSPredictor

# Create predictor instance
predictor = RMSPredictor()

# Predict RMS probability
result = predictor.predict_probability(
    product_type="Food supplement",
    hs_code="0910.30",
    description="Organic turmeric powder for health and wellness"
)

print(f"Probability: {result.probability_percentage}%")
print(f"Risk Level: {result.risk_level}")
print(f"Risk Factors: {result.risk_factors}")
print(f"Red Flag Keywords: {result.red_flag_keywords}")
print(f"Mitigation Tips: {result.mitigation_tips}")
```

### With Export History

```python
# Include export history for more accurate assessment
result = predictor.predict_probability(
    product_type="Pharmaceutical",
    hs_code="3004.90",
    description="Pharmaceutical tablets for medical use",
    export_history={
        "is_first_time_exporter": True,
        "past_violations": False,
        "high_value_shipment": True,
        "export_count": 0
    }
)
```

### Identify Risk Factors Only

```python
# Get risk factors without full probability calculation
risk_factors = predictor.identify_risk_factors(
    product_type="Chemical",
    description="Industrial chemical powder for manufacturing"
)

print(f"Risk Factors: {risk_factors}")
```

## Risk Assessment Logic

### Base Probability
- Starting point: 15% (average RMS check rate in India)

### Risk Factor Additions
1. **High-risk product type**: +20%
   - Food, beverage, cosmetic, pharmaceutical, chemical
   - Supplement, herbal, ayurvedic, medical device
   - Electronics, battery, agricultural products

2. **Red flag keywords**: +5% per keyword (capped at +25%)
   - Chemical, powder, liquid, explosive, flammable
   - Drug, pharmaceutical, medicine, supplement
   - Herbal, organic, natural, extract

3. **High-risk HS code**: +15%
   - Chapter 29: Organic chemicals
   - Chapter 30: Pharmaceutical products
   - Chapter 33: Essential oils and cosmetics
   - Chapter 38: Miscellaneous chemical products
   - Chapter 84: Nuclear reactors and machinery
   - Chapter 85: Electrical machinery
   - Chapter 90: Optical, medical instruments
   - Chapter 93: Arms and ammunition

4. **Medium-risk HS code**: +8%
   - Chapters 04-22: Food and beverages
   - Chapters 61-63: Textiles and apparel
   - Chapter 71: Precious stones and metals

5. **Export history factors**:
   - First-time exporter: +10%
   - Past violations: +15%
   - High-value shipment (>$50,000): +5%
   - Experienced exporter (>10 shipments, clean record): -5%

### Probability Cap
- Maximum probability: 95% (never 100% certain)

### Risk Level Determination
- **HIGH**: Probability ≥ 50%
- **MEDIUM**: Probability 30-49%
- **LOW**: Probability < 30%

## Mitigation Tips

The service provides tailored mitigation tips based on risk factors:

### Universal Tips (Always Included)
- Provide detailed and accurate product documentation
- Ensure all documents are consistent and error-free
- Declare correct HS code and product classification
- Include complete ingredient/component list with percentages

### Red Flag Keyword Tips
- Use technical/scientific names instead of generic terms
- Avoid using red flag keywords; be specific and precise
- Provide Material Safety Data Sheets (MSDS) if applicable

### High-Risk Product Tips
- Obtain pre-clearance certifications (FDA, FSSAI, BIS, etc.)
- Include test certificates and quality reports from accredited labs
- Work with experienced customs broker familiar with your product category
- Consider pre-shipment inspection by authorized agencies

### First-Time Exporter Tips
- Register with relevant export promotion councils
- Attend customs facilitation workshops
- Consider using a customs house agent (CHA) for first few shipments
- Start with smaller shipments to build export track record

### High-Risk Level Tips
- Consider voluntary pre-inspection to identify issues early
- Maintain comprehensive documentation trail for audit
- Budget extra time for potential customs delays (3-5 days)
- Ensure product packaging clearly displays all required information

## Integration with Knowledge Base

The RMS Predictor can be integrated with a knowledge base (RAG pipeline) to retrieve:
- Specific customs RMS rules for product categories
- Historical inspection rates by HS code
- Recent regulatory changes
- Country-specific requirements

```python
from services.rag_pipeline import RAGPipeline

# Create predictor with knowledge base
rag_pipeline = RAGPipeline()
predictor = RMSPredictor(knowledge_base=rag_pipeline)

# Predictions will now include insights from knowledge base
result = predictor.predict_probability(
    product_type="Food",
    hs_code="0910.30",
    description="Turmeric powder"
)
```

## Examples

### Example 1: Low-Risk Product
```python
result = predictor.predict_probability(
    product_type="Textile",
    hs_code="6109.10",
    description="100% cotton knitted T-shirts for men, crew neck, short sleeves"
)
# Expected: 15-25% probability, LOW risk
```

### Example 2: Medium-Risk Product
```python
result = predictor.predict_probability(
    product_type="Food",
    hs_code="0910.30",
    description="Turmeric powder for cooking and culinary use"
)
# Expected: 30-45% probability, MEDIUM risk
```

### Example 3: High-Risk Product
```python
result = predictor.predict_probability(
    product_type="Pharmaceutical",
    hs_code="3004.90",
    description="Pharmaceutical tablets containing chemical compounds for medical use",
    export_history={"is_first_time_exporter": True}
)
# Expected: 60-80% probability, HIGH risk
```

## Testing

Run the test suite:
```bash
pytest backend/services/test_rms_predictor.py -v
```

Test coverage includes:
- Low, medium, and high-risk products
- Red flag keyword detection
- HS code risk assessment
- Export history impact
- Probability bounds and capping
- Risk level consistency
- Mitigation tip quality
- Edge cases (empty descriptions, invalid HS codes)

## Dependencies

- `pydantic`: Data validation and models
- `models.logistics`: RMSProbability model
- `models.enums`: RiskSeverity enum

## Related Services

- **LogisticsRiskShield**: Uses RMSPredictor for comprehensive logistics risk analysis
- **RAGPipeline**: Can provide knowledge base integration for enhanced predictions
- **ReportGenerator**: Includes RMS probability in export readiness reports

## Future Enhancements

1. **Machine Learning Model**: Train ML model on historical RMS data for more accurate predictions
2. **Country-Specific Rules**: Expand to include destination country customs requirements
3. **Real-Time Data**: Integrate with live customs data feeds
4. **Historical Trends**: Track RMS check rates over time by product category
5. **Seasonal Factors**: Consider seasonal variations in inspection rates
6. **Port-Specific Data**: Include port-specific RMS patterns

## References

- DGFT (Directorate General of Foreign Trade) regulations
- Indian Customs RMS guidelines
- HS Code classification system
- Export compliance best practices

## Support

For questions or issues with the RMS Predictor service, please refer to:
- Design document: `.kiro/specs/export-readiness-platform/design.md`
- Requirements: `.kiro/specs/export-readiness-platform/requirements.md` (Requirement 6.2, 6.5)
- Task list: `.kiro/specs/export-readiness-platform/tasks.md` (Task 10.2)
