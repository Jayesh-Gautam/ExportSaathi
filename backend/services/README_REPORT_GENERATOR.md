# Report Generator Service

## Overview

The Report Generator Service is a **CRITICAL MVP COMPONENT** that orchestrates the generation of comprehensive export readiness reports for ExportSathi. It combines multiple AI-powered services to provide MSMEs with actionable export guidance.

## Features

### Core Capabilities

1. **HS Code Prediction Integration**
   - Uses existing HSCodePredictor service
   - Handles pre-computed or on-demand prediction
   - Confidence-based alternative suggestions

2. **Certification Identification**
   - Destination-specific certification mapping
   - Business type awareness (Manufacturing/SaaS/Merchant)
   - Mandatory vs optional certification classification
   - Cost and timeline estimation

3. **Risk Analysis**
   - Multi-factor risk scoring (0-100 scale)
   - HS code confidence assessment
   - Restricted substance detection
   - Historical rejection analysis
   - Actionable mitigation strategies

4. **Cost Estimation**
   - Certification costs (min/max ranges)
   - Documentation costs
   - Logistics costs
   - Total cost breakdown in INR

5. **Subsidy Identification**
   - ZED certification subsidy (80% for micro enterprises)
   - RoDTEP benefits
   - Company size-based eligibility

6. **Compliance Roadmap**
   - Step-by-step export readiness plan
   - Dependency tracking
   - Timeline estimation per step
   - GST LUT and documentation guidance

7. **7-Day Action Plan**
   - Day-by-day task breakdown
   - Task categorization (documentation, certification, logistics, finance)
   - Progress tracking support
   - Dependency management

8. **Source Citations**
   - RAG-based document retrieval
   - Regulatory source references
   - Relevance scoring

## Requirements Addressed

- **Requirement 2.2**: Certification identification for product-market combinations
- **Requirement 2.5**: Compliance cost and timeline estimation
- **Requirement 2.6**: Risk score calculation (0-100)
- **Requirement 2.7**: Complete report structure with all sections

## Usage

### Basic Usage

```python
from models.query import QueryInput
from models.enums import BusinessType, CompanySize
from services.report_generator import ReportGenerator

# Create query
query = QueryInput(
    product_name="Organic Turmeric Powder",
    destination_country="United States",
    business_type=BusinessType.MANUFACTURING,
    company_size=CompanySize.MICRO,
    ingredients="100% organic turmeric",
    bom="Turmeric rhizomes, paper packaging"
)

# Generate report
generator = ReportGenerator()
report = generator.generate_report(query)

# Access report components
print(f"HS Code: {report.hs_code.code}")
print(f"Risk Score: {report.risk_score}")
print(f"Total Cost: ₹{report.costs.total:,.2f}")
print(f"Timeline: {report.timeline.estimated_days} days")
print(f"Certifications: {len(report.certifications)}")
```

### With Pre-computed HS Code

```python
from models.query import HSCodePrediction

# Pre-compute HS code
hs_code = HSCodePrediction(
    code="0910.30",
    confidence=92.5,
    description="Turmeric (curcuma)",
    alternatives=[]
)

# Generate report with pre-computed HS code
report = generator.generate_report(query, hs_code=hs_code)
```

### Convenience Function

```python
from services.report_generator import generate_report

# Quick report generation
report = generate_report(query)
```

## Report Structure

### ExportReadinessReport

