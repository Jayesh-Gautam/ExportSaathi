"""
Unit tests for Finance Module service.

Tests cover:
- Working capital calculation
- Pre-shipment credit eligibility assessment
- RoDTEP benefit calculation
- GST refund estimation
- Cash flow timeline generation
- Liquidity gap identification
- Financing options suggestion
"""
import pytest
from datetime import date, timedelta
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.finance_module import FinanceModule
from models.enums import CompanySize, CashFlowEventType
from models.finance import (
    WorkingCapitalAnalysis,
    PreShipmentCredit,
    RoDTEPBenefit,
    GSTRefund,
    CashFlowTimeline,
    FinanceAnalysis
)
import uuid


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def finance_module(mock_db_session):
    """Create a FinanceModule instance with mock database."""
    return FinanceModule(mock_db_session)


@pytest.fixture
def sample_report():
    """Create a sample report for testing."""
    # Create a mock report without importing database.models
    report = Mock()
    report.id = str(uuid.uuid4())
    report.hs_code = "0910.30"
    report.destination_country = "United States"
    report.company_size = "Small"
    report.monthly_volume = 1000
    report.price_range = "₹500-₹1500"
    report.report_data = {
        "costs": {
            "certifications": 50000,
            "logistics": 25000,
            "documentation": 10000,
            "total": 85000
        }
    }
    return report


class TestWorkingCapitalCalculation:
    """Test working capital calculation."""
    
    def test_calculate_working_capital_basic(self, finance_module, mock_db_session, sample_report):
        """Test basic working capital calculation."""
        # Setup mock
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Calculate working capital
        result = finance_module.calculate_working_capital(sample_report.id)
        
        # Assertions
        assert isinstance(result, WorkingCapitalAnalysis)
        assert result.certification_costs == 50000
        assert result.logistics_costs == 25000
        assert result.documentation_costs == 10000
        assert result.product_cost > 0
        assert result.buffer > 0
        assert result.total > 0
        assert result.currency == "INR"
        
        # Verify total is sum of components
        expected_total = (
            result.product_cost +
            result.certification_costs +
            result.logistics_costs +
            result.documentation_costs +
            result.buffer
        )
        assert abs(result.total - expected_total) < 0.01
    
    def test_calculate_working_capital_with_buffer(self, finance_module, mock_db_session, sample_report):
        """Test that buffer is 15% of subtotal."""
        # Setup mock
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Calculate working capital
        result = finance_module.calculate_working_capital(sample_report.id)
        
        # Calculate expected buffer
        subtotal = (
            result.product_cost +
            result.certification_costs +
            result.logistics_costs +
            result.documentation_costs
        )
        expected_buffer = subtotal * 0.15
        
        # Verify buffer is 15%
        assert abs(result.buffer - expected_buffer) < 0.01
    
    def test_calculate_working_capital_report_not_found(self, finance_module, mock_db_session):
        """Test error handling when report not found."""
        # Setup mock to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Report .* not found"):
            finance_module.calculate_working_capital("nonexistent_id")
    
    def test_product_cost_estimation(self, finance_module, mock_db_session, sample_report):
        """Test product cost estimation from monthly volume and price range."""
        # Setup mock
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Calculate working capital
        result = finance_module.calculate_working_capital(sample_report.id)
        
        # Product cost should be based on monthly volume * average price
        # Price range: ₹500-₹1500, average = ₹1000
        # Monthly volume: 1000
        # Expected: 1000 * 1000 = 1,000,000
        assert result.product_cost == 1000000.0


class TestPreShipmentCredit:
    """Test pre-shipment credit eligibility assessment."""
    
    def test_assess_credit_eligibility_small_company(self, finance_module, mock_db_session, sample_report):
        """Test credit eligibility for small company."""
        # Setup mock
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Assess credit eligibility
        result = finance_module.assess_credit_eligibility(sample_report.id, order_value=200000)
        
        # Assertions
        assert isinstance(result, PreShipmentCredit)
        assert result.eligible is True
        assert result.interest_rate == 8.0  # Small company rate
        assert result.tenure_days == 90
        assert len(result.requirements) > 0
        
        # Credit amount should be 75% of order value for small companies
        expected_amount = 200000 * 0.75
        assert result.estimated_amount == expected_amount
    
    def test_assess_credit_eligibility_micro_company(self, finance_module, mock_db_session, sample_report):
        """Test credit eligibility for micro company."""
        # Modify sample report to be micro
        sample_report.company_size = "Micro"
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Assess credit eligibility
        result = finance_module.assess_credit_eligibility(sample_report.id, order_value=100000)
        
        # Assertions
        assert result.eligible is True
        assert result.interest_rate == 7.5  # Micro company rate (lower)
        
        # Credit amount should be 80% of order value for micro companies
        expected_amount = 100000 * 0.80
        assert result.estimated_amount == expected_amount
    
    def test_assess_credit_eligibility_medium_company(self, finance_module, mock_db_session, sample_report):
        """Test credit eligibility for medium company."""
        # Modify sample report to be medium
        sample_report.company_size = "Medium"
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Assess credit eligibility
        result = finance_module.assess_credit_eligibility(sample_report.id, order_value=500000)
        
        # Assertions
        assert result.eligible is True
        assert result.interest_rate == 8.5  # Medium company rate (higher)
        
        # Credit amount should be 70% of order value for medium companies
        expected_amount = 500000 * 0.70
        assert result.estimated_amount == expected_amount
        
        # Medium companies should have additional requirements
        assert any("financial statements" in req.lower() for req in result.requirements)


