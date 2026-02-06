# Finance Module Service

## Overview

The Finance Module service provides comprehensive finance readiness analysis for exporters. It helps MSMEs understand their working capital requirements, assess financing options, calculate government benefits, and plan cash flow to avoid the "Liquidity-Compliance Trap."

## Features

### 1. Working Capital Calculation
Calculates total working capital requirements including:
- Product/manufacturing costs
- Certification costs
- Logistics costs
- Documentation costs
- 15% buffer for contingencies

### 2. Pre-Shipment Credit Assessment
Assesses eligibility for pre-shipment credit based on:
- Company size (Micro/Small/Medium)
- Order value
- Interest rates vary by company size:
  - Micro: 7.5% (80% of order value)
  - Small: 8.0% (75% of order value)
  - Medium: 8.5% (70% of order value)

### 3. RoDTEP Benefit Calculation
Calculates Remission of Duties and Taxes on Exported Products (RoDTEP) benefits:
- Uses HS code to determine applicable rate
- Supports exact match, prefix match, and default rates
- Estimates benefit amount based on FOB value

### 4. GST Refund Estimation
Estimates GST refund timeline and amount:
- Typical timeline: 45 days
- Estimates GST at 18% if not provided
- Lists requirements for refund claim

### 5. Cash Flow Timeline Generation
Generates detailed cash flow timeline with:
- Expense events (documentation, certification, production, logistics)
- Income events (customer payment, RoDTEP benefit, GST refund)
- Liquidity gap identification
- Timeline spans ~120 days from start to GST refund

### 6. Financing Options Suggestion
Suggests appropriate financing options based on:
- Company size
- Liquidity gap amount
- Options include:
  - Pre-shipment credit
  - Export credit guarantee (for Micro/Small)
  - Working capital loans
  - Invoice discounting
  - MUDRA loans (for Micro enterprises)

### 7. Currency Hedging Advice
Provides currency hedging recommendations:
- Recommended for exports > ₹10 lakh
- Suggests forward contracts and currency options
- Estimates potential savings

### 8. Bank Referral Programs
Lists bank programs for export financing:
- State Bank of India
- HDFC Bank
- ICICI Bank
- SIDBI (for MSMEs)

## Usage

### Basic Usage

```python
from services.finance_module import FinanceModule
from database.connection import get_db

# Initialize with database session
db = next(get_db())
finance_module = FinanceModule(db)

# Generate complete finance analysis
analysis = finance_module.generate_complete_analysis(report_id="rpt_123")

print(f"Total working capital: ₹{analysis.working_capital.total:,.2f}")
print(f"Pre-shipment credit eligible: {analysis.pre_shipment_credit.eligible}")
print(f"RoDTEP benefit: ₹{analysis.rodtep_benefit.estimated_amount:,.2f}")
print(f"Liquidity gap: ₹{analysis.cash_flow_timeline.liquidity_gap.amount:,.2f}")
```

### Individual Calculations

```python
# Calculate working capital only
working_capital = finance_module.calculate_working_capital(report_id="rpt_123")

# Assess pre-shipment credit eligibility
credit = finance_module.assess_credit_eligibility(
    report_id="rpt_123",
    order_value=200000
)

# Calculate RoDTEP benefit
rodtep = finance_module.calculate_rodtep_benefit(
    hs_code="0910.30",
    destination="United States",
    fob_value=200000
)

# Generate cash flow timeline
timeline = finance_module.generate_cash_flow_timeline(report_id="rpt_123")

# Suggest financing options
options = finance_module.suggest_financing_options(
    report_id="rpt_123",
    liquidity_gap=150000
)
```

## Data Models

### WorkingCapitalAnalysis
```python
{
    "product_cost": 1000000,
    "certification_costs": 50000,
    "logistics_costs": 25000,
    "documentation_costs": 10000,
    "buffer": 162750,  # 15% of subtotal
    "total": 1247750,
    "currency": "INR"
}
```

