"""
Test suite for Finance API Router

Tests the finance API endpoints to ensure they work correctly with:
1. GET /api/finance/analysis/{report_id} - Complete finance analysis
2. POST /api/finance/rodtep-calculator - RoDTEP benefit calculation
3. POST /api/finance/working-capital - Working capital calculation

This is a comprehensive integration test for the finance module.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import date, timedelta

from main import app
from models.finance import (
    FinanceAnalysis,
    WorkingCapitalAnalysis,
    PreShipmentCredit,
    RoDTEPBenefit,
    GSTRefund,
    CashFlowTimeline,
    CashFlowEvent,
    LiquidityGap,
    CurrencyHedging,
    FinancingOption
)
from models.enums import CashFlowEventType


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_working_capital():
    """Create a mock working capital analysis."""
    return WorkingCapitalAnalysis(
        product_cost=100000.0,
        certification_costs=50000.0,
        logistics_costs=25000.0,
        documentation_costs=10000.0,
        buffer=27750.0,
        total=212750.0,
        currency="INR"
    )


@pytest.fixture
def mock_pre_shipment_credit():
    """Create a mock pre-shipment credit assessment."""
    return PreShipmentCredit(
        eligible=True,
        estimated_amount=150000.0,
        interest_rate=8.5,
        tenure_days=90,
        requirements=[
            "Valid export order",
            "Company registration",
            "Bank account with export credit facility"
        ]
    )


@pytest.fixture
def mock_rodtep_benefit():
    """Create a mock RoDTEP benefit."""
    return RoDTEPBenefit(
        hs_code="0910.30",
        rate_percentage=2.5,
        estimated_amount=5000.0,
        currency="INR"
    )


@pytest.fixture
def mock_gst_refund():
    """Create a mock GST refund."""
    return GSTRefund(
        estimated_amount=18000.0,
        timeline_days=45,
        requirements=[
            "GST LUT filed",
            "Shipping bill filed",
            "Bank realization certificate"
        ]
    )


@pytest.fixture
def mock_cash_flow_timeline():
    """Create a mock cash flow timeline."""
    start_date = date.today()
    
    events = [
        CashFlowEvent(
            event_date=start_date + timedelta(days=3),
            event_type=CashFlowEventType.EXPENSE,
            category="Documentation",
            amount=-10000.0,
            description="Export documentation preparation"
        ),
        CashFlowEvent(
            event_date=start_date + timedelta(days=90),
            event_type=CashFlowEventType.INCOME,
            category="Customer Payment",
            amount=240000.0,
            description="Customer payment received"
        )
    ]
    
    liquidity_gap = LiquidityGap(
        start_date=start_date,
        end_date=start_date + timedelta(days=90),
        amount=212750.0
    )
    
    return CashFlowTimeline(
        events=events,
        liquidity_gap=liquidity_gap
    )


@pytest.fixture
def mock_currency_hedging():
    """Create a mock currency hedging recommendation."""
    return CurrencyHedging(
        recommended=True,
        strategies=[
            "Forward contract for 50-70% of order value",
            "Currency options for remaining 30-50%"
        ],
        estimated_savings=6000.0
    )


@pytest.fixture
def mock_financing_options():
    """Create mock financing options."""
    return [
        FinancingOption(
            type="Pre-shipment credit",
            provider="State Bank of India",
            amount=150000.0,
            interest_rate=8.5,
            tenure="90 days",
            eligibility="Valid export order, company registration"
        ),
        FinancingOption(
            type="Working capital loan",
            provider="Public/Private sector banks",
            amount=212750.0,
            interest_rate=9.5,
            tenure="12 months",
            eligibility="Business vintage of 2+ years"
        )
    ]


@pytest.fixture
def mock_finance_analysis(
    mock_working_capital,
    mock_pre_shipment_credit,
    mock_rodtep_benefit,
    mock_gst_refund,
    mock_cash_flow_timeline,
    mock_currency_hedging,
    mock_financing_options
):
    """Create a complete mock finance analysis."""
    return FinanceAnalysis(
        report_id="rpt_test123456",
        working_capital=mock_working_capital,
        pre_shipment_credit=mock_pre_shipment_credit,
        rodtep_benefit=mock_rodtep_benefit,
        gst_refund=mock_gst_refund,
        cash_flow_timeline=mock_cash_flow_timeline,
        currency_hedging=mock_currency_hedging,
        financing_options=mock_financing_options
    )


@pytest.fixture
def mock_db_report():
    """Create a mock database report."""
    mock_report = MagicMock()
    mock_report.id = uuid.uuid4()
    mock_report.product_name = "Organic Turmeric Powder"
    mock_report.destination_country = "United States"
    mock_report.hs_code = "0910.30"
    mock_report.business_type = "Manufacturing"
    mock_report.company_size = "Small"
    mock_report.monthly_volume = 1000
    mock_report.price_range = "₹100-₹200"
    mock_report.report_data = {
        "costs": {
            "certifications": 50000.0,
            "logistics": 25000.0,
            "documentation": 10000.0
        }
    }
    return mock_report


# Test GET /api/finance/analysis/{report_id}


def test_get_finance_analysis_success(client, mock_finance_analysis, mock_db_report):
    """Test successful finance analysis retrieval."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        mock_db.return_value = mock_session
        
        with patch('routers.finance.FinanceModule') as mock_finance_module:
            mock_instance = Mock()
            mock_instance.generate_complete_analysis.return_value = mock_finance_analysis
            mock_finance_module.return_value = mock_instance
            
            response = client.get("/api/finance/analysis/rpt_test123456")
            
            assert response.status_code == 200
            data = response.json()
            assert data["report_id"] == "rpt_test123456"
            assert data["working_capital"]["total"] == 212750.0
            assert data["pre_shipment_credit"]["eligible"] is True
            assert data["rodtep_benefit"]["rate_percentage"] == 2.5
            assert data["gst_refund"]["estimated_amount"] == 18000.0
            assert len(data["financing_options"]) == 2


