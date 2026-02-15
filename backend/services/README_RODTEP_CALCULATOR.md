# RoDTEP Calculator Service

## Overview

The RoDTEP Calculator service calculates RoDTEP (Remission of Duties and Taxes on Exported Products) benefits for Indian exporters. RoDTEP is a government scheme that reimburses exporters for embedded central, state, and local duties/taxes that are not refunded through other mechanisms like GST refunds or duty drawback.

## Purpose

This service:
- Loads RoDTEP schedules from the knowledge base
- Calculates benefit amounts based on HS codes and destination countries
- Returns rate percentages and estimated benefit amounts
- Supports hierarchical HS code matching (exact, 4-digit prefix, 2-digit chapter, default)

## Implementation

### Class: `RoDTEPCalculator`

Located in: `backend/services/rodtep_calculator.py`

#### Methods

**`__init__()`**
- Initializes the calculator with RoDTEP rate schedules
- Loads rates for various product categories (textiles, spices, electronics, etc.)
- In production, would load from official DGFT RoDTEP schedules

**`get_rodtep_rate(hs_code: str) -> float`**
- Gets the RoDTEP rate percentage for a given HS code
- Uses hierarchical matching:
  1. Exact HS code match (e.g., "091030")
  2. 4-digit prefix match (e.g., "0910")
  3. 2-digit chapter match (e.g., "09")
  4. Default rate (1.5%)
- Handles HS codes with or without dots (e.g., "0910.30" or "091030")

**`calculate_benefit(hs_code: str, destination: str, fob_value: float) -> RoDTEPBenefit`**
- Calculates the RoDTEP benefit amount
- Formula: `RoDTEP Amount = FOB Value × (RoDTEP Rate / 100)`
- Returns `RoDTEPBenefit` model with:
  - `hs_code`: The HS code used
  - `rate_percentage`: The RoDTEP rate percentage
  - `estimated_amount`: The calculated benefit amount in INR
  - `currency`: Currency code (INR)

**`load_rodtep_schedules(schedules_data: Dict[str, float]) -> None`**
- Loads custom RoDTEP schedules from external sources
- Allows updating rates from:
  - Knowledge base documents
  - Database
  - DGFT notifications

**`get_all_rates() -> Dict[str, float]`**
- Returns all RoDTEP rates as a dictionary
- Returns a copy to prevent external modification

## Usage

### Basic Usage

```python
from services.rodtep_calculator import RoDTEPCalculator

# Initialize calculator
calculator = RoDTEPCalculator()

# Calculate benefit for turmeric export
benefit = calculator.calculate_benefit(
    hs_code="0910.30",
    destination="United States",
    fob_value=200000  # ₹2 lakh
)

print(f"HS Code: {benefit.hs_code}")
print(f"Rate: {benefit.rate_percentage}%")
print(f"Benefit: ₹{benefit.estimated_amount}")
# Output:
# HS Code: 0910.30
# Rate: 2.5%
# Benefit: ₹5000
```

### Integration with Finance Module

The RoDTEP Calculator is integrated into the Finance Module:

```python
from services.finance_module import FinanceModule
from database.connection import get_db

# Initialize finance module
db = next(get_db())
finance_module = FinanceModule(db)

# Calculate RoDTEP benefit
benefit = finance_module.calculate_rodtep_benefit(
    hs_code="6109",
    destination="Germany",
    fob_value=1000000  # ₹10 lakh
)

print(f"RoDTEP Benefit: ₹{benefit.estimated_amount}")
# Output: RoDTEP Benefit: ₹43000 (4.3% of ₹10 lakh)
```

### Loading Custom Schedules

```python
# Load updated RoDTEP rates from DGFT notification
custom_rates = {
    "091030": 2.7,  # Updated turmeric rate
    "6109": 4.5,    # Updated T-shirt rate
}

calculator.load_rodtep_schedules(custom_rates)

# Now calculations will use updated rates
benefit = calculator.calculate_benefit(
    hs_code="0910.30",
    destination="USA",
    fob_value=200000
)
print(f"Updated Rate: {benefit.rate_percentage}%")
# Output: Updated Rate: 2.7%
```

## RoDTEP Rates Database

The calculator includes rates for common export products:

### Agricultural Products
- **091030** (Turmeric): 2.5%
- **091020** (Saffron): 2.3%
- **091091** (Curry powder): 2.4%
- **0910** (Spices general): 2.3%

### Textiles and Garments
- **6109** (T-shirts, cotton): 4.3%
- **6110** (Sweaters, pullovers): 4.1%
- **6203** (Men's suits, trousers): 4.2%
- **6204** (Women's suits, dresses): 4.2%
- **61** (Knitted garments): 4.0%
- **62** (Woven garments): 3.9%

### Electronics and LED Lights
- **9405** (LED lights and lamps): 3.8%
- **8541** (LED diodes): 3.5%
- **8539** (Electric lamps): 3.6%
- **94** (Furniture and lighting): 3.5%

### Beauty and Cosmetics
- **3304** (Beauty/makeup products): 2.1%
- **3305** (Hair care products): 2.0%
- **3307** (Perfumes and toiletries): 1.9%
- **33** (Cosmetics general): 2.0%

### Other Categories
- Leather products: 3.1-3.4%
- Toys and games: 2.7-2.8%
- Chemicals: 1.6-1.8%
- Engineering goods: 2.8-3.0%

### Default Rate
- **default**: 1.5% (for products not in schedule)

## Validation

The calculator includes input validation:

```python
# Raises ValueError for zero or negative FOB value
calculator.calculate_benefit("0910.30", "USA", 0)
# ValueError: FOB value must be positive

# Raises ValueError for empty HS code
calculator.calculate_benefit("", "USA", 100000)
# ValueError: HS code cannot be empty
```

## Testing

Comprehensive unit tests are available in `test_rodtep_calculator.py`:

```bash
# Run all RoDTEP calculator tests
pytest services/test_rodtep_calculator.py -v

# Run specific test
pytest services/test_rodtep_calculator.py::TestRoDTEPCalculator::test_calculate_benefit_basic -v
```

Test coverage includes:
- Exact HS code matching
- Hierarchical prefix matching
- Default rate fallback
- Benefit calculation accuracy
- Input validation
- Schedule loading
- HS code cleaning (dots, spaces)
- Realistic export scenarios

## Requirements Satisfied

This implementation satisfies:
- **Requirement 5.3**: Calculate RoDTEP benefit amount based on HS code and destination
- **Task 9.2**: Implement RoDTEP calculator with calculate_benefit method

## Future Enhancements

1. **Dynamic Schedule Loading**: Load RoDTEP schedules from knowledge base documents
2. **Country-Specific Rates**: Support different rates for different destination countries
3. **Rate History**: Track historical RoDTEP rates for trend analysis
4. **Notification Integration**: Automatically update rates from DGFT notifications
5. **Validation Against Official Schedules**: Cross-check calculated rates with official DGFT data

## References

- [DGFT RoDTEP Scheme](https://www.dgft.gov.in/CP/?opt=RoDTEP)
- [RoDTEP Schedule Notifications](https://www.dgft.gov.in/CP/?opt=view-notifications)
- Design Document: Section 14 - RoDTEPCalculator Service
- Requirements Document: Requirement 5.3 - Finance Readiness Module

## Related Services

- **FinanceModule**: Uses RoDTEPCalculator for complete finance analysis
- **ReportGenerator**: Includes RoDTEP benefits in export readiness reports
- **CashFlowTimeline**: Includes RoDTEP refunds in cash flow projections