### PreShipmentCredit
```python
{
    "eligible": True,
    "estimated_amount": 150000,
    "interest_rate": 8.0,
    "tenure_days": 90,
    "requirements": [
        "Valid export order or Letter of Credit (LC)",
        "Company registration documents (GST, IEC)",
        ...
    ]
}
```

### CashFlowTimeline
```python
{
    "events": [
        {
            "date": "2024-02-01",
            "type": "expense",
            "category": "Documentation",
            "amount": -10000,
            "description": "Export documentation preparation"
        },
        ...
    ],
    "liquidity_gap": {
        "start_date": "2024-02-01",
        "end_date": "2024-03-15",
        "amount": 75000
    }
}
```

## Requirements Mapping

This service implements the following requirements from the specification:

- **Requirement 5.1**: Calculate total working capital requirements
- **Requirement 5.2**: Assess pre-shipment credit eligibility
- **Requirement 5.5**: Generate cash-flow timeline showing when expenses occur and when refunds/payments are expected
- **Requirement 5.6**: Identify the liquidity gap period and suggest financing options
- **Requirement 5.7**: Connect users to bank referral programs for export financing

## Testing

The service includes comprehensive unit tests covering:
- Working capital calculation with various inputs
- Pre-shipment credit assessment for different company sizes
- RoDTEP calculation with known and unknown HS codes
- GST refund estimation
- Cash flow timeline generation
- Liquidity gap identification
- Financing options suggestion
- Edge cases and error handling

Run tests:
```bash
cd backend
python -m pytest services/test_finance_module.py -v
```

## Dependencies

- SQLAlchemy: Database ORM
- Pydantic: Data validation and models
- Python 3.10+

## Implementation Notes

### RoDTEP Rates
The service includes a simplified RoDTEP rates database. In production, this should be:
- Loaded from official DGFT RoDTEP schedules
- Updated regularly as rates change
- Stored in a database table for easy updates

### Product Cost Estimation
Product costs are estimated from:
1. Monthly volume × average price (from price range)
2. Fallback: Monthly volume × ₹1000 (default unit price)
3. Default: ₹100,000 if no volume data

### Cash Flow Timeline
The timeline is generated with typical timelines:
- Day 1-7: Documentation preparation
- Day 7-30: Certification applications and testing
- Day 30-45: Production/procurement
- Day 45-60: Logistics and shipping
- Day 90: Customer payment (30 days after shipment)
- Day 105: RoDTEP benefit
- Day 120: GST refund

These timelines can be customized based on actual certification and processing times from the report.

### Liquidity Gap
The liquidity gap is identified by:
1. Calculating cumulative cash flow from all events
2. Finding the period where cumulative cash flow is negative
3. Identifying the maximum negative amount (gap amount)
4. Gap ends when cumulative cash flow becomes positive

## Future Enhancements

1. **Dynamic RoDTEP Rates**: Load from official DGFT database
2. **Bank API Integration**: Real-time interest rates and eligibility checks
3. **Currency Hedging Tools**: Integration with forex platforms
4. **Historical Data**: Track actual vs. estimated timelines
5. **Scenario Analysis**: What-if analysis for different financing options
6. **Export Credit Insurance**: Integration with ECGC for insurance quotes
7. **Working Capital Optimization**: ML-based recommendations for cost reduction

## Related Services

- **Report Generator**: Provides the base report data
- **Certification Solver**: Provides certification costs and timelines
- **Logistics Risk Shield**: Provides logistics costs
- **Document Generator**: Provides documentation costs

## API Integration

This service is exposed through the Finance API router at:
- `GET /api/finance/analysis/{report_id}`: Get complete finance analysis
- `POST /api/finance/working-capital`: Calculate working capital
- `POST /api/finance/rodtep-calculator`: Calculate RoDTEP benefits
- `GET /api/finance/credit-eligibility`: Assess pre-shipment credit
- `GET /api/finance/banks`: List bank referral programs

## Support

For issues or questions about the Finance Module:
1. Check the test cases for usage examples
2. Review the requirements document (Section 5)
3. Check the design document (Finance Module section)
4. Contact the development team