def test_get_finance_analysis_report_not_found(client):
    """Test finance analysis with non-existent report."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = mock_session
        
        response = client.get("/api/finance/analysis/rpt_00000000000000000000000000000000")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_get_finance_analysis_invalid_report_id(client):
    """Test finance analysis with invalid report ID format."""
    response = client.get("/api/finance/analysis/invalid-id")
    
    assert response.status_code == 400
    assert "Invalid report ID format" in response.json()["detail"]


def test_get_finance_analysis_service_error(client, mock_db_report):
    """Test finance analysis when service raises an error."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        mock_db.return_value = mock_session
        
        with patch('routers.finance.FinanceModule') as mock_finance_module:
            mock_instance = Mock()
            mock_instance.generate_complete_analysis.side_effect = Exception("Service error")
            mock_finance_module.return_value = mock_instance
            
            response = client.get("/api/finance/analysis/rpt_test123456")
            
            assert response.status_code == 500
            assert "error occurred" in response.json()["detail"]


# Test POST /api/finance/rodtep-calculator


def test_calculate_rodtep_success(client, mock_rodtep_benefit):
    """Test successful RoDTEP calculation."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        with patch('routers.finance.FinanceModule') as mock_finance_module:
            mock_instance = Mock()
            mock_instance.calculate_rodtep_benefit.return_value = mock_rodtep_benefit
            mock_finance_module.return_value = mock_instance
            
            response = client.post(
                "/api/finance/rodtep-calculator",
                json={
                    "hs_code": "0910.30",
                    "destination": "United States",
                    "fob_value": 200000.0
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["hs_code"] == "0910.30"
            assert data["rate_percentage"] == 2.5
            assert data["estimated_amount"] == 5000.0
            assert data["currency"] == "INR"


def test_calculate_rodtep_with_dots_in_hs_code(client, mock_rodtep_benefit):
    """Test RoDTEP calculation with dots in HS code."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        with patch('routers.finance.FinanceModule') as mock_finance_module:
            mock_instance = Mock()
            mock_instance.calculate_rodtep_benefit.return_value = mock_rodtep_benefit
            mock_finance_module.return_value = mock_instance
            
            response = client.post(
                "/api/finance/rodtep-calculator",
                json={
                    "hs_code": "09.10.30",
                    "destination": "United States",
                    "fob_value": 200000.0
                }
            )
            
            assert response.status_code == 200
            # Verify that dots were removed
            mock_instance.calculate_rodtep_benefit.assert_called_once()
            call_args = mock_instance.calculate_rodtep_benefit.call_args
            assert call_args[1]["hs_code"] == "091030"


