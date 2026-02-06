"""
Unit tests for ActionPlanGenerator service.

Tests the generation of 7-day action plans with proper task distribution,
dependency handling, and processing time considerations.
"""
import pytest
from datetime import datetime
from action_plan_generator import ActionPlanGenerator
from models import (
    ExportReadinessReport,
    ActionPlan,
    DayPlan,
    Task,
    TaskCategory,
    Certification,
    Priority,
    HSCodePrediction,
    Timeline,
    TimelinePhase,
    CostBreakdown,
    ReportStatus,
    CertificationType,
    CostRange,
)


@pytest.fixture
def action_plan_generator():
    """Create an ActionPlanGenerator instance."""
    return ActionPlanGenerator()


@pytest.fixture
def sample_certifications():
    """Create sample certifications for testing."""
    return [
        Certification(
            id="cert_fda",
            name="FDA Registration",
            type=CertificationType.FDA,
            mandatory=True,
            estimated_cost=CostRange(min=15000, max=25000, currency="INR"),
            estimated_timeline_days=30,
            priority=Priority.HIGH,
        ),
        Certification(
            id="cert_ce",
            name="CE Marking",
            type=CertificationType.CE,
            mandatory=True,
            estimated_cost=CostRange(min=20000, max=35000, currency="INR"),
            estimated_timeline_days=45,
            priority=Priority.HIGH,
        ),
        Certification(
            id="cert_bis",
            name="BIS Certification",
            type=CertificationType.BIS,
            mandatory=False,
            estimated_cost=CostRange(min=10000, max=15000, currency="INR"),
            estimated_timeline_days=5,
            priority=Priority.MEDIUM,
        ),
    ]


@pytest.fixture
def sample_report(sample_certifications):
    """Create a sample export readiness report."""
    return ExportReadinessReport(
        report_id="rpt_test_123",
        status=ReportStatus.COMPLETED,
        hs_code=HSCodePrediction(
            code="0910.30",
            confidence=92.5,
            description="Turmeric (curcuma)",
            alternatives=[],
        ),
        certifications=sample_certifications,
        restricted_substances=[],
        past_rejections=[],
        compliance_roadmap=[],
        risks=[],
        risk_score=35,
        timeline=Timeline(
            estimated_days=60,
            breakdown=[
                TimelinePhase(phase="Documentation", duration_days=10),
                TimelinePhase(phase="Certification", duration_days=30),
                TimelinePhase(phase="Logistics", duration_days=20),
            ]
        ),
        costs=CostBreakdown(
            certifications=50000,
            documentation=10000,
            logistics=25000,
            total=85000,
            currency="INR",
        ),
        subsidies=[],
        action_plan=ActionPlan(
            days=[
                DayPlan(
                    day=i,
                    title=f"Day {i}",
                    tasks=[
                        Task(
                            id=f"task_{i}",
                            title=f"Task {i}",
                            description="Placeholder",
                            category=TaskCategory.DOCUMENTATION,
                        )
                    ]
                ) for i in range(1, 8)
            ],
            progress_percentage=0.0,
        ),
        retrieved_sources=[],
        generated_at=datetime.now(),
    )


