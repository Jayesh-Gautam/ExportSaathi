"""
Test suite for Action Plan API Router

Tests the action plan API endpoints to ensure they work correctly with:
1. GET /api/action-plan/{report_id} - Get 7-day action plan
2. PUT /api/action-plan/{report_id}/tasks/{task_id} - Update task status
3. GET /api/action-plan/{report_id}/download - Download action plan as PDF

This is a comprehensive test suite for the action plan router implementation.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime

from main import app
from models import ExportReadinessReport, HSCodePrediction, ReportStatus
from models.certification import Certification, Priority
from models.action_plan import ActionPlan, DayPlan, Task
from models.enums import TaskCategory
from models.report import Timeline, CostBreakdown, TimelinePhase


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_report():
    """Create a mock export readiness report."""
    from models.common import CostRange
    from models.enums import CertificationType
    
    return ExportReadinessReport(
        report_id="rpt_test123456",
        status=ReportStatus.COMPLETED,
        hs_code=HSCodePrediction(
            code="0910.30",
            confidence=92.5,
            description="Turmeric (curcuma)",
            alternatives=[]
        ),
        certifications=[
            Certification(
                id="cert_fda",
                name="FDA Registration",
                type=CertificationType.FDA,
                priority=Priority.HIGH,
                mandatory=True,
                estimated_cost=CostRange(min=20000.0, max=30000.0, currency="INR"),
                estimated_timeline_days=30,
                description="FDA registration for food products"
            )
        ],
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
        action_plan=ActionPlan(
            days=[
                DayPlan(
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
                ) for i in range(1, 8)
            ],
            progress_percentage=0.0
        ),
        retrieved_sources=[],
        generated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_action_plan():
    """Create a mock action plan."""
    days = []
    for i in range(1, 8):
        tasks = [
            Task(
                id=f"task_day{i}_1",
                title=f"Task 1 for day {i}",
                description=f"Description 1 for day {i}",
                category=TaskCategory.DOCUMENTATION,
                completed=False,
                estimated_duration="2-3 hours",
                dependencies=[]
            ),
            Task(
                id=f"task_day{i}_2",
                title=f"Task 2 for day {i}",
                description=f"Description 2 for day {i}",
                category=TaskCategory.CERTIFICATION if i in [2, 3] else TaskCategory.LOGISTICS,
                completed=False,
                estimated_duration="3-4 hours",
                dependencies=[]
            )
        ]
        days.append(DayPlan(
            day=i,
            title=f"Day {i} - Test Title",
            tasks=tasks
        ))
    
    return ActionPlan(days=days, progress_percentage=0.0)


# Test GET /api/action-plan/{report_id}

def test_get_action_plan_success(client, mock_report, mock_action_plan):
    """Test successful action plan retrieval."""
    report_uuid = uuid.uuid4()
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query
        mock_db_report = Mock()
        mock_db_report.id = report_uuid
        mock_db_report.report_data = mock_report.model_dump(mode='json')
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        
        # Mock action plan progress query (no completed tasks)
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        # Mock ActionPlanGenerator
        with patch('routers.action_plan.ActionPlanGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.generate_plan.return_value = mock_action_plan
            mock_generator.return_value = mock_instance
            
            # Make request
            response = client.get(f"/api/action-plan/rpt_{str(report_uuid).replace('-', '')}")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert "days" in data
            assert len(data["days"]) == 7
            assert "progress_percentage" in data
            assert data["progress_percentage"] == 0.0


def test_get_action_plan_with_completed_tasks(client, mock_report, mock_action_plan):
    """Test action plan retrieval with some completed tasks."""
    report_uuid = uuid.uuid4()
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query
        mock_db_report = Mock()
        mock_db_report.id = report_uuid
        mock_db_report.report_data = mock_report.model_dump(mode='json')
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        
        # Mock action plan progress query (2 completed tasks)
        mock_progress_1 = Mock()
        mock_progress_1.task_id = "task_day1_1"
        mock_progress_1.completed = True
        
        mock_progress_2 = Mock()
        mock_progress_2.task_id = "task_day2_1"
        mock_progress_2.completed = True
        
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_progress_1, mock_progress_2
        ]
        
        # Mock ActionPlanGenerator
        with patch('routers.action_plan.ActionPlanGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.generate_plan.return_value = mock_action_plan
            mock_generator.return_value = mock_instance
            
            # Make request
            response = client.get(f"/api/action-plan/rpt_{str(report_uuid).replace('-', '')}")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert "progress_percentage" in data
            # 2 completed out of 14 total tasks (2 tasks per day * 7 days)
            expected_progress = (2 / 14) * 100
            assert abs(data["progress_percentage"] - expected_progress) < 0.1


def test_get_action_plan_report_not_found(client):
    """Test action plan retrieval for non-existent report."""
    # Use a valid UUID format that doesn't exist
    nonexistent_uuid = str(uuid.uuid4()).replace('-', '')
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query returning None
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Make request
        response = client.get(f"/api/action-plan/rpt_{nonexistent_uuid}")
        
        # Assertions
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_get_action_plan_invalid_report_id(client):
    """Test action plan retrieval with invalid report ID format."""
    response = client.get("/api/action-plan/invalid-id-format")
    
    # Assertions
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


# Test PUT /api/action-plan/{report_id}/tasks/{task_id}

def test_update_task_status_mark_completed(client, mock_report, mock_action_plan):
    """Test marking a task as completed."""
    report_uuid = uuid.uuid4()
    task_id = "task_day1_1"
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query
        mock_db_report = Mock()
        mock_db_report.id = report_uuid
        mock_db_report.user_id = None
        mock_db_report.report_data = mock_report.model_dump(mode='json')
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        
        # Mock ActionPlanGenerator
        with patch('routers.action_plan.ActionPlanGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.generate_plan.return_value = mock_action_plan
            mock_generator.return_value = mock_instance
            
            # Mock task progress query (no existing record)
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            # Mock all progress query (empty)
            mock_session.query.return_value.filter.return_value.all.return_value = []
            
            # Make request
            response = client.put(
                f"/api/action-plan/rpt_{str(report_uuid).replace('-', '')}/tasks/{task_id}",
                json={"completed": True}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == task_id
            assert data["completed"] is True
            assert "progress_percentage" in data
            assert "completed_tasks" in data
            assert "total_tasks" in data


def test_update_task_status_mark_incomplete(client, mock_report, mock_action_plan):
    """Test marking a task as incomplete."""
    report_uuid = uuid.uuid4()
    task_id = "task_day1_1"
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query
        mock_db_report = Mock()
        mock_db_report.id = report_uuid
        mock_db_report.user_id = None
        mock_db_report.report_data = mock_report.model_dump(mode='json')
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        
        # Mock ActionPlanGenerator
        with patch('routers.action_plan.ActionPlanGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.generate_plan.return_value = mock_action_plan
            mock_generator.return_value = mock_instance
            
            # Mock existing task progress record
            mock_task_progress = Mock()
            mock_task_progress.task_id = task_id
            mock_task_progress.completed = True
            mock_task_progress.completed_at = datetime.utcnow()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_task_progress
            
            # Mock all progress query
            mock_session.query.return_value.filter.return_value.all.return_value = [mock_task_progress]
            
            # Make request
            response = client.put(
                f"/api/action-plan/rpt_{str(report_uuid).replace('-', '')}/tasks/{task_id}",
                json={"completed": False}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == task_id
            assert data["completed"] is False


def test_update_task_status_task_not_found(client, mock_report, mock_action_plan):
    """Test updating status for non-existent task."""
    report_uuid = uuid.uuid4()
    task_id = "task_nonexistent"
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query
        mock_db_report = Mock()
        mock_db_report.id = report_uuid
        mock_db_report.report_data = mock_report.model_dump(mode='json')
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        
        # Mock ActionPlanGenerator
        with patch('routers.action_plan.ActionPlanGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.generate_plan.return_value = mock_action_plan
            mock_generator.return_value = mock_instance
            
            # Make request
            response = client.put(
                f"/api/action-plan/rpt_{str(report_uuid).replace('-', '')}/tasks/{task_id}",
                json={"completed": True}
            )
            
            # Assertions
            assert response.status_code == 404
            assert "task not found" in response.json()["detail"].lower()


def test_update_task_status_report_not_found(client):
    """Test updating task status for non-existent report."""
    # Use a valid UUID format that doesn't exist
    nonexistent_uuid = str(uuid.uuid4()).replace('-', '')
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query returning None
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Make request
        response = client.put(
            f"/api/action-plan/rpt_{nonexistent_uuid}/tasks/task_1",
            json={"completed": True}
        )
        
        # Assertions
        assert response.status_code == 404
        assert "report not found" in response.json()["detail"].lower()


def test_update_task_status_invalid_report_id(client):
    """Test updating task status with invalid report ID format."""
    response = client.put(
        "/api/action-plan/invalid-id/tasks/task_1",
        json={"completed": True}
    )
    
    # Assertions
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


# Test GET /api/action-plan/{report_id}/download

def test_download_action_plan_success(client, mock_report, mock_action_plan):
    """Test successful action plan download."""
    report_uuid = uuid.uuid4()
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query
        mock_db_report = Mock()
        mock_db_report.id = report_uuid
        mock_db_report.product_name = "Turmeric Powder"
        mock_db_report.destination_country = "United States"
        mock_db_report.report_data = mock_report.model_dump(mode='json')
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        
        # Mock action plan progress query
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        # Mock ActionPlanGenerator
        with patch('routers.action_plan.ActionPlanGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.generate_plan.return_value = mock_action_plan
            mock_generator.return_value = mock_instance
            
            # Make request
            response = client.get(f"/api/action-plan/rpt_{str(report_uuid).replace('-', '')}/download")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert "report_id" in data
            assert "product_name" in data
            assert data["product_name"] == "Turmeric Powder"
            assert "destination_country" in data
            assert data["destination_country"] == "United States"
            assert "action_plan" in data
            assert "generated_at" in data
            assert "format" in data


def test_download_action_plan_with_completed_tasks(client, mock_report, mock_action_plan):
    """Test action plan download with completed tasks."""
    report_uuid = uuid.uuid4()
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query
        mock_db_report = Mock()
        mock_db_report.id = report_uuid
        mock_db_report.product_name = "Turmeric Powder"
        mock_db_report.destination_country = "United States"
        mock_db_report.report_data = mock_report.model_dump(mode='json')
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        
        # Mock action plan progress query (some completed tasks)
        mock_progress = Mock()
        mock_progress.task_id = "task_day1_1"
        mock_progress.completed = True
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_progress]
        
        # Mock ActionPlanGenerator
        with patch('routers.action_plan.ActionPlanGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.generate_plan.return_value = mock_action_plan
            mock_generator.return_value = mock_instance
            
            # Make request
            response = client.get(f"/api/action-plan/rpt_{str(report_uuid).replace('-', '')}/download")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert "action_plan" in data
            # Verify that completed status is reflected in the action plan
            action_plan_data = data["action_plan"]
            assert "days" in action_plan_data


def test_download_action_plan_report_not_found(client):
    """Test action plan download for non-existent report."""
    # Use a valid UUID format that doesn't exist
    nonexistent_uuid = str(uuid.uuid4()).replace('-', '')
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query returning None
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Make request
        response = client.get(f"/api/action-plan/rpt_{nonexistent_uuid}/download")
        
        # Assertions
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_download_action_plan_invalid_report_id(client):
    """Test action plan download with invalid report ID format."""
    response = client.get("/api/action-plan/invalid-id/download")
    
    # Assertions
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


# Integration test

def test_complete_action_plan_workflow(client, mock_report, mock_action_plan):
    """Test complete workflow: get plan -> update tasks -> download."""
    report_uuid = uuid.uuid4()
    
    with patch('routers.action_plan.get_db') as mock_db:
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock report query
        mock_db_report = Mock()
        mock_db_report.id = report_uuid
        mock_db_report.user_id = None
        mock_db_report.product_name = "Turmeric Powder"
        mock_db_report.destination_country = "United States"
        mock_db_report.report_data = mock_report.model_dump(mode='json')
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        
        # Mock ActionPlanGenerator
        with patch('routers.action_plan.ActionPlanGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.generate_plan.return_value = mock_action_plan
            mock_generator.return_value = mock_instance
            
            # Step 1: Get action plan
            mock_session.query.return_value.filter.return_value.all.return_value = []
            response1 = client.get(f"/api/action-plan/rpt_{str(report_uuid).replace('-', '')}")
            assert response1.status_code == 200
            assert response1.json()["progress_percentage"] == 0.0
            
            # Step 2: Update task status
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.query.return_value.filter.return_value.all.return_value = []
            response2 = client.put(
                f"/api/action-plan/rpt_{str(report_uuid).replace('-', '')}/tasks/task_day1_1",
                json={"completed": True}
            )
            assert response2.status_code == 200
            assert response2.json()["completed"] is True
            
            # Step 3: Download action plan
            mock_progress = Mock()
            mock_progress.task_id = "task_day1_1"
            mock_progress.completed = True
            mock_session.query.return_value.filter.return_value.all.return_value = [mock_progress]
            response3 = client.get(f"/api/action-plan/rpt_{str(report_uuid).replace('-', '')}/download")
            assert response3.status_code == 200
            assert "action_plan" in response3.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
