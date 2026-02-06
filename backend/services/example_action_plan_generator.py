"""
Example usage of ActionPlanGenerator service.

This script demonstrates how to generate a 7-day export readiness action plan
from an export readiness report.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from services.action_plan_generator import ActionPlanGenerator
from models import (
    ExportReadinessReport,
    HSCodePrediction,
    Certification,
    CertificationType,
    Priority,
    CostRange,
    Timeline,
    TimelinePhase,
    CostBreakdown,
    ReportStatus,
    ActionPlan,
    DayPlan,
    Task,
    TaskCategory,
)


def create_sample_report() -> ExportReadinessReport:
    """Create a sample export readiness report for demonstration."""
    
    # Sample certifications
    certifications = [
        Certification(
            id="cert_fda",
            name="FDA Registration",
            type=CertificationType.FDA,
            mandatory=True,
            estimated_cost=CostRange(min=15000, max=25000, currency="INR"),
            estimated_timeline_days=30,  # Exceeds 7 days
            priority=Priority.HIGH,
        ),
        Certification(
            id="cert_ce",
            name="CE Marking",
            type=CertificationType.CE,
            mandatory=True,
            estimated_cost=CostRange(min=20000, max=35000, currency="INR"),
            estimated_timeline_days=45,  # Exceeds 7 days
            priority=Priority.HIGH,
        ),
        Certification(
            id="cert_bis",
            name="BIS Certification",
            type=CertificationType.BIS,
            mandatory=False,
            estimated_cost=CostRange(min=10000, max=15000, currency="INR"),
            estimated_timeline_days=5,  # Within 7 days
            priority=Priority.MEDIUM,
        ),
    ]
    
    # Create placeholder action plan (will be replaced)
    placeholder_action_plan = ActionPlan(
        days=[
            DayPlan(
                day=i,
                title=f"Day {i}",
                tasks=[
                    Task(
                        id=f"placeholder_{i}",
                        title="Placeholder",
                        description="Placeholder task",
                        category=TaskCategory.DOCUMENTATION,
                    )
                ]
            ) for i in range(1, 8)
        ],
        progress_percentage=0.0,
    )
    
    # Create sample report
    report = ExportReadinessReport(
        report_id="rpt_example_001",
        status=ReportStatus.COMPLETED,
        hs_code=HSCodePrediction(
            code="0910.30",
            confidence=92.5,
            description="Turmeric (curcuma)",
            alternatives=[],
        ),
        certifications=certifications,
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
        action_plan=placeholder_action_plan,
        retrieved_sources=[],
        generated_at=datetime.now(),
    )
    
    return report


def print_action_plan(action_plan: ActionPlan):
    """Print the action plan in a readable format."""
    print("\n" + "="*80)
    print("7-DAY EXPORT READINESS ACTION PLAN")
    print("="*80)
    print(f"Overall Progress: {action_plan.progress_percentage:.1f}%\n")
    
    for day in action_plan.days:
        print(f"\n{'─'*80}")
        print(f"DAY {day.day}: {day.title}")
        print(f"{'─'*80}")
        
        for i, task in enumerate(day.tasks, 1):
            status = "✓" if task.completed else "○"
            print(f"\n{status} Task {i}: {task.title}")
            print(f"   Category: {task.category.value}")
            print(f"   Duration: {task.estimated_duration}")
            if task.dependencies:
                print(f"   Dependencies: {', '.join(task.dependencies)}")
            print(f"   Description: {task.description}")
    
    print("\n" + "="*80)
    
    # Summary statistics
    total_tasks = sum(len(day.tasks) for day in action_plan.days)
    completed_tasks = sum(
        sum(1 for task in day.tasks if task.completed)
        for day in action_plan.days
    )
    
    print(f"\nSummary:")
    print(f"  Total Tasks: {total_tasks}")
    print(f"  Completed: {completed_tasks}")
    print(f"  Remaining: {total_tasks - completed_tasks}")
    print(f"  Progress: {action_plan.progress_percentage:.1f}%")
    
    # Category breakdown
    category_counts = {}
    for day in action_plan.days:
        for task in day.tasks:
            category = task.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
    
    print(f"\nTasks by Category:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category.capitalize()}: {count}")


def main():
    """Main example function."""
    print("ActionPlanGenerator Example")
    print("="*80)
    
    # Create sample report
    print("\n1. Creating sample export readiness report...")
    report = create_sample_report()
    print(f"   Report ID: {report.report_id}")
    print(f"   Product: {report.hs_code.description} (HS Code: {report.hs_code.code})")
    print(f"   Certifications Required: {len(report.certifications)}")
    for cert in report.certifications:
        print(f"     - {cert.name} ({cert.estimated_timeline_days} days, {cert.priority.value} priority)")
    
    # Initialize generator
    print("\n2. Initializing ActionPlanGenerator...")
    generator = ActionPlanGenerator()
    print("   Generator initialized successfully")
    
    # Generate action plan
    print("\n3. Generating 7-day action plan...")
    action_plan = generator.generate_plan(report)
    print("   Action plan generated successfully")
    
    # Print the action plan
    print_action_plan(action_plan)
    
    # Demonstrate task completion
    print("\n" + "="*80)
    print("SIMULATING TASK COMPLETION")
    print("="*80)
    
    # Mark some Day 1 tasks as completed
    print("\nMarking Day 1 tasks as completed...")
    for task in action_plan.days[0].tasks:
        task.completed = True
    
    # Recalculate progress
    total_tasks = sum(len(day.tasks) for day in action_plan.days)
    completed_tasks = sum(
        sum(1 for task in day.tasks if task.completed)
        for day in action_plan.days
    )
    action_plan.progress_percentage = (completed_tasks / total_tasks) * 100
    
    print(f"Progress updated: {action_plan.progress_percentage:.1f}%")
    
    # Show updated Day 1
    print(f"\nDay 1 Status:")
    for task in action_plan.days[0].tasks:
        status = "✓" if task.completed else "○"
        print(f"  {status} {task.title}")
    
    print("\n" + "="*80)
    print("Example completed successfully!")
    print("="*80)


if __name__ == "__main__":
    main()
