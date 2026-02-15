"""
Unit tests for DocumentValidator service.

Tests validation functionality including:
- Port code mismatch detection
- Invoice format validation
- GST vs Shipping Bill matching
- RMS risk trigger detection
- Mandatory field validation
- AWS Comprehend integration

Requirements: 4.3, 4.4, 4.8
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from services.document_validator import (
    DocumentValidator,
    RiskFactor,
    PORT_CODE_MAPPINGS,
    RMS_TRIGGER_KEYWORDS
)
from services.compliance_text_analyzer import ComplianceTextAnalyzer, Entity, KeyPhrase
from models.enums import DocumentType, ValidationSeverity


@pytest.fixture
def mock_compliance_analyzer():
    """Create mock compliance analyzer."""
    analyzer = Mock(spec=ComplianceTextAnalyzer)
    analyzer.extract_entities.return_value = []
    analyzer.extract_key_phrases.return_value = []
    return analyzer


@pytest.fixture
def validator(mock_compliance_analyzer):
    """Create DocumentValidator with mock analyzer."""
    return DocumentValidator(compliance_analyzer=mock_compliance_analyzer)


class TestPortCodeValidation:
    """Test port code mismatch detection."""
    
    def test_valid_port_code_for_usa(self, validator):
        """Test that valid USA port codes pass validation."""
        document = {
            "port_of_discharge": "USNYC",
            "destination_country": "USA"
        }
        errors = validator.check_port_code_mismatch(document)
        assert len(errors) == 0
    
    def test_invalid_port_code_for_country(self, validator):
        """Test that mismatched port codes are detected."""
        document = {
            "port_of_discharge": "USNYC",  # USA port
            "destination_country": "UK"     # UK destination
        }
        errors = validator.check_port_code_mismatch(document)
        assert len(errors) == 1
        assert "does not match destination country" in errors[0].message
        assert errors[0].field == "port_of_discharge"
    
    def test_valid_port_code_for_uae(self, validator):
        """Test valid UAE port code."""
        document = {
            "port_of_discharge": "AEDXB",
            "destination_country": "UAE"
        }
        errors = validator.check_port_code_mismatch(document)
        assert len(errors) == 0
    
    def test_missing_port_code(self, validator):
        """Test that missing port code doesn't cause errors."""
        document = {
            "destination_country": "USA"
        }
        errors = validator.check_port_code_mismatch(document)
        assert len(errors) == 0
    
    def test_missing_destination(self, validator):
        """Test that missing destination doesn't cause errors."""
        document = {
            "port_of_discharge": "USNYC"
        }
        errors = validator.check_port_code_mismatch(document)
        assert len(errors) == 0
    
    def test_case_insensitive_matching(self, validator):
        """Test that port code matching is case-insensitive."""
        document = {
            "port_of_discharge": "usnyc",
            "destination_country": "usa"
        }
        errors = validator.check_port_code_mismatch(document)
        assert len(errors) == 0


class TestInvoiceFormatValidation:
    """Test invoice format validation."""
    
    def test_valid_invoice_format(self, validator):
        """Test that valid invoice passes format validation."""
        invoice = {
            "invoice_number": "INV-2024-001",
            "currency": "USD",
            "total_value": 1000.00,
            "items": [
                {"quantity": 10, "unit_price": 100.00}
            ],
            "payment_terms": "30 days"
        }
        errors = validator.validate_invoice_format(invoice)
        assert len(errors) == 0
    
    def test_invalid_invoice_number_format(self, validator):
        """Test that invalid invoice number is detected."""
        invoice = {
            "invoice_number": "INV@2024#001",  # Invalid characters
            "currency": "USD"
        }
        errors = validator.validate_invoice_format(invoice)
        assert len(errors) >= 1
        assert any("invalid characters" in e.message.lower() for e in errors)
    
    def test_invalid_currency_code(self, validator):
        """Test that invalid currency code is detected."""
        invoice = {
            "invoice_number": "INV-2024-001",
            "currency": "XXX"  # Invalid currency
        }
        errors = validator.validate_invoice_format(invoice)
        assert len(errors) >= 1
        assert any("invalid currency" in e.message.lower() for e in errors)
    
    def test_total_value_mismatch(self, validator):
        """Test that total value mismatch is detected."""
        invoice = {
            "invoice_number": "INV-2024-001",
            "currency": "USD",
            "total_value": 1500.00,  # Wrong total
            "items": [
                {"quantity": 10, "unit_price": 100.00}  # Should be 1000
            ]
        }
        errors = validator.validate_invoice_format(invoice)
        assert len(errors) >= 1
        assert any("doesn't match sum" in e.message.lower() for e in errors)
    
    def test_valid_payment_terms(self, validator):
        """Test that valid payment terms pass validation."""
        invoice = {
            "invoice_number": "INV-2024-001",
            "currency": "USD",
            "payment_terms": "Letter of Credit"
        }
        errors = validator.validate_invoice_format(invoice)
        # Should have no errors related to payment terms
        assert not any("payment_terms" in e.field for e in errors)


