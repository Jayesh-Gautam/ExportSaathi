# Export Document Templates

This directory contains India-specific document templates for export documentation, compliant with DGFT (Directorate General of Foreign Trade) and Indian Customs requirements.

## Overview

All templates are in JSON format for easy parsing, validation, and auto-filling. Each template includes:
- **_template_info**: Metadata about the template including compliance information and mandatory fields
- **Structured fields**: Organized sections for exporter, consignee, shipment details, etc.
- **Mandatory fields list**: Fields that must be filled for the document to be valid
- **Compliance notes**: Important regulatory information

## Available Templates

### 1. Commercial Invoice (`commercial_invoice.json`)
**Purpose**: Primary document for international trade showing transaction details  
**Compliance**: DGFT and Indian Customs compliant  
**Key Features**:
- Exporter details with GSTIN, IEC, PAN
- Consignee and buyer information
- Shipment details (ports, terms of delivery)
- Itemized goods list
- Payment terms and bank details
- Declaration statement

**Mandatory Fields**:
- Invoice number and date
- Exporter: name, GSTIN, IEC code, PAN
- Consignee: name, country
- Shipment: port of loading, port of discharge
- Items and totals

### 2. Packing List (`packing_list.json`)
**Purpose**: Details of packages, weights, and dimensions  
**Compliance**: DGFT and Indian Customs compliant  
**Key Features**:
- Package-wise breakdown
- Weight (gross and net) and volume
- Container and seal details
- Marks and numbers

**Mandatory Fields**:
- Packing list number and date
- Invoice reference
- Exporter and consignee details
- Package details

### 3. Shipping Bill (`shipping_bill.json`)
**Purpose**: Main customs clearance document for exports  
**Compliance**: Indian Customs and DGFT compliant  
**Key Features**:
- Customs declaration fields
- IEC code and AD code (Authorized Dealer)
- Exchange rate details
- RoDTEP claim section
- Duty drawback and IGST refund sections

**Mandatory Fields**:
- Shipping bill number and date
- Exporter: IEC code, GSTIN, AD code
- Port of loading
- Country of final destination
- Items with HS codes

**Important Notes**:
- Must be filed electronically through ICEGATE portal
- Required for claiming duty drawback, IGST refund, and RoDTEP benefits
- Exchange rate should be RBI reference rate

### 4. GST Letter of Undertaking - LUT (`gst_lut.json`)
**Purpose**: Export goods/services without paying IGST  
**Compliance**: GST Act 2017 - Rule 96A compliant  
**Key Features**:
- Undertaking to export without IGST payment
- Jurisdictional officer details
- Financial year validity
- Separate for goods and services

**Mandatory Fields**:
- LUT number and financial year
- Exporter: GSTIN, PAN, IEC code
- Authorized signatory details

**Important Notes**:
- Valid for entire financial year
- Must be filed on GST portal before first export
- Separate LUT required for goods and services
- Failure to comply can result in penalties

### 5. SOFTEX Declaration (`softex.json`)
**Purpose**: Software and IT service export declaration  
**Compliance**: STPI/SEZ and DGFT compliant  
**Key Features**:
- Service description and category
- Contract details
- Payment and FIRC details
- STPI/SEZ registration
- Multiple service categories supported

**Mandatory Fields**:
- SOFTEX number and date
- Exporter: IEC code, GSTIN
- Buyer details and country
- Service description and category
- Invoice details

**Service Categories Supported**:
- Software Development
- Software Testing & Maintenance
- IT Consulting
- Cloud Services (SaaS/PaaS/IaaS)
- Mobile & Web Development
- Data Analytics & AI/ML
- Cybersecurity Services
- BPO/KPO Services
- Digital Marketing
- Other IT Enabled Services

**Important Notes**:
- Required for all software and IT service exports
- Can be filed through STPI portal or customs
- Required for claiming GST refund
- Service exports are zero-rated under GST

### 6. Certificate of Origin (`certificate_of_origin.json`)
**Purpose**: Prove goods are manufactured/produced in India  
**Compliance**: Export Inspection Council and Chamber of Commerce compliant  
**Key Features**:
- Origin criteria (wholly obtained, substantially transformed)
- FTA scheme support
- Issuing authority details
- Multiple certificate types

