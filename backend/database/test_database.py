"""
Unit tests for database models and connection.
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.models import (
    Base, User, Report, CertificationProgress, 
    GeneratedDocument, ActionPlanProgress, ChatSession, 
    ChatMessage, FinanceAnalysis, LogisticsAnalysis, UserMetrics
)
from backend.database.connection import db_connection


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session with clean state."""
    # Create all tables
    Base.metadata.create_all(bind=db_connection.engine)
    
    # Get session
    session = db_connection.get_session()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=db_connection.engine)


class TestUserModel:
    """Tests for User model."""
    
    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            business_type="Manufacturing",
            company_size="Small",
            company_name="Test Company"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.business_type == "Manufacturing"
        assert user.created_at is not None
    
    def test_user_email_unique(self, db_session):
        """Test that email must be unique."""
        user1 = User(
            email="test@example.com",
            password_hash="hash1",
            business_type="Manufacturing",
            company_size="Small"
        )
        user2 = User(
            email="test@example.com",
            password_hash="hash2",
            business_type="SaaS",
            company_size="Micro"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestReportModel:
    """Tests for Report model."""
    
    def test_create_report(self, db_session):
        """Test creating a report."""
        # Create user first
        user = User(
            email="test@example.com",
            password_hash="hash",
            business_type="Manufacturing",
            company_size="Small"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create report
        report = Report(
            user_id=user.id,
            product_name="Test Product",
            destination_country="USA",
            business_type="Manufacturing",
            company_size="Small",
            report_data={"test": "data"},
            risk_score=50
        )
        db_session.add(report)
        db_session.commit()
        
        assert report.id is not None
        assert report.user_id == user.id
        assert report.product_name == "Test Product"
        assert report.risk_score == 50
    
    def test_report_cascade_delete(self, db_session):
        """Test that deleting user deletes reports."""
        user = User(
            email="test@example.com",
            password_hash="hash",
            business_type="Manufacturing",
            company_size="Small"
        )
        db_session.add(user)
        db_session.commit()
        
        report = Report(
            user_id=user.id,
            product_name="Test Product",
            destination_country="USA",
            business_type="Manufacturing",
            company_size="Small",
            report_data={}
        )
        db_session.add(report)
        db_session.commit()
        
        report_id = report.id
        
        # Delete user
        db_session.delete(user)
        db_session.commit()
        
        # Report should be deleted
        deleted_report = db_session.query(Report).filter(Report.id == report_id).first()
        assert deleted_report is None


class TestCertificationProgress:
    """Tests for CertificationProgress model."""
    
    def test_create_certification_progress(self, db_session):
        """Test creating certification progress."""
        user = User(
            email="test@example.com",
            password_hash="hash",
            business_type="Manufacturing",
            company_size="Small"
        )
        db_session.add(user)
        db_session.commit()
        
        report = Report(
            user_id=user.id,
            product_name="Test Product",
            destination_country="USA",
            business_type="Manufacturing",
            company_size="Small",
            report_data={}
        )
        db_session.add(report)
        db_session.commit()
        
        cert_progress = CertificationProgress(
            user_id=user.id,
            report_id=report.id,
            certification_id="fda-food",
            certification_name="FDA Food Facility",
            certification_type="FDA",
            status="in_progress"
        )
        db_session.add(cert_progress)
        db_session.commit()
        
        assert cert_progress.id is not None
        assert cert_progress.status == "in_progress"


class TestChatSession:
    """Tests for ChatSession and ChatMessage models."""
    
    def test_create_chat_session(self, db_session):
        """Test creating a chat session with messages."""
        user = User(
            email="test@example.com",
            password_hash="hash",
            business_type="Manufacturing",
            company_size="Small"
        )
        db_session.add(user)
        db_session.commit()
        
        report = Report(
            user_id=user.id,
            product_name="Test Product",
            destination_country="USA",
            business_type="Manufacturing",
            company_size="Small",
            report_data={}
        )
        db_session.add(report)
        db_session.commit()
        
        session = ChatSession(
            user_id=user.id,
            report_id=report.id,
            context_data={"product": "Test Product"}
        )
        db_session.add(session)
        db_session.commit()
        
        message = ChatMessage(
            session_id=session.id,
            role="user",
            content="What certifications do I need?"
        )
        db_session.add(message)
        db_session.commit()
        
        assert session.id is not None
        assert message.id is not None
        assert message.role == "user"


class TestUserMetrics:
    """Tests for UserMetrics model."""
    
    def test_create_user_metrics(self, db_session):
        """Test creating user metrics."""
        user = User(
            email="test@example.com",
            password_hash="hash",
            business_type="Manufacturing",
            company_size="Small"
        )
        db_session.add(user)
        db_session.commit()
        
        metrics = UserMetrics(
            user_id=user.id,
            reports_generated=5,
            certifications_completed=2,
            cost_savings=150000.00
        )
        db_session.add(metrics)
        db_session.commit()
        
        assert metrics.id is not None
        assert metrics.reports_generated == 5
        assert metrics.cost_savings == 150000.00


class TestDatabaseConnection:
    """Tests for database connection utilities."""
    
    def test_check_connection(self):
        """Test database connection check."""
        from backend.database.connection import check_db_connection
        
        # This will fail if database is not configured
        # In a real test environment, this should pass
        result = check_db_connection()
        assert isinstance(result, bool)
    
    def test_session_scope(self):
        """Test session scope context manager."""
        from backend.database.connection import db_connection
        
        # Create tables
        Base.metadata.create_all(bind=db_connection.engine)
        
        try:
            with db_connection.session_scope() as session:
                user = User(
                    email="scope_test@example.com",
                    password_hash="hash",
                    business_type="Manufacturing",
                    company_size="Small"
                )
                session.add(user)
                # Should auto-commit
            
            # Verify user was created
            with db_connection.session_scope() as session:
                user = session.query(User).filter(
                    User.email == "scope_test@example.com"
                ).first()
                assert user is not None
        finally:
            # Cleanup
            Base.metadata.drop_all(bind=db_connection.engine)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