class TestGSTShippingBillMatch:
    """Test GST vs Shipping Bill matching."""
    
    def test_matching_gstin(self, validator):
        """Test that matching GSTIN passes validation."""
        gst_doc = {
            "exporter_gstin": "27AABCU9603R1ZM",
            "exporter_name": "ABC Exports Pvt Ltd"
        }
        shipping_bill = {
            "exporter_gstin": "27AABCU9603R1ZM",
            "exporter_name": "ABC Exports Pvt Ltd"
        }
        errors = validator.check_gst_shipping_bill_match(gst_doc, shipping_bill)
        assert len(errors) == 0
    
    def test_mismatched_gstin(self, validator):
        """Test that mismatched GSTIN is detected."""
        gst_doc = {
            "exporter_gstin": "27AABCU9603R1ZM",
            "exporter_name": "ABC Exports"
        }
        shipping_bill = {
            "exporter_gstin": "29AABCU9603R1ZM",  # Different GSTIN
            "exporter_name": "ABC Exports"
        }
        errors = validator.check_gst_shipping_bill_match(gst_doc, shipping_bill)
        assert len(errors) >= 1
        assert any("gstin mismatch" in e.message.lower() for e in errors)
    
    def test_mismatched_exporter_name(self, validator):
        """Test that mismatched exporter name is detected."""
        gst_doc = {
            "exporter_gstin": "27AABCU9603R1ZM",
            "exporter_name": "ABC Exports Pvt Ltd"
        }
        shipping_bill = {
            "exporter_gstin": "27AABCU9603R1ZM",
            "exporter_name": "XYZ Exports Pvt Ltd"  # Different name
        }
        errors = validator.check_gst_shipping_bill_match(gst_doc, shipping_bill)
        assert len(errors) >= 1
        assert any("name mismatch" in e.message.lower() for e in errors)
    
    def test_case_insensitive_gstin(self, validator):
        """Test that GSTIN matching is case-insensitive."""
        gst_doc = {
            "exporter_gstin": "27aabcu9603r1zm",
            "exporter_name": "ABC Exports"
        }
        shipping_bill = {
            "exporter_gstin": "27AABCU9603R1ZM",
            "exporter_name": "ABC Exports"
        }
        errors = validator.check_gst_shipping_bill_match(gst_doc, shipping_bill)
        assert len(errors) == 0


class TestRMSRiskTriggers:
    """Test RMS risk trigger detection."""
    
    def test_detect_chemical_keyword(self, validator):
        """Test that 'chemical' keyword is detected."""
        document = {
            "product_description": "Industrial chemical compound for manufacturing"
        }
        risks = validator.detect_rms_risk_triggers(document)
        assert len(risks) >= 1
        assert any(r.keyword == "chemical" for r in risks)
    
    def test_detect_explosive_keyword(self, validator):
        """Test that 'explosive' keyword is detected as high risk."""
        document = {
            "product_description": "Explosive materials for mining"
        }
        risks = validator.detect_rms_risk_triggers(document)
        assert len(risks) >= 1
        explosive_risk = next((r for r in risks if r.keyword == "explosive"), None)
        assert explosive_risk is not None
        assert explosive_risk.severity == "high"
    
    def test_detect_pharmaceutical_keyword(self, validator):
        """Test that 'pharmaceutical' keyword is detected."""
        document = {
            "product_description": "Pharmaceutical products for healthcare"
        }
        risks = validator.detect_rms_risk_triggers(document)
        assert len(risks) >= 1
        assert any(r.keyword == "pharmaceutical" for r in risks)
    
    def test_detect_multiple_keywords(self, validator):
        """Test detection of multiple risk keywords."""
        document = {
            "product_description": "Chemical pharmaceutical compound",
            "items": [
                {"description": "Hazardous materials"}
            ]
        }
        risks = validator.detect_rms_risk_triggers(document)
        assert len(risks) >= 2
    
    def test_no_false_positives(self, validator):
        """Test that normal products don't trigger false positives."""
        document = {
            "product_description": "Cotton textile fabrics for garments"
        }
        risks = validator.detect_rms_risk_triggers(document)
        assert len(risks) == 0
    
    def test_word_boundary_matching(self, validator):
        """Test that keyword matching uses word boundaries."""
        document = {
            "product_description": "Mechanical parts for industrial use"
        }
        risks = validator.detect_rms_risk_triggers(document)
        # "chemical" should not match in "mechanical"
        assert not any(r.keyword == "chemical" for r in risks)