class TestActionPlanGenerator:
    """Test suite for ActionPlanGenerator."""
    
    def test_generate_plan_returns_action_plan(self, action_plan_generator, sample_report):
        """Test that generate_plan returns a valid ActionPlan."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        assert isinstance(action_plan, ActionPlan)
        assert len(action_plan.days) == 7
        assert action_plan.progress_percentage == 0.0
    
    def test_generate_plan_has_all_7_days(self, action_plan_generator, sample_report):
        """Test that the action plan has exactly 7 days."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        assert len(action_plan.days) == 7
        day_numbers = [day.day for day in action_plan.days]
        assert sorted(day_numbers) == list(range(1, 8))
    
    def test_generate_plan_each_day_has_tasks(self, action_plan_generator, sample_report):
        """Test that each day has at least one task."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        for day in action_plan.days:
            assert len(day.tasks) > 0, f"Day {day.day} has no tasks"
    
    def test_day_1_has_foundational_tasks(self, action_plan_generator, sample_report):
        """Test that Day 1 includes foundational tasks like GST LUT and HS code confirmation."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        day_1 = action_plan.days[0]
        task_ids = [task.id for task in day_1.tasks]
        
        # Check for key foundational tasks
        assert "task_gst_lut" in task_ids
        assert "task_hs_code_confirmation" in task_ids
        assert "task_iec_verification" in task_ids
        assert "task_bank_account_setup" in task_ids
    
    def test_certification_tasks_on_days_2_3(self, action_plan_generator, sample_report):
        """Test that certification tasks are scheduled on days 2-3."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        # Collect all certification tasks
        cert_tasks = []
        for day in action_plan.days:
            for task in day.tasks:
                if task.category == TaskCategory.CERTIFICATION:
                    cert_tasks.append((day.day, task))
        
        # Check that certification tasks exist
        assert len(cert_tasks) > 0, "No certification tasks found"
        
        # Check that they are on days 2 or 3
        for day_num, task in cert_tasks:
            assert day_num in [2, 3], f"Certification task {task.id} on day {day_num}, expected day 2 or 3"
    
    def test_document_tasks_on_days_4_5(self, action_plan_generator, sample_report):
        """Test that document preparation tasks are on days 4-5."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        # Check for document preparation task
        doc_prep_found = False
        for day in action_plan.days:
            if day.day in [4, 5]:
                for task in day.tasks:
                    if "document_preparation" in task.id or "certificate_of_origin" in task.id:
                        doc_prep_found = True
                        break
        
        assert doc_prep_found, "Document preparation tasks not found on days 4-5"
    
    def test_logistics_tasks_on_day_6(self, action_plan_generator, sample_report):
        """Test that logistics tasks are scheduled on day 6."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        day_6 = action_plan.days[5]  # Index 5 is day 6
        
        # Check for logistics tasks
        logistics_tasks = [task for task in day_6.tasks if task.category == TaskCategory.LOGISTICS]
        assert len(logistics_tasks) > 0, "No logistics tasks found on day 6"
        
        # Check for specific logistics tasks
        task_ids = [task.id for task in day_6.tasks]
        assert any("freight_booking" in tid or "customs_broker" in tid for tid in task_ids)
    
    def test_final_review_on_day_7(self, action_plan_generator, sample_report):
        """Test that final review tasks are on day 7."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        day_7 = action_plan.days[6]  # Index 6 is day 7
        task_ids = [task.id for task in day_7.tasks]
        
        assert "task_final_review" in task_ids or "task_readiness_checklist" in task_ids
    
    def test_certifications_exceeding_7_days_flagged(self, action_plan_generator, sample_report):
        """Test that certifications requiring >7 days are flagged with interim steps."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        # Find certification tasks
        cert_tasks = []
        for day in action_plan.days:
            for task in day.tasks:
                if task.category == TaskCategory.CERTIFICATION:
                    cert_tasks.append(task)
        
        # Check for interim step notation in tasks for long certifications
        long_cert_found = False
        for task in cert_tasks:
            if "Interim Step" in task.title or "exceeds 7 days" in task.description:
                long_cert_found = True
                break
        
        # We have certifications with 30 and 45 days, so should find interim steps
        assert long_cert_found, "Long certifications not flagged with interim steps"
    
    def test_task_dependencies_respected(self, action_plan_generator, sample_report):
        """Test that task dependencies are properly set."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        # Find document preparation task
        doc_prep_task = None
        for day in action_plan.days:
            for task in day.tasks:
                if task.id == "task_document_preparation":
                    doc_prep_task = task
                    break
        
        assert doc_prep_task is not None
        # Document preparation should depend on GST LUT and HS code confirmation
        assert "task_gst_lut" in doc_prep_task.dependencies
        assert "task_hs_code_confirmation" in doc_prep_task.dependencies
    
    def test_high_priority_certifications_first(self, action_plan_generator, sample_report):
        """Test that high priority certifications are scheduled before lower priority ones."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        # Collect certification tasks in order
        cert_tasks_ordered = []
        for day in action_plan.days:
            for task in day.tasks:
                if task.category == TaskCategory.CERTIFICATION:
                    cert_tasks_ordered.append(task)
        
        # Check that high priority certs (FDA, CE) come before medium priority (BIS)
        # FDA and CE should appear before BIS
        fda_index = None
        ce_index = None
        bis_index = None
        
        for i, task in enumerate(cert_tasks_ordered):
            if "FDA" in task.title:
                fda_index = i
            elif "CE" in task.title:
                ce_index = i
            elif "BIS" in task.title:
                bis_index = i
        
        # If all are present, high priority should come first
        if fda_index is not None and bis_index is not None:
            assert fda_index < bis_index, "High priority FDA should come before medium priority BIS"
        if ce_index is not None and bis_index is not None:
            assert ce_index < bis_index, "High priority CE should come before medium priority BIS"
    
    def test_all_tasks_have_required_fields(self, action_plan_generator, sample_report):
        """Test that all generated tasks have required fields."""
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        for day in action_plan.days:
            for task in day.tasks:
                assert task.id, "Task missing ID"
                assert task.title, "Task missing title"
                assert task.description, "Task missing description"
                assert task.category, "Task missing category"
                assert isinstance(task.completed, bool), "Task completed should be boolean"
    
    def test_generate_plan_with_no_certifications(self, action_plan_generator, sample_report):
        """Test action plan generation when there are no certifications."""
        # Create report with no certifications
        sample_report.certifications = []
        
        action_plan = action_plan_generator.generate_plan(sample_report)
        
        # Should still generate a valid 7-day plan
        assert len(action_plan.days) == 7
        
        # Should still have foundational, document, logistics, and review tasks
        all_task_ids = []
        for day in action_plan.days:
            all_task_ids.extend([task.id for task in day.tasks])
        
        assert "task_gst_lut" in all_task_ids
        assert "task_document_preparation" in all_task_ids
        assert "task_final_review" in all_task_ids
    
    def test_generate_foundational_tasks(self, action_plan_generator):
        """Test generation of foundational tasks."""
        tasks = action_plan_generator._generate_foundational_tasks()
        
        assert len(tasks) == 4  # GST LUT, HS code, IEC, bank
        task_ids = [task.id for task in tasks]
        
        assert "task_gst_lut" in task_ids
        assert "task_hs_code_confirmation" in task_ids
        assert "task_iec_verification" in task_ids
        assert "task_bank_account_setup" in task_ids
    
    def test_generate_certification_tasks(self, action_plan_generator, sample_certifications):
        """Test generation of certification tasks."""
        tasks = action_plan_generator._generate_certification_tasks(sample_certifications)
        
        assert len(tasks) == 3  # FDA, CE, BIS
        
        # Check that all certifications are represented
        task_titles = [task.title for task in tasks]
        assert any("FDA" in title for title in task_titles)
        assert any("CE" in title for title in task_titles)
        assert any("BIS" in title for title in task_titles)
    
    def test_generate_document_tasks(self, action_plan_generator, sample_report):
        """Test generation of document tasks."""
        tasks = action_plan_generator._generate_document_tasks(sample_report)
        
        assert len(tasks) >= 2  # At least document prep and certificate of origin
        
        task_ids = [task.id for task in tasks]
        assert "task_document_preparation" in task_ids
        assert "task_certificate_of_origin" in task_ids
    
    def test_generate_logistics_tasks(self, action_plan_generator, sample_report):
        """Test generation of logistics tasks."""
        tasks = action_plan_generator._generate_logistics_tasks(sample_report)
        
        assert len(tasks) >= 2  # At least customs broker and freight booking
        
        task_ids = [task.id for task in tasks]
        assert "task_customs_broker" in task_ids
        assert "task_freight_booking" in task_ids
    
    def test_generate_final_review_tasks(self, action_plan_generator):
        """Test generation of final review tasks."""
        tasks = action_plan_generator._generate_final_review_tasks()
        
        assert len(tasks) >= 1  # At least final review
        
        task_ids = [task.id for task in tasks]
        assert "task_final_review" in task_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
