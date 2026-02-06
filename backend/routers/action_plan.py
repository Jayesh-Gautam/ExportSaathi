"""
Action Plan API Router
Handles 7-day action plan generation and tracking

This router implements the core API endpoints for action plan management.
It provides:
1. GET /api/action-plan/{report_id} - Get 7-day action plan for a report
2. PUT /api/action-plan/{report_id}/tasks/{task_id} - Update task completion status
3. GET /api/action-plan/{report_id}/download - Download action plan as PDF

Requirements: 8.1
"""
from fastapi import APIRouter, HTTPException, Depends, status, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
import uuid
from datetime import datetime

from models.action_plan import ActionPlan, Task, DayPlan
from models import ExportReadinessReport
from services.action_plan_generator import ActionPlanGenerator
from database.connection import get_db
from database.models import (
    Report as DBReport,
    ActionPlanProgress as DBActionPlanProgress
)
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


class TaskUpdateRequest(BaseModel):
    """Request model for updating task status."""
    completed: bool = Field(..., description="Task completion status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "completed": True
            }
        }


@router.get("/{report_id}", response_model=ActionPlan)
async def get_action_plan(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Get 7-day action plan for an export readiness report.
    
    This endpoint generates or retrieves a 7-day action plan with tasks distributed
    across days based on dependencies and priorities. The plan includes:
    - Day 1: Foundation setup (GST LUT, HS code, IEC, bank account)
    - Day 2-3: Certification applications
    - Day 4-5: Document preparation
    - Day 6: Logistics planning
    - Day 7: Final review and readiness check
    
    Task completion status is tracked and persisted in the database.
    
    **Path Parameters:**
    - report_id: Unique report identifier (format: rpt_xxxxxxxxxxxx or UUID)
    
    **Returns:**
    - ActionPlan with 7 days of tasks and overall progress percentage
    
    **Errors:**
    - 400: Invalid report ID format
    - 404: Report not found
    - 500: Internal server error during plan generation
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Retrieving action plan for report: {report_id}")
        
        # Parse report ID
        report_uuid = parse_report_id(report_id)
        
        # Retrieve report from database
        db_report = db.query(DBReport).filter(DBReport.id == report_uuid).first()
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )
        
        # Convert database report to ExportReadinessReport model
        report = ExportReadinessReport(**db_report.report_data)
        
        # Generate action plan using ActionPlanGenerator service
        logger.info("Generating action plan...")
        generator = ActionPlanGenerator()
        action_plan = generator.generate_plan(report)
        
        # Retrieve task completion status from database
        task_progress = db.query(DBActionPlanProgress).filter(
            DBActionPlanProgress.report_id == report_uuid
        ).all()
        
        # Create a map of task_id -> completed status
        completed_tasks = {tp.task_id: tp.completed for tp in task_progress}
        
        # Update task completion status in the action plan
        total_tasks = 0
        completed_count = 0
        
        for day in action_plan.days:
            for task in day.tasks:
                total_tasks += 1
                if task.id in completed_tasks:
                    task.completed = completed_tasks[task.id]
                    if task.completed:
                        completed_count += 1
        
        # Calculate progress percentage
        if total_tasks > 0:
            action_plan.progress_percentage = (completed_count / total_tasks) * 100
        else:
            action_plan.progress_percentage = 0.0
        
        logger.info(f"Action plan retrieved: {completed_count}/{total_tasks} tasks completed ({action_plan.progress_percentage:.1f}%)")
        
        return action_plan
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error retrieving action plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the action plan. Please try again later."
        )


