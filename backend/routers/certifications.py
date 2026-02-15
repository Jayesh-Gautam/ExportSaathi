"""
Certifications API Router
Handles certification guidance and progress tracking

Requirements: 8.1, 3.7
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from uuid import UUID
import logging

from sqlalchemy.orm import Session

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
from services.certification_progress import CertificationProgressService
from services.consultant_marketplace import get_consultant_marketplace
from database.connection import get_db

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
    user_id: UUID = Query(..., description="User ID"),
    report_id: UUID = Query(..., description="Report ID"),
    status: str = Query(..., description="Progress status (not_started/in_progress/completed/rejected)"),
    documents_completed: Optional[List[str]] = Query(None, description="List of completed document IDs"),
    notes: Optional[str] = Query(None, description="Optional notes"),
    db: Session = Depends(get_db)
):
    """
    Update certification progress.
    
    Args:
        cert_id: Certification identifier
        user_id: User UUID
        report_id: Report UUID
        status: Progress status (not_started/in_progress/completed/rejected)
        documents_completed: Optional list of completed document IDs
        notes: Optional notes
        db: Database session
        
    Returns:
        Updated progress status
        
    Requirements: 3.7, 8.1
    """
    try:
        logger.info(f"Updating progress for {cert_id}: {status}")
        
        # Validate status
        valid_statuses = ['not_started', 'in_progress', 'completed', 'rejected']
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Initialize progress service
        progress_service = CertificationProgressService(db)
        
        # Check if progress record exists
        existing_progress = progress_service.get_progress(user_id, report_id, cert_id)
        
        if not existing_progress:
            # Create new progress record if it doesn't exist
            # We need certification name and type - for MVP, derive from cert_id
            cert_name = cert_id.replace('-', ' ').title()
            cert_type = cert_id.split('-')[0].upper() if '-' in cert_id else 'OTHER'
            
            existing_progress = progress_service.create_progress(
                user_id=user_id,
                report_id=report_id,
                certification_id=cert_id,
                certification_name=cert_name,
                certification_type=cert_type
            )
        
        # Update progress
        updated_progress = progress_service.update_progress(
            user_id=user_id,
            report_id=report_id,
            certification_id=cert_id,
            status=status,
            documents_completed=documents_completed,
            notes=notes
        )
        
        if not updated_progress:
            raise HTTPException(status_code=404, detail="Progress record not found")
        
        return {
            "cert_id": cert_id,
            "status": updated_progress.status,
            "report_id": str(updated_progress.report_id),
            "documents_completed": updated_progress.documents_completed or [],
            "started_at": updated_progress.started_at.isoformat() if updated_progress.started_at else None,
            "completed_at": updated_progress.completed_at.isoformat() if updated_progress.completed_at else None,
            "updated_at": updated_progress.updated_at.isoformat() if updated_progress.updated_at else None,
            "notes": updated_progress.notes,
            "message": "Progress updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating progress for {cert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")


@router.get("/{cert_id}/progress")
async def get_progress(
    cert_id: str,
    user_id: UUID = Query(..., description="User ID"),
    report_id: UUID = Query(..., description="Report ID"),
    db: Session = Depends(get_db)
):
    """
    Get certification progress.
    
    Args:
        cert_id: Certification identifier
        user_id: User UUID
        report_id: Report UUID
        db: Database session
        
    Returns:
        Current progress status
        
    Requirements: 3.7, 8.1
    """
    try:
        logger.info(f"Getting progress for {cert_id}")
        
        # Initialize progress service
        progress_service = CertificationProgressService(db)
        
        # Get progress
        progress = progress_service.get_progress(user_id, report_id, cert_id)
        
        if not progress:
            raise HTTPException(status_code=404, detail="Progress record not found")
        
        return {
            "cert_id": progress.certification_id,
            "certification_name": progress.certification_name,
            "certification_type": progress.certification_type,
            "status": progress.status,
            "report_id": str(progress.report_id),
            "documents_completed": progress.documents_completed or [],
            "started_at": progress.started_at.isoformat() if progress.started_at else None,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
            "updated_at": progress.updated_at.isoformat() if progress.updated_at else None,
            "notes": progress.notes
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress for {cert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@router.put("/{cert_id}/progress/documents/{document_id}")
async def toggle_document_completion(
    cert_id: str,
    document_id: str,
    user_id: UUID = Query(..., description="User ID"),
    report_id: UUID = Query(..., description="Report ID"),
    completed: bool = Query(..., description="Mark as completed (true) or incomplete (false)"),
    db: Session = Depends(get_db)
):
    """
    Toggle document completion status.
    
    Args:
        cert_id: Certification identifier
        document_id: Document identifier
        user_id: User UUID
        report_id: Report UUID
        completed: True to mark as completed, False to mark as incomplete
        db: Database session
        
    Returns:
        Updated progress with document status
        
    Requirements: 3.7, 8.1
    """
    try:
        logger.info(f"Toggling document {document_id} for {cert_id}: completed={completed}")
        
        # Initialize progress service
        progress_service = CertificationProgressService(db)
        
        # Toggle document completion
        if completed:
            updated_progress = progress_service.mark_document_completed(
                user_id=user_id,
                report_id=report_id,
                certification_id=cert_id,
                document_id=document_id
            )
        else:
            updated_progress = progress_service.mark_document_incomplete(
                user_id=user_id,
                report_id=report_id,
                certification_id=cert_id,
                document_id=document_id
            )
        
        if not updated_progress:
            raise HTTPException(status_code=404, detail="Progress record not found")
        
        return {
            "cert_id": cert_id,
            "document_id": document_id,
            "completed": completed,
            "documents_completed": updated_progress.documents_completed or [],
            "updated_at": updated_progress.updated_at.isoformat() if updated_progress.updated_at else None,
            "message": f"Document {document_id} marked as {'completed' if completed else 'incomplete'}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling document {document_id} for {cert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to toggle document completion: {str(e)}")


@router.get("/reports/{report_id}/progress/summary")
async def get_progress_summary(
    report_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Get progress summary for all certifications in a report.
    
    Args:
        report_id: Report UUID
        user_id: User UUID
        db: Database session
        
    Returns:
        Progress summary with statistics
        
    Requirements: 3.7, 8.1
    """
    try:
        logger.info(f"Getting progress summary for report {report_id}")
        
        # Initialize progress service
        progress_service = CertificationProgressService(db)
        
        # Get summary
        summary = progress_service.get_progress_summary(user_id, report_id)
        
        return summary
    
    except Exception as e:
        logger.error(f"Error getting progress summary for report {report_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get progress summary: {str(e)}")