def test_calculate_rodtep_missing_fields(client):
    """Test RoDTEP calculation with missing required fields."""
    response = client.post(
        "/api/finance/rodtep-calculator",
        json={
            "hs_code": "0910.30"
            # Missing destination and fob_value
        }
    )
    
    assert response.status_code == 422


def test_calculate_rodtep_negative_fob_value(client):
    """Test RoDTEP calculation with negative FOB value."""
    response = client.post(
        "/api/finance/rodtep-calculator",
        json={
            "hs_code": "0910.30",
            "destination": "United States",
            "fob_value": -100000.0
        }
    )
    
    assert response.status_code == 422


def test_calculate_rodtep_zero_fob_value(client):
    """Test RoDTEP calculation with zero FOB value."""
    response = client.post(
        "/api/finance/rodtep-calculator",
        json={
            "hs_code": "0910.30",
            "destination": "United States",
            "fob_value": 0.0
        }
    )
    
    assert response.status_code == 422


def test_calculate_rodtep_empty_hs_code(client):
    """Test RoDTEP calculation with empty HS code."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        response = client.post(
            "/api/finance/rodtep-calculator",
            json={
                "hs_code": "   ",
                "destination": "United States",
                "fob_value": 200000.0
            }
        )
        
        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"]


def test_calculate_rodtep_service_error(client):
    """Test RoDTEP calculation when service raises an error."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        with patch('routers.finance.FinanceModule') as mock_finance_module:
            mock_instance = Mock()
            mock_instance.calculate_rodtep_benefit.side_effect = Exception("Service error")
            mock_finance_module.return_value = mock_instance
            
            response = client.post(
                "/api/finance/rodtep-calculator",
                json={
                    "hs_code": "0910.30",
                    "destination": "United States",
                    "fob_value": 200000.0
                }
            )
            
            assert response.status_code == 500
            assert "error occurred" in response.json()["detail"]


# Test POST /api/finance/working-capital


