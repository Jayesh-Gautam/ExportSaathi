"""
Reports API Router
Handles export readiness report generation

CRITICAL MVP TASK: This router implements the core API endpoints for report generation.
It provides:
1. POST /api/reports/generate - Generate new export readiness report with image upload
2. GET /api/reports/{report_id} - Retrieve existing report
3. GET /api/reports/{report_id}/status - Check report generation status
4. PUT /api/reports/{report_id}/hs-code - Update HS code manually

Requirements: 8.1, 8.2, 8.3, 8.6
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
import logging
import uuid
from datetime import datetime

from models import (
    QueryInput,
    ExportReadinessReport,
    HSCodePrediction,
    BusinessType,
    CompanySize,
    ReportStatus
)
from models.internal import ErrorResponse
from services.report_generator import ReportGenerator
from database.connection import get_db
from database.models import Report as DBReport

logger = logging.getLogger(__name__)

router = APIRouter()


def parse_report_id(report_id: str) -> uuid.UUID:
    """
    Parse report ID string to UUID.
    
    Handles both UUID format and hex string format (with or without rpt_ prefix).
    
    Args:
        report_id: Report ID string (e.g., "rpt_abc123..." or "abc123...")
        
    Returns:
        UUID object
        
    Raises:
        HTTPException: If report ID format is invalid
    """
    # Remove rpt_ prefix if present
    clean_id = report_id.replace("rpt_", "")
    
    # Try to parse as UUID - if it fails, it might be a hex string without dashes
    try:
        # First try direct UUID parsing
        return uuid.UUID(clean_id)
    except ValueError:
        # Try adding dashes if it's a 32-character hex string
        if len(clean_id) == 32 and all(c in '0123456789abcdefABCDEF' for c in clean_id):
            try:
                # Format as UUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                formatted = f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"
                return uuid.UUID(formatted)
            except ValueError:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report ID format"
        )


@router.post("/generate", response_model=ExportReadinessReport, status_code=status.HTTP_201_CREATED)
async def generate_report(
    product_name: str = Form(..., min_length=1, max_length=200, description="Product name"),
    destination_country: str = Form(..., min_length=1, max_length=100, description="Destination country"),
    business_type: str = Form(..., description="Business type (Manufacturing/SaaS/Merchant)"),
    company_size: str = Form(..., description="Company size (Micro/Small/Medium)"),
    product_image: Optional[UploadFile] = File(None, description="Product image (optional)"),
    ingredients: Optional[str] = Form(None, max_length=2000, description="Product ingredients"),
    bom: Optional[str] = Form(None, max_length=2000, description="Bill of Materials"),
    monthly_volume: Optional[float] = Form(None, gt=0, description="Monthly export volume"),
    price_range: Optional[str] = Form(None, description="Price range"),
    payment_mode: Optional[str] = Form(None, description="Payment mode"),
    db: Session = Depends(get_db)
):
    """
    Generate export readiness report with multipart form data.
    
    This endpoint accepts product details including an optional image upload,
    generates a comprehensive export readiness report, and stores it in the database.
    
    **Request Parameters:**
    - product_name: Name of the product (required)
    - destination_country: Target export country (required)
    - business_type: Type of business - Manufacturing, SaaS, or Merchant (required)
    - company_size: Company size - Micro, Small, or Medium (required)
    - product_image: Product image file (optional, helps with HS code prediction)
    - ingredients: Product ingredients (optional)
    - bom: Bill of Materials (optional)
    - monthly_volume: Monthly export volume (optional)
    - price_range: Price range of product (optional)
    - payment_mode: Preferred payment mode (optional)
    
    **Returns:**
    - Complete ExportReadinessReport with HS code, certifications, risks, costs, timeline, and action plan
    
    **Errors:**
    - 400: Invalid input data
    - 422: Validation error
    - 500: Internal server error during report generation
    
    Requirements: 8.1, 8.2, 8.3
    """
    try:
        logger.info(f"Generating report for: {product_name} -> {destination_country}")
        
        # Validate business_type and company_size enums
        try:
            business_type_enum = BusinessType(business_type)
            company_size_enum = CompanySize(company_size)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid enum value: {str(e)}"
            )
        
        # Process image upload if provided
        image_bytes = None
        image_url = None
        if product_image:
            # Validate file size (max 10MB)
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            content = await product_image.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image file size exceeds 10MB limit"
                )
            
            # Validate file type
            allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
            if product_image.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
                )
            
            image_bytes = content
            # In MVP, we'll store image_url as None - can be enhanced to upload to S3
            logger.info(f"Image uploaded: {product_image.filename}, size: {len(content)} bytes")
        
        # Create QueryInput model
        query = QueryInput(
            product_name=product_name.strip(),
            product_image=image_bytes,
            ingredients=ingredients.strip() if ingredients else None,
            bom=bom.strip() if bom else None,
            destination_country=destination_country.strip(),
            business_type=business_type_enum,
            company_size=company_size_enum,
            monthly_volume=monthly_volume,
            price_range=price_range,
            payment_mode=payment_mode
        )
        
        # Generate report using ReportGenerator service
        logger.info("Calling ReportGenerator service...")
        generator = ReportGenerator()
        report = generator.generate_report(query)
        
        logger.info(f"Report generated successfully: {report.report_id}")
        
        # Store report in database
        try:
            db_report = DBReport(
                id=uuid.UUID(report.report_id.replace("rpt_", "")),
                user_id=None,  # MVP: No user authentication yet
                product_name=query.product_name,
                product_image_url=image_url,
                ingredients=query.ingredients,
                bom=query.bom,
                destination_country=query.destination_country,
                business_type=query.business_type.value,
                company_size=query.company_size.value,
                monthly_volume=int(query.monthly_volume) if query.monthly_volume else None,
                price_range=query.price_range,
                payment_mode=query.payment_mode,
                hs_code=report.hs_code.code,
                hs_code_confidence=float(report.hs_code.confidence),
                risk_score=report.risk_score,
                estimated_cost=float(report.costs.total),
                estimated_timeline_days=report.timeline.estimated_days,
                report_data=report.model_dump(mode='json'),
                status=report.status.value
            )
            
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
            
            logger.info(f"Report saved to database: {db_report.id}")
        
        except Exception as db_error:
            logger.error(f"Failed to save report to database: {db_error}")
            db.rollback()
            # Continue - report was generated successfully, just not persisted
        
        return report
    
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
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the report. Please try again later."
        )


@router.get("/{report_id}", response_model=ExportReadinessReport)
async def get_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve existing export readiness report by ID.
    
    **Path Parameters:**
    - report_id: Unique report identifier (format: rpt_xxxxxxxxxxxx)
    
    **Returns:**
    - Complete ExportReadinessReport
    
    **Errors:**
    - 404: Report not found
    - 500: Internal server error
    
    Requirements: 8.2
    """
    try:
        logger.info(f"Retrieving report: {report_id}")
        
        # Parse report ID
        report_uuid = parse_report_id(report_id)
        
        # Query database
        db_report = db.query(DBReport).filter(DBReport.id == report_uuid).first()
        
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )
        
        # Convert database model to Pydantic model
        report = ExportReadinessReport(**db_report.report_data)
        
        logger.info(f"Report retrieved successfully: {report_id}")
        return report
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error retrieving report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the report."
        )


