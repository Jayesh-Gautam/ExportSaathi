"""
Unit tests for Logistics API Router

Tests the logistics router endpoints including:
- POST /api/logistics/risk-analysis
- POST /api/logistics/rms-probability
- POST /api/logistics/freight-estimate
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

# Import only the logistics router
from routers.logistics import router
from models.logistics import (
    LogisticsRiskAnalysis,
    LogisticsRiskRequest,
    LCLFCLComparison,
    ShippingOption,
    RMSProbability,
    RouteAnalysis,
    Route,
    FreightEstimate,
    InsuranceRecommendation
)
from models.enums import ShippingMode, FreightMode, RiskSeverity

# Create a minimal FastAPI app for testing
app = FastAPI()
app.include_router(router, prefix="/api/logistics")


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_logistics_risk_analysis():
    """Create a mock logistics risk analysis."""
    return LogisticsRiskAnalysis(
        lcl_fcl_comparison=LCLFCLComparison(
            recommendation=ShippingMode.LCL,
            lcl=ShippingOption(
                cost=15000.0,
                risk_level=RiskSeverity.MEDIUM,
                pros=["Lower cost for small volumes", "Flexible scheduling"],
                cons=["Higher risk of damage", "Longer customs clearance"]
            ),
            fcl=ShippingOption(
                cost=3000.0,
                risk_level=RiskSeverity.LOW,
                pros=["Lower risk of damage", "Faster customs clearance"],
                cons=["Higher upfront cost", "Need sufficient volume"]
            )
        ),
        rms_probability=RMSProbability(
            probability_percentage=35.5,
            risk_level=RiskSeverity.MEDIUM,
            risk_factors=["High-risk product category: food"],
            red_flag_keywords=["powder", "organic"],
            mitigation_tips=["Provide detailed product documentation"]
        ),
        route_analysis=RouteAnalysis(
            recommended_route="Mumbai to New York via Suez Canal",
            routes=[
                Route(
                    name="Mumbai to New York via Suez Canal",
                    transit_time_days=25,
                    delay_risk=RiskSeverity.MEDIUM,
                    geopolitical_factors=["Congestion during peak seasons"],
                    cost_estimate=1600.0
                )
            ]
        ),
        freight_estimate=FreightEstimate(
            sea_freight=1000.0,
            air_freight=7000.0,
            recommended_mode=FreightMode.SEA,
            currency="USD"
        ),
        insurance_recommendation=InsuranceRecommendation(
            recommended_coverage=22000.0,
            premium_estimate=110.0,
            coverage_type="All-risk marine cargo insurance"
        )
    )


@pytest.fixture
def mock_rms_probability():
    """Create a mock RMS probability."""
    return RMSProbability(
        probability_percentage=35.5,
        risk_level=RiskSeverity.MEDIUM,
        risk_factors=["High-risk product category: food", "Red flag keywords detected: powder, organic"],
        red_flag_keywords=["powder", "organic"],
        mitigation_tips=[
            "Provide detailed and accurate product documentation",
            "Use specific product descriptions (avoid vague terms)",
            "Include test certificates and quality reports"
        ]
    )


@pytest.fixture
def mock_freight_estimate():
    """Create a mock freight estimate."""
    return FreightEstimate(
        sea_freight=1000.0,
        air_freight=7000.0,
        recommended_mode=FreightMode.SEA,
        currency="USD"
    )


# Test POST /api/logistics/risk-analysis

def test_analyze_logistics_risks_success(client, mock_logistics_risk_analysis):
    """Test successful logistics risk analysis."""
    with patch('routers.logistics.LogisticsRiskShield') as mock_service:
        # Setup mock
        mock_instance = Mock()
        mock_instance.analyze_risks.return_value = mock_logistics_risk_analysis
        mock_service.return_value = mock_instance
        
        # Make request
        response = client.post(
            "/api/logistics/risk-analysis",
            json={
                "product_type": "Turmeric powder",
                "hs_code": "0910.30",
                "volume": 10.0,
                "value": 20000.0,
                "destination_country": "United States",
                "product_description": "Organic turmeric powder for food use"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "lcl_fcl_comparison" in data
        assert "rms_probability" in data
        assert "route_analysis" in data
        assert "freight_estimate" in data
        assert "insurance_recommendation" in data
        assert data["rms_probability"]["probability_percentage"] == 35.5
        assert data["freight_estimate"]["recommended_mode"] == "sea"


def test_analyze_logistics_risks_empty_product_type(client):
    """Test logistics risk analysis with empty product type."""
    response = client.post(
        "/api/logistics/risk-analysis",
        json={
            "product_type": "   ",
            "hs_code": "0910.30",
            "volume": 10.0,
            "value": 20000.0,
            "destination_country": "United States",
            "product_description": "Organic turmeric powder"
        }
    )
    
    assert response.status_code == 400
    assert "Product type cannot be empty" in response.json()["detail"]


def test_analyze_logistics_risks_empty_hs_code(client):
    """Test logistics risk analysis with empty HS code."""
    response = client.post(
        "/api/logistics/risk-analysis",
        json={
            "product_type": "Turmeric powder",
            "hs_code": "   ",
            "volume": 10.0,
            "value": 20000.0,
            "destination_country": "United States",
            "product_description": "Organic turmeric powder"
        }
    )
    
    assert response.status_code == 400
    assert "HS code cannot be empty" in response.json()["detail"]


def test_analyze_logistics_risks_empty_destination(client):
    """Test logistics risk analysis with empty destination country."""
    response = client.post(
        "/api/logistics/risk-analysis",
        json={
            "product_type": "Turmeric powder",
            "hs_code": "0910.30",
            "volume": 10.0,
            "value": 20000.0,
            "destination_country": "   ",
            "product_description": "Organic turmeric powder"
        }
    )
    
    assert response.status_code == 400
    assert "Destination country cannot be empty" in response.json()["detail"]


def test_analyze_logistics_risks_empty_description(client):
    """Test logistics risk analysis with empty product description."""
    response = client.post(
        "/api/logistics/risk-analysis",
        json={
            "product_type": "Turmeric powder",
            "hs_code": "0910.30",
            "volume": 10.0,
            "value": 20000.0,
            "destination_country": "United States",
            "product_description": "   "
        }
    )
    
    assert response.status_code == 400
    assert "Product description cannot be empty" in response.json()["detail"]


def test_analyze_logistics_risks_negative_volume(client):
    """Test logistics risk analysis with negative volume."""
    response = client.post(
        "/api/logistics/risk-analysis",
        json={
            "product_type": "Turmeric powder",
            "hs_code": "0910.30",
            "volume": -10.0,
            "value": 20000.0,
            "destination_country": "United States",
            "product_description": "Organic turmeric powder"
        }
    )
    
    assert response.status_code == 422


def test_analyze_logistics_risks_negative_value(client):
    """Test logistics risk analysis with negative value."""
    response = client.post(
        "/api/logistics/risk-analysis",
        json={
            "product_type": "Turmeric powder",
            "hs_code": "0910.30",
            "volume": 10.0,
            "value": -20000.0,
            "destination_country": "United States",
            "product_description": "Organic turmeric powder"
        }
    )
    
    assert response.status_code == 422


def test_analyze_logistics_risks_service_error(client):
    """Test logistics risk analysis when service raises an error."""
    with patch('routers.logistics.LogisticsRiskShield') as mock_service:
        # Setup mock to raise exception
        mock_instance = Mock()
        mock_instance.analyze_risks.side_effect = Exception("Service error")
        mock_service.return_value = mock_instance
        
        # Make request
        response = client.post(
            "/api/logistics/risk-analysis",
            json={
                "product_type": "Turmeric powder",
                "hs_code": "0910.30",
                "volume": 10.0,
                "value": 20000.0,
                "destination_country": "United States",
                "product_description": "Organic turmeric powder"
            }
        )
        
        # Assertions
        assert response.status_code == 500
        assert "error occurred while analyzing logistics risks" in response.json()["detail"]


# Test POST /api/logistics/rms-probability

def test_calculate_rms_probability_success(client, mock_rms_probability):
    """Test successful RMS probability calculation."""
    with patch('routers.logistics.LogisticsRiskShield') as mock_service:
        # Setup mock
        mock_instance = Mock()
        mock_instance.estimate_rms_probability.return_value = mock_rms_probability
        mock_service.return_value = mock_instance
        
        # Make request
        response = client.post(
            "/api/logistics/rms-probability",
            json={
                "product_type": "Turmeric powder",
                "hs_code": "0910.30",
                "product_description": "Organic turmeric powder for food use"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["probability_percentage"] == 35.5
        assert data["risk_level"] == "medium"
        assert "powder" in data["red_flag_keywords"]
        assert "organic" in data["red_flag_keywords"]
        assert len(data["mitigation_tips"]) > 0


def test_calculate_rms_probability_empty_product_type(client):
    """Test RMS probability calculation with empty product type."""
    response = client.post(
        "/api/logistics/rms-probability",
        json={
            "product_type": "   ",
            "hs_code": "0910.30",
            "product_description": "Organic turmeric powder"
        }
    )
    
    assert response.status_code == 400
    assert "Product type cannot be empty" in response.json()["detail"]


def test_calculate_rms_probability_empty_hs_code(client):
    """Test RMS probability calculation with empty HS code."""
    response = client.post(
        "/api/logistics/rms-probability",
        json={
            "product_type": "Turmeric powder",
            "hs_code": "",
            "product_description": "Organic turmeric powder"
        }
    )
    
    # Pydantic validation returns 422 for empty string that doesn't meet min_length
    assert response.status_code == 422


def test_calculate_rms_probability_empty_description(client):
    """Test RMS probability calculation with empty product description."""
    response = client.post(
        "/api/logistics/rms-probability",
        json={
            "product_type": "Turmeric powder",
            "hs_code": "0910.30",
            "product_description": "   "
        }
    )
    
    assert response.status_code == 400
    assert "Product description cannot be empty" in response.json()["detail"]


def test_calculate_rms_probability_high_risk_product(client):
    """Test RMS probability calculation with high-risk product."""
    with patch('routers.logistics.LogisticsRiskShield') as mock_service:
        # Setup mock for high-risk product
        mock_instance = Mock()
        mock_instance.estimate_rms_probability.return_value = RMSProbability(
            probability_percentage=65.0,
            risk_level=RiskSeverity.HIGH,
            risk_factors=["High-risk product category: pharmaceutical", "Red flag keywords detected: chemical, powder"],
            red_flag_keywords=["chemical", "powder"],
            mitigation_tips=["Obtain pre-clearance certifications", "Work with experienced customs broker"]
        )
        mock_service.return_value = mock_instance
        
        # Make request
        response = client.post(
            "/api/logistics/rms-probability",
            json={
                "product_type": "pharmaceutical",
                "hs_code": "3004.90",
                "product_description": "Chemical powder for pharmaceutical use"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["probability_percentage"] == 65.0
        assert data["risk_level"] == "high"
        assert "chemical" in data["red_flag_keywords"]


def test_calculate_rms_probability_service_error(client):
    """Test RMS probability calculation when service raises an error."""
    with patch('routers.logistics.LogisticsRiskShield') as mock_service:
        # Setup mock to raise exception
        mock_instance = Mock()
        mock_instance.estimate_rms_probability.side_effect = Exception("Service error")
        mock_service.return_value = mock_instance
        
        # Make request
        response = client.post(
            "/api/logistics/rms-probability",
            json={
                "product_type": "Turmeric powder",
                "hs_code": "0910.30",
                "product_description": "Organic turmeric powder"
            }
        )
        
        # Assertions
        assert response.status_code == 500
        assert "error occurred while calculating RMS probability" in response.json()["detail"]


# Test POST /api/logistics/freight-estimate

def test_estimate_freight_success(client, mock_freight_estimate):
    """Test successful freight cost estimation."""
    with patch('routers.logistics.LogisticsRiskShield') as mock_service:
        # Setup mock
        mock_instance = Mock()
        mock_instance.estimate_freight_cost.return_value = mock_freight_estimate
        mock_service.return_value = mock_instance
        
        # Make request
        response = client.post(
            "/api/logistics/freight-estimate",
            json={
                "destination_country": "United States",
                "volume": 10.0,
                "weight": 2000.0
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["sea_freight"] == 1000.0
        assert data["air_freight"] == 7000.0
        assert data["recommended_mode"] == "sea"
        assert data["currency"] == "USD"


def test_estimate_freight_empty_destination(client):
    """Test freight estimation with empty destination country."""
    response = client.post(
        "/api/logistics/freight-estimate",
        json={
            "destination_country": "   ",
            "volume": 10.0,
            "weight": 2000.0
        }
    )
    
    assert response.status_code == 400
    assert "Destination country cannot be empty" in response.json()["detail"]


def test_estimate_freight_zero_volume(client):
    """Test freight estimation with zero volume."""
    response = client.post(
        "/api/logistics/freight-estimate",
        json={
            "destination_country": "United States",
            "volume": 0.0,
            "weight": 2000.0
        }
    )
    
    # Pydantic validation returns 422 for values that don't meet gt=0 constraint
    assert response.status_code == 422


def test_estimate_freight_negative_volume(client):
    """Test freight estimation with negative volume."""
    response = client.post(
        "/api/logistics/freight-estimate",
        json={
            "destination_country": "United States",
            "volume": -10.0,
            "weight": 2000.0
        }
    )
    
    # Pydantic validation returns 422 for negative values
    assert response.status_code == 422


def test_estimate_freight_zero_weight(client):
    """Test freight estimation with zero weight."""
    response = client.post(
        "/api/logistics/freight-estimate",
        json={
            "destination_country": "United States",
            "volume": 10.0,
            "weight": 0.0
        }
    )
    
    # Pydantic validation returns 422 for values that don't meet gt=0 constraint
    assert response.status_code == 422


def test_estimate_freight_negative_weight(client):
    """Test freight estimation with negative weight."""
    response = client.post(
        "/api/logistics/freight-estimate",
        json={
            "destination_country": "United States",
            "volume": 10.0,
            "weight": -2000.0
        }
    )
    
    # Pydantic validation returns 422 for negative values
    assert response.status_code == 422


def test_estimate_freight_air_recommended(client):
    """Test freight estimation where air freight is recommended."""
    with patch('routers.logistics.LogisticsRiskShield') as mock_service:
        # Setup mock for light cargo where air is cheaper
        mock_instance = Mock()
        mock_instance.estimate_freight_cost.return_value = FreightEstimate(
            sea_freight=1000.0,
            air_freight=2500.0,  # Less than 3x sea freight
            recommended_mode=FreightMode.AIR,
            currency="USD"
        )
        mock_service.return_value = mock_instance
        
        # Make request
        response = client.post(
            "/api/logistics/freight-estimate",
            json={
                "destination_country": "United States",
                "volume": 1.0,
                "weight": 100.0
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_mode"] == "air"


def test_estimate_freight_different_destinations(client):
    """Test freight estimation for different destination regions."""
    test_cases = [
        ("United States", 1000.0, 6000.0),
        ("United Kingdom", 800.0, 5000.0),
        ("Singapore", 500.0, 3500.0),
        ("Australia", 900.0, 6500.0)
    ]
    
    for destination, sea_cost, air_cost in test_cases:
        with patch('routers.logistics.LogisticsRiskShield') as mock_service:
            mock_instance = Mock()
            mock_instance.estimate_freight_cost.return_value = FreightEstimate(
                sea_freight=sea_cost,
                air_freight=air_cost,
                recommended_mode=FreightMode.SEA,
                currency="USD"
            )
            mock_service.return_value = mock_instance
            
            response = client.post(
                "/api/logistics/freight-estimate",
                json={
                    "destination_country": destination,
                    "volume": 10.0,
                    "weight": 2000.0
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["sea_freight"] == sea_cost
            assert data["air_freight"] == air_cost


def test_estimate_freight_service_error(client):
    """Test freight estimation when service raises an error."""
    with patch('routers.logistics.LogisticsRiskShield') as mock_service:
        # Setup mock to raise exception
        mock_instance = Mock()
        mock_instance.estimate_freight_cost.side_effect = Exception("Service error")
        mock_service.return_value = mock_instance
        
        # Make request
        response = client.post(
            "/api/logistics/freight-estimate",
            json={
                "destination_country": "United States",
                "volume": 10.0,
                "weight": 2000.0
            }
        )
        
        # Assertions
        assert response.status_code == 500
        assert "error occurred while estimating freight costs" in response.json()["detail"]


# Integration test

def test_complete_logistics_workflow(client, mock_logistics_risk_analysis, mock_rms_probability, mock_freight_estimate):
    """Test complete logistics workflow: risk analysis -> RMS probability -> freight estimate."""
    with patch('routers.logistics.LogisticsRiskShield') as mock_service:
        mock_instance = Mock()
        mock_instance.analyze_risks.return_value = mock_logistics_risk_analysis
        mock_instance.estimate_rms_probability.return_value = mock_rms_probability
        mock_instance.estimate_freight_cost.return_value = mock_freight_estimate
        mock_service.return_value = mock_instance
        
        # Step 1: Get complete risk analysis
        response1 = client.post(
            "/api/logistics/risk-analysis",
            json={
                "product_type": "Turmeric powder",
                "hs_code": "0910.30",
                "volume": 10.0,
                "value": 20000.0,
                "destination_country": "United States",
                "product_description": "Organic turmeric powder"
            }
        )
        assert response1.status_code == 200
        
        # Step 2: Get detailed RMS probability
        response2 = client.post(
            "/api/logistics/rms-probability",
            json={
                "product_type": "Turmeric powder",
                "hs_code": "0910.30",
                "product_description": "Organic turmeric powder"
            }
        )
        assert response2.status_code == 200
        
        # Step 3: Get freight estimate
        response3 = client.post(
            "/api/logistics/freight-estimate",
            json={
                "destination_country": "United States",
                "volume": 10.0,
                "weight": 2000.0
            }
        )
        assert response3.status_code == 200
        
        # Verify all responses are consistent
        data1 = response1.json()
        data2 = response2.json()
        data3 = response3.json()
        
        assert data1["rms_probability"]["probability_percentage"] == data2["probability_percentage"]
        assert data1["freight_estimate"]["sea_freight"] == data3["sea_freight"]
        assert data1["freight_estimate"]["air_freight"] == data3["air_freight"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
