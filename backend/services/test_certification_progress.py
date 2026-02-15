"""
Unit tests for Certification Progress Service

Tests database operations for certification progress tracking.

Requirements: 3.7
"""

import pytest
from uuid import uuid4
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, User, Report, CertificationProgress
from services.certification_progress import CertificationProgressService


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        business_type="Manufacturing",
        company_size="Small"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_report(db_session, test_user):
    """Create a test report."""
    report = Report(
        user_id=test_user.id,
        product_name="Test Product",
        destination_country="United States",
        hs_code="1234.56",
        report_data={}
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


@pytest.fixture
def progress_service(db_session):
    """Create certification progress service."""
    return CertificationProgressService(db_session)


class TestCertificationProgressService:
    """Tests for CertificationProgressService."""
    
    def test_create_progress(self, progress_service, test_user, test_report):
        """Test creating a new certification progress record."""
        progress = progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        assert progress is not None
        assert progress.user_id == test_user.id
        assert progress.report_id == test_report.id
        assert progress.certification_id == "fda-food-facility"
        assert progress.certification_name == "FDA Food Facility Registration"
        assert progress.certification_type == "FDA"
        assert progress.status == "not_started"
        assert progress.documents_completed == []
        assert progress.started_at is None
        assert progress.completed_at is None
    
    def test_update_progress_to_in_progress(self, progress_service, test_user, test_report):
        """Test updating progress status to in_progress."""
        # Create initial progress
        progress = progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        # Update to in_progress
        updated = progress_service.update_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            status="in_progress"
        )
        
        assert updated is not None
        assert updated.status == "in_progress"
        assert updated.started_at is not None
        assert updated.completed_at is None
    
    def test_update_progress_to_completed(self, progress_service, test_user, test_report):
        """Test updating progress status to completed."""
        # Create and start progress
        progress = progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        progress_service.update_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            status="in_progress"
        )
        
        # Update to completed
        updated = progress_service.update_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            status="completed"
        )
        
        assert updated is not None
        assert updated.status == "completed"
        assert updated.started_at is not None
        assert updated.completed_at is not None
    
    def test_update_progress_with_documents(self, progress_service, test_user, test_report):
        """Test updating progress with document completion list."""
        # Create progress
        progress = progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        # Update with documents
        documents = ["fda-doc-1", "fda-doc-2", "fda-doc-3"]
        updated = progress_service.update_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            status="in_progress",
            documents_completed=documents
        )
        
        assert updated is not None
        assert updated.documents_completed == documents
    
    def test_update_progress_with_notes(self, progress_service, test_user, test_report):
        """Test updating progress with notes."""
        # Create progress
        progress = progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        # Update with notes
        notes = "Submitted application on 2024-01-15"
        updated = progress_service.update_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            status="in_progress",
            notes=notes
        )
        
        assert updated is not None
        assert updated.notes == notes
    
    def test_update_nonexistent_progress(self, progress_service, test_user, test_report):
        """Test updating progress that doesn't exist returns None."""
        updated = progress_service.update_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="nonexistent-cert",
            status="in_progress"
        )
        
        assert updated is None
    
    def test_mark_document_completed(self, progress_service, test_user, test_report):
        """Test marking a document as completed."""
        # Create progress
        progress = progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        # Mark document as completed
        updated = progress_service.mark_document_completed(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            document_id="fda-doc-1"
        )
        
        assert updated is not None
        assert "fda-doc-1" in updated.documents_completed
    
    def test_mark_multiple_documents_completed(self, progress_service, test_user, test_report):
        """Test marking multiple documents as completed."""
        # Create progress
        progress = progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        # Mark multiple documents as completed
        progress_service.mark_document_completed(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            document_id="fda-doc-1"
        )
        
        progress_service.mark_document_completed(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            document_id="fda-doc-2"
        )
        
        updated = progress_service.mark_document_completed(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            document_id="fda-doc-3"
        )
        
        assert updated is not None
        assert len(updated.documents_completed) == 3
        assert "fda-doc-1" in updated.documents_completed
        assert "fda-doc-2" in updated.documents_completed
        assert "fda-doc-3" in updated.documents_completed
    
    def test_mark_document_completed_idempotent(self, progress_service, test_user, test_report):
        """Test marking the same document as completed multiple times is idempotent."""
        # Create progress
        progress = progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        # Mark document as completed twice
        progress_service.mark_document_completed(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            document_id="fda-doc-1"
        )
        
        updated = progress_service.mark_document_completed(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            document_id="fda-doc-1"
        )
        
        assert updated is not None
        assert updated.documents_completed.count("fda-doc-1") == 1
    
    def test_mark_document_incomplete(self, progress_service, test_user, test_report):
        """Test marking a document as incomplete."""
        # Create progress and mark document as completed
        progress = progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        progress_service.mark_document_completed(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            document_id="fda-doc-1"
        )
        
        # Mark as incomplete
        updated = progress_service.mark_document_incomplete(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            document_id="fda-doc-1"
        )
        
        assert updated is not None
        assert "fda-doc-1" not in updated.documents_completed
    
    def test_get_progress(self, progress_service, test_user, test_report):
        """Test retrieving certification progress."""
        # Create progress
        created = progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        # Retrieve progress
        retrieved = progress_service.get_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility"
        )
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.certification_id == "fda-food-facility"
    
    def test_get_nonexistent_progress(self, progress_service, test_user, test_report):
        """Test retrieving nonexistent progress returns None."""
        retrieved = progress_service.get_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="nonexistent-cert"
        )
        
        assert retrieved is None
    
    def test_get_all_progress_for_report(self, progress_service, test_user, test_report):
        """Test retrieving all progress records for a report."""
        # Create multiple progress records
        progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="ce-marking",
            certification_name="CE Marking",
            certification_type="CE"
        )
        
        progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="bis-certification",
            certification_name="BIS Certification",
            certification_type="BIS"
        )
        
        # Retrieve all progress
        all_progress = progress_service.get_all_progress_for_report(
            user_id=test_user.id,
            report_id=test_report.id
        )
        
        assert len(all_progress) == 3
        cert_ids = [p.certification_id for p in all_progress]
        assert "fda-food-facility" in cert_ids
        assert "ce-marking" in cert_ids
        assert "bis-certification" in cert_ids
    
    def test_get_progress_summary(self, progress_service, test_user, test_report):
        """Test getting progress summary statistics."""
        # Create progress records with different statuses
        progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            certification_name="FDA Food Facility Registration",
            certification_type="FDA"
        )
        
        progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="ce-marking",
            certification_name="CE Marking",
            certification_type="CE"
        )
        
        progress_service.create_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="bis-certification",
            certification_name="BIS Certification",
            certification_type="BIS"
        )
        
        # Update statuses
        progress_service.update_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="fda-food-facility",
            status="in_progress"
        )
        
        progress_service.update_progress(
            user_id=test_user.id,
            report_id=test_report.id,
            certification_id="ce-marking",
            status="completed"
        )
        
        # Get summary
        summary = progress_service.get_progress_summary(
            user_id=test_user.id,
            report_id=test_report.id
        )
        
        assert summary['total_certifications'] == 3
        assert summary['not_started'] == 1
        assert summary['in_progress'] == 1
        assert summary['completed'] == 1
        assert summary['rejected'] == 0
        assert summary['completion_percentage'] == pytest.approx(33.33, rel=0.01)
    
    def test_get_progress_summary_empty(self, progress_service, test_user, test_report):
        """Test getting progress summary with no certifications."""
        summary = progress_service.get_progress_summary(
            user_id=test_user.id,
            report_id=test_report.id
        )
        
        assert summary['total_certifications'] == 0
        assert summary['not_started'] == 0
        assert summary['in_progress'] == 0
        assert summary['completed'] == 0
        assert summary['rejected'] == 0
        assert summary['completion_percentage'] == 0
