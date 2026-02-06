"""
Documents API Router
Handles document generation, validation, and download

This router implements the core API endpoints for export document management.
It provides:
1. POST /api/documents/generate - Generate export document with auto-fill
2. POST /api/documents/validate - Validate document for compliance
3. GET /api/documents/{doc_id}/download - Download document as PDF

Requirements: 8.1
"""
from fastapi import APIRouter, HTTPException, Depends, status, Response
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
import uuid
from datetime import datetime

from models.document import (
    DocumentGenerationRequest,
    GeneratedDocument,
    ValidationResult
)
from models.enums import DocumentType
from services.document_generator import get_document_generator
from database.connection import get_db
from database.models import GeneratedDocument as DBGeneratedDocument, Report as DBReport

logger = logging.getLogger(__name__)

router = APIRouter()


def parse_uuid(id_str: str, prefix: str = "") -> uuid.UUID:
    """
    Parse ID string to UUID.
    
    Handles both UUID format and hex string format (with or without prefix).
    
    Args:
        id_str: ID string (e.g., "doc_abc123..." or "abc123...")
        prefix: Optional prefix to remove (e.g., "doc_", "rpt_")
        
    Returns:
        UUID object
        
    Raises:
        HTTPException: If ID format is invalid
    """
    # Remove prefix if present
    clean_id = id_str.replace(prefix, "") if prefix else id_str
    
    # Try to parse as UUID
    try:
        return uuid.UUID(clean_id)
    except ValueError:
        # Try adding dashes if it's a 32-character hex string
        if len(clean_id) == 32 and all(c in '0123456789abcdefABCDEF' for c in clean_id):
            try:
                formatted = f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"
                return uuid.UUID(formatted)
            except ValueError:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID format: {id_str}"
        )


@router.post("/generate", response_model=GeneratedDocument, status_code=status.HTTP_201_CREATED)
async def generate_document(
    request: DocumentGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate export document with auto-filled template.
    
    This endpoint generates export documents (commercial invoice, packing list, 
    shipping bill, GST LUT, SOFTEX, certificate of origin) using India-specific 
    templates. Documents are auto-filled with data from the associated report 
    and user profile, then validated for compliance.
    
    **Request Body:**
    - document_type: Type of document to generate (required)
    - report_id: Associated export readiness report ID (required)
    - custom_data: Optional custom fields to override auto-filled values
    
    **Returns:**
    - GeneratedDocument with content, validation results, and download URLs
    
    **Errors:**
    - 400: Invalid request data
    - 404: Report not found
    - 422: Validation error
    - 500: Internal server error during document generation
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Generating document: {request.document_type} for report {request.report_id}")
        
        # Parse report ID
        report_uuid = parse_uuid(request.report_id, prefix="rpt_")
        
        # Retrieve report from database
        db_report = db.query(DBReport).filter(DBReport.id == report_uuid).first()
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {request.report_id}"
            )
        
        # Extract report data
        report_data = {
            "product_name": db_report.product_name,
            "destination_country": db_report.destination_country,
            "hs_code": db_report.hs_code,
            "business_type": db_report.business_type,
            "company_size": db_report.company_size,
            "monthly_volume": db_report.monthly_volume,
            "price_range": db_report.price_range
        }
        
        # Extract user data (in MVP, we use placeholder data)
        # In production, this would come from authenticated user profile
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
        
        # Generate document using DocumentGenerator service
        logger.info("Calling DocumentGenerator service...")
        generator = get_document_generator()
        document = generator.generate_document(
            document_type=request.document_type,
            report_data=report_data,
            user_data=user_data,
            custom_data=request.custom_data
        )
        
        logger.info(f"Document generated successfully: {document.document_id}")
        
        # Store document in database
        try:
            doc_uuid = uuid.UUID(document.document_id.replace("doc_", ""))
            
            db_document = DBGeneratedDocument(
                id=doc_uuid,
                user_id=None,  # MVP: No user authentication yet
                report_id=report_uuid,
                document_type=document.document_type.value,
                document_data=document.content,
                pdf_url=document.pdf_url,
                editable_url=document.editable_url,
                validation_results=document.validation_results.model_dump(mode='json'),
                is_valid=document.validation_results.is_valid,
                created_at=document.generated_at
            )
            
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            
            logger.info(f"Document saved to database: {db_document.id}")
        
        except Exception as db_error:
            logger.error(f"Failed to save document to database: {db_error}")
            db.rollback()
            # Continue - document was generated successfully, just not persisted
        
        return document
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as e:
        # Validation errors
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error generating document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the document. Please try again later."
        )