class TestRoDTEPBenefit:
    """Test RoDTEP benefit calculation."""
    
    def test_calculate_rodtep_benefit_known_hs_code(self, finance_module):
        """Test RoDTEP calculation for known HS code."""
        # Calculate RoDTEP for turmeric (0910.30)
        result = finance_module.calculate_rodtep_benefit(
            hs_code="0910.30",
            destination="United States",
            fob_value=200000
        )
        
        # Assertions
        assert isinstance(result, RoDTEPBenefit)
        assert result.hs_code == "0910.30"
        assert result.rate_percentage == 2.5  # Known rate for turmeric
        assert result.estimated_amount == 200000 * 0.025
        assert result.currency == "INR"
    
    def test_calculate_rodtep_benefit_prefix_match(self, finance_module):
        """Test RoDTEP calculation with prefix match."""
        # Calculate RoDTEP for T-shirts (6109.10.00 should match 6109)
        result = finance_module.calculate_rodtep_benefit(
            hs_code="6109.10.00",
            destination="United Kingdom",
            fob_value=300000
        )
        
        # Assertions
        assert result.hs_code == "6109.10.00"
        assert result.rate_percentage == 4.3  # Rate for 6109
        assert result.estimated_amount == 300000 * 0.043
    
    def test_calculate_rodtep_benefit_default_rate(self, finance_module):
        """Test RoDTEP calculation with default rate for unknown HS code."""
        # Calculate RoDTEP for unknown HS code
        result = finance_module.calculate_rodtep_benefit(
            hs_code="9999.99",
            destination="Germany",
            fob_value=150000
        )
        
        # Assertions
        assert result.hs_code == "9999.99"
        assert result.rate_percentage == 1.5  # Default rate
        assert result.estimated_amount == 150000 * 0.015


class TestGSTRefund:
    """Test GST refund estimation."""
    
    def test_estimate_gst_refund_with_gst_paid(self, finance_module):
        """Test GST refund estimation with known GST paid."""
        result = finance_module.estimate_gst_refund(
            export_value=200000,
            gst_paid=36000
        )
        
        # Assertions
        assert isinstance(result, GSTRefund)
        assert result.estimated_amount == 36000
        assert result.timeline_days == 45
        assert len(result.requirements) > 0
        assert any("GST LUT" in req for req in result.requirements)
    
    def test_estimate_gst_refund_without_gst_paid(self, finance_module):
        """Test GST refund estimation without GST paid (estimated at 18%)."""
        result = finance_module.estimate_gst_refund(export_value=200000)
        
        # Assertions
        # Should estimate GST at 18% of export value
        expected_gst = 200000 * 0.18
        assert result.estimated_amount == expected_gst
        assert result.timeline_days == 45


class TestCashFlowTimeline:
    """Test cash flow timeline generation."""
    
    def test_generate_cash_flow_timeline(self, finance_module, mock_db_session, sample_report):
        """Test cash flow timeline generation."""
        # Setup mock
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Generate timeline
        result = finance_module.generate_cash_flow_timeline(sample_report.id)
        
        # Assertions
        assert isinstance(result, CashFlowTimeline)
        assert len(result.events) > 0
        assert result.liquidity_gap is not None
        
        # Verify events are sorted by date
        dates = [event.event_date for event in result.events]
        assert dates == sorted(dates)
        
        # Verify we have both expense and income events
        expense_events = [e for e in result.events if e.event_type == CashFlowEventType.EXPENSE]
        income_events = [e for e in result.events if e.event_type == CashFlowEventType.INCOME]
        assert len(expense_events) > 0
        assert len(income_events) > 0
    
    def test_cash_flow_events_categories(self, finance_module, mock_db_session, sample_report):
        """Test that cash flow events cover all major categories."""
        # Setup mock
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Generate timeline
        result = finance_module.generate_cash_flow_timeline(sample_report.id)
        
        # Check for expected categories
        categories = {event.category for event in result.events}
        expected_categories = {
            "Documentation",
            "Certification",
            "Production",
            "Logistics",
            "Customer Payment",
            "RoDTEP Benefit",
            "GST Refund"
        }
        
        # Should have most expected categories
        assert len(categories.intersection(expected_categories)) >= 5
    
    def test_liquidity_gap_identification(self, finance_module, mock_db_session, sample_report):
        """Test liquidity gap identification."""
        # Setup mock
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Generate timeline
        result = finance_module.generate_cash_flow_timeline(sample_report.id)
        
        # Assertions on liquidity gap
        gap = result.liquidity_gap
        assert gap.start_date <= gap.end_date
        assert gap.amount > 0
        
        # Gap should start from today or near today
        today = date.today()
        assert abs((gap.start_date - today).days) <= 7


