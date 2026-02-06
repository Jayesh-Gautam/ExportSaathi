# Document Generator Service

## Overview

The Document Generator Service generates export documents with India-specific templates. It supports 6 document types, auto-fills templates with user data from reports and profiles, validates documents for compliance, and generates documents in PDF and editable formats.

**Requirements:** 4.1, 4.2, 4.5

## Features

- **6 Document Types Supported:**
  - Commercial Invoice
  - Packing List
  - Shipping Bill
  - GST LUT (Letter of Undertaking)
  - SOFTEX (Software Export Declaration)
  - Certificate of Origin

- **India-Specific Templates:**
  - Compliant with DGFT and customs requirements
  - Include all mandatory fields for Indian exports
  - Support for IEC code, GSTIN, PAN, and other Indian identifiers

- **Auto-Fill Capability:**
  - Automatically fills templates with user profile data
  - Uses report data for product and destination information
  - Supports custom data overrides

- **AI Validation:**
  - Required field validation
  - Format validation (GSTIN, IEC, PAN)
  - Port code mismatch detection
  - RMS risk trigger keyword detection
  - Cross-document consistency checks

- **Multiple Output Formats:**
  - PDF for printing and submission
  - Editable formats (DOCX) for customization

## Usage

### Basic Usage

```python
from backend.services.document_generator import DocumentGenerator, get_document_generator
from backend.models.enums import DocumentType

# Get document generator instance
generator = get_document_generator()

# Prepare data
user_data = {
    "company_name": "ABC Exports Pvt Ltd",
    "address": "123 Export Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "gstin": "27AABCU9603R1ZM",
    "iec_code": "0512345678",
    "pan": "AABCU9603R"
}

report_data = {
    "product_name": "Organic Turmeric Powder",
    "destination_country": "United States",
    "hs_code": "0910.30.00"
}

# Generate commercial invoice
document = generator.generate_document(
    document_type=DocumentType.COMMERCIAL_INVOICE,
    report_data=report_data,
    user_data=user_data
)

print(f"Document ID: {document.document_id}")
print(f"Valid: {document.validation_results.is_valid}")
print(f"PDF URL: {document.pdf_url}")
```

### Custom Data Override

```python
# Override specific fields
custom_data = {
    "invoice_number": "CUSTOM-INV-001",
    "payment_terms": "Net 60 days",
    "items": [
        {
            "description": "Organic Turmeric Powder",
            "hs_code": "0910.30.00",
            "quantity": 1000,
            "unit": "kg",
            "unit_price": 5.50,
            "total": 5500.00
        }
    ]
}

document = generator.generate_document(
    document_type=DocumentType.COMMERCIAL_INVOICE,
    report_data=report_data,
    user_data=user_data,
    custom_data=custom_data
)
```

### Validation Results

```python
# Check validation results
if not document.validation_results.is_valid:
    print("Validation errors:")
    for error in document.validation_results.errors:
        print(f"  - {error.field}: {error.message}")
        print(f"    Suggestion: {error.suggestion}")

if document.validation_results.warnings:
    print("Validation warnings:")
    for warning in document.validation_results.warnings:
        print(f"  - {warning.field}: {warning.message}")
```

## Document Types

### 1. Commercial Invoice

Standard export invoice with exporter, consignee, items, and payment details.

**Key Fields:**
- Invoice number and date
- Exporter details (name, address, GSTIN, IEC, PAN)
- Consignee and buyer details
- Shipment details (ports, terms of delivery)
- Line items with HS codes
- Totals and currency
- Bank details for payment

### 2. Packing List

Detailed list of packages with weights and dimensions.

**Key Fields:**
- Packing list number
- Package details (number, weight, volume)
- Container information
- Totals (packages, gross weight, net weight, volume)

### 3. Shipping Bill

Customs declaration for export shipments.

**Key Fields:**
- Shipping bill number
- Exporter details with IEC and AD code
- Port information
- FOB value in INR and foreign currency
- Exchange rate
- RoDTEP claim details

### 4. GST LUT (Letter of Undertaking)

Declaration to export without paying IGST.

**Key Fields:**
- LUT number and financial year
- Exporter GSTIN and PAN
- Jurisdictional officer details
- Undertaking declarations
- Authorized signatory

### 5. SOFTEX

Software/service export declaration.

**Key Fields:**
- SOFTEX number
- Service description and category
- Contract details
- Invoice and payment information
- STPI/SEZ registration (if applicable)