```python
{
    "report_id": "rpt_abc123",
    "status": "completed",
    "hs_code": {
        "code": "0910.30",
        "confidence": 92.5,
        "description": "Turmeric (curcuma)",
        "alternatives": []
    },
    "certifications": [
        {
            "id": "fda-food-facility",
            "name": "FDA Food Facility Registration",
            "type": "FDA",
            "mandatory": true,
            "estimated_cost": {"min": 15000, "max": 30000, "currency": "INR"},
            "estimated_timeline_days": 30,
            "priority": "high"
        }
    ],
    "restricted_substances": [],
    "past_rejections": [],
    "compliance_roadmap": [
        {
            "step": 1,
            "title": "Apply for GST LUT",
            "description": "Submit Letter of Undertaking...",
            "duration_days": 7,
            "dependencies": []
        }
    ],
    "risks": [
        {
            "title": "Multiple Certifications Required",
            "description": "2 mandatory certifications needed...",
            "severity": "medium",
            "mitigation": "Start certification applications early..."
        }
    ],
    "risk_score": 35,
    "timeline": {
        "estimated_days": 60,
        "breakdown": [
            {"phase": "Documentation", "duration_days": 10},
            {"phase": "Certifications", "duration_days": 30},
            {"phase": "Logistics Setup", "duration_days": 7}
        ]
    },
    "costs": {
        "certifications": 50000,
        "documentation": 10000,
        "logistics": 25000,
        "total": 85000,
        "currency": "INR"
    },
    "subsidies": [
        {
            "name": "ZED Certification Subsidy",
            "amount": 80000,
            "percentage": 80,
            "eligibility": "Micro enterprises only",
            "application_process": "Apply through ZED portal..."
        }
    ],
    "action_plan": {
        "days": [
            {
                "day": 1,
                "title": "Documentation Setup",
                "tasks": [...]
            }
        ],
        "progress_percentage": 0.0
    },
    "retrieved_sources": [
        {
            "title": "DGFT Export Policy 2023",
            "source": "DGFT",
            "excerpt": "All exports require...",
            "relevance_score": 0.95
        }
    ],
    "generated_at": "2024-01-15T10:30:00Z"
}
```

## Certification Identification Logic

### MVP Implementation

The service uses rule-based certification mapping:

#### US Exports
- **Food Products** (HS 01-24): FDA Food Facility Registration
- **All Products**: RoDTEP eligibility

#### EU Exports
- **Electronics/Machinery** (HS 84-85): CE Marking
- **Toys** (HS 95): CE Marking

#### SaaS Exports
- **All SaaS**: SOFTEX Declaration (mandatory)

#### Manufacturing
- **All Manufacturing**: ZED Certification (optional, 80% subsidy for micro enterprises)
- **Electronics/Machinery**: BIS Certification (optional)

### Future Enhancement

The certification identification can be enhanced with:
- RAG-based retrieval from regulatory knowledge base
- LLM-powered certification analysis
- Country-specific regulation databases
- Product category-specific rules

## Risk Scoring Algorithm

### Risk Factors

1. **Base Risk**: 20 points (all exports)

2. **HS Code Confidence** (up to +15 points)
   - Confidence < 70%: +15 points
   - Triggers: "HS Code Uncertainty" risk

3. **Certification Complexity** (up to +10 points)
   - More than 2 mandatory certifications: +10 points
   - Triggers: "Multiple Certifications Required" risk

4. **Restricted Substances** (up to +20 points)
   - Any restricted substance detected: +20 points
   - Triggers: "Restricted Substances Detected" risk

5. **Historical Rejections** (up to +15 points)
   - Past rejections found: +15 points
   - Triggers: "Historical Rejections" risk

### Risk Score Interpretation

- **0-30**: Low Risk - Standard export process
- **31-60**: Medium Risk - Extra caution needed
- **61-100**: High Risk - Expert consultation recommended

## Cost Estimation

### Components

1. **Certification Costs**
   - Sum of average costs for all certifications
   - Uses (min + max) / 2 for each certification

2. **Documentation Costs**
   - Fixed: ₹10,000 (MVP estimate)
   - Covers: Invoice, packing list, shipping bill, GST LUT

3. **Logistics Costs**
   - Fixed: ₹25,000 (MVP estimate)
   - Covers: Freight forwarding, customs clearance

### Future Enhancement

- Dynamic pricing based on destination
- Volume-based logistics costs
- Consultant fees (optional)
- Testing and inspection costs

## Action Plan Generation

### 7-Day Structure

- **Day 1**: Documentation Setup (GST LUT, HS code confirmation)
- **Day 2-3**: Certification Applications
- **Day 4-5**: Export Documentation & Financial Planning
- **Day 6**: Logistics Planning
- **Day 7**: Final Review

### Task Categories

- `documentation`: Document preparation and filing
- `certification`: Certification applications
- `logistics`: Freight and shipping setup
- `finance`: Working capital and financing

## Dependencies

### Required Services

- `HSCodePredictor`: HS code prediction
- `RAGPipeline`: Document retrieval and context
- `LLMClient`: LLM inference (optional for enhanced features)

### Required Models

- `QueryInput`: User query structure
- `ExportReadinessReport`: Report structure
- `Certification`, `Risk`, `ActionPlan`: Component models

