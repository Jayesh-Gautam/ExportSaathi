"""
Integration test for Documents API Router with DocumentGenerator service

Tests the full flow from router to service.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import uuid
from datetime import datetime

from services.document_generator import DocumentGenerator, get_document_generator
from models.document import GeneratedDocument, ValidationResult
from models.enums import DocumentType


def test_document_generator_service_exists():
    """Test that DocumentGenerator service can be instantiated."""
    generator = DocumentGenerator()
    assert generator is not None
    assert hasattr(generator, 'generate_document')
    assert hasattr(generator, '_validate_document')


def test_get_document_generator_singleton():
    """Test that get_document_generator returns singleton instance."""
    gen1 = get_document_generator()
    gen2 = get_document_generator()
    assert gen1 is gen2


def test_generate_commercial_invoice_basic():
    """Test generating a basic commercial invoice."""
    generator = DocumentGenerator()
    
    report_data = {
        "product_name": "Organic Turmeric Powder",
        "destination_country": "United States",
        "hs_code": "0910.30"
    }
    
    user_data = {
        "company_name": "Sample Exports Pvt Ltd",
        "address": "123 Export Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pin_code": "400001",
        "gstin": "27AABCU9603R1ZM",
        "iec_code": "0512345678",
        "pan": "AABCU9603R",
        "email": "exports@sample.com",
        "phone": "+91-22-12345678"
    }
    
    document = generator.generate_document(
        document_type=DocumentType.COMMERCIAL_INVOICE,
        report_data=report_data,
        user_data=user_data,
        custom_data={}
    )
    
    # Verify document structure
    assert isinstance(document, GeneratedDocument)
    assert document.document_type == DocumentType.COMMERCIAL_INVOICE
    assert document.document_id.startswith("doc_")
    assert "invoice_number" in document.content
    assert "exporter" in document.content
    assert document.content["exporter"]["name"] == "Sample Exports Pvt Ltd"
    assert document.content["exporter"]["gstin"] == "27AABCU9603R1ZM"
    assert isinstance(document.validation_results, ValidationResult)
    assert document.pdf_url is not None
    assert document.editable_url is not None


def test_generate_packing_list_basic():
    """Test generating a basic packing list."""
    generator = DocumentGenerator()
    
    report_data = {
        "product_name": "Organic Turmeric Powder",
        "destination_country": "United States"
    }
    
    user_data = {
        "company_name": "Sample Exports Pvt Ltd",
        "address": "123 Export Street",
        "city": "Mumbai"
    }
    
    document = generator.generate_document(
        document_type=DocumentType.PACKING_LIST,
        report_data=report_data,
        user_data=user_data,
        custom_data={}
    )
    
    # Verify document structure
    assert document.document_type == DocumentType.PACKING_LIST
    assert "packing_list_number" in document.content
    assert "exporter" in document.content
    assert document.content["exporter"]["name"] == "Sample Exports Pvt Ltd"


def test_generate_gst_lut_basic():
    """Test generating a GST LUT document."""
    generator = DocumentGenerator()
    
    report_data = {
        "product_name": "Software Services",
        "destination_country": "United States"
    }
    
    user_data = {
        "company_name": "Sample Tech Pvt Ltd",
        "address": "123 Tech Park",
        "gstin": "29AABCU9603R1ZM",
        "pan": "AABCU9603R",
        "iec_code": "0512345678"
    }
    
    document = generator.generate_document(
        document_type=DocumentType.GST_LUT,
        report_data=report_data,
        user_data=user_data,
        custom_data={}
    )
    
    # Verify document structure
    assert document.document_type == DocumentType.GST_LUT
    assert "lut_number" in document.content
    assert "financial_year" in document.content
    assert document.content["exporter"]["gstin"] == "29AABCU9603R1ZM"


def test_generate_with_custom_data_override():
    """Test that custom data overrides auto-filled values."""
    generator = DocumentGenerator()
    
    report_data = {"product_name": "Test Product", "destination_country": "USA"}
    user_data = {"company_name": "Test Company"}
    custom_data = {
        "invoice_number": "CUSTOM-INV-001",
        "payment_terms": "60 days"
    }
    
    document = generator.generate_document(
        document_type=DocumentType.COMMERCIAL_INVOICE,
        report_data=report_data,
        user_data=user_data,
        custom_data=custom_data
    )
    
    # Verify custom data was applied
    assert document.content["invoice_number"] == "CUSTOM-INV-001"
    assert document.content["payment_terms"] == "60 days"


def test_validation_detects_invalid_gstin():
    """Test that validation detects invalid GSTIN format."""
    generator = DocumentGenerator()
    
    content = {
        "invoice_number": "INV-001",
        "exporter": {
            "gstin": "ABC123",  # Invalid - should be 15 characters
            "iec_code": "0512345678"
        },
        "consignee": {"name": "Test Consignee"},
        "totals": {"total": 1000.0}
    }
    
    validation_result = generator._validate_document(
        document_type=DocumentType.COMMERCIAL_INVOICE,
        content=content,
        report_data={}
    )
    
    # Should have validation errors
    assert validation_result.is_valid is False
    assert len(validation_result.errors) > 0
    # Check for GSTIN error
    gstin_errors = [e for e in validation_result.errors if "gstin" in e.field.lower()]
    assert len(gstin_errors) > 0


def test_validation_detects_invalid_iec():
    """Test that validation detects invalid IEC code format."""
    generator = DocumentGenerator()
    
    content = {
        "invoice_number": "INV-001",
        "exporter": {
            "gstin": "27AABCU9603R1ZM",
            "iec_code": "123"  # Invalid - should be 10 characters
        },
        "consignee": {"name": "Test Consignee"},
        "totals": {"total": 1000.0}
    }
    
    validation_result = generator._validate_document(
        document_type=DocumentType.COMMERCIAL_INVOICE,
        content=content,
        report_data={}
    )
    
    # Should have validation errors
    assert validation_result.is_valid is False
    iec_errors = [e for e in validation_result.errors if "iec" in e.field.lower()]
    assert len(iec_errors) > 0


def test_all_document_types_supported():
    """Test that all document types can be generated."""
    generator = DocumentGenerator()
    
    report_data = {"product_name": "Test", "destination_country": "USA"}
    user_data = {
        "company_name": "Test Co",
        "gstin": "27AABCU9603R1ZM",
        "iec_code": "0512345678",
        "pan": "AABCU9603R"
    }
    
    document_types = [
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.SHIPPING_BILL,
        DocumentType.GST_LUT,
        DocumentType.SOFTEX,
        DocumentType.CERTIFICATE_OF_ORIGIN
    ]
    
    for doc_type in document_types:
        document = generator.generate_document(
            document_type=doc_type,
            report_data=report_data,
            user_data=user_data,
            custom_data={}
        )
        assert document.document_type == doc_type
        assert document.document_id.startswith("doc_")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