class TestFinancingOptions:
    """Test financing options suggestion."""
    
    def test_suggest_financing_options_small_company(self, finance_module, mock_db_session, sample_report):
        """Test financing options for small company."""
        # Setup mock
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Suggest financing options
        result = finance_module.suggest_financing_options(
            report_id=sample_report.id,
            liquidity_gap=150000
        )
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Should include pre-shipment credit
        assert any("Pre-shipment credit" in opt.type for opt in result)
        
        # Should include export credit guarantee for small companies
        assert any("Export Credit Guarantee" in opt.type for opt in result)
    
    def test_suggest_financing_options_micro_company(self, finance_module, mock_db_session, sample_report):
        """Test financing options for micro company."""
        # Modify sample report to be micro
        sample_report.company_size = "Micro"
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Suggest financing options
        result = finance_module.suggest_financing_options(
            report_id=sample_report.id,
            liquidity_gap=100000
        )
        
        # Assertions
        # Should include MUDRA loan for micro enterprises
        assert any("MUDRA" in opt.type for opt in result)
    
    def test_suggest_financing_options_medium_company(self, finance_module, mock_db_session, sample_report):
        """Test financing options for medium company."""
        # Modify sample report to be medium
        sample_report.company_size = "Medium"
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Suggest financing options
        result = finance_module.suggest_financing_options(
            report_id=sample_report.id,
            liquidity_gap=500000
        )
        
        # Assertions
        # Should NOT include export credit guarantee for medium companies
        assert not any("Export Credit Guarantee" in opt.type for opt in result)
        
        # Should include working capital loan
        assert any("Working capital" in opt.type for opt in result)


class TestCompleteAnalysis:
    """Test complete finance analysis generation."""
    
    def test_generate_complete_analysis(self, finance_module, mock_db_session, sample_report):
        """Test complete finance analysis generation."""
        # Setup mock
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Generate complete analysis
        result = finance_module.generate_complete_analysis(sample_report.id)
        
        # Assertions
        assert isinstance(result, FinanceAnalysis)
        assert result.report_id == sample_report.id
        
        # Verify all components are present
        assert result.working_capital is not None
        assert result.pre_shipment_credit is not None
        assert result.rodtep_benefit is not None
        assert result.gst_refund is not None
        assert result.cash_flow_timeline is not None
        assert result.currency_hedging is not None
        assert len(result.financing_options) > 0
        
        # Verify working capital
        assert isinstance(result.working_capital, WorkingCapitalAnalysis)
        assert result.working_capital.total > 0
        
        # Verify cash flow timeline
        assert isinstance(result.cash_flow_timeline, CashFlowTimeline)
        assert len(result.cash_flow_timeline.events) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_working_capital_with_zero_costs(self, finance_module, mock_db_session, sample_report):
        """Test working capital calculation with zero costs."""
        # Modify report to have zero costs
        sample_report.report_data = {
            "costs": {
                "certifications": 0,
                "logistics": 0,
                "documentation": 0,
                "total": 0
            }
        }
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Calculate working capital
        result = finance_module.calculate_working_capital(sample_report.id)
        
        # Should still calculate product cost and buffer
        assert result.total > 0
        assert result.product_cost > 0
        assert result.buffer > 0
    
    def test_product_cost_estimation_no_volume(self, finance_module, mock_db_session, sample_report):
        """Test product cost estimation with no monthly volume."""
        # Modify report to have no volume
        sample_report.monthly_volume = None
        sample_report.price_range = None
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Calculate working capital
        result = finance_module.calculate_working_capital(sample_report.id)
        
        # Should use default product cost
        assert result.product_cost == 100000.0
    
    def test_currency_hedging_small_export(self, finance_module):
        """Test currency hedging for small export value."""
        result = finance_module.generate_currency_hedging_advice(
            export_value=500000,  # 5 lakh (below 10 lakh threshold)
            destination="United States"
        )
        
        # Should not recommend hedging for small exports
        assert result.recommended is False
        assert len(result.strategies) > 0
    
    def test_currency_hedging_large_export(self, finance_module):
        """Test currency hedging for large export value."""
        result = finance_module.generate_currency_hedging_advice(
            export_value=2000000,  # 20 lakh (above 10 lakh threshold)
            destination="United States"
        )
        
        # Should recommend hedging for large exports
        assert result.recommended is True
        assert len(result.strategies) > 0
        assert result.estimated_savings > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
