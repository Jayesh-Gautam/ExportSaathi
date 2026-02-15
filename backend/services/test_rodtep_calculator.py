"""
Unit tests for RoDTEP Calculator service.

Tests the RoDTEP benefit calculation functionality including:
- Rate lookup with hierarchical matching
- Benefit amount calculation
- Input validation
- Schedule loading
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.rodtep_calculator import RoDTEPCalculator
from models.finance import RoDTEPBenefit


class TestRoDTEPCalculator:
    """Test suite for RoDTEP Calculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create a RoDTEP calculator instance."""
        return RoDTEPCalculator()
    
    def test_exact_hs_code_match(self, calculator):
        """Test exact HS code match returns correct rate."""
        # Test with turmeric HS code
        rate = calculator.get_rodtep_rate("0910.30")
        assert rate == 2.5
        
        # Test with T-shirts HS code
        rate = calculator.get_rodtep_rate("6109")
        assert rate == 4.3
        
        # Test with LED lights HS code
        rate = calculator.get_rodtep_rate("9405")
        assert rate == 3.8
    
    def test_four_digit_prefix_match(self, calculator):
        """Test 4-digit prefix matching when exact match not found."""
        # Test with HS code that should match "0910" prefix
        rate = calculator.get_rodtep_rate("0910.99")
        assert rate == 2.3  # Should match "0910" general spices rate
        
        # Test with HS code that should match "6109" exactly
        rate = calculator.get_rodtep_rate("610910")
        assert rate == 4.3
    
    def test_two_digit_chapter_match(self, calculator):
        """Test 2-digit chapter matching when prefix match not found."""
        # Test with HS code that should match chapter "61"
        rate = calculator.get_rodtep_rate("6115")  # Hosiery
        assert rate == 4.0  # Should match "61" knitted garments
        
        # Test with HS code that should match chapter "94"
        rate = calculator.get_rodtep_rate("9403")  # Furniture
        assert rate == 3.5  # Should match "94" furniture and lighting
    
    def test_default_rate_for_unknown_hs_code(self, calculator):
        """Test default rate is used for unknown HS codes."""
        # Test with completely unknown HS code
        rate = calculator.get_rodtep_rate("1234.56")
        assert rate == 1.5  # Default rate
        
        # Test with another unknown code
        rate = calculator.get_rodtep_rate("9999")
        assert rate == 1.5
    
    def test_calculate_benefit_basic(self, calculator):
        """Test basic RoDTEP benefit calculation."""
        # Calculate benefit for turmeric export
        benefit = calculator.calculate_benefit(
            hs_code="0910.30",
            destination="United States",
            fob_value=200000
        )
        
        assert isinstance(benefit, RoDTEPBenefit)
        assert benefit.hs_code == "0910.30"
        assert benefit.rate_percentage == 2.5
        assert benefit.estimated_amount == 5000  # 2.5% of 200000
        assert benefit.currency == "INR"
    
    def test_calculate_benefit_different_rates(self, calculator):
        """Test benefit calculation with different HS codes and rates."""
        # Test with T-shirts (4.3% rate)
        benefit = calculator.calculate_benefit(
            hs_code="6109",
            destination="Germany",
            fob_value=500000
        )
        assert benefit.rate_percentage == 4.3
        assert benefit.estimated_amount == 21500  # 4.3% of 500000
        
        # Test with LED lights (3.8% rate)
        benefit = calculator.calculate_benefit(
            hs_code="9405",
            destination="UAE",
            fob_value=1000000
        )
        assert benefit.rate_percentage == 3.8
        assert benefit.estimated_amount == 38000  # 3.8% of 1000000
    
    def test_calculate_benefit_with_default_rate(self, calculator):
        """Test benefit calculation using default rate."""
        benefit = calculator.calculate_benefit(
            hs_code="9999.99",
            destination="Japan",
            fob_value=300000
        )
        
        assert benefit.rate_percentage == 1.5  # Default rate
        assert benefit.estimated_amount == 4500  # 1.5% of 300000
    
    def test_calculate_benefit_zero_fob_value_raises_error(self, calculator):
        """Test that zero FOB value raises ValueError."""
        with pytest.raises(ValueError, match="FOB value must be positive"):
            calculator.calculate_benefit(
                hs_code="0910.30",
                destination="USA",
                fob_value=0
            )
    
    def test_calculate_benefit_negative_fob_value_raises_error(self, calculator):
        """Test that negative FOB value raises ValueError."""
        with pytest.raises(ValueError, match="FOB value must be positive"):
            calculator.calculate_benefit(
                hs_code="0910.30",
                destination="USA",
                fob_value=-100000
            )
    
    def test_calculate_benefit_empty_hs_code_raises_error(self, calculator):
        """Test that empty HS code raises ValueError."""
        with pytest.raises(ValueError, match="HS code cannot be empty"):
            calculator.calculate_benefit(
                hs_code="",
                destination="USA",
                fob_value=100000
            )
        
        with pytest.raises(ValueError, match="HS code cannot be empty"):
            calculator.calculate_benefit(
                hs_code="   ",
                destination="USA",
                fob_value=100000
            )
    
    def test_hs_code_cleaning(self, calculator):
        """Test that HS codes are properly cleaned (dots, spaces removed)."""
        # Test with dots
        rate1 = calculator.get_rodtep_rate("09.10.30")
        rate2 = calculator.get_rodtep_rate("091030")
        assert rate1 == rate2 == 2.5
        
        # Test with spaces
        rate3 = calculator.get_rodtep_rate("0910 30")
        assert rate3 == 2.5
    
    def test_load_rodtep_schedules(self, calculator):
        """Test loading custom RoDTEP schedules."""
        # Load custom schedules
        custom_schedules = {
            "1234": 5.0,
            "5678": 3.5,
            "9012": 2.0
        }
        
        calculator.load_rodtep_schedules(custom_schedules)
        
        # Verify custom rates are loaded
        assert calculator.get_rodtep_rate("1234") == 5.0
        assert calculator.get_rodtep_rate("5678") == 3.5
        assert calculator.get_rodtep_rate("9012") == 2.0
        
        # Verify existing rates still work
        assert calculator.get_rodtep_rate("0910.30") == 2.5
    
    def test_load_rodtep_schedules_empty_data(self, calculator):
        """Test loading empty schedules data."""
        original_count = len(calculator.get_all_rates())
        
        # Load empty data
        calculator.load_rodtep_schedules({})
        
        # Verify no change
        assert len(calculator.get_all_rates()) == original_count
    
    def test_get_all_rates(self, calculator):
        """Test getting all RoDTEP rates."""
        rates = calculator.get_all_rates()
        
        # Verify it's a dictionary
        assert isinstance(rates, dict)
        
        # Verify it contains expected entries (without dots)
        assert "091030" in rates  # Turmeric
        assert "6109" in rates    # T-shirts
        assert "default" in rates
        
        # Verify it's a copy (modifying it doesn't affect calculator)
        rates["test"] = 99.9
        assert "test" not in calculator.get_all_rates()
    
    def test_benefit_calculation_precision(self, calculator):
        """Test that benefit calculations maintain precision."""
        # Test with decimal FOB value
        benefit = calculator.calculate_benefit(
            hs_code="0910.30",
            destination="USA",
            fob_value=123456.78
        )
        
        # 2.5% of 123456.78 = 3086.4195
        assert abs(benefit.estimated_amount - 3086.4195) < 0.01
    
    def test_multiple_destinations_same_rate(self, calculator):
        """Test that destination doesn't affect rate (for now)."""
        # Note: In future, rates might vary by destination
        # For now, destination is stored but doesn't affect calculation
        
        benefit_usa = calculator.calculate_benefit(
            hs_code="0910.30",
            destination="United States",
            fob_value=100000
        )
        
        benefit_uk = calculator.calculate_benefit(
            hs_code="0910.30",
            destination="United Kingdom",
            fob_value=100000
        )
        
        # Same HS code and FOB value should give same benefit
        assert benefit_usa.rate_percentage == benefit_uk.rate_percentage
        assert benefit_usa.estimated_amount == benefit_uk.estimated_amount


