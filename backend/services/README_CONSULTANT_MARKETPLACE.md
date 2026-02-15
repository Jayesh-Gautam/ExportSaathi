# Consultant Marketplace Service

## Overview

The Consultant Marketplace Service provides search and filter functionality for finding consultants who can help with certification acquisition. This service is part of the Certification Solver and Guidance System.

**Requirements:** 3.4

## Features

### 1. Consultant Data Model

Each consultant has the following attributes:
- **id**: Unique identifier
- **name**: Consultant/company name
- **specialization**: List of areas of expertise
- **rating**: Rating from 0-5 stars
- **cost_range**: Min and max consultation costs in INR
- **contact**: Email, phone, and website
- **experience_years**: Years of experience
- **certifications_handled**: List of certifications they specialize in
- **success_rate**: Success rate percentage (optional)
- **location**: Geographic location (optional)

### 2. Search and Filter Functionality

The marketplace supports comprehensive search and filtering:

#### Filter Options:
- **certification_type**: Filter by certification (e.g., "FDA", "CE", "BIS")
- **min_rating**: Minimum rating threshold (0-5)
- **max_cost**: Maximum cost budget
- **min_experience**: Minimum years of experience
- **location**: Geographic location (partial match)
- **specialization**: Area of expertise (partial match)

#### Sort Options:
- **sort_by**: "rating", "cost", or "experience"
- **sort_order**: "asc" or "desc"

### 3. API Endpoints

#### Search Consultants
```
GET /api/certifications/consultants/search
```

Query Parameters:
- `certification_type` (optional): Filter by certification type
- `min_rating` (optional): Minimum rating (0-5)
- `max_cost` (optional): Maximum cost in INR
- `min_experience` (optional): Minimum years of experience
- `location` (optional): Filter by location
- `specialization` (optional): Filter by specialization
- `sort_by` (optional): Sort field (default: "rating")
- `sort_order` (optional): Sort order (default: "desc")

Example:
```bash
GET /api/certifications/consultants/search?certification_type=FDA&min_rating=4.0&sort_by=rating
```

#### Get Consultant Details
```
GET /api/certifications/consultants/{consultant_id}
```

Returns complete information about a specific consultant.

Example:
```bash
GET /api/certifications/consultants/cons-fda-1
```

#### Get Consultants for Certification
```
GET /api/certifications/{cert_id}/consultants
```

Returns top-rated consultants for a specific certification (used in certification guidance).

Example:
```bash
GET /api/certifications/fda-food-facility/consultants
```

## Usage Examples

### Python Service Usage

```python
from services.consultant_marketplace import get_consultant_marketplace

# Get marketplace instance
marketplace = get_consultant_marketplace()

# Search for FDA consultants with high ratings
consultants = marketplace.search_consultants(
    certification_type="FDA",
    min_rating=4.5,
    sort_by="rating",
    sort_order="desc"
)

# Get consultant by ID
consultant = marketplace.get_consultant_by_id("cons-fda-1")

# Get top consultants for a certification
top_consultants = marketplace.get_consultants_for_certification(
    "fda-food-facility",
    limit=5
)
```

### API Usage

```bash
# Search for CE consultants in Mumbai with budget under 100k
curl "http://localhost:8000/api/certifications/consultants/search?certification_type=CE&location=Mumbai&max_cost=100000"

# Get details of a specific consultant
curl "http://localhost:8000/api/certifications/consultants/cons-ce-1"

# Get consultants for BIS certification
curl "http://localhost:8000/api/certifications/bis-certification/consultants"
```

## Sample Consultants

The marketplace includes consultants for:
- **FDA**: Food facility registration, FSVP, labeling
- **CE Marking**: EU compliance, technical files, product safety
- **BIS**: Indian standards, ISI mark, factory audits
- **SOFTEX**: Software export declarations, STPI
- **ZED**: Zero Defect Zero Effect certification
- **Multi-certification**: Consultants handling multiple certifications

## Integration with Certification Solver

The Consultant Marketplace is integrated with the Certification Solver service:

```python
from services.certification_solver import CertificationSolver

solver = CertificationSolver()

# Generate guidance includes consultant recommendations
guidance = solver.generate_guidance(
    certification_id="fda-food-facility",
    product_type="Organic Tea",
    destination="United States",
    company_size="Small"
)

# Consultants are automatically included in guidance
print(guidance.consultants)
```

## Testing

Run the test suite:

```bash
cd backend/services
python -m pytest test_consultant_marketplace.py -v
```

Test coverage includes:
- Initialization and data loading
- Search by certification type
- Filtering by rating, cost, experience, location, specialization
- Combined filters
- Sorting by rating, cost, experience
- Getting consultant by ID
- Getting consultants for specific certifications
- Singleton pattern
- Data validation

## Future Enhancements

Potential improvements for production:
1. **Database Integration**: Store consultants in database instead of in-memory
2. **Real-time Ratings**: Integrate with user feedback system
3. **Availability Calendar**: Show consultant availability
4. **Direct Booking**: Enable booking consultations through the platform
5. **Reviews and Testimonials**: Add user reviews and success stories
6. **Verified Badges**: Mark verified and certified consultants
7. **Price Negotiation**: Enable price negotiation features
8. **Multi-language Support**: Support for regional languages
9. **Video Consultations**: Integrate video call functionality
10. **Payment Integration**: Process consultation payments

## Architecture

```
ConsultantMarketplace
├── _load_consultants()          # Load consultant data
├── search_consultants()          # Search with filters and sorting
├── get_consultant_by_id()        # Get by ID
└── get_consultants_for_certification()  # Get for specific cert

Integration Points:
├── CertificationSolver.find_consultants()  # Uses marketplace
├── API Router: /api/certifications/consultants/*  # REST endpoints
└── Frontend: ConsultantMarketplace component  # UI display
```

## Data Model

```python
Consultant(
    id="cons-fda-1",
    name="FDA Compliance Experts India",
    specialization=["FDA Registration", "Food Safety"],
    rating=4.5,
    cost_range=CostRange(min=25000, max=75000, currency="INR"),
    contact=ContactInfo(
        email="info@fdacompliance.in",
        phone="+91-98765-43210",
        website="https://www.fdacompliance.in"
    ),
    experience_years=10,
    certifications_handled=["FDA", "FSSAI", "HACCP"],
    success_rate=95.0,
    location="Mumbai, India"
)
```

## Error Handling

The service handles errors gracefully:
- Invalid filter parameters return appropriate HTTP 400 errors
- Missing consultants return HTTP 404 errors
- Service errors return HTTP 500 with error details
- All errors are logged for debugging

## Performance Considerations

- In-memory storage for fast searches (current implementation)
- Efficient filtering using list comprehensions
- Sorting performed after filtering to minimize operations
- Singleton pattern to avoid reloading data
- For production: Consider caching, database indexing, pagination

## Compliance

The consultant marketplace helps users comply with:
- **Requirement 3.4**: Connect users to consultant marketplace for certification assistance
- Provides ratings and cost ranges for informed decision-making
- Includes contact information for direct communication
- Shows specialization details to match user needs
