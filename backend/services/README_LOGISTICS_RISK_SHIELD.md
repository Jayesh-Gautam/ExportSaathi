# Logistics Risk Shield Service

## Overview

The **LogisticsRiskShield** service provides comprehensive logistics risk analysis for export shipments. It helps exporters make informed decisions about shipping options, understand customs inspection risks, evaluate routes, estimate costs, and determine appropriate insurance coverage.

## Features

### 1. LCL vs FCL Comparison
Analyzes whether to use Less than Container Load (LCL) or Full Container Load (FCL) based on:
- Shipment volume (cubic meters)
- Product type and risk level
- Cost-benefit analysis
- Risk assessment

**Recommendation Logic:**
- FCL recommended when container utilization ≥ 60%
- For high-risk products, FCL recommended at ≥ 40% utilization
- LCL recommended for smaller volumes

### 2. RMS Probability Estimation
Estimates the likelihood of customs Risk Management System (RMS) inspection based on:
- Product type (high-risk categories: food, pharmaceutical, chemical, etc.)
- HS code classification
- Red flag keywords in product description
- Historical risk factors

**Risk Factors:**
- Base probability: 15%
- High-risk product types: +20%
- Red flag keywords: +5% per keyword
- High-risk HS codes: +15%
- Maximum probability capped at 95%

### 3. Route Delay Prediction
Predicts shipping route delays based on:
- Destination country and region
- Geopolitical factors (Red Sea tensions, Suez Canal congestion, etc.)
- Seasonal conditions
- Transit time estimates

**Supported Routes:**
- Asia: Direct routes (10 days)
- Middle East: Arabian Sea routes (7 days)
- Europe/North America: Suez Canal or Cape of Good Hope (25-35 days)
- Africa: East Africa routes (15 days)
- South America: Cape of Good Hope (40 days)
- Oceania: Southeast Asia routes (20 days)

### 4. Freight Cost Estimation
Estimates freight costs for different shipping modes:
- **Sea Freight**: Based on volume (CBM)
- **Air Freight**: Based on actual or volumetric weight (whichever is higher)
- Regional pricing variations
- Mode recommendations

**Volumetric Weight Calculation:**
- Volumetric weight = Volume (CBM) × 167 kg/CBM

### 5. Insurance Recommendations
Recommends insurance coverage based on:
- Shipment value
- Risk level assessment
- Coverage type selection

**Insurance Rates:**
- Low risk: 0.3% of coverage
- Medium risk: 0.5% of coverage
- High risk: 0.8% of coverage
- Coverage: 110% of shipment value (standard practice)

### 6. Red Flag Keyword Detection
Identifies keywords in product descriptions that may trigger RMS checks:
- Chemical, powder, liquid, explosive, flammable
- Hazardous, toxic, radioactive
- Pharmaceutical, medicine, supplement
- Herbal, ayurvedic, organic, natural, extract

## Usage

### Basic Usage

```python
from services.logistics_risk_shield import LogisticsRiskShield
from models.logistics import LogisticsRiskRequest

# Initialize service
service = LogisticsRiskShield()

# Create request
request = LogisticsRiskRequest(
    product_type="Turmeric powder",
    hs_code="0910.30",
    volume=10.0,  # cubic meters
    value=200000.0,  # INR
    destination_country="United States",
    product_description="Organic turmeric powder for food use"
)

# Perform complete analysis
analysis = service.analyze_risks(request)

# Access results
print(f"Recommended shipping mode: {analysis.lcl_fcl_comparison.recommendation}")
print(f"RMS probability: {analysis.rms_probability.probability_percentage}%")
print(f"Recommended route: {analysis.route_analysis.recommended_route}")
print(f"Sea freight cost: ${analysis.freight_estimate.sea_freight}")
print(f"Insurance coverage: ${analysis.insurance_recommendation.recommended_coverage}")
```

### Individual Method Usage

#### LCL vs FCL Comparison
```python
comparison = service.compare_lcl_fcl(
    volume=10.0,
    product_type="Textiles"
)

print(f"Recommendation: {comparison.recommendation}")
print(f"LCL cost: ${comparison.lcl.cost}")
print(f"FCL cost: ${comparison.fcl.cost}")
print(f"LCL pros: {comparison.lcl.pros}")
print(f"LCL cons: {comparison.lcl.cons}")
```

#### RMS Probability Estimation
```python
rms = service.estimate_rms_probability(
    product_type="Food",
    hs_code="0910.30",
    description="Organic turmeric powder"
)

print(f"RMS probability: {rms.probability_percentage}%")
print(f"Risk level: {rms.risk_level}")
print(f"Risk factors: {rms.risk_factors}")
print(f"Red flag keywords: {rms.red_flag_keywords}")
print(f"Mitigation tips: {rms.mitigation_tips}")
```

#### Route Analysis
```python
routes = service.predict_route_delays(
    destination="Germany"
)

print(f"Recommended route: {routes.recommended_route}")
for route in routes.routes:
    print(f"Route: {route.name}")
    print(f"Transit time: {route.transit_time_days} days")
    print(f"Delay risk: {route.delay_risk}")
    print(f"Cost: ${route.cost_estimate}")
```