class TestRoDTEPCalculatorIntegration:
    """Integration tests for RoDTEP Calculator."""
    
    def test_realistic_export_scenario_textiles(self):
        """Test realistic textile export scenario."""
        calculator = RoDTEPCalculator()
        
        # Scenario: Exporting T-shirts worth ₹10 lakh to USA
        benefit = calculator.calculate_benefit(
            hs_code="6109",
            destination="United States",
            fob_value=1000000
        )
        
        # T-shirts have 4.3% RoDTEP rate
        assert benefit.rate_percentage == 4.3
        assert benefit.estimated_amount == 43000
        
        # Verify this is a meaningful benefit (4.3% of export value)
        assert benefit.estimated_amount / 1000000 == 0.043
    
    def test_realistic_export_scenario_spices(self):
        """Test realistic spice export scenario."""
        calculator = RoDTEPCalculator()
        
        # Scenario: Exporting turmeric worth ₹5 lakh to Germany
        benefit = calculator.calculate_benefit(
            hs_code="0910.30",
            destination="Germany",
            fob_value=500000
        )
        
        # Turmeric has 2.5% RoDTEP rate
        assert benefit.rate_percentage == 2.5
        assert benefit.estimated_amount == 12500
    
    def test_realistic_export_scenario_electronics(self):
        """Test realistic electronics export scenario."""
        calculator = RoDTEPCalculator()
        
        # Scenario: Exporting LED lights worth ₹20 lakh to UAE
        benefit = calculator.calculate_benefit(
            hs_code="9405",
            destination="UAE",
            fob_value=2000000
        )
        
        # LED lights have 3.8% RoDTEP rate
        assert benefit.rate_percentage == 3.8
        assert benefit.estimated_amount == 76000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
