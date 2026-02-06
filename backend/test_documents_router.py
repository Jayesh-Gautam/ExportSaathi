"""
Test suite for Documents API Router

Tests the documents API endpoints to ensure they work correctly with:
1. POST /api/documents/generate - Document generation with auto-fill
2. POST /api/documents/validate - Document validation
3. GET /api/documents/{doc_id}/download - Document download

This is a basic integration test for the MVP implementation.

Requirements: 8.1
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime

from main import app
from models.document import (
    GeneratedDocument,
    ValidationResult,
    ValidationError,
    ValidationWarning
)
from models.enums import DocumentType, ValidationSeverity


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_generated_document():
    """Create a mock generated document."""
    return GeneratedDocument(
        document_id="doc_test123456",
        document_type=DocumentType.COMMERCIAL_INVOICE,
        content={
            "invoice_number": "INV-20240115-ABC123",
            "invoice_date": "2024-01-15",
            "exporter": {
                "name": "Sample Exports Pvt Ltd",
                "address": "123 Export Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "country": "India",
                "pin_code": "400001",
                "gstin": "27AABCU9603R1ZM",
                "iec_code": "0512345678",
                "pan": "AABCU9603R",
                "email": "exports@sample.com",
                "phone": "+91-22-12345678"
            },
            "consignee": {
                "name": "ABC Imports Inc",
                "address": "456 Import Ave",
                "city": "New York",
                "state": "NY",
                "country": "United States",
                "postal_code": "10001",
                "tax_id": "12-3456789"
            },
            "buyer": {
                "name": "ABC Imports Inc",
                "address": "456 Import Ave",
                "city": "New York",
                "country": "United States"
            },
            "shipment_details": {
                "port_of_loading": "INMUN1",
                "port_of_discharge": "USNYC",
                "country_of_origin": "India",
                "country_of_final_destination": "United States",
                "terms_of_delivery": "FOB",
                "mode_of_transport": "Sea"
            },
            "items": [
                {
                    "description": "Organic Turmeric Powder",
                    "hs_code": "0910.30",
                    "quantity": 1000,
                    "unit": "kg",
                    "unit_price": 5.0,
                    "total_price": 5000.0
                }
            ],
            "totals": {
                "subtotal": 5000.0,
                "freight": 500.0,
                "insurance": 100.0,
                "total": 5600.0,
                "currency": "USD"
            },
            "payment_terms": "30 days from B/L date",
            "bank_details": {
                "bank_name": "State Bank of India",
                "branch": "Mumbai Main",
                "account_number": "1234567890",
                "swift_code": "SBININBB123",
                "ifsc_code": "SBIN0001234"
            },
            "declaration": "We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct."
        },
        validation_results=ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        ),
        pdf_url="https://exportsathi-docs.s3.amazonaws.com/doc_test123456.pdf",
        editable_url="https://exportsathi-docs.s3.amazonaws.com/doc_test123456.docx",
        generated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_validation_result():
    """Create a mock validation result."""
    return ValidationResult(
        is_valid=False,
        errors=[
            ValidationError(
                field="exporter.gstin",
                message="GSTIN must be 15 characters",
                severity=ValidationSeverity.ERROR,
                suggestion="Verify GSTIN format: 2 digits (state) + 10 digits (PAN) + 1 digit (entity) + 1 letter (Z) + 1 check digit"
            )
        ],
        warnings=[
            ValidationWarning(
                field="items[0].description",
                message="Product description contains potential RMS trigger keyword: 'chemical'",
                suggestion="Consider using more specific terminology or be prepared for customs inspection"
            )
        ]
    )


def test_generate_document_commercial_invoice(client, mock_generated_document):
    """Test generating a commercial invoice."""
    with patch('routers.documents.get_document_generator') as mock_generator:
        # Mock the document generator
        mock_instance = Mock()
        mock_instance.generate_document.return_value = mock_generated_document
        mock_generator.return_value = mock_instance
        
        # Mock database operations
        with patch('routers.documents.get_db') as mock_db:
            mock_session = MagicMock()
            
            # Mock report retrieval
            mock_db_report = MagicMock()
            mock_db_report.product_name = "Organic Turmeric Powder"
            mock_db_report.destination_country = "United States"
            mock_db_report.hs_code = "0910.30"
            mock_db_report.business_type = "Manufacturing"
            mock_db_report.company_size = "Small"
            mock_db_report.monthly_volume = 1000
            mock_db_report.price_range = "$5-10"
            mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
            
            mock_db.return_value = mock_session
            
            # Make request
            response = client.post(
                "/api/documents/generate",
                json={
                    "document_type": "commercial_invoice",
                    "report_id": "rpt_test123456",
                    "custom_data": {}
                }
            )
            
            # Assertions
            assert response.status_code == 201
            data = response.json()
            assert data["document_id"] == "doc_test123456"
            assert data["document_type"] == "commercial_invoice"
            assert data["validation_results"]["is_valid"] is True
            assert "pdf_url" in data
            assert "editable_url" in data


def test_generate_document_packing_list(client, mock_generated_document):
    """Test generating a packing list."""
    # Modify mock for packing list
    mock_generated_document.document_type = DocumentType.PACKING_LIST
    mock_generated_document.content = {
        "packing_list_number": "PL-20240115-ABC123",
        "date": "2024-01-15",
        "invoice_number": "INV-20240115-ABC123",
        "exporter": {
            "name": "Sample Exports Pvt Ltd",
            "address": "123 Export Street",
            "city": "Mumbai",
            "country": "India"
        },
        "consignee": {
            "name": "ABC Imports Inc",
            "address": "456 Import Ave",
            "city": "New York",
            "country": "United States"
        },
        "shipment_details": {
            "port_of_loading": "INMUN1",
            "port_of_discharge": "USNYC",
            "vessel_name": "MV Export Ship",
            "container_number": "ABCD1234567"
        },
        "packages": [
            {
                "package_number": 1,
                "description": "Organic Turmeric Powder",
                "quantity": 20,
                "unit": "cartons",
                "gross_weight_kg": 500.0,
                "net_weight_kg": 450.0,
                "dimensions": "50x40x30 cm",
                "volume_cbm": 0.06
            }
        ],
        "totals": {
            "total_packages": 20,
            "total_gross_weight_kg": 500.0,
            "total_net_weight_kg": 450.0,
            "total_volume_cbm": 1.2
        }
    }
    
    with patch('routers.documents.get_document_generator') as mock_generator:
        mock_instance = Mock()
        mock_instance.generate_document.return_value = mock_generated_document
        mock_generator.return_value = mock_instance
        
        with patch('routers.documents.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db_report = MagicMock()
            mock_db_report.product_name = "Organic Turmeric Powder"
            mock_db_report.destination_country = "United States"
            mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
            mock_db.return_value = mock_session
            
            response = client.post(
                "/api/documents/generate",
                json={
                    "document_type": "packing_list",
                    "report_id": "rpt_test123456",
                    "custom_data": {}
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["document_type"] == "packing_list"


def test_generate_document_with_custom_data(client, mock_generated_document):
    """Test generating a document with custom data override."""
    with patch('routers.documents.get_document_generator') as mock_generator:
        mock_instance = Mock()
        mock_instance.generate_document.return_value = mock_generated_document
        mock_generator.return_value = mock_instance
        
        with patch('routers.documents.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db_report = MagicMock()
            mock_db_report.product_name = "Organic Turmeric Powder"
            mock_db_report.destination_country = "United States"
            mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
            mock_db.return_value = mock_session
            
            response = client.post(
                "/api/documents/generate",
                json={
                    "document_type": "commercial_invoice",
                    "report_id": "rpt_test123456",
                    "custom_data": {
                        "invoice_number": "CUSTOM-INV-001",
                        "payment_terms": "60 days from B/L date"
                    }
                }
            )
            
            assert response.status_code == 201
            # Verify custom data was passed to generator
            mock_instance.generate_document.assert_called_once()
            call_args = mock_instance.generate_document.call_args
            assert call_args[1]["custom_data"]["invoice_number"] == "CUSTOM-INV-001"


def test_generate_document_report_not_found(client):
    """Test generating a document for non-existent report."""
    with patch('routers.documents.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = mock_session
        
        response = client.post(
            "/api/documents/generate",
            json={
                "document_type": "commercial_invoice",
                "report_id": "rpt_00000000000000000000000000000000",
                "custom_data": {}
            }
        )
        
        assert response.status_code == 404
        assert "Report not found" in response.json()["detail"]


def test_generate_document_invalid_report_id(client):
    """Test generating a document with invalid report ID format."""
    response = client.post(
        "/api/documents/generate",
        json={
            "document_type": "commercial_invoice",
            "report_id": "invalid-id",
            "custom_data": {}
        }
    )
    
    assert response.status_code == 400
    assert "Invalid ID format" in response.json()["detail"]


def test_validate_document_success(client, mock_validation_result):
    """Test validating a document."""
    with patch('routers.documents.get_document_generator') as mock_generator:
        mock_instance = Mock()
        mock_instance._validate_document.return_value = mock_validation_result
        mock_generator.return_value = mock_instance
        
        with patch('routers.documents.get_db') as mock_db:
            mock_session = MagicMock()
            
            # Mock document retrieval
            mock_db_document = MagicMock()
            mock_db_document.document_type = "commercial_invoice"
            mock_db_document.document_data = {
                "invoice_number": "INV-001",
                "exporter": {"gstin": "ABC123"}  # Invalid GSTIN
            }
            mock_db_document.report_id = uuid.uuid4()
            
            # Mock report retrieval
            mock_db_report = MagicMock()
            mock_db_report.destination_country = "United States"
            mock_db_report.hs_code = "0910.30"
            
            # Setup query chain
            def query_side_effect(model):
                mock_query = MagicMock()
                if model.__name__ == "GeneratedDocument":
                    mock_query.filter.return_value.first.return_value = mock_db_document
                elif model.__name__ == "Report":
                    mock_query.filter.return_value.first.return_value = mock_db_report
                return mock_query
            
            mock_session.query.side_effect = query_side_effect
            mock_db.return_value = mock_session
            
            response = client.post(
                "/api/documents/validate",
                json={"doc_id": "doc_test123456"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert len(data["errors"]) == 1
            assert len(data["warnings"]) == 1
            assert data["errors"][0]["field"] == "exporter.gstin"


def test_validate_document_not_found(client):
    """Test validating a non-existent document."""
    with patch('routers.documents.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = mock_session
        
        response = client.post(
            "/api/documents/validate",
            json={"doc_id": "doc_00000000000000000000000000000000"}
        )
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]


def test_validate_document_invalid_id(client):
    """Test validating a document with invalid ID format."""
    response = client.post(
        "/api/documents/validate",
        json={"doc_id": "invalid-id"}
    )
    
    assert response.status_code == 400
    assert "Invalid ID format" in response.json()["detail"]


def test_download_document_pdf(client):
    """Test downloading a document as PDF."""
    with patch('routers.documents.get_db') as mock_db:
        mock_session = MagicMock()
        
        # Mock document retrieval
        test_uuid = uuid.uuid4()
        mock_db_document = MagicMock()
        mock_db_document.id = test_uuid
        mock_db_document.document_type = "commercial_invoice"
        mock_db_document.pdf_url = "https://exportsathi-docs.s3.amazonaws.com/doc_test123456.pdf"
        mock_db_document.editable_url = "https://exportsathi-docs.s3.amazonaws.com/doc_test123456.docx"
        mock_db_document.is_valid = True
        mock_db_document.created_at = datetime.utcnow()
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_document
        mock_db.return_value = mock_session
        
        doc_id = f"doc_{str(test_uuid).replace('-', '')}"
        response = client.get(f"/api/documents/{doc_id}/download?format=pdf")
        
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "pdf"
        assert data["download_url"] == mock_db_document.pdf_url
        assert data["file_extension"] == "pdf"
        assert data["is_valid"] is True


def test_download_document_editable(client):
    """Test downloading a document in editable format."""
    with patch('routers.documents.get_db') as mock_db:
        mock_session = MagicMock()
        
        test_uuid = uuid.uuid4()
        mock_db_document = MagicMock()
        mock_db_document.id = test_uuid
        mock_db_document.document_type = "commercial_invoice"
        mock_db_document.pdf_url = "https://exportsathi-docs.s3.amazonaws.com/doc_test123456.pdf"
        mock_db_document.editable_url = "https://exportsathi-docs.s3.amazonaws.com/doc_test123456.docx"
        mock_db_document.is_valid = True
        mock_db_document.created_at = datetime.utcnow()
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_document
        mock_db.return_value = mock_session
        
        doc_id = f"doc_{str(test_uuid).replace('-', '')}"
        response = client.get(f"/api/documents/{doc_id}/download?format=editable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "editable"
        assert data["download_url"] == mock_db_document.editable_url
        assert data["file_extension"] == "docx"


def test_download_document_invalid_format(client):
    """Test downloading a document with invalid format."""
    response = client.get("/api/documents/doc_test123456/download?format=invalid")
    
    assert response.status_code == 400
    assert "Invalid format" in response.json()["detail"]


def test_download_document_not_found(client):
    """Test downloading a non-existent document."""
    with patch('routers.documents.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = mock_session
        
        response = client.get("/api/documents/doc_00000000000000000000000000000000/download")
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]


def test_download_document_invalid_id(client):
    """Test downloading a document with invalid ID format."""
    response = client.get("/api/documents/invalid-id/download")
    
    assert response.status_code == 400
    assert "Invalid ID format" in response.json()["detail"]


def test_generate_document_gst_lut(client, mock_generated_document):
    """Test generating a GST LUT document."""
    # Modify mock for GST LUT
    mock_generated_document.document_type = DocumentType.GST_LUT
    mock_generated_document.content = {
        "lut_number": "LUT-20240115-ABC123",
        "financial_year": "2023-2024",
        "date": "2024-01-15",
        "exporter": {
            "name": "Sample Exports Pvt Ltd",
            "address": "123 Export Street, Mumbai",
            "gstin": "27AABCU9603R1ZM",
            "pan": "AABCU9603R",
            "iec_code": "0512345678"
        }
    }
    
    with patch('routers.documents.get_document_generator') as mock_generator:
        mock_instance = Mock()
        mock_instance.generate_document.return_value = mock_generated_document
        mock_generator.return_value = mock_instance
        
        with patch('routers.documents.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db_report = MagicMock()
            mock_db_report.product_name = "Software Services"
            mock_db_report.destination_country = "United States"
            mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
            mock_db.return_value = mock_session
            
            response = client.post(
                "/api/documents/generate",
                json={
                    "document_type": "gst_lut",
                    "report_id": "rpt_test123456",
                    "custom_data": {}
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["document_type"] == "gst_lut"


def test_generate_document_softex(client, mock_generated_document):
    """Test generating a SOFTEX document for SaaS exports."""
    # Modify mock for SOFTEX
    mock_generated_document.document_type = DocumentType.SOFTEX
    mock_generated_document.content = {
        "softex_number": "SOFTEX-20240115-ABC123",
        "date": "2024-01-15",
        "exporter": {
            "name": "Sample Tech Pvt Ltd",
            "address": "123 Tech Park, Bangalore",
            "city": "Bangalore",
            "state": "Karnataka",
            "pin_code": "560001",
            "iec_code": "0512345678",
            "gstin": "29AABCU9603R1ZM",
            "pan": "AABCU9603R",
            "stpi_registration": "STPI/BLR/2020/12345"
        },
        "service_details": {
            "description": "Software Development Services",
            "service_category": "Software Development",
            "delivery_mode": "Electronic"
        }
    }
    
    with patch('routers.documents.get_document_generator') as mock_generator:
        mock_instance = Mock()
        mock_instance.generate_document.return_value = mock_generated_document
        mock_generator.return_value = mock_instance
        
        with patch('routers.documents.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db_report = MagicMock()
            mock_db_report.product_name = "Software Development Services"
            mock_db_report.destination_country = "United States"
            mock_db_report.business_type = "SaaS"
            mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
            mock_db.return_value = mock_session
            
            response = client.post(
                "/api/documents/generate",
                json={
                    "document_type": "softex",
                    "report_id": "rpt_test123456",
                    "custom_data": {}
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["document_type"] == "softex"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
