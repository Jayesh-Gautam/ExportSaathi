"""
Example: RMS Risk Trigger Detection

This example demonstrates how the DocumentValidator detects RMS (Risk Management System)
trigger keywords in export documents that may flag shipments for customs inspection.

Requirements: 4.3, 6.5
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.document_validator import DocumentValidator, RMS_TRIGGER_KEYWORDS
from models.enums import DocumentType


def main():
    """Demonstrate RMS risk trigger detection."""
    
    print("=" * 80)
    print("RMS RISK TRIGGER DETECTION EXAMPLE")
    print("=" * 80)
    print()
    
    # Initialize validator
    validator = DocumentValidator()
    
    # Example 1: Low-risk product (no triggers)
    print("Example 1: Low-Risk Product")
    print("-" * 80)
    safe_document = {
        "invoice_number": "INV-2024-001",
        "invoice_date": "2024-01-15",
        "exporter_name": "ABC Textiles Pvt Ltd",
        "exporter_address": "123 Export Street, Mumbai, India",
        "consignee_name": "XYZ Imports Inc",
        "consignee_address": "456 Import Ave, New York, USA",
        "destination_country": "USA",
        "port_of_discharge": "USNYC",
        "product_description": "Cotton textile fabrics for garment manufacturing",
        "items": [
            {
                "description": "100% cotton fabric, plain weave",
                "quantity": 1000,
                "unit_price": 5.50
            }
        ],
        "total_value": 5500.00,
        "currency": "USD",
        "payment_terms": "30 days"
    }
    
    result = validator.validate(safe_document, DocumentType.COMMERCIAL_INVOICE)
    print(f"Product: {safe_document['product_description']}")
    print(f"Validation Result: {'✓ PASS' if result.is_valid else '✗ FAIL'}")
    print(f"RMS Triggers Detected: {len([w for w in result.warnings if 'RMS' in w.message or 'trigger' in w.message.lower()])}")
    print()
    
    # Example 2: Medium-risk product (chemical)
    print("Example 2: Medium-Risk Product (Chemical)")
    print("-" * 80)
    chemical_document = {
        "invoice_number": "INV-2024-002",
        "invoice_date": "2024-01-15",
        "exporter_name": "ChemCorp Industries Ltd",
        "exporter_address": "789 Industrial Zone, Pune, India",
        "consignee_name": "Global Chemicals Inc",
        "consignee_address": "123 Chemical Blvd, Houston, USA",
        "destination_country": "USA",
        "port_of_discharge": "USHOU",
        "product_description": "Industrial chemical compound for manufacturing processes",
        "items": [
            {
                "description": "Chemical reagent, CAS 123-45-6",
                "quantity": 500,
                "unit_price": 25.00
            }
        ],
        "total_value": 12500.00,
        "currency": "USD",
        "payment_terms": "Letter of Credit"
    }
    
    result = validator.validate(chemical_document, DocumentType.COMMERCIAL_INVOICE)
    risks = validator.detect_rms_risk_triggers(chemical_document)
    
    print(f"Product: {chemical_document['product_description']}")
    print(f"Validation Result: {'✓ PASS' if result.is_valid else '✗ FAIL'}")
    print(f"RMS Triggers Detected: {len(risks)}")
    
    for risk in risks:
        print(f"\n  ⚠ Trigger Keyword: '{risk.keyword}'")
        print(f"    Location: {risk.location}")
        print(f"    Severity: {risk.severity.upper()}")
        print(f"    Context: ...{risk.context}...")
        print(f"    Suggestion: {risk.suggestion}")
    print()
    
    # Example 3: High-risk product (explosive)
    print("Example 3: High-Risk Product (Explosive)")
    print("-" * 80)
    explosive_document = {
        "invoice_number": "INV-2024-003",
        "invoice_date": "2024-01-15",
        "exporter_name": "Mining Supplies Ltd",
        "exporter_address": "456 Mining Road, Jaipur, India",
        "consignee_name": "Mining Operations Inc",
        "consignee_address": "789 Mine St, Denver, USA",
        "destination_country": "USA",
        "port_of_discharge": "USDEN",
        "product_description": "Explosive materials for mining operations",
        "items": [
            {
                "description": "Industrial explosive compound",
                "quantity": 100,
                "unit_price": 150.00
            }
        ],
        "total_value": 15000.00,
        "currency": "USD",
        "payment_terms": "Advance payment"
    }
    
    result = validator.validate(explosive_document, DocumentType.COMMERCIAL_INVOICE)
    risks = validator.detect_rms_risk_triggers(explosive_document)
    
    print(f"Product: {explosive_document['product_description']}")
    print(f"Validation Result: {'✗ FAIL - HIGH RISK' if not result.is_valid else '⚠ WARNING'}")
    print(f"RMS Triggers Detected: {len(risks)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    
    for risk in risks:
        print(f"\n  🚨 Trigger Keyword: '{risk.keyword}'")
        print(f"    Location: {risk.location}")
        print(f"    Severity: {risk.severity.upper()}")
        print(f"    Context: ...{risk.context}...")
        print(f"    Suggestion: {risk.suggestion}")
    
    if result.errors:
        print("\n  Validation Errors:")
        for error in result.errors:
            print(f"    • {error.field}: {error.message}")
    print()
    
    # Example 4: Multiple triggers
    print("Example 4: Multiple Risk Triggers")
    print("-" * 80)
    multi_risk_document = {
        "invoice_number": "INV-2024-004",
        "product_description": "Pharmaceutical chemical compounds",
        "items": [
            {
                "description": "Hazardous pharmaceutical drug for medical use"
            }
        ]
    }
    
    risks = validator.detect_rms_risk_triggers(multi_risk_document)
    
    print(f"Product: {multi_risk_document['product_description']}")
    print(f"RMS Triggers Detected: {len(risks)}")
    
    keywords_found = set(r.keyword for r in risks)
    print(f"Keywords Found: {', '.join(sorted(keywords_found))}")
    
    for risk in risks:
        print(f"\n  ⚠ '{risk.keyword}' in {risk.location}")
        print(f"    Severity: {risk.severity.upper()}")
    print()
    
    # Show all monitored keywords
    print("=" * 80)
    print("ALL MONITORED RMS TRIGGER KEYWORDS")
    print("=" * 80)
    print(f"Total Keywords: {len(RMS_TRIGGER_KEYWORDS)}")
    print()
    
    # Group by category
    categories = {
        "High-risk substances": [
            "chemical", "explosive", "radioactive", "hazardous", "toxic", "flammable",
            "corrosive", "biohazard", "pesticide", "narcotic", "drug", "pharmaceutical"
        ],
        "Dual-use items": [
            "military", "weapon", "ammunition", "defense", "surveillance", "encryption"
        ],
        "Restricted materials": [
            "ivory", "wildlife", "endangered", "antique", "artifact", "cultural"
        ],
        "High-value items": [
            "gold", "diamond", "jewelry", "precious", "gemstone"
        ],
        "Sensitive electronics": [
            "drone", "satellite", "missile", "nuclear", "laser"
        ],
        "Food safety concerns": [
            "meat", "dairy", "seafood", "poultry", "egg", "honey"
        ],
        "Agricultural concerns": [
            "seed", "plant", "soil", "fertilizer", "animal"
        ],
        "Generic risk terms": [
            "restricted", "prohibited", "controlled", "regulated", "sanctioned"
        ]
    }
    
    for category, keywords in categories.items():
        print(f"{category}:")
        print(f"  {', '.join(keywords)}")
        print()
    
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
1. Use specific, technical terminology instead of generic risk terms
2. Provide detailed specifications and certifications for flagged items
3. Include proper documentation (MSDS, licenses, certificates)
4. Consider alternative wording that accurately describes the product
5. Ensure all regulatory approvals are in place before export
6. Consult with customs broker for high-risk shipments
    """)


if __name__ == "__main__":
    main()
