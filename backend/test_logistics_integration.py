"""
Integration tests for Logistics API Router

Tests the logistics router endpoints with the actual LogisticsRiskShield service.
"""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_risk_analysis_integration():
    """Test complete risk analysis with real service."""
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
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all components are present
    assert "lcl_fcl_comparison" in data
    assert "rms_probability" in data
    assert "route_analysis" in data
    assert "freight_estimate" in data
    assert "insurance_recommendation" in data
    
    # Verify LCL/FCL comparison
    assert "recommendation" in data["lcl_fcl_comparison"]
    assert data["lcl_fcl_comparison"]["recommendation"] in ["LCL", "FCL"]
    assert "lcl" in data["lcl_fcl_comparison"]
    assert "fcl" in data["lcl_fcl_comparison"]
    
    # Verify RMS probability
    assert "probability_percentage" in data["rms_probability"]
    assert 0 <= data["rms_probability"]["probability_percentage"] <= 100
    assert "risk_level" in data["rms_probability"]
    assert data["rms_probability"]["risk_level"] in ["low", "medium", "high"]
    
    # Verify route analysis
    assert "recommended_route" in data["route_analysis"]
    assert "routes" in data["route_analysis"]
    assert len(data["route_analysis"]["routes"]) > 0
    
    # Verify freight estimate
    assert "sea_freight" in data["freight_estimate"]
    assert "air_freight" in data["freight_estimate"]
    assert data["freight_estimate"]["sea_freight"] > 0
    assert data["freight_estimate"]["air_freight"] > 0
    
    # Verify insurance recommendation
    assert "recommended_coverage" in data["insurance_recommendation"]
    assert "premium_estimate" in data["insurance_recommendation"]
    assert data["insurance_recommendation"]["recommended_coverage"] > 0


def test_rms_probability_integration():
    """Test RMS probability calculation with real service."""
    response = client.post(
        "/api/logistics/rms-probability",
        json={
            "product_type": "Turmeric powder",
            "hs_code": "0910.30",
            "product_description": "Organic turmeric powder for food use"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "probability_percentage" in data
    assert "risk_level" in data
    assert "risk_factors" in data
    assert "red_flag_keywords" in data
    assert "mitigation_tips" in data
    
    # Verify values
    assert 0 <= data["probability_percentage"] <= 100
    assert data["risk_level"] in ["low", "medium", "high"]
    assert isinstance(data["risk_factors"], list)
    assert isinstance(data["red_flag_keywords"], list)
    assert isinstance(data["mitigation_tips"], list)
    assert len(data["mitigation_tips"]) > 0


def test_freight_estimate_integration():
    """Test freight cost estimation with real service."""
    response = client.post(
        "/api/logistics/freight-estimate",
        json={
            "destination_country": "United States",
            "volume": 10.0,
            "weight": 2000.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "sea_freight" in data
    assert "air_freight" in data
    assert "recommended_mode" in data
    assert "currency" in data
    
    # Verify values
    assert data["sea_freight"] > 0
    assert data["air_freight"] > 0
    assert data["recommended_mode"] in ["sea", "air"]
    assert data["currency"] == "USD"
    
    # Air freight should typically be more expensive than sea freight
    assert data["air_freight"] > data["sea_freight"]


def test_high_risk_product_integration():
    """Test with high-risk product (pharmaceutical)."""
    response = client.post(
        "/api/logistics/rms-probability",
        json={
            "product_type": "pharmaceutical",
            "hs_code": "3004.90",
            "product_description": "Chemical powder for pharmaceutical use"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # High-risk product should have higher probability
    assert data["probability_percentage"] > 30
    assert len(data["red_flag_keywords"]) > 0
    assert "chemical" in data["red_flag_keywords"] or "powder" in data["red_flag_keywords"]


def test_different_destinations_integration():
    """Test freight estimates for different destinations."""
    destinations = ["United States", "United Kingdom", "Singapore", "Australia"]
    
    for destination in destinations:
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
        assert data["sea_freight"] > 0
        assert data["air_freight"] > 0


def test_lcl_vs_fcl_small_volume():
    """Test LCL recommendation for small volume."""
    response = client.post(
        "/api/logistics/risk-analysis",
        json={
            "product_type": "Textiles",
            "hs_code": "6109.10",
            "volume": 5.0,  # Small volume
            "value": 10000.0,
            "destination_country": "United States",
            "product_description": "Cotton t-shirts"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Small volume should recommend LCL
    assert data["lcl_fcl_comparison"]["recommendation"] == "LCL"


def test_lcl_vs_fcl_large_volume():
    """Test FCL recommendation for large volume."""
    response = client.post(
        "/api/logistics/risk-analysis",
        json={
            "product_type": "Textiles",
            "hs_code": "6109.10",
            "volume": 25.0,  # Large volume (>60% of container)
            "value": 50000.0,
            "destination_country": "United States",
            "product_description": "Cotton t-shirts"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Large volume should recommend FCL
    assert data["lcl_fcl_comparison"]["recommendation"] == "FCL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