#### Freight Cost Estimation
```python
freight = service.estimate_freight_cost(
    destination="United States",
    volume=10.0,  # CBM
    weight=2000.0  # kg
)

print(f"Sea freight: ${freight.sea_freight}")
print(f"Air freight: ${freight.air_freight}")
print(f"Recommended mode: {freight.recommended_mode}")
```

#### Insurance Recommendation
```python
insurance = service.recommend_insurance(
    shipment_value=200000.0,
    risk_level=RiskSeverity.MEDIUM
)

print(f"Recommended coverage: ${insurance.recommended_coverage}")
print(f"Premium estimate: ${insurance.premium_estimate}")
print(f"Coverage type: {insurance.coverage_type}")
```

#### Red Flag Keyword Detection
```python
keywords = service.detect_red_flag_keywords(
    "Organic turmeric powder with herbal extracts"
)

print(f"Detected keywords: {keywords}")
```

## Data Models

### LogisticsRiskRequest
Input model for risk analysis:
- `product_type`: Type of product
- `hs_code`: Harmonized System code
- `volume`: Shipment volume in CBM
- `value`: Shipment value
- `destination_country`: Destination country
- `product_description`: Product description

### LogisticsRiskAnalysis
Complete analysis output:
- `lcl_fcl_comparison`: LCL vs FCL comparison
- `rms_probability`: RMS check probability
- `route_analysis`: Route analysis with delays
- `freight_estimate`: Freight cost estimates
- `insurance_recommendation`: Insurance recommendations

## Requirements Mapping

This service implements the following requirements from Requirement 6 (Logistics Risk Shield):

- **6.1**: Analyze LCL vs FCL risks based on shipment volume ✓
- **6.2**: Estimate RMS probability for customs inspection ✓
- **6.3**: Predict route delays based on geopolitical factors ✓
- **6.4**: Provide freight cost estimates for different shipping options ✓
- **6.5**: Identify red flag keywords in product descriptions ✓
- **6.6**: Recommend insurance coverage based on shipment value and risk level ✓

## Testing

Run the test suite:
```bash
pytest backend/services/test_logistics_risk_shield.py -v
```

### Test Coverage
- LCL vs FCL comparison (4 tests)
- RMS probability estimation (5 tests)
- Route delay prediction (4 tests)
- Freight cost estimation (4 tests)
- Insurance recommendations (3 tests)
- Red flag keyword detection (3 tests)
- Complete analysis integration (4 tests)

**Total: 27 tests, all passing**

## Configuration

### FCL Container Capacity
- Standard 20ft container: 33 CBM
- Can be adjusted in `__init__` method

### RMS Red Flag Keywords
Configurable list of keywords that trigger higher RMS probability:
```python
self.rms_red_flag_keywords = [
    "chemical", "powder", "liquid", "explosive", "flammable",
    "hazardous", "toxic", "radioactive", "weapon", "drug",
    "pharmaceutical", "medicine", "supplement", "herbal",
    "ayurvedic", "organic", "natural", "extract", "oil"
]
```

### High-Risk Product Types
```python
self.high_risk_product_types = [
    "food", "beverage", "cosmetic", "pharmaceutical", "chemical",
    "supplement", "herbal", "ayurvedic", "medical device"
]
```

### Freight Rates
Base rates by region (configurable):
- Sea freight: USD per CBM
- Air freight: USD per kg

### Geopolitical Risk Database
Current risk factors for major shipping routes:
- Red Sea: HIGH risk, +10 days delay
- Suez Canal: MEDIUM risk, +3 days delay
- Panama Canal: LOW risk, +2 days delay

## Best Practices

1. **Always provide accurate product descriptions** to get reliable RMS probability estimates
2. **Use correct HS codes** for accurate risk assessment
3. **Consider geopolitical factors** when selecting routes
4. **Factor in insurance costs** when calculating total logistics expenses
5. **Review red flag keywords** and adjust product descriptions if needed
6. **Compare LCL vs FCL** for every shipment to optimize costs

## Future Enhancements

Potential improvements:
1. Integration with real-time shipping rate APIs
2. Machine learning model for RMS prediction based on historical data
3. Real-time geopolitical risk monitoring
4. Port-specific requirements and restrictions database
5. Carrier-specific transit time and reliability data
6. Seasonal factor analysis for route delays
7. Carbon footprint calculation for different shipping modes

## Dependencies

- Pydantic: Data validation and serialization
- Python 3.10+: Type hints and modern Python features

## Related Services

- **FinanceModule**: For working capital and cost analysis
- **ReportGenerator**: For including logistics analysis in export readiness reports
- **RAGPipeline**: For retrieving customs regulations and shipping guidelines

## Support

For issues or questions about the Logistics Risk Shield service:
1. Check the test suite for usage examples
2. Review the design document for detailed specifications
3. Consult the requirements document for acceptance criteria
