"""
Unit tests for Document Generator Service

Tests document generation, template loading, auto-fill, and validation.
"""

import pytest
from datetime import datetime
from services.document_generator import DocumentGenerator, get_document_generator
from models.enums import DocumentType, ValidationSeverity


@pytest.fixture
def document_generator():
    """Create document generator instance for testing."""
    return DocumentGenerator()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "company_name": "ABC Exports Pvt Ltd",
        "address": "123 Export Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pin_code": "400001",
        "gstin": "27AABCU9603R1ZM",
        "iec_code": "0512345678",
        "pan": "AABCU9603R",
        "email": "exports@abc.com",
        "phone": "+91-22-12345678"
    }


@pytest.fixture
def sample_report_data():
    """Sample report data for testing."""
    return {
        "product_name": "Organic Turmeric Powder",
        "destination_country": "United States",
        "hs_code": "0910.30.00"
    }


class TestDocumentGenerator:
    """Test DocumentGenerator class."""
    
    def test_initialization(self, document_generator):
        """Test document generator initializes correctly."""
        assert document_generator is not None
        assert document_generator.compliance_analyzer is not None
    
    def test_get_document_generator_singleton(self):
        """Test global singleton instance."""
        gen1 = get_document_generator()
        gen2 = get_document_generator()
        assert gen1 is gen2

    
    def test_generate_commercial_invoice(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test commercial invoice generation."""
        doc = document_generator.generate_document(
            document_type=DocumentType.COMMERCIAL_INVOICE,
            report_data=sample_report_data,
            user_data=sample_user_data
        )
        
        assert doc.document_id.startswith("doc_")
        assert doc.document_type == DocumentType.COMMERCIAL_INVOICE
        assert doc.content["invoice_number"].startswith("INV-")
        assert doc.content["exporter"]["name"] == "ABC Exports Pvt Ltd"
        assert doc.content["exporter"]["gstin"] == "27AABCU9603R1ZM"
        assert doc.content["consignee"]["country"] == "United States"
        assert doc.pdf_url.endswith(".pdf")
        assert doc.editable_url.endswith(".docx")
    
    def test_generate_packing_list(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test packing list generation."""
        doc = document_generator.generate_document(
            document_type=DocumentType.PACKING_LIST,
            report_data=sample_report_data,
            user_data=sample_user_data
        )
        
        assert doc.document_id.startswith("doc_")
        assert doc.document_type == DocumentType.PACKING_LIST
        assert doc.content["packing_list_number"].startswith("PL-")
        assert doc.content["exporter"]["name"] == "ABC Exports Pvt Ltd"
        assert doc.content["consignee"]["country"] == "United States"
    
    def test_generate_shipping_bill(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test shipping bill generation."""
        doc = document_generator.generate_document(
            document_type=DocumentType.SHIPPING_BILL,
            report_data=sample_report_data,
            user_data=sample_user_data
        )
        
        assert doc.document_id.startswith("doc_")
        assert doc.document_type == DocumentType.SHIPPING_BILL
        assert doc.content["shipping_bill_number"].startswith("SB-")
        assert doc.content["exporter"]["iec_code"] == "0512345678"
        assert doc.content["exporter"]["gstin"] == "27AABCU9603R1ZM"
        assert doc.content["country_of_final_destination"] == "United States"
    
    def test_generate_gst_lut(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test GST LUT generation."""
        doc = document_generator.generate_document(
            document_type=DocumentType.GST_LUT,
            report_data=sample_report_data,
            user_data=sample_user_data
        )
        
        assert doc.document_id.startswith("doc_")
        assert doc.document_type == DocumentType.GST_LUT
        assert doc.content["lut_number"].startswith("LUT-")
        assert doc.content["exporter"]["gstin"] == "27AABCU9603R1ZM"
        assert doc.content["exporter"]["pan"] == "AABCU9603R"
        assert doc.content["financial_year"]  # Should be auto-filled

    
    def test_generate_softex(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test SOFTEX declaration generation."""
        doc = document_generator.generate_document(
            document_type=DocumentType.SOFTEX,
            report_data=sample_report_data,
            user_data=sample_user_data
        )
        
        assert doc.document_id.startswith("doc_")
        assert doc.document_type == DocumentType.SOFTEX
        assert doc.content["softex_number"].startswith("SOFTEX-")
        assert doc.content["exporter"]["iec_code"] == "0512345678"
        assert doc.content["buyer"]["country"] == "United States"
    
    def test_generate_certificate_of_origin(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test certificate of origin generation."""
        doc = document_generator.generate_document(
            document_type=DocumentType.CERTIFICATE_OF_ORIGIN,
            report_data=sample_report_data,
            user_data=sample_user_data
        )
        
        assert doc.document_id.startswith("doc_")
        assert doc.document_type == DocumentType.CERTIFICATE_OF_ORIGIN
        assert doc.content["certificate_number"].startswith("COO-")
        assert doc.content["exporter"]["name"] == "ABC Exports Pvt Ltd"
        assert doc.content["transport_details"]["country_of_origin"] == "India"
        assert doc.content["transport_details"]["country_of_destination"] == "United States"
    
    def test_custom_data_override(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test custom data overrides template defaults."""
        custom_data = {
            "invoice_number": "CUSTOM-INV-001",
            "payment_terms": "Net 60 days"
        }
        
        doc = document_generator.generate_document(
            document_type=DocumentType.COMMERCIAL_INVOICE,
            report_data=sample_report_data,
            user_data=sample_user_data,
            custom_data=custom_data
        )
        
        assert doc.content["invoice_number"] == "CUSTOM-INV-001"
        assert doc.content["payment_terms"] == "Net 60 days"
    
    def test_validation_invalid_gstin(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test validation catches invalid GSTIN."""
        # Invalid GSTIN (wrong length)
        sample_user_data["gstin"] = "INVALID"
        
        doc = document_generator.generate_document(
            document_type=DocumentType.COMMERCIAL_INVOICE,
            report_data=sample_report_data,
            user_data=sample_user_data
        )
        
        assert not doc.validation_results.is_valid
        assert any("GSTIN" in error.message for error in doc.validation_results.errors)

    
    def test_validation_invalid_iec(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test validation catches invalid IEC code."""
        # Invalid IEC (wrong length)
        sample_user_data["iec_code"] = "123"
        
        doc = document_generator.generate_document(
            document_type=DocumentType.SHIPPING_BILL,
            report_data=sample_report_data,
            user_data=sample_user_data
        )
        
        assert not doc.validation_results.is_valid
        assert any("IEC" in error.message for error in doc.validation_results.errors)
    
    def test_validation_missing_required_fields(
        self,
        document_generator,
        sample_report_data
    ):
        """Test validation catches missing required fields."""
        # Empty user data
        doc = document_generator.generate_document(
            document_type=DocumentType.COMMERCIAL_INVOICE,
            report_data=sample_report_data,
            user_data={}
        )
        
        assert not doc.validation_results.is_valid
        assert any("Exporter name" in error.message for error in doc.validation_results.errors)
    
    def test_validation_rms_trigger_keywords(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test validation warns about RMS trigger keywords."""
        custom_data = {
            "items": [
                {
                    "description": "Chemical compound for industrial use",
                    "quantity": 100
                }
            ]
        }
        
        doc = document_generator.generate_document(
            document_type=DocumentType.COMMERCIAL_INVOICE,
            report_data=sample_report_data,
            user_data=sample_user_data,
            custom_data=custom_data
        )
        
        # Should have warning about "chemical" keyword
        assert len(doc.validation_results.warnings) > 0
        assert any("chemical" in warning.message.lower() for warning in doc.validation_results.warnings)
    
    def test_template_loading_all_types(self, document_generator):
        """Test all document type templates can be loaded."""
        for doc_type in DocumentType:
            template = document_generator._get_template(doc_type)
            assert template is not None
            assert isinstance(template, dict)
    
    def test_auto_fill_preserves_custom_data(
        self,
        document_generator,
        sample_user_data,
        sample_report_data
    ):
        """Test auto-fill doesn't override custom data."""
        custom_data = {
            "exporter": {
                "name": "Custom Company Name"
            }
        }
        
        doc = document_generator.generate_document(
            document_type=DocumentType.COMMERCIAL_INVOICE,
            report_data=sample_report_data,
            user_data=sample_user_data,
            custom_data=custom_data
        )
        
        # Custom name should be preserved
        assert doc.content["exporter"]["name"] == "Custom Company Name"
        # But other fields should still be auto-filled
        assert doc.content["exporter"]["gstin"] == "27AABCU9603R1ZM"


class TestTemplateStructures:
    """Test template structures are correct."""
    
    def test_commercial_invoice_template_structure(self, document_generator):
        """Test commercial invoice template has required fields."""
        template = document_generator._get_commercial_invoice_template()
        
        assert "invoice_number" in template
        assert "exporter" in template
        assert "consignee" in template
        assert "shipment_details" in template
        assert "items" in template
        assert "totals" in template
        assert "bank_details" in template
        assert template["exporter"]["country"] == "India"
    
    def test_gst_lut_template_structure(self, document_generator):
        """Test GST LUT template has required fields."""
        template = document_generator._get_gst_lut_template()
        
        assert "lut_number" in template
        assert "financial_year" in template
        assert "exporter" in template
        assert "undertaking" in template
        assert "declaration" in template
        assert template["undertaking"]["export_without_payment_of_igst"] is True
    
    def test_softex_template_structure(self, document_generator):
        """Test SOFTEX template has required fields."""
        template = document_generator._get_softex_template()
        
        assert "softex_number" in template
        assert "exporter" in template
        assert "service_details" in template
        assert "invoice_details" in template
        assert "payment_details" in template
        assert template["service_details"]["delivery_mode"] == "Electronic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