@router.put("/{report_id}/tasks/{task_id}", response_model=Dict[str, Any])
async def update_task_status(
    report_id: str,
    task_id: str,
    request: TaskUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update task completion status in the action plan.
    
    This endpoint allows users to mark tasks as completed or not completed.
    The status is persisted in the database and affects the overall progress
    percentage calculation.
    
    **Path Parameters:**
    - report_id: Unique report identifier (format: rpt_xxxxxxxxxxxx or UUID)
    - task_id: Unique task identifier (e.g., "task_gst_lut")
    
    **Request Body:**
    - completed: Boolean indicating task completion status
    
    **Returns:**
    - JSON with updated task status and overall progress
    
    **Errors:**
    - 400: Invalid report ID format or task ID
    - 404: Report or task not found
    - 500: Internal server error during update
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Updating task status: {task_id} in report {report_id} to completed={request.completed}")
        
        # Parse report ID
        report_uuid = parse_report_id(report_id)
        
        # Verify report exists
        db_report = db.query(DBReport).filter(DBReport.id == report_uuid).first()
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )
        
        # Generate action plan to verify task exists
        report = ExportReadinessReport(**db_report.report_data)
        generator = ActionPlanGenerator()
        action_plan = generator.generate_plan(report)
        
        # Find the task in the action plan
        task_found = False
        task_info = None
        
        for day in action_plan.days:
            for task in day.tasks:
                if task.id == task_id:
                    task_found = True
                    task_info = {
                        "day_number": day.day,
                        "title": task.title,
                        "description": task.description,
                        "category": task.category.value
                    }
                    break
            if task_found:
                break
        
        if not task_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found: {task_id}"
            )
        
        # Check if task progress record exists
        task_progress = db.query(DBActionPlanProgress).filter(
            DBActionPlanProgress.report_id == report_uuid,
            DBActionPlanProgress.task_id == task_id
        ).first()
        
        if task_progress:
            # Update existing record
            task_progress.completed = request.completed
            task_progress.completed_at = datetime.utcnow() if request.completed else None
            task_progress.updated_at = datetime.utcnow()
        else:
            # Create new record
            task_progress = DBActionPlanProgress(
                user_id=db_report.user_id,
                report_id=report_uuid,
                task_id=task_id,
                day_number=task_info["day_number"],
                task_title=task_info["title"],
                task_description=task_info["description"],
                task_category=task_info["category"],
                completed=request.completed,
                completed_at=datetime.utcnow() if request.completed else None
            )
            db.add(task_progress)
        
        db.commit()
        db.refresh(task_progress)
        
        # Calculate overall progress
        all_progress = db.query(DBActionPlanProgress).filter(
            DBActionPlanProgress.report_id == report_uuid
        ).all()
        
        # Count total tasks in the action plan
        total_tasks = sum(len(day.tasks) for day in action_plan.days)
        
        # Count completed tasks
        completed_tasks_map = {tp.task_id: tp.completed for tp in all_progress}
        completed_count = sum(1 for task_id, completed in completed_tasks_map.items() if completed)
        
        # Calculate progress percentage
        progress_percentage = (completed_count / total_tasks * 100) if total_tasks > 0 else 0.0
        
        logger.info(f"Task status updated: {task_id} completed={request.completed}, progress={progress_percentage:.1f}%")
        
        return {
            "report_id": f"rpt_{str(report_uuid).replace('-', '')}",
            "task_id": task_id,
            "completed": request.completed,
            "completed_at": task_progress.completed_at.isoformat() if task_progress.completed_at else None,
            "progress_percentage": round(progress_percentage, 1),
            "completed_tasks": completed_count,
            "total_tasks": total_tasks
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error updating task status: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating task status. Please try again later."
        )


@router.get("/{report_id}/download")
async def download_action_plan(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Download action plan as PDF.
    
    This endpoint generates a downloadable PDF version of the 7-day action plan
    with all tasks, descriptions, and completion status. The PDF is formatted
    as a checklist that users can print and use offline.
    
    **Path Parameters:**
    - report_id: Unique report identifier (format: rpt_xxxxxxxxxxxx or UUID)
    
    **Returns:**
    - JSON with download URL and metadata
    
    **Errors:**
    - 400: Invalid report ID format
    - 404: Report not found
    - 500: Internal server error during PDF generation
    
    **Note:**
    In the MVP, this returns a placeholder response. Full PDF generation
    would require additional libraries (e.g., ReportLab, WeasyPrint) and
    S3 storage for the generated files.
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Generating PDF download for action plan: {report_id}")
        
        # Parse report ID
        report_uuid = parse_report_id(report_id)
        
        # Verify report exists
        db_report = db.query(DBReport).filter(DBReport.id == report_uuid).first()
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )
        
        # Generate action plan
        report = ExportReadinessReport(**db_report.report_data)
        generator = ActionPlanGenerator()
        action_plan = generator.generate_plan(report)
        
        # Retrieve task completion status
        task_progress = db.query(DBActionPlanProgress).filter(
            DBActionPlanProgress.report_id == report_uuid
        ).all()
        
        completed_tasks = {tp.task_id: tp.completed for tp in task_progress}
        
        # Update task completion status
        for day in action_plan.days:
            for task in day.tasks:
                if task.id in completed_tasks:
                    task.completed = completed_tasks[task.id]
        
        # In MVP, return structured data that frontend can use to generate PDF
        # In production, this would generate an actual PDF file and upload to S3
        logger.info("Returning action plan data for PDF generation")
        
        return {
            "report_id": f"rpt_{str(report_uuid).replace('-', '')}",
            "product_name": db_report.product_name,
            "destination_country": db_report.destination_country,
            "generated_at": datetime.utcnow().isoformat(),
            "action_plan": action_plan.model_dump(mode='json'),
            "download_url": None,  # MVP: Frontend will generate PDF client-side
            "format": "json",
            "message": "Action plan data ready for PDF generation. In production, this would return a pre-generated PDF URL."
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error generating action plan download: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while preparing the action plan download. Please try again later."
        )
