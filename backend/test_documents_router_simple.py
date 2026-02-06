"""
Simple test for Documents API Router endpoints

Tests the documents router in isolation without importing the full app.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import uuid
from datetime import datetime

from models.document import (
    GeneratedDocument,
    ValidationResult,
    ValidationError,
    ValidationWarning,
    DocumentGenerationRequest
)
from models.enums import DocumentType, ValidationSeverity


def test_document_generation_request_model():
    """Test DocumentGenerationRequest model validation."""
    request = DocumentGenerationRequest(
        document_type=DocumentType.COMMERCIAL_INVOICE,
        report_id="rpt_test123456",
        custom_data={"invoice_number": "INV-001"}
    )
    
    assert request.document_type == DocumentType.COMMERCIAL_INVOICE
    assert request.report_id == "rpt_test123456"
    assert request.custom_data["invoice_number"] == "INV-001"


def test_generated_document_model():
    """Test GeneratedDocument model."""
    doc = GeneratedDocument(
        document_id="doc_test123456",
        document_type=DocumentType.COMMERCIAL_INVOICE,
        content={"invoice_number": "INV-001"},
        validation_results=ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        ),
        pdf_url="https://example.com/doc.pdf",
        editable_url="https://example.com/doc.docx",
        generated_at=datetime.utcnow()
    )
    
    assert doc.document_id == "doc_test123456"
    assert doc.document_type == DocumentType.COMMERCIAL_INVOICE
    assert doc.validation_results.is_valid is True


def test_validation_result_with_errors():
    """Test ValidationResult with errors."""
    result = ValidationResult(
        is_valid=False,
        errors=[
            ValidationError(
                field="exporter.gstin",
                message="GSTIN must be 15 characters",
                severity=ValidationSeverity.ERROR,
                suggestion="Verify GSTIN format"
            )
        ],
        warnings=[
            ValidationWarning(
                field="items[0].description",
                message="Description contains trigger keyword",
                suggestion="Consider revising"
            )
        ]
    )
    
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert len(result.warnings) == 1
    assert result.errors[0].field == "exporter.gstin"


def test_parse_uuid_function():
    """Test the parse_uuid helper function from documents router."""
    from routers.documents import parse_uuid
    
    # Test with UUID format
    test_uuid = uuid.uuid4()
    result = parse_uuid(str(test_uuid))
    assert result == test_uuid
    
    # Test with hex string (no dashes)
    hex_str = str(test_uuid).replace('-', '')
    result = parse_uuid(hex_str)
    assert result == test_uuid
    
    # Test with prefix
    prefixed = f"doc_{hex_str}"
    result = parse_uuid(prefixed, prefix="doc_")
    assert result == test_uuid


def test_parse_uuid_invalid():
    """Test parse_uuid with invalid input."""
    from routers.documents import parse_uuid
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        parse_uuid("invalid-id-format")
    
    assert exc_info.value.status_code == 400
    assert "Invalid ID format" in exc_info.value.detail


def test_document_types_enum():
    """Test DocumentType enum values."""
    assert DocumentType.COMMERCIAL_INVOICE.value == "commercial_invoice"
    assert DocumentType.PACKING_LIST.value == "packing_list"
    assert DocumentType.SHIPPING_BILL.value == "shipping_bill"
    assert DocumentType.GST_LUT.value == "gst_lut"
    assert DocumentType.SOFTEX.value == "softex"
    assert DocumentType.CERTIFICATE_OF_ORIGIN.value == "certificate_of_origin"


def test_validation_severity_enum():
    """Test ValidationSeverity enum values."""
    assert ValidationSeverity.ERROR.value == "error"
    assert ValidationSeverity.WARNING.value == "warning"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
