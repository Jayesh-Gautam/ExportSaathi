"""
Document generation and validation models.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from .enums import DocumentType, ValidationSeverity


class ValidationError(BaseModel):
    """Validation error in a document."""
    field: str = Field(..., description="Field with error")
    message: str = Field(..., description="Error message")
    severity: ValidationSeverity = Field(..., description="Error severity")
    suggestion: str = Field(..., description="Suggestion to fix the error")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "port_code",
                "message": "Port code does not match destination country",
                "severity": "error",
                "suggestion": "Use port code USNYC for New York, USA"
            }
        }


class ValidationWarning(BaseModel):
    """Validation warning in a document."""
    field: str = Field(..., description="Field with warning")
    message: str = Field(..., description="Warning message")
    suggestion: str = Field(..., description="Suggestion to address the warning")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "product_description",
                "message": "Description contains potential RMS trigger keyword: 'chemical'",
                "suggestion": "Consider using more specific terminology"
            }
        }


class ValidationResult(BaseModel):
    """Result of document validation."""
    is_valid: bool = Field(..., description="Whether document is valid")
    errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: List[ValidationWarning] = Field(default_factory=list, description="Validation warnings")

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": [
                    {
                        "field": "product_description",
                        "message": "Description is very long",
                        "suggestion": "Consider shortening to improve clarity"
                    }
                ]
            }
        }


class GeneratedDocument(BaseModel):
    """Generated export document."""
    document_id: str = Field(..., description="Unique document identifier")
    document_type: DocumentType = Field(..., description="Type of document")
    content: Dict[str, Any] = Field(..., description="Document content")
    validation_results: ValidationResult = Field(..., description="Validation results")
    pdf_url: str = Field(..., description="URL to PDF version")
    editable_url: str = Field(..., description="URL to editable version")
    generated_at: datetime = Field(..., description="Generation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123e4567",
                "document_type": "commercial_invoice",
                "content": {
                    "invoice_number": "INV-2024-001",
                    "date": "2024-01-15",
                    "exporter": "ABC Exports Pvt Ltd",
                    "consignee": "XYZ Imports Inc",
                    "items": []
                },
                "validation_results": {
                    "is_valid": True,
                    "errors": [],
                    "warnings": []
                },
                "pdf_url": "https://s3.amazonaws.com/docs/doc_123e4567.pdf",
                "editable_url": "https://s3.amazonaws.com/docs/doc_123e4567.docx",
                "generated_at": "2024-01-15T10:30:00Z"
            }
        }


class DocumentGenerationRequest(BaseModel):
    """Request to generate a document."""
    document_type: DocumentType = Field(..., description="Type of document to generate")
    report_id: str = Field(..., description="Associated report ID")
    custom_data: Dict[str, Any] = Field(default_factory=dict, description="Custom document data")

    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "commercial_invoice",
                "report_id": "rpt_123e4567",
                "custom_data": {
                    "invoice_number": "INV-2024-001",
                    "payment_terms": "30 days"
                }
            }
        }
