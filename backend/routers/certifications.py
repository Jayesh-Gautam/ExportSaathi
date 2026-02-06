"""
Certifications API Router
Handles certification guidance and progress tracking

Requirements: 8.1
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from models.certification import (
    Certification,
    CertificationGuidance,
    TestLab,
    Consultant,
    Subsidy
)
from models.enums import CertificationType
from models.common import CostRange
from services.certification_solver import CertificationSolver

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize certification solver
certification_solver = CertificationSolver()


@router.get("/", response_model=List[dict])
async def list_certifications():
    """
    List all supported certifications.
    
    Returns:
        List of supported certification types with basic information
        
    Requirements: 8.1
    """
    try:
        # Return list of supported certifications
        certifications = [
            {
                "id": "fda-food-facility",
                "name": "FDA Food Facility Registration",
                "type": "FDA",
                "description": "Required for exporting food products to the United States",
                "typical_cost_range": {"min": 15000, "max": 30000, "currency": "INR"},
                "typical_timeline_days": 60
            },
            {
                "id": "ce-marking",
                "name": "CE Marking",
                "type": "CE",
                "description": "Required for products sold in the European Economic Area",
                "typical_cost_range": {"min": 50000, "max": 150000, "currency": "INR"},
                "typical_timeline_days": 90
            },
            {
                "id": "reach-registration",
                "name": "REACH Registration",
                "type": "REACH",
                "description": "Required for chemicals exported to the EU",
                "typical_cost_range": {"min": 100000, "max": 500000, "currency": "INR"},
                "typical_timeline_days": 120
            },
            {
                "id": "bis-certification",
                "name": "BIS Certification",
                "type": "BIS",
                "description": "Required for certain products under India's Compulsory Registration Scheme",
                "typical_cost_range": {"min": 30000, "max": 80000, "currency": "INR"},
                "typical_timeline_days": 60
            },
            {
                "id": "zed-certification",
                "name": "ZED Certification",
                "type": "ZED",
                "description": "Zero Defect Zero Effect certification for MSMEs with government subsidies",
                "typical_cost_range": {"min": 20000, "max": 100000, "currency": "INR"},
                "typical_timeline_days": 90
            },
            {
                "id": "softex",
                "name": "SOFTEX Declaration",
                "type": "SOFTEX",
                "description": "Required for exporting software and IT services from India",
                "typical_cost_range": {"min": 5000, "max": 10000, "currency": "INR"},
                "typical_timeline_days": 7
            }
        ]
        
        return certifications
    
    except Exception as e:
        logger.error(f"Error listing certifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list certifications")


@router.get("/{cert_id}")
async def get_certification(cert_id: str):
    """
    Get basic certification details.
    
    Args:
        cert_id: Certification identifier
        
    Returns:
        Certification details
        
    Requirements: 8.1
    """
    try:
        # Get certification details from list
        certifications = await list_certifications()
        cert = next((c for c in certifications if c["id"] == cert_id), None)
        
        if not cert:
            raise HTTPException(status_code=404, detail=f"Certification {cert_id} not found")
        
        return cert
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting certification {cert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get certification details")


@router.post("/{cert_id}/guidance", response_model=CertificationGuidance)
async def get_certification_guidance(
    cert_id: str,
    product_type: str = Query(..., description="Product type/name"),
    destination_country: str = Query(..., description="Destination country"),
    company_size: str = Query("Small", description="Company size (Micro/Small/Medium)")
):
    """
    Generate detailed certification guidance.
    
    Args:
        cert_id: Certification identifier
        product_type: Product type/name
        destination_country: Destination country
        company_size: Company size for subsidy eligibility
        
    Returns:
        Complete certification guidance with roadmap, documents, labs, consultants, subsidies
        
    Requirements: 8.1
    """
    try:
        logger.info(f"Generating guidance for {cert_id}: {product_type} -> {destination_country}")
        
        # Generate guidance using certification solver
        guidance = certification_solver.generate_guidance(
            certification_id=cert_id,
            product_type=product_type,
            destination=destination_country,
            company_size=company_size
        )
        
        return guidance
    
    except Exception as e:
        logger.error(f"Error generating guidance for {cert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate certification guidance: {str(e)}")


@router.get("/{cert_id}/test-labs", response_model=List[TestLab])
async def get_test_labs(
    cert_id: str,
    location: Optional[str] = Query("India", description="Location to search for labs")
):
    """
    List approved test labs for certification.
    
    Args:
        cert_id: Certification identifier
        location: Location to search for labs
        
    Returns:
        List of approved test labs
        
    Requirements: 8.1
    """
    try:
        logger.info(f"Finding test labs for {cert_id} in {location}")
        
        # Get test labs using certification solver
        test_labs = certification_solver.find_test_labs(cert_id, location)
        
        return test_labs
    
    except Exception as e:
        logger.error(f"Error finding test labs for {cert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to find test labs")


@router.get("/{cert_id}/consultants", response_model=List[Consultant])
async def get_consultants(cert_id: str):
    """
    List available consultants for certification.
    
    Args:
        cert_id: Certification identifier
        
    Returns:
        List of available consultants
        
    Requirements: 8.1
    """
    try:
        logger.info(f"Finding consultants for {cert_id}")
        
        # Get consultants using certification solver
        consultants = certification_solver.find_consultants(cert_id)
        
        return consultants
    
    except Exception as e:
        logger.error(f"Error finding consultants for {cert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to find consultants")


@router.get("/{cert_id}/subsidies", response_model=List[Subsidy])
async def get_subsidies(
    cert_id: str,
    company_size: str = Query(..., description="Company size (Micro/Small/Medium)")
):
    """
    Get subsidy information for certification.
    
    Args:
        cert_id: Certification identifier
        company_size: Company size for eligibility
        
    Returns:
        List of applicable subsidies
        
    Requirements: 8.1
    """
    try:
        logger.info(f"Finding subsidies for {cert_id}, company size: {company_size}")
        
        # Get subsidies using certification solver
        subsidies = certification_solver.get_subsidies(cert_id, company_size)
        
        return subsidies
    
    except Exception as e:
        logger.error(f"Error finding subsidies for {cert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to find subsidies")


@router.put("/{cert_id}/progress")
async def update_progress(
    cert_id: str,
    status: str = Query(..., description="Progress status (in-progress/completed)"),
    report_id: str = Query(..., description="Report ID")
):
    """
    Update certification progress.
    
    Args:
        cert_id: Certification identifier
        status: Progress status
        report_id: Associated report ID
        
    Returns:
        Updated progress status
        
    Requirements: 8.1
    """
    try:
        logger.info(f"Updating progress for {cert_id}: {status}")
        
        # MVP: Return success without database persistence
        # In full implementation, this would update the certification_progress table
        return {
            "cert_id": cert_id,
            "status": status,
            "report_id": report_id,
            "updated_at": "2024-01-01T00:00:00Z",
            "message": "Progress updated successfully"
        }
    
    except Exception as e:
        logger.error(f"Error updating progress for {cert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update progress")