### 6. Certificate of Origin

Certifies goods originated in India.

**Key Fields:**
- Certificate number
- Exporter and consignee details
- Transport details
- Goods description
- Issuing authority (EIC/Chamber of Commerce)

## Template Structure

All templates follow a consistent structure:

```python
{
    "document_number": "",  # Auto-generated
    "date": "",  # Auto-filled with current date
    "exporter": {
        "name": "",
        "address": "",
        "gstin": "",
        "iec_code": "",
        # ... other fields
    },
    "consignee": {
        "name": "",
        "address": "",
        "country": "",
        # ... other fields
    },
    # Document-specific fields
}
```

## Validation Rules

### Required Field Validation

Each document type has specific required fields that must be filled.

### Format Validation

- **GSTIN:** Must be 15 characters (2 state + 10 PAN + 1 entity + 1 Z + 1 check)
- **IEC Code:** Must be 10 characters
- **PAN:** Must be 10 characters

### Port Code Validation

Validates that port of discharge matches destination country.

### RMS Trigger Detection

Warns about keywords that may trigger customs inspection:
- chemical, drug, medicine, pharmaceutical
- weapon, explosive, radioactive, hazardous
- dual-use, military, restricted

## Auto-Fill Logic

### Priority Order

1. **Custom Data** (highest priority) - User-provided overrides
2. **User Profile Data** - Company information, identifiers
3. **Report Data** - Product and destination information
4. **Template Defaults** - Fallback values

### Auto-Generated Fields

- Document numbers (invoice, packing list, shipping bill, etc.)
- Dates (current date if not provided)
- Financial year (for GST LUT)

## Integration with Other Services

### Compliance Text Analyzer

Used for advanced validation of document content.

### Report Generator

Provides product and destination data for auto-fill.

### User Service

Provides company profile data for exporter details.

## Testing

Run tests with:

```bash
cd backend/services
pytest test_document_generator.py -v
```

### Test Coverage

- Document generation for all 6 types
- Template loading and structure
- Auto-fill with user and report data
- Custom data override
- Validation (required fields, formats, RMS triggers)
- Error handling

## Future Enhancements

### Phase 2 Features

1. **Actual PDF Generation**
   - Use ReportLab or WeasyPrint
   - Professional formatting with logos
   - Digital signatures

2. **Actual Editable Format Generation**
   - Use python-docx for DOCX
   - Use openpyxl for XLSX
   - Template-based generation

3. **S3 Integration**
   - Upload generated documents to S3
   - Generate signed URLs for download
   - Document versioning

4. **Advanced Validation**
   - Cross-document consistency (invoice vs shipping bill)
   - GST vs Shipping Bill matching
   - Real-time port code database lookup

5. **Document Templates Management**
   - User-customizable templates
   - Company-specific branding
   - Multi-language support

6. **Batch Generation**
   - Generate multiple documents at once
   - Document packages (invoice + packing list + shipping bill)

## API Integration

The Document Generator is used by the Documents Router:

```python
# In routers/documents.py
from backend.services.document_generator import get_document_generator

@router.post("/generate")
async def generate_document(request: DocumentGenerationRequest):
    generator = get_document_generator()
    document = generator.generate_document(
        document_type=request.document_type,
        report_data=report_data,
        user_data=user_data,
        custom_data=request.custom_data
    )
    return document
```

## Error Handling

The service handles errors gracefully:

- **Invalid Document Type:** Raises ValueError
- **Missing Required Data:** Returns validation errors
- **Template Loading Failure:** Raises ValueError
- **Generation Failure:** Logs error and raises exception

## Performance Considerations

- Templates are loaded on-demand (not cached in MVP)
- Validation is synchronous (fast for MVP)
- PDF/DOCX generation is placeholder (instant in MVP)

## Security Considerations

- Validates all input data
- Sanitizes user-provided content
- No execution of user code
- Safe template rendering

## Compliance

All templates are designed to comply with:
- DGFT (Directorate General of Foreign Trade) requirements
- Indian Customs regulations
- GST Network (GSTN) requirements
- International trade documentation standards

## Support

For issues or questions:
1. Check validation error messages and suggestions
2. Review template structure documentation
3. Consult DGFT and customs guidelines
4. Contact support team

## Version History

- **v1.0** (Current) - MVP implementation with 6 document types, auto-fill, and validation