# Consultant Marketplace Endpoints

@router.get("/consultants/search", response_model=List[Consultant])
async def search_consultants(
    certification_type: Optional[str] = Query(None, description="Filter by certification type (e.g., FDA, CE, BIS)"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum rating (0-5)"),
    max_cost: Optional[float] = Query(None, ge=0, description="Maximum cost in INR"),
    min_experience: Optional[int] = Query(None, ge=0, description="Minimum years of experience"),
    location: Optional[str] = Query(None, description="Filter by location (partial match)"),
    specialization: Optional[str] = Query(None, description="Filter by specialization (partial match)"),
    sort_by: str = Query("rating", description="Sort field (rating, cost, experience)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)")
):
    """
    Search and filter consultants in the marketplace.
    
    This endpoint provides comprehensive search and filter functionality for finding
    consultants based on various criteria including certification type, rating, cost,
    experience, location, and specialization.
    
    Args:
        certification_type: Filter by certification type (e.g., "FDA", "CE", "BIS")
        min_rating: Minimum rating (0-5)
        max_cost: Maximum cost (filters by cost_range.max)
        min_experience: Minimum years of experience
        location: Filter by location (partial match)
        specialization: Filter by specialization (partial match)
        sort_by: Sort field ("rating", "cost", "experience")
        sort_order: Sort order ("asc" or "desc")
        
    Returns:
        List of matching consultants sorted by specified criteria
        
    Requirements: 3.4
    
    Example:
        GET /api/certifications/consultants/search?certification_type=FDA&min_rating=4.0&sort_by=rating
    """
    try:
        logger.info(f"Searching consultants with filters: cert={certification_type}, "
                   f"rating>={min_rating}, cost<={max_cost}, exp>={min_experience}")
        
        # Validate sort parameters
        valid_sort_by = ["rating", "cost", "experience"]
        if sort_by not in valid_sort_by:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by. Must be one of: {', '.join(valid_sort_by)}"
            )
        
        valid_sort_order = ["asc", "desc"]
        if sort_order not in valid_sort_order:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_order. Must be one of: {', '.join(valid_sort_order)}"
            )
        
        # Get marketplace instance
        marketplace = get_consultant_marketplace()
        
        # Search consultants
        consultants = marketplace.search_consultants(
            certification_type=certification_type,
            min_rating=min_rating,
            max_cost=max_cost,
            min_experience=min_experience,
            location=location,
            specialization=specialization,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        logger.info(f"Found {len(consultants)} consultants matching criteria")
        return consultants
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching consultants: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search consultants: {str(e)}")


@router.get("/consultants/{consultant_id}", response_model=Consultant)
async def get_consultant_details(consultant_id: str):
    """
    Get detailed information about a specific consultant.
    
    Args:
        consultant_id: Consultant identifier
        
    Returns:
        Complete consultant information including ratings, cost, experience, and contact details
        
    Requirements: 3.4
    
    Example:
        GET /api/certifications/consultants/cons-fda-1
    """
    try:
        logger.info(f"Getting details for consultant {consultant_id}")
        
        # Get marketplace instance
        marketplace = get_consultant_marketplace()
        
        # Get consultant by ID
        consultant = marketplace.get_consultant_by_id(consultant_id)
        
        if not consultant:
            raise HTTPException(
                status_code=404,
                detail=f"Consultant {consultant_id} not found"
            )
        
        return consultant
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consultant {consultant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get consultant details: {str(e)}")