## Testing

### Run Tests

```bash
# Run all tests
pytest backend/services/test_report_generator.py -v

# Run specific test
pytest backend/services/test_report_generator.py::TestReportGenerator::test_generate_report_basic -v

# Run with coverage
pytest backend/services/test_report_generator.py --cov=services.report_generator --cov-report=html
```

### Test Coverage

- ✅ Report generation with pre-computed HS code
- ✅ Certification identification (US, EU, SaaS)
- ✅ Restricted substance detection
- ✅ Risk score calculation
- ✅ Cost estimation
- ✅ Subsidy identification
- ✅ Action plan generation
- ✅ Compliance roadmap generation
- ✅ Timeline estimation

## API Integration

### Example API Endpoint

```python
from fastapi import APIRouter, HTTPException
from models.query import QueryInput
from models.report import ExportReadinessReport
from services.report_generator import generate_report

router = APIRouter()

@router.post("/api/reports/generate", response_model=ExportReadinessReport)
async def generate_export_report(query: QueryInput):
    """Generate export readiness report."""
    try:
        report = generate_report(query)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## MVP Limitations & Future Enhancements

### Current MVP Limitations

1. **Certification Identification**: Rule-based, limited coverage
2. **Restricted Substances**: Keyword matching only
3. **Past Rejections**: Not implemented (returns empty list)
4. **Cost Estimation**: Fixed estimates, not dynamic
5. **Source Citations**: Basic RAG retrieval

### Planned Enhancements

1. **RAG-Enhanced Certification Identification**
   - Query knowledge base for country-specific regulations
   - LLM-powered certification analysis
   - Comprehensive coverage of all destinations

2. **Advanced Risk Analysis**
   - ML-based risk prediction
   - Historical data integration
   - Geopolitical risk factors

3. **Dynamic Cost Estimation**
   - Real-time pricing from service providers
   - Volume-based calculations
   - Currency conversion

4. **Past Rejection Database**
   - FDA refusal database integration
   - EU RASFF integration
   - Pattern analysis

5. **Enhanced Action Plans**
   - User progress tracking
   - Automated reminders
   - Integration with calendar systems

## Performance Considerations

### Optimization Tips

1. **Pre-compute HS Code**: Pass pre-computed HS code to avoid redundant prediction
2. **Caching**: Cache certification rules and cost estimates
3. **Async Processing**: Use async/await for parallel operations
4. **Batch Processing**: Generate multiple reports in batch

### Expected Performance

- **Report Generation**: 2-5 seconds (with pre-computed HS code)
- **Full Pipeline**: 10-15 seconds (including HS code prediction)
- **Memory Usage**: ~50-100 MB per report

## Error Handling

### Common Errors

1. **Invalid Query**: Missing required fields
   - Solution: Validate QueryInput before calling

2. **HS Code Prediction Failure**: LLM unavailable
   - Solution: Service returns low-confidence fallback

3. **RAG Pipeline Failure**: Vector store unavailable
   - Solution: Returns empty sources list, continues generation

### Error Recovery

The service is designed to be resilient:
- Continues generation even if optional components fail
- Returns partial reports with warnings
- Logs all errors for debugging

## Logging

### Log Levels

- **INFO**: Report generation progress, component results
- **DEBUG**: Detailed component execution, intermediate results
- **WARNING**: Fallback usage, missing data
- **ERROR**: Component failures, exceptions

### Example Logs

```
INFO: Generating export readiness report for: Organic Turmeric Powder -> United States
INFO: Predicting HS code...
INFO: HS Code: 0910.30 (confidence: 92.5%)
INFO: Identifying required certifications...
INFO: Identified 2 certifications
INFO: Calculating risk score...
INFO: Risk score: 35
INFO: Report generation completed: rpt_abc123
```

## Contributing

When extending the Report Generator:

1. **Add Tests**: Write tests for new functionality
2. **Update Documentation**: Document new features
3. **Maintain MVP Focus**: Keep implementation simple and functional
4. **Log Appropriately**: Add logging for debugging
5. **Handle Errors**: Implement graceful error handling

## Support

For issues or questions:
- Check test cases for usage examples
- Review error logs for debugging
- Consult design.md for architecture details
- See requirements.md for feature specifications
