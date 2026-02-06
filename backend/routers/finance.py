"""
Finance API Router
Handles finance readiness analysis, RoDTEP calculations, and working capital calculations

This router implements the core API endpoints for finance module.
It provides:
1. GET /api/finance/analysis/{report_id} - Get complete finance readiness analysis
2. POST /api/finance/rodtep-calculator - Calculate RoDTEP benefits
3. POST /api/finance/working-capital - Calculate working capital requirements

Requirements: 8.1
"""
from fastapi import APIRouter, HTTPException, Depends, status, Body
from sqlalchemy.orm import Session
from typing import Optional
import logging
import uuid

from models.finance import (
    FinanceAnalysis,
    WorkingCapitalAnalysis,
    RoDTEPBenefit
)
from services.finance_module import FinanceModule
from database.connection import get_db
from database.models import Report as DBReport
from pydantic import BaseModel, Field

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


class RoDTEPCalculatorRequest(BaseModel):
    """Request model for RoDTEP calculator."""
    hs_code: str = Field(..., min_length=4, max_length=20, description="HS code")
    destination: str = Field(..., min_length=1, max_length=100, description="Destination country")
    fob_value: float = Field(..., gt=0, description="FOB (Free on Board) value in INR")
    
    class Config:
        json_schema_extra = {
            "example": {
                "hs_code": "0910.30",
                "destination": "United States",
                "fob_value": 200000
            }
        }


class WorkingCapitalRequest(BaseModel):
    """Request model for working capital calculator."""
    report_id: str = Field(..., description="Report ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "rpt_123e4567e89b12d3"
            }
        }


@router.get("/analysis/{report_id}", response_model=FinanceAnalysis)
async def get_finance_analysis(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete finance readiness analysis for a report.
    
    This endpoint generates a comprehensive finance analysis including:
    - Working capital requirements breakdown
    - Pre-shipment credit eligibility assessment
    - RoDTEP benefit calculation
    - GST refund estimation
    - Cash flow timeline with liquidity gap identification
    - Currency hedging recommendations
    - Available financing options
    
    **Path Parameters:**
    - report_id: Unique report identifier (format: rpt_xxxxxxxxxxxx or UUID)
    
    **Returns:**
    - Complete FinanceAnalysis with all financial metrics and recommendations
    
    **Errors:**
    - 400: Invalid report ID format
    - 404: Report not found
    - 500: Internal server error during analysis
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Generating finance analysis for report: {report_id}")
        
        # Parse report ID
        report_uuid = parse_report_id(report_id)
        
        # Verify report exists
        db_report = db.query(DBReport).filter(DBReport.id == report_uuid).first()
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )
        
        # Generate finance analysis using FinanceModule service
        logger.info("Calling FinanceModule service...")
        finance_module = FinanceModule(db)
        analysis = finance_module.generate_complete_analysis(str(report_uuid))
        
        logger.info(f"Finance analysis generated successfully for report: {report_id}")
        
        return analysis
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as e:
        # Validation errors from FinanceModule
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error generating finance analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the finance analysis. Please try again later."
        )


@router.post("/rodtep-calculator", response_model=RoDTEPBenefit)
async def calculate_rodtep(
    request: RoDTEPCalculatorRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate RoDTEP (Remission of Duties and Taxes on Exported Products) benefit.
    
    This endpoint calculates the RoDTEP benefit amount based on the HS code,
    destination country, and FOB value. RoDTEP is a government scheme that
    provides refunds on embedded duties and taxes that are not refunded through
    other mechanisms.
    
    **Request Body:**
    - hs_code: Harmonized System code (4-20 characters)
    - destination: Destination country name
    - fob_value: FOB (Free on Board) value in INR (must be positive)
    
    **Returns:**
    - RoDTEPBenefit with HS code, rate percentage, and estimated benefit amount
    
    **Errors:**
    - 400: Invalid request data
    - 422: Validation error
    - 500: Internal server error during calculation
    
    **Example:**
    ```json
    {
        "hs_code": "0910.30",
        "destination": "United States",
        "fob_value": 200000
    }
    ```
    
    **Response:**
    ```json
    {
        "hs_code": "0910.30",
        "rate_percentage": 2.5,
        "estimated_amount": 5000,
        "currency": "INR"
    }
    ```
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Calculating RoDTEP for HS code: {request.hs_code}, destination: {request.destination}")
        
        # Validate and clean HS code
        hs_code = request.hs_code.strip().replace(".", "").replace(" ", "")
        if not hs_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HS code cannot be empty"
            )
        
        # Calculate RoDTEP using FinanceModule service
        logger.info("Calling FinanceModule RoDTEP calculator...")
        finance_module = FinanceModule(db)
        rodtep_benefit = finance_module.calculate_rodtep_benefit(
            hs_code=hs_code,
            destination=request.destination.strip(),
            fob_value=request.fob_value
        )
        
        logger.info(f"RoDTEP calculated: {rodtep_benefit.rate_percentage}% = ₹{rodtep_benefit.estimated_amount}")
        
        return rodtep_benefit
    
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
        logger.error(f"Error calculating RoDTEP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while calculating RoDTEP benefit. Please try again later."
        )


@router.post("/working-capital", response_model=WorkingCapitalAnalysis)
async def calculate_working_capital(
    request: WorkingCapitalRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate working capital requirements for an export order.
    
    This endpoint calculates the total working capital needed to fulfill an
    export order, including:
    - Product/manufacturing costs
    - Certification costs
    - Logistics costs (freight, insurance, customs)
    - Documentation costs
    - Buffer amount (15% contingency)
    
    **Request Body:**
    - report_id: Associated export readiness report ID
    
    **Returns:**
    - WorkingCapitalAnalysis with detailed cost breakdown and total
    
    **Errors:**
    - 400: Invalid report ID format
    - 404: Report not found
    - 422: Validation error
    - 500: Internal server error during calculation
    
    **Example:**
    ```json
    {
        "report_id": "rpt_123e4567e89b12d3"
    }
    ```
    
    **Response:**
    ```json
    {
        "product_cost": 100000,
        "certification_costs": 50000,
        "logistics_costs": 25000,
        "documentation_costs": 10000,
        "buffer": 27750,
        "total": 212750,
        "currency": "INR"
    }
    ```
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Calculating working capital for report: {request.report_id}")
        
        # Parse report ID
        report_uuid = parse_report_id(request.report_id)
        
        # Verify report exists
        db_report = db.query(DBReport).filter(DBReport.id == report_uuid).first()
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {request.report_id}"
            )
        
        # Calculate working capital using FinanceModule service
        logger.info("Calling FinanceModule working capital calculator...")
        finance_module = FinanceModule(db)
        working_capital = finance_module.calculate_working_capital(str(report_uuid))
        
        logger.info(f"Working capital calculated: ₹{working_capital.total}")
        
        return working_capital
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as e:
        # Validation errors from FinanceModule
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error calculating working capital: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while calculating working capital. Please try again later."
        )
