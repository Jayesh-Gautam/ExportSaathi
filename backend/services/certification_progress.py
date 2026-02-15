"""
Certification Progress Tracking Service for ExportSathi

This service handles database operations for tracking certification progress,
including marking certifications as in-progress/completed and tracking document
completion status.

Requirements: 3.7
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import CertificationProgress
from models.enums import CertificationStatus

logger = logging.getLogger(__name__)


class CertificationProgressService:
    """
    Service for managing certification progress tracking.
    
    This service provides methods to:
    1. Create certification progress records
    2. Update certification status (not_started, in_progress, completed, rejected)
    3. Track document completion status
    4. Retrieve progress for users and reports
    
    Requirements: 3.7
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
    
    def create_progress(
        self,
        user_id: UUID,
        report_id: UUID,
        certification_id: str,
        certification_name: str,
        certification_type: str
    ) -> CertificationProgress:
        """
        Create a new certification progress record.
        
        Args:
            user_id: User UUID
            report_id: Report UUID
            certification_id: Certification identifier
            certification_name: Certification name
            certification_type: Certification type
            
        Returns:
            Created CertificationProgress record
            
        Requirements: 3.7
        """
        try:
            progress = CertificationProgress(
                user_id=user_id,
                report_id=report_id,
                certification_id=certification_id,
                certification_name=certification_name,
                certification_type=certification_type,
                status='not_started',
                documents_completed=[]
            )
            
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)
            
            logger.info(f"Created progress record for {certification_id}")
            return progress
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating progress: {e}", exc_info=True)
            raise
    
    def update_progress(
        self,
        user_id: UUID,
        report_id: UUID,
        certification_id: str,
        status: str,
        documents_completed: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Optional[CertificationProgress]:
        """
        Update certification progress status.
        
        Args:
            user_id: User UUID
            report_id: Report UUID
            certification_id: Certification identifier
            status: New status (not_started, in_progress, completed, rejected)
            documents_completed: List of completed document IDs
            notes: Optional notes
            
        Returns:
            Updated CertificationProgress record or None if not found
            
        Requirements: 3.7
        """
        try:
            # Find existing progress record
            progress = self.db.query(CertificationProgress).filter(
                CertificationProgress.user_id == user_id,
                CertificationProgress.report_id == report_id,
                CertificationProgress.certification_id == certification_id
            ).first()
            
            if not progress:
                logger.warning(f"Progress record not found for {certification_id}")
                return None
            
            # Update status
            old_status = progress.status
            progress.status = status
            
            # Update timestamps based on status
            if status == 'in_progress' and old_status == 'not_started':
                progress.started_at = datetime.utcnow()
            elif status == 'completed' and old_status != 'completed':
                progress.completed_at = datetime.utcnow()
            
            # Update documents if provided
            if documents_completed is not None:
                progress.documents_completed = documents_completed
            
            # Update notes if provided
            if notes is not None:
                progress.notes = notes
            
            self.db.commit()
            self.db.refresh(progress)
            
            logger.info(f"Updated progress for {certification_id}: {old_status} -> {status}")
            return progress
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating progress: {e}", exc_info=True)
            raise
    
    def mark_document_completed(
        self,
        user_id: UUID,
        report_id: UUID,
        certification_id: str,
        document_id: str
    ) -> Optional[CertificationProgress]:
        """
        Mark a specific document as completed.
        
        Args:
            user_id: User UUID
            report_id: Report UUID
            certification_id: Certification identifier
            document_id: Document identifier to mark as completed
            
        Returns:
            Updated CertificationProgress record or None if not found
            
        Requirements: 3.7
        """
        try:
            progress = self.db.query(CertificationProgress).filter(
                CertificationProgress.user_id == user_id,
                CertificationProgress.report_id == report_id,
                CertificationProgress.certification_id == certification_id
            ).first()
            
            if not progress:
                logger.warning(f"Progress record not found for {certification_id}")
                return None
            
            # Add document to completed list if not already there
            completed_docs = progress.documents_completed or []
            if document_id not in completed_docs:
                completed_docs.append(document_id)
                progress.documents_completed = completed_docs
                
                self.db.commit()
                self.db.refresh(progress)
                
                logger.info(f"Marked document {document_id} as completed for {certification_id}")
            
            return progress
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error marking document completed: {e}", exc_info=True)
            raise
    
    def mark_document_incomplete(
        self,
        user_id: UUID,
        report_id: UUID,
        certification_id: str,
        document_id: str
    ) -> Optional[CertificationProgress]:
        """
        Mark a specific document as incomplete (remove from completed list).
        
        Args:
            user_id: User UUID
            report_id: Report UUID
            certification_id: Certification identifier
            document_id: Document identifier to mark as incomplete
            
        Returns:
            Updated CertificationProgress record or None if not found
            
        Requirements: 3.7
        """
        try:
            progress = self.db.query(CertificationProgress).filter(
                CertificationProgress.user_id == user_id,
                CertificationProgress.report_id == report_id,
                CertificationProgress.certification_id == certification_id
            ).first()
            
            if not progress:
                logger.warning(f"Progress record not found for {certification_id}")
                return None
            
            # Remove document from completed list if present
            completed_docs = progress.documents_completed or []
            if document_id in completed_docs:
                completed_docs.remove(document_id)
                progress.documents_completed = completed_docs
                
                self.db.commit()
                self.db.refresh(progress)
                
                logger.info(f"Marked document {document_id} as incomplete for {certification_id}")
            
            return progress
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error marking document incomplete: {e}", exc_info=True)
            raise
    
    def get_progress(
        self,
        user_id: UUID,
        report_id: UUID,
        certification_id: str
    ) -> Optional[CertificationProgress]:
        """
        Get certification progress for a specific certification.
        
        Args:
            user_id: User UUID
            report_id: Report UUID
            certification_id: Certification identifier
            
        Returns:
            CertificationProgress record or None if not found
            
        Requirements: 3.7
        """
        try:
            progress = self.db.query(CertificationProgress).filter(
                CertificationProgress.user_id == user_id,
                CertificationProgress.report_id == report_id,
                CertificationProgress.certification_id == certification_id
            ).first()
            
            return progress
            
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving progress: {e}", exc_info=True)
            raise
    
    def get_all_progress_for_report(
        self,
        user_id: UUID,
        report_id: UUID
    ) -> List[CertificationProgress]:
        """
        Get all certification progress records for a report.
        
        Args:
            user_id: User UUID
            report_id: Report UUID
            
        Returns:
            List of CertificationProgress records
            
        Requirements: 3.7
        """
        try:
            progress_list = self.db.query(CertificationProgress).filter(
                CertificationProgress.user_id == user_id,
                CertificationProgress.report_id == report_id
            ).all()
            
            return progress_list
            
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving progress list: {e}", exc_info=True)
            raise
    
    def get_progress_summary(
        self,
        user_id: UUID,
        report_id: UUID
    ) -> Dict[str, Any]:
        """
        Get progress summary for a report.
        
        Args:
            user_id: User UUID
            report_id: Report UUID
            
        Returns:
            Dictionary with progress summary statistics
            
        Requirements: 3.7
        """
        try:
            progress_list = self.get_all_progress_for_report(user_id, report_id)
            
            total = len(progress_list)
            not_started = sum(1 for p in progress_list if p.status == 'not_started')
            in_progress = sum(1 for p in progress_list if p.status == 'in_progress')
            completed = sum(1 for p in progress_list if p.status == 'completed')
            rejected = sum(1 for p in progress_list if p.status == 'rejected')
            
            completion_percentage = (completed / total * 100) if total > 0 else 0
            
            return {
                'total_certifications': total,
                'not_started': not_started,
                'in_progress': in_progress,
                'completed': completed,
                'rejected': rejected,
                'completion_percentage': round(completion_percentage, 2)
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error calculating progress summary: {e}", exc_info=True)
            raise
