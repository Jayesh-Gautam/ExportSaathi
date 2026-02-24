"""
Integration test for GST refund estimator in FinanceModule.
Tests the actual implementation in the finance_module.py service.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.finance_module import FinanceModule
from models.finance import GSTRefund


def test_gst_refund_estimator():
    """Test GST refund estimator functionality in FinanceModule."""
    
    # Create a FinanceModule instance (without database for this test)
    # We'll test the estimate_gst_refund method directly
    finance_module = FinanceModule(db_session=None)
    
    print("Testing GST Refund Estimator Implementation...")
    print("=" * 60)
    
    # Test 1: GST refund with known GST paid
    print("\n1. Testing with known GST paid amount...")
    export_value = 200000.0
    gst_paid = 36000.0
    
    result = finance_module.estimate_gst_refund(
        export_value=export_value,
        gst_paid=gst_paid
    )
    
    assert isinstance(result, GSTRefund), "Result should be GSTRefund instance"
    assert result.estimated_amount == gst_paid, f"Expected {gst_paid}, got {result.estimated_amount}"
    assert result.timeline_days == 45, f"Expected 45 days, got {result.timeline_days}"
    assert len(result.requirements) > 0, "Should have requirements"
    
    print(f"   ✓ Estimated amount: ₹{result.estimated_amount:,.2f}")
    print(f"   ✓ Timeline: {result.timeline_days} days")
    print(f"   ✓ Requirements: {len(result.requirements)} items")
    
    # Test 2: GST refund without GST paid (auto-estimated at 18%)
    print("\n2. Testing with auto-estimated GST (18% of export value)...")
    export_value = 500000.0
    
    result = finance_module.estimate_gst_refund(export_value=export_value)
    
    expected_gst = export_value * 0.18
    assert result.estimated_amount == expected_gst, f"Expected {expected_gst}, got {result.estimated_amount}"
    assert result.timeline_days == 45, "Timeline should be 45 days"
    
    print(f"   ✓ Export value: ₹{export_value:,.2f}")
    print(f"   ✓ Estimated GST (18%): ₹{result.estimated_amount:,.2f}")
    print(f"   ✓ Timeline: {result.timeline_days} days")
    
    # Test 3: Verify timeline is within expected range (30-60 days)
    print("\n3. Verifying timeline is within expected range...")
    assert 30 <= result.timeline_days <= 60, "Timeline should be between 30-60 days"
    print(f"   ✓ Timeline {result.timeline_days} days is within 30-60 day range")
    
    # Test 4: Verify all required documents are listed
    print("\n4. Verifying GST refund requirements...")
    required_keywords = ["GST LUT", "Shipping bill", "Bank realization", "Invoice", "GST returns"]
    requirements_text = " ".join(result.requirements)
    
    for keyword in required_keywords:
        assert keyword in requirements_text, f"Missing requirement: {keyword}"
        print(f"   ✓ Requirement found: {keyword}")
    
    # Test 5: Display all requirements
    print("\n5. Complete list of GST refund requirements:")
    for i, req in enumerate(result.requirements, 1):
        print(f"   {i}. {req}")
    
    # Test 6: Test with different export values
    print("\n6. Testing with various export values...")
    test_values = [100000, 500000, 1000000, 5000000]
    
    for value in test_values:
        result = finance_module.estimate_gst_refund(export_value=value)
        expected = value * 0.18
        assert result.estimated_amount == expected
        print(f"   ✓ Export ₹{value:,} → GST refund ₹{result.estimated_amount:,.2f}")
    
    print("\n" + "=" * 60)
    print("✅ All GST refund estimator tests passed!")
    print("\n📋 Task 9.3 Implementation Verification:")
    print("   ✅ Calculate GST refund amount based on export value")
    print("   ✅ Estimate refund timeline (typically 30-60 days)")
    print("   ✅ List requirements for GST refund application")
    print("\n🎯 Implementation Status: COMPLETE")


if __name__ == "__main__":
    test_gst_refund_estimator()