def test_calculate_working_capital_success(client, mock_working_capital, mock_db_report):
    """Test successful working capital calculation."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        mock_db.return_value = mock_session
        
        with patch('routers.finance.FinanceModule') as mock_finance_module:
            mock_instance = Mock()
            mock_instance.calculate_working_capital.return_value = mock_working_capital
            mock_finance_module.return_value = mock_instance
            
            response = client.post(
                "/api/finance/working-capital",
                json={
                    "report_id": "rpt_test123456"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["product_cost"] == 100000.0
            assert data["certification_costs"] == 50000.0
            assert data["logistics_costs"] == 25000.0
            assert data["documentation_costs"] == 10000.0
            assert data["buffer"] == 27750.0
            assert data["total"] == 212750.0
            assert data["currency"] == "INR"


def test_calculate_working_capital_report_not_found(client):
    """Test working capital calculation with non-existent report."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = mock_session
        
        response = client.post(
            "/api/finance/working-capital",
            json={
                "report_id": "rpt_00000000000000000000000000000000"
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_calculate_working_capital_invalid_report_id(client):
    """Test working capital calculation with invalid report ID format."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        response = client.post(
            "/api/finance/working-capital",
            json={
                "report_id": "invalid-id"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid report ID format" in response.json()["detail"]


def test_calculate_working_capital_missing_report_id(client):
    """Test working capital calculation with missing report_id."""
    response = client.post(
        "/api/finance/working-capital",
        json={}
    )
    
    assert response.status_code == 422


def test_calculate_working_capital_service_error(client, mock_db_report):
    """Test working capital calculation when service raises an error."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        mock_db.return_value = mock_session
        
        with patch('routers.finance.FinanceModule') as mock_finance_module:
            mock_instance = Mock()
            mock_instance.calculate_working_capital.side_effect = Exception("Service error")
            mock_finance_module.return_value = mock_instance
            
            response = client.post(
                "/api/finance/working-capital",
                json={
                    "report_id": "rpt_test123456"
                }
            )
            
            assert response.status_code == 500
            assert "error occurred" in response.json()["detail"]


# Integration tests


def test_complete_finance_workflow(client, mock_finance_analysis, mock_db_report):
    """Test complete finance workflow: analysis -> RoDTEP -> working capital."""
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
        mock_db.return_value = mock_session
        
        with patch('routers.finance.FinanceModule') as mock_finance_module:
            mock_instance = Mock()
            mock_instance.generate_complete_analysis.return_value = mock_finance_analysis
            mock_instance.calculate_rodtep_benefit.return_value = mock_finance_analysis.rodtep_benefit
            mock_instance.calculate_working_capital.return_value = mock_finance_analysis.working_capital
            mock_finance_module.return_value = mock_instance
            
            # Step 1: Get complete analysis
            response1 = client.get("/api/finance/analysis/rpt_test123456")
            assert response1.status_code == 200
            analysis = response1.json()
            
            # Step 2: Calculate RoDTEP separately
            response2 = client.post(
                "/api/finance/rodtep-calculator",
                json={
                    "hs_code": analysis["rodtep_benefit"]["hs_code"],
                    "destination": "United States",
                    "fob_value": 200000.0
                }
            )
            assert response2.status_code == 200
            rodtep = response2.json()
            assert rodtep["rate_percentage"] == analysis["rodtep_benefit"]["rate_percentage"]
            
            # Step 3: Calculate working capital separately
            response3 = client.post(
                "/api/finance/working-capital",
                json={
                    "report_id": "rpt_test123456"
                }
            )
            assert response3.status_code == 200
            working_capital = response3.json()
            assert working_capital["total"] == analysis["working_capital"]["total"]


def test_rodtep_calculation_different_hs_codes(client):
    """Test RoDTEP calculation with different HS codes."""
    test_cases = [
        ("0910.30", 2.5),  # Turmeric
        ("6109", 4.3),     # T-shirts
        ("9405", 3.8),     # LED lights
        ("3304", 2.1),     # Beauty products
        ("9999", 1.5),     # Default rate
    ]
    
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        for hs_code, expected_rate in test_cases:
            with patch('routers.finance.FinanceModule') as mock_finance_module:
                mock_instance = Mock()
                mock_instance.calculate_rodtep_benefit.return_value = RoDTEPBenefit(
                    hs_code=hs_code,
                    rate_percentage=expected_rate,
                    estimated_amount=200000.0 * (expected_rate / 100),
                    currency="INR"
                )
                mock_finance_module.return_value = mock_instance
                
                response = client.post(
                    "/api/finance/rodtep-calculator",
                    json={
                        "hs_code": hs_code,
                        "destination": "United States",
                        "fob_value": 200000.0
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["rate_percentage"] == expected_rate


def test_working_capital_with_different_company_sizes(client, mock_db_report):
    """Test working capital calculation for different company sizes."""
    company_sizes = ["Micro", "Small", "Medium"]
    
    with patch('routers.finance.get_db') as mock_db:
        mock_session = MagicMock()
        
        for company_size in company_sizes:
            mock_db_report.company_size = company_size
            mock_session.query.return_value.filter.return_value.first.return_value = mock_db_report
            mock_db.return_value = mock_session
            
            with patch('routers.finance.FinanceModule') as mock_finance_module:
                mock_instance = Mock()
                mock_instance.calculate_working_capital.return_value = WorkingCapitalAnalysis(
                    product_cost=100000.0,
                    certification_costs=50000.0,
                    logistics_costs=25000.0,
                    documentation_costs=10000.0,
                    buffer=27750.0,
                    total=212750.0,
                    currency="INR"
                )
                mock_finance_module.return_value = mock_instance
                
                response = client.post(
                    "/api/finance/working-capital",
                    json={
                        "report_id": "rpt_test123456"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["total"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
