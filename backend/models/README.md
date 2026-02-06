# ExportSathi Pydantic Models

This directory contains all Pydantic v2.5.3 data models for the ExportSathi platform.

## Overview

The models are organized into logical modules for better maintainability:

### Core Modules

1. **enums.py** - All enumeration types
   - BusinessType, CompanySize, CertificationType
   - RiskSeverity, Priority, DocumentType
   - TaskCategory, ShippingMode, FreightMode
   - ReportStatus, CertificationStatus, MessageRole
   - RejectionSource, CashFlowEventType, ValidationSeverity

2. **common.py** - Shared models used across the platform
   - CostRange - Cost range with min/max values
   - Source - Source citation for documents
   - GuidanceStep - Step in a guidance process

3. **user.py** - User and profile models
   - UserProfile - User account information
   - UserMetrics - User success metrics

4. **query.py** - Query input and HS code models
   - QueryInput - Product and destination input
   - HSCodePrediction - HS code prediction with confidence
   - HSCodeAlternative - Alternative HS codes
   - ImageFeatures - Extracted image features

5. **certification.py** - Certification-related models
   - Certification - Certification requirement
   - CertificationGuidance - Detailed guidance
   - DocumentChecklistItem - Required documents
   - TestLab - Approved test laboratories
   - Consultant - Certification consultants
   - Subsidy - Government subsidies
   - MockAuditQuestion - Mock audit questions

6. **action_plan.py** - 7-day action plan models
   - ActionPlan - Complete 7-day plan
   - DayPlan - Plan for a specific day
   - Task - Individual task

7. **report.py** - Export readiness report models
   - ExportReadinessReport - Complete report
   - RestrictedSubstance - Restricted substances
   - PastRejection - Past rejection data
   - RoadmapStep - Compliance roadmap step
   - Risk - Identified risk
   - Timeline - Timeline with phases
   - CostBreakdown - Cost breakdown

8. **document.py** - Document generation models
   - GeneratedDocument - Generated export document
   - DocumentGenerationRequest - Generation request
   - ValidationResult - Validation results
   - ValidationError - Validation error
   - ValidationWarning - Validation warning

9. **finance.py** - Finance readiness models
   - FinanceAnalysis - Complete finance analysis
   - WorkingCapitalAnalysis - Working capital breakdown
   - PreShipmentCredit - Credit eligibility
   - RoDTEPBenefit - RoDTEP benefit calculation
   - GSTRefund - GST refund estimation
   - CashFlowTimeline - Cash flow timeline
   - CashFlowEvent - Individual cash flow event
   - LiquidityGap - Liquidity gap period
   - CurrencyHedging - Hedging recommendations
   - FinancingOption - Financing options

10. **logistics.py** - Logistics risk models
    - LogisticsRiskAnalysis - Complete risk analysis
    - LogisticsRiskRequest - Analysis request
    - LCLFCLComparison - LCL vs FCL comparison
    - ShippingOption - Shipping option details
    - RMSProbability - RMS check probability
    - RouteAnalysis - Route analysis
    - Route - Individual route
    - FreightEstimate - Freight cost estimate
    - InsuranceRecommendation - Insurance recommendation

11. **chat.py** - Chat and conversation models
    - ChatSession - Chat session
    - ChatMessage - Individual message
    - ChatRequest - Chat request
    - ChatResponse - Chat response
    - QueryContext - Conversation context

12. **internal.py** - Internal service models
    - Document - Retrieved document
    - EmbeddingRequest/Response - Embedding operations
    - VectorSearchRequest/Response - Vector search
    - LLMRequest/Response - LLM operations
    - ErrorResponse - Standard error response

## Features

### Validation Rules

All models include comprehensive validation:

- **Field Validation**: Type checking, min/max values, string patterns
- **Cross-Field Validation**: Totals match sums, dates are in order
- **Business Logic Validation**: 7-day plans have exactly 7 days, progress percentages match completion
- **String Sanitization**: Trimming whitespace, email validation

### Pydantic v2 Features

- **field_validator**: Modern decorator for field validation
- **model_config**: Configuration using dict instead of Config class
- **Field aliases**: Support for both API names and internal names (e.g., `type` → `event_type`)
- **JSON Schema**: Automatic OpenAPI schema generation with examples

### Examples

Each model includes comprehensive examples in `json_schema_extra` for:
- API documentation
- Testing
- Frontend development reference

## Usage

```python
from backend.models import (
    QueryInput,
    BusinessType,
    CompanySize,
    ExportReadinessReport,
)

# Create a query
query = QueryInput(
    product_name="Organic Turmeric Powder",
    destination_country="United States",
    business_type=BusinessType.MANUFACTURING,
    company_size=CompanySize.SMALL,
    monthly_volume=1000.0
)

# Validation happens automatically
print(query.product_name)  # "Organic Turmeric Powder"
```

## Testing

Run the test script to verify all models:

```bash
cd backend
python test_models.py
```

## Requirements Mapping

These models satisfy the following requirements:

- **Requirement 1.1**: Product and destination input validation
- **Requirement 2.7**: Export readiness report structure
- **Requirement 3.1**: Certification guidance models
- **Requirement 4.1**: Document generation models
- **Requirement 5.1**: Finance readiness models
- **Requirement 6.1**: Logistics risk models
- **Requirement 8.7**: Consistent JSON response structure

## Total Models

- **79 models** exported from the models package
- **14 enums** for type safety
- **Comprehensive validation** on all input models
- **Full API contract** coverage

## Notes

- All models use Pydantic v2.5.3 syntax
- Email validation uses custom regex (no email-validator dependency)
- Field aliases handle Python reserved keywords (`type`, `date`)
- All validators use the new `@field_validator` decorator
- Models are fully compatible with FastAPI automatic documentation