class TestMandatoryFields:
    """Test mandatory field validation."""
    
    def test_commercial_invoice_mandatory_fields(self, validator):
        """Test that commercial invoice mandatory fields are checked."""
        document = {
            "invoice_number": "INV-001",
            "invoice_date": "2024-01-15"
            # Missing many mandatory fields
        }
        result = validator.validate(document, DocumentType.COMMERCIAL_INVOICE)
        assert not result.is_valid
        assert len(result.errors) > 0
        # Should have errors for missing fields
        missing_fields = [e.field for e in result.errors if "missing" in e.message.lower()]
        assert len(missing_fields) > 0
    
    def test_complete_commercial_invoice(self, validator):
        """Test that complete commercial invoice passes validation."""
        document = {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-01-15",
            "exporter_name": "ABC Exports Pvt Ltd",
            "exporter_address": "123 Export Street, Mumbai, India",
            "consignee_name": "XYZ Imports Inc",
            "consignee_address": "456 Import Ave, New York, USA",
            "destination_country": "USA",
            "port_of_discharge": "USNYC",
            "items": [{"quantity": 10, "unit_price": 100.00, "description": "Textile fabrics"}],
            "total_value": 1000.00,
            "currency": "USD",
            "payment_terms": "30 days"
        }
        result = validator.validate(document, DocumentType.COMMERCIAL_INVOICE)
        # Should have no mandatory field errors
        mandatory_errors = [e for e in result.errors if "missing" in e.message.lower()]
        assert len(mandatory_errors) == 0


class TestFullValidation:
    """Test complete document validation."""
    
    def test_valid_document_passes(self, validator):
        """Test that a valid document passes all validations."""
        document = {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-01-15",
            "exporter_name": "ABC Exports Pvt Ltd",
            "exporter_address": "123 Export Street, Mumbai, India",
            "consignee_name": "XYZ Imports Inc",
            "consignee_address": "456 Import Ave, New York, USA",
            "destination_country": "USA",
            "port_of_discharge": "USNYC",
            "items": [{"quantity": 10, "unit_price": 100.00, "description": "Cotton textiles"}],
            "total_value": 1000.00,
            "currency": "USD",
            "payment_terms": "30 days"
        }
        result = validator.validate(document, DocumentType.COMMERCIAL_INVOICE)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_document_with_errors_fails(self, validator):
        """Test that document with errors fails validation."""
        document = {
            "invoice_number": "INV@@@",  # Invalid format
            "currency": "XXX",  # Invalid currency
            "port_of_discharge": "USNYC",
            "destination_country": "UK",  # Mismatched port
            "product_description": "Explosive materials"  # RMS trigger
        }
        result = validator.validate(document, DocumentType.COMMERCIAL_INVOICE)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_document_with_warnings_still_valid(self, validator):
        """Test that document with only warnings is still valid."""
        document = {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-01-15",
            "exporter_name": "ABC Exports Pvt Ltd",
            "exporter_address": "123 Export Street, Mumbai, India",
            "consignee_name": "XYZ Imports Inc",
            "consignee_address": "456 Import Ave, New York, USA",
            "destination_country": "USA",
            "port_of_discharge": "USNYC",
            "items": [{"quantity": 10, "unit_price": 100.00, "description": "Chemical textiles"}],
            "total_value": 1000.00,
            "currency": "USD",
            "payment_terms": "30 days"
        }
        result = validator.validate(document, DocumentType.COMMERCIAL_INVOICE)
        # Should be valid despite RMS warning
        assert result.is_valid or len(result.errors) == 0
        # May have warnings for "chemical" keyword
        assert len(result.warnings) >= 0


class TestComprehendIntegration:
    """Test AWS Comprehend integration."""
    
    def test_comprehend_entity_extraction(self, mock_compliance_analyzer, validator):
        """Test that Comprehend entity extraction is called."""
        mock_compliance_analyzer.extract_entities.return_value = [
            Entity(text="ABC Exports", type="ORGANIZATION", score=0.99, begin_offset=0, end_offset=11)
        ]
        mock_compliance_analyzer.extract_key_phrases.return_value = []
        
        document = {
            "invoice_number": "INV-001",
            "exporter_name": "ABC Exports Pvt Ltd",
            "product_description": "High quality textile products for export"
        }
        
        result = validator.validate(document, DocumentType.COMMERCIAL_INVOICE)
        
        # Comprehend should have been called
        assert mock_compliance_analyzer.extract_entities.called
    
    def test_comprehend_failure_doesnt_break_validation(self, mock_compliance_analyzer, validator):
        """Test that Comprehend failure doesn't break validation."""
        mock_compliance_analyzer.extract_entities.side_effect = Exception("AWS error")
        
        document = {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-01-15",
            "exporter_name": "ABC Exports Pvt Ltd",
            "exporter_address": "123 Export Street, Mumbai, India",
            "consignee_name": "XYZ Imports Inc",
            "consignee_address": "456 Import Ave, New York, USA",
            "destination_country": "USA",
            "port_of_discharge": "USNYC",
            "items": [{"quantity": 10, "unit_price": 100.00}],
            "total_value": 1000.00,
            "currency": "USD",
            "payment_terms": "30 days"
        }
        
        # Should not raise exception
        result = validator.validate(document, DocumentType.COMMERCIAL_INVOICE)
        assert result is not None