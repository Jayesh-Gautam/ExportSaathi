"""
Test suite for Reports API Router

Tests the reports API endpoints to ensure they work correctly with:
1. POST /api/reports/generate - Report generation with multipart form data
2. GET /api/reports/{report_id} - Report retrieval
3. GET /api/reports/{report_id}/status - Status check
4. PUT /api/reports/{report_id}/hs-code - HS code update

This is a basic integration test for the MVP implementation.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import io
import uuid
from datetime import datetime

from main import app
from models import ExportReadinessReport, HSCodePrediction, ReportStatus
from models.certification import Certification
from models.action_plan import ActionPlan
from models.report import Timeline, CostBreakdown, TimelinePhase


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_report():
    """Create a mock export readiness report."""
    # Create a minimal 7-day action plan
    from models.action_plan import DayPlan, Task
    from models.enums import TaskCategory
    
    days = []
    for i in range(1, 8):
        days.append(DayPlan(
            day=i,
            title=f"Day {i}",
            tasks=[
                Task(
                    id=f"task_day{i}",
                    title=f"Task for day {i}",
                    description=f"Description for day {i}",
                    category=TaskCategory.DOCUMENTATION,
                    completed=False,
                    estimated_duration="2-3 hours",
                    dependencies=[]
                )
            ]
        ))
    
    return ExportReadinessReport(
        report_id="rpt_test123456",
        status=ReportStatus.COMPLETED,
        hs_code=HSCodePrediction(
            code="0910.30",
            confidence=92.5,
            description="Turmeric (curcuma)",
            alternatives=[]
        ),
        certifications=[],
        restricted_substances=[],
        past_rejections=[],
        compliance_roadmap=[],
        risks=[],
        risk_score=35,
        timeline=Timeline(
            estimated_days=60,
            breakdown=[
                TimelinePhase(phase="Documentation", duration_days=10),
                TimelinePhase(phase="Certifications", duration_days=30),
                TimelinePhase(phase="Logistics Setup", duration_days=20)
            ]
        ),
        costs=CostBreakdown(
            certifications=50000.0,
            documentation=10000.0,
            logistics=25000.0,
            total=85000.0,
            currency="INR"
        ),
        subsidies=[],
        action_plan=ActionPlan(days=days, progress_percentage=0.0),
        retrieved_sources=[],
        generated_at=datetime.utcnow()
    )


def test_generate_report_minimal(client, mock_report):
    """Test report generation with minimal required fields."""
    with patch('routers.reports.ReportGenerator') as mock_generator:
        # Mock the report generator
        mock_instance = Mock()
        mock_instance.generate_report.return_value = mock_report
        mock_generator.return_value = mock_instance
        
        # Mock database operations
        with patch('routers.reports.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Make request
            response = client.post(
                "/api/reports/generate",
                data={
                    "product_name": "Organic Turmeric Powder",
                    "destination_country": "United States",
                    "business_type": "Manufacturing",
                    "company_size": "Small"
                }
            )
            
            # Assertions
            assert response.status_code == 201
            data = response.json()
            assert data["report_id"] == "rpt_test123456"
            assert data["status"] == "completed"
            assert data["hs_code"]["code"] == "0910.30"
            assert data["risk_score"] == 35


def test_generate_report_with_image(client, mock_report):
    """Test report generation with image upload."""
    with patch('routers.reports.ReportGenerator') as mock_generator:
        mock_instance = Mock()
        mock_instance.generate_report.return_value = mock_report
        mock_generator.return_value = mock_instance
        
        with patch('routers.reports.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Create a fake image file
            image_data = b"fake image data"
            image_file = io.BytesIO(image_data)
            
            # Make request with file upload
            response = client.post(
                "/api/reports/generate",
                data={
                    "product_name": "Organic Turmeric Powder",
                    "destination_country": "United States",
                    "business_type": "Manufacturing",
                    "company_size": "Small",
                    "ingredients": "100% organic turmeric",
                    "bom": "Turmeric rhizomes, packaging"
                },
                files={
                    "product_image": ("test.jpg", image_file, "image/jpeg")
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["report_id"] == "rpt_test123456"


def test_generate_report_invalid_business_type(client):
    """Test report generation with invalid business type."""
    response = client.post(
        "/api/reports/generate",
        data={
            "product_name": "Test Product",
            "destination_country": "United States",
            "business_type": "InvalidType",
            "company_size": "Small"
        }
    )
    
    assert response.status_code == 400
    assert "Invalid enum value" in response.json()["detail"]


def test_generate_report_invalid_company_size(client):
    """Test report generation with invalid company size."""
    response = client.post(
        "/api/reports/generate",
        data={
            "product_name": "Test Product",
            "destination_country": "United States",
            "business_type": "Manufacturing",
            "company_size": "InvalidSize"
        }
    )
    
    assert response.status_code == 400
    assert "Invalid enum value" in response.json()["detail"]


def test_generate_report_empty_product_name(client):
    """Test report generation with empty product name."""
    response = client.post(
        "/api/reports/generate",
        data={
            "product_name": "   ",
            "destination_country": "United States",
            "business_type": "Manufacturing",
            "company_size": "Small"
        }
    )
    
    # Should fail validation
    assert response.status_code in [400, 422]


def test_generate_report_large_image(client):
    """Test report generation with oversized image."""
    # Create a fake image larger than 10MB
    large_image = io.BytesIO(b"x" * (11 * 1024 * 1024))
    
    response = client.post(
        "/api/reports/generate",
        data={
            "product_name": "Test Product",
            "destination_country": "United States",
            "business_type": "Manufacturing",
            "company_size": "Small"
        },
        files={
            "product_image": ("large.jpg", large_image, "image/jpeg")
        }
    )
    
    assert response.status_code == 400
    assert "exceeds 10MB limit" in response.json()["detail"]


def test_generate_report_invalid_image_type(client):
    """Test report generation with invalid image type."""
    pdf_file = io.BytesIO(b"fake pdf data")
    
    response = client.post(
        "/api/reports/generate",
        data={
            "product_name": "Test Product",
            "destination_country": "United States",
            "business_type": "Manufacturing",
            "company_size": "Small"
        },
        files={
            "product_image": ("test.pdf", pdf_file, "application/pdf")
        }
    )
    
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_get_report_success(client, mock_report):
    """Test retrieving an existing report."""
    with patch('routers.reports.get_db') as mock_db:
        mock_session = MagicMock()
        mock_db_report = MagicMock()
        mock_db_report.report_data = mock_report.model_dump(mode='json')
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        mock_db.return_value = mock_session
        
        response = client.get("/api/reports/rpt_test123456")
        
        assert response.status_code == 200
        data = response.json()
        assert data["report_id"] == "rpt_test123456"


def test_get_report_not_found(client):
    """Test retrieving a non-existent report."""
    with patch('routers.reports.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = mock_session
        
        # Use a valid UUID format
        response = client.get("/api/reports/rpt_00000000000000000000000000000000")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_get_report_invalid_id(client):
    """Test retrieving a report with invalid ID format."""
    response = client.get("/api/reports/invalid-id-format")
    
    assert response.status_code == 400
    assert "Invalid report ID format" in response.json()["detail"]


def test_get_report_status_success(client):
    """Test checking report status."""
    with patch('routers.reports.get_db') as mock_db:
        mock_session = MagicMock()
        mock_db_report = MagicMock()
        # Use a valid UUID
        test_uuid = uuid.uuid4()
        mock_db_report.id = test_uuid
        mock_db_report.status = "completed"
        mock_db_report.created_at = datetime.utcnow()
        mock_db_report.updated_at = datetime.utcnow()
        mock_db_report.hs_code = "0910.30"
        mock_db_report.risk_score = 35
        mock_db_report.estimated_cost = 85000.0
        mock_db_report.estimated_timeline_days = 60
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        mock_db.return_value = mock_session
        
        # Use the UUID without dashes
        report_id = f"rpt_{str(test_uuid).replace('-', '')}"
        response = client.get(f"/api/reports/{report_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["hs_code"] == "0910.30"
        assert data["risk_score"] == 35


def test_get_report_status_not_found(client):
    """Test checking status of non-existent report."""
    with patch('routers.reports.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = mock_session
        
        # Use a valid UUID format
        response = client.get("/api/reports/rpt_00000000000000000000000000000000/status")
        
        assert response.status_code == 404


def test_update_hs_code_success(client, mock_report):
    """Test updating HS code manually."""
    with patch('routers.reports.get_db') as mock_db:
        mock_session = MagicMock()
        mock_db_report = MagicMock()
        mock_db_report.hs_code = "0910.30"
        mock_db_report.report_data = mock_report.model_dump(mode='json')
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        mock_db.return_value = mock_session
        
        response = client.put(
            "/api/reports/rpt_test123456/hs-code",
            data={"hs_code": "0910.99"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["hs_code"]["code"] == "0910.99"
        assert data["hs_code"]["confidence"] == 100.0


def test_update_hs_code_invalid_format(client):
    """Test updating HS code with invalid format."""
    with patch('routers.reports.get_db') as mock_db:
        mock_session = MagicMock()
        mock_db_report = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        mock_db.return_value = mock_session
        
        response = client.put(
            "/api/reports/rpt_test123456/hs-code",
            data={"hs_code": "ABC123"}
        )
        
        assert response.status_code == 400
        assert "must contain only digits" in response.json()["detail"]


def test_update_hs_code_not_found(client):
    """Test updating HS code for non-existent report."""
    with patch('routers.reports.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = mock_session
        
        # Use a valid UUID format
        response = client.put(
            "/api/reports/rpt_00000000000000000000000000000000/hs-code",
            data={"hs_code": "0910.99"}
        )
        
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