**Mandatory Fields**:
- Certificate number and date
- Exporter and consignee details
- Transport details
- Goods description
- Country of origin and destination

**Certificate Types Supported**:
- Non-Preferential Certificate of Origin
- Preferential Certificate of Origin (under FTA)
- GSP Certificate (Form A)
- ASEAN Certificate
- SAFTA Certificate
- India-UAE CEPA Certificate
- Other FTA Certificates

**FTA Schemes Supported**:
- ASEAN-India FTA
- India-UAE CEPA
- India-Mauritius CECPA
- SAFTA (South Asian FTA)
- India-Korea CEPA
- India-Japan CEPA
- India-Singapore CECA
- GSP (Generalized System of Preferences)

## Template Structure

Each template follows this structure:

```json
{
  "_template_info": {
    "name": "Document Name",
    "version": "1.0",
    "compliance": "Regulatory compliance information",
    "description": "Template description",
    "mandatory_fields": ["field1", "field2.subfield"],
    "notes": ["Important note 1", "Important note 2"]
  },
  "field1": "value",
  "field2": {
    "subfield": "value"
  }
}
```

## Mandatory Fields

Mandatory fields are specified in dot notation (e.g., `exporter.gstin`). The document generator validates these fields before generating the final document.

## Compliance Requirements

### GSTIN (GST Identification Number)
- **Format**: 15 characters
- **Structure**: 2 digits (state) + 10 digits (PAN) + 1 digit (entity) + 1 letter (Z) + 1 check digit
- **Required for**: All export documents

### IEC (Import Export Code)
- **Format**: 10 characters
- **Issued by**: DGFT
- **Required for**: All export/import transactions

### PAN (Permanent Account Number)
- **Format**: 10 characters
- **Structure**: 5 letters + 4 digits + 1 letter
- **Required for**: GST LUT, tax purposes

### AD Code (Authorized Dealer Code)
- **Format**: 14 characters
- **Issued by**: Bank authorized by RBI
- **Required for**: Shipping bill, foreign exchange transactions

## Usage in Document Generator

The DocumentGenerator service loads these templates and auto-fills them with:
1. **User profile data** (company information, GSTIN, IEC, etc.)
2. **Report data** (product details, destination country, HS code)
3. **Custom data** (user-provided overrides)

Priority order (lowest to highest):
1. Template defaults
2. User profile data
3. Report data
4. Custom data

## Validation

Each document is validated for:
- **Mandatory fields**: All required fields must be filled
- **Format validation**: GSTIN, IEC, PAN format checks
- **Cross-document consistency**: Invoice numbers match across documents
- **RMS triggers**: Red flag keywords detection
- **Port code validation**: Port matches destination country
- **Compliance text**: AWS Comprehend validation

## Future Enhancements

1. **Multi-language support**: Templates in regional languages
2. **Custom branding**: Company logo and letterhead
3. **Digital signatures**: Integration with digital signature providers
4. **E-filing integration**: Direct submission to ICEGATE, GST portal
5. **Template versioning**: Support for regulatory changes
6. **Additional formats**: PDF templates with visual formatting
7. **FTA-specific templates**: Specialized templates for each FTA

## References

- **DGFT**: https://www.dgft.gov.in/
- **ICEGATE**: https://www.icegate.gov.in/
- **GST Portal**: https://www.gst.gov.in/
- **STPI**: https://www.stpi.in/
- **Export Inspection Council**: https://www.eicindia.gov.in/

## Compliance Notes

All templates are designed to comply with:
- **DGFT Foreign Trade Policy 2023**
- **GST Act 2017 and Rules**
- **Customs Act 1962**
- **FEMA (Foreign Exchange Management Act) 1999**
- **RBI Guidelines for Export Proceeds**
- **STPI/SEZ Regulations**

## Support

For questions about template usage or compliance requirements, refer to:
- Document Generator Service: `backend/services/document_generator.py`
- Document Validator Service: `backend/services/document_validator.py`
- API Documentation: `backend/routers/documents.py`