@router.post("/validate", response_model=ValidationResult)
async def validate_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    Validate document for compliance.
    
    This endpoint validates a previously generated document for compliance issues.
    It performs AI validation checks including:
    - Port code mismatch detection
    - Invoice format validation
    - GST vs Shipping Bill matching
    - RMS risk trigger detection
    
    **Request Body:**
    - doc_id: Document ID to validate (required)
    
    **Returns:**
    - ValidationResult with errors and warnings
    
    **Errors:**
    - 400: Invalid document ID
    - 404: Document not found
    - 500: Internal server error during validation
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Validating document: {doc_id}")
        
        # Parse document ID
        doc_uuid = parse_uuid(doc_id, prefix="doc_")
        
        # Retrieve document from database
        db_document = db.query(DBGeneratedDocument).filter(
            DBGeneratedDocument.id == doc_uuid
        ).first()
        
        if not db_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {doc_id}"
            )
        
        # Get associated report for validation context
        report_data = {}
        if db_document.report_id:
            db_report = db.query(DBReport).filter(
                DBReport.id == db_document.report_id
            ).first()
            if db_report:
                report_data = {
                    "destination_country": db_report.destination_country,
                    "hs_code": db_report.hs_code
                }
        
        # Re-validate document using DocumentGenerator service
        logger.info("Calling DocumentGenerator validation...")
        generator = get_document_generator()
        validation_results = generator._validate_document(
            document_type=DocumentType(db_document.document_type),
            content=db_document.document_data,
            report_data=report_data
        )
        
        # Update validation results in database
        try:
            db_document.validation_results = validation_results.model_dump(mode='json')
            db_document.is_valid = validation_results.is_valid
            db.commit()
            
            logger.info(f"Document validation updated: {doc_id}, valid={validation_results.is_valid}")
        
        except Exception as db_error:
            logger.error(f"Failed to update validation results: {db_error}")
            db.rollback()
        
        return validation_results
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error validating document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while validating the document."
        )


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: str,
    format: str = "pdf",
    db: Session = Depends(get_db)
):
    """
    Download document as PDF or editable format.
    
    This endpoint provides download URLs for generated documents in PDF or 
    editable formats (DOCX/XLSX).
    
    **Path Parameters:**
    - doc_id: Document ID to download (required)
    
    **Query Parameters:**
    - format: Download format - "pdf" or "editable" (default: "pdf")
    
    **Returns:**
    - JSON with download URL and document metadata
    
    **Errors:**
    - 400: Invalid document ID or format
    - 404: Document not found
    - 500: Internal server error
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Downloading document: {doc_id}, format: {format}")
        
        # Validate format parameter
        if format not in ["pdf", "editable"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Must be 'pdf' or 'editable'"
            )
        
        # Parse document ID
        doc_uuid = parse_uuid(doc_id, prefix="doc_")
        
        # Retrieve document from database
        db_document = db.query(DBGeneratedDocument).filter(
            DBGeneratedDocument.id == doc_uuid
        ).first()
        
        if not db_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {doc_id}"
            )
        
        # Get download URL based on format
        download_url = db_document.pdf_url if format == "pdf" else db_document.editable_url
        
        if not download_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document file not available in {format} format"
            )
        
        # Return download information
        return {
            "document_id": f"doc_{str(db_document.id).replace('-', '')}",
            "document_type": db_document.document_type,
            "format": format,
            "download_url": download_url,
            "is_valid": db_document.is_valid,
            "created_at": db_document.created_at.isoformat() if db_document.created_at else None,
            "file_extension": "pdf" if format == "pdf" else "docx"
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error downloading document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while preparing the document download."
        )
