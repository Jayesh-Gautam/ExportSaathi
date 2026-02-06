"""
Simple test script to verify Pydantic models work correctly.
"""
from models import (
    QueryInput,
    BusinessType,
    CompanySize,
    HSCodePrediction,
    HSCodeAlternative,
    Certification,
    CertificationType,
    Priority,
    CostRange,
    ExportReadinessReport,
    ReportStatus,
    ActionPlan,
    DayPlan,
    Task,
    TaskCategory,
)
from datetime import datetime


def test_query_input():
    """Test QueryInput model."""
    query = QueryInput(
        product_name="Organic Turmeric Powder",
        ingredients="100% organic turmeric",
        destination_country="United States",
        business_type=BusinessType.MANUFACTURING,
        company_size=CompanySize.SMALL,
        monthly_volume=1000.0
    )
    assert query.product_name == "Organic Turmeric Powder"
    assert query.business_type == BusinessType.MANUFACTURING
    print("✓ QueryInput model works correctly")


def test_hs_code_prediction():
    """Test HSCodePrediction model."""
    hs_code = HSCodePrediction(
        code="0910.30",
        confidence=92.5,
        description="Turmeric (curcuma)",
        alternatives=[
            HSCodeAlternative(
                code="0910.99",
                confidence=65.0,
                description="Other spices"
            )
        ]
    )
    assert hs_code.code == "0910.30"
    assert hs_code.confidence == 92.5
    assert len(hs_code.alternatives) == 1
    print("✓ HSCodePrediction model works correctly")


def test_certification():
    """Test Certification model."""
    cert = Certification(
        id="fda-food-facility",
        name="FDA Food Facility Registration",
        type=CertificationType.FDA,
        mandatory=True,
        estimated_cost=CostRange(min=15000, max=30000, currency="INR"),
        estimated_timeline_days=30,
        priority=Priority.HIGH
    )
    assert cert.id == "fda-food-facility"
    assert cert.type == CertificationType.FDA
    assert cert.mandatory is True
    print("✓ Certification model works correctly")


def test_action_plan():
    """Test ActionPlan model."""
    action_plan = ActionPlan(
        days=[
            DayPlan(
                day=i,
                title=f"Day {i}",
                tasks=[
                    Task(
                        id=f"task_{i}_1",
                        title=f"Task {i}.1",
                        description=f"Description for task {i}.1",
                        category=TaskCategory.DOCUMENTATION,
                        completed=False
                    )
                ]
            )
            for i in range(1, 8)
        ],
        progress_percentage=0.0
    )
    assert len(action_plan.days) == 7
    assert action_plan.progress_percentage == 0.0
    print("✓ ActionPlan model works correctly")


def test_validation_errors():
    """Test validation errors are raised correctly."""
    try:
        # Empty product name should fail
        QueryInput(
            product_name="   ",
            destination_country="USA",
            business_type=BusinessType.MANUFACTURING,
            company_size=CompanySize.SMALL
        )
        assert False, "Should have raised validation error"
    except ValueError as e:
        assert "empty" in str(e).lower()
        print("✓ Validation errors work correctly")


if __name__ == "__main__":
    print("Testing Pydantic models...\n")
    test_query_input()
    test_hs_code_prediction()
    test_certification()
    test_action_plan()
    test_validation_errors()
    print("\n✅ All model tests passed!")