@router.get("/{report_id}/status")
async def get_report_status(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Check report generation status.
    
    This endpoint is useful for polling report status when generation is async.
    In the MVP, reports are generated synchronously, so this will always return 'completed'.
    
    **Path Parameters:**
    - report_id: Unique report identifier
    
    **Returns:**
    - JSON with report_id, status, and optional metadata
    
    **Errors:**
    - 404: Report not found
    - 500: Internal server error
    
    Requirements: 8.3
    """
    try:
        logger.info(f"Checking status for report: {report_id}")
        
        # Parse report ID
        report_uuid = parse_report_id(report_id)
        
        # Query database
        db_report = db.query(DBReport).filter(DBReport.id == report_uuid).first()
        
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )
        
        # Return status information
        return {
            "report_id": f"rpt_{str(db_report.id).replace('-', '')}",
            "status": db_report.status,
            "created_at": db_report.created_at.isoformat() if db_report.created_at else None,
            "updated_at": db_report.updated_at.isoformat() if db_report.updated_at else None,
            "hs_code": db_report.hs_code,
            "risk_score": db_report.risk_score,
            "estimated_cost": float(db_report.estimated_cost) if db_report.estimated_cost else None,
            "estimated_timeline_days": db_report.estimated_timeline_days
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error checking report status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking report status."
        )


@router.put("/{report_id}/hs-code")
async def update_hs_code(
    report_id: str,
    hs_code: str = Form(..., min_length=4, max_length=20, description="New HS code"),
    db: Session = Depends(get_db)
):
    """
    Update HS code manually for a report.
    
    This endpoint allows users to override the AI-predicted HS code with a manually
    verified code from a customs broker or trade consultant.
    
    **Path Parameters:**
    - report_id: Unique report identifier
    
    **Form Parameters:**
    - hs_code: New HS code to set (4-20 characters)
    
    **Returns:**
    - Updated report with new HS code
    
    **Errors:**
    - 400: Invalid HS code format
    - 404: Report not found
    - 500: Internal server error
    
    Requirements: 8.6
    """
    try:
        logger.info(f"Updating HS code for report {report_id} to {hs_code}")
        
        # Validate HS code format (basic validation)
        hs_code = hs_code.strip().replace(".", "").replace(" ", "")
        if not hs_code.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HS code must contain only digits (dots and spaces are allowed)"
            )
        
        # Parse report ID
        report_uuid = parse_report_id(report_id)
        
        # Query database
        db_report = db.query(DBReport).filter(DBReport.id == report_uuid).first()
        
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )
        
        # Update HS code in database
        old_hs_code = db_report.hs_code
        db_report.hs_code = hs_code
        db_report.hs_code_confidence = 100.0  # Manual override = 100% confidence
        
        # Update HS code in report_data JSON
        report_data = db_report.report_data
        if report_data and 'hs_code' in report_data:
            report_data['hs_code']['code'] = hs_code
            report_data['hs_code']['confidence'] = 100.0
            db_report.report_data = report_data
        
        db.commit()
        db.refresh(db_report)
        
        logger.info(f"HS code updated: {old_hs_code} -> {hs_code}")
        
        # Return updated report
        report = ExportReadinessReport(**db_report.report_data)
        return report
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error updating HS code: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the HS code."
        )
