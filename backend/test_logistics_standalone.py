"""
Standalone test for Logistics API Router

Tests the logistics router endpoints directly without importing main.py
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.logistics import router

# Create a minimal FastAPI app for testing
app = FastAPI()
app.include_router(router, prefix="/api/logistics")

client = TestClient(app)


def test_risk_analysis_endpoint():
    """Test complete risk analysis endpoint."""
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
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200
    
    data = response.json()
    print(f"Response keys: {data.keys()}")
    
    # Verify all components are present
    assert "lcl_fcl_comparison" in data
    assert "rms_probability" in data
    assert "route_analysis" in data
    assert "freight_estimate" in data
    assert "insurance_recommendation" in data
    
    print(f"✓ Risk analysis endpoint works correctly")
    print(f"  - RMS Probability: {data['rms_probability']['probability_percentage']}%")
    print(f"  - Recommended Mode: {data['lcl_fcl_comparison']['recommendation']}")
    print(f"  - Sea Freight: ${data['freight_estimate']['sea_freight']}")
    print(f"  - Air Freight: ${data['freight_estimate']['air_freight']}")


def test_rms_probability_endpoint():
    """Test RMS probability calculation endpoint."""
    response = client.post(
        "/api/logistics/rms-probability",
        json={
            "product_type": "Turmeric powder",
            "hs_code": "0910.30",
            "product_description": "Organic turmeric powder for food use"
        }
    )
    
    print(f"\nStatus Code: {response.status_code}")
    assert response.status_code == 200
    
    data = response.json()
    print(f"Response keys: {data.keys()}")
    
    # Verify response structure
    assert "probability_percentage" in data
    assert "risk_level" in data
    assert "risk_factors" in data
    assert "red_flag_keywords" in data
    assert "mitigation_tips" in data
    
    print(f"✓ RMS probability endpoint works correctly")
    print(f"  - Probability: {data['probability_percentage']}%")
    print(f"  - Risk Level: {data['risk_level']}")
    print(f"  - Red Flag Keywords: {data['red_flag_keywords']}")


def test_freight_estimate_endpoint():
    """Test freight cost estimation endpoint."""
    response = client.post(
        "/api/logistics/freight-estimate",
        json={
            "destination_country": "United States",
            "volume": 10.0,
            "weight": 2000.0
        }
    )
    
    print(f"\nStatus Code: {response.status_code}")
    assert response.status_code == 200
    
    data = response.json()
    print(f"Response keys: {data.keys()}")
    
    # Verify response structure
    assert "sea_freight" in data
    assert "air_freight" in data
    assert "recommended_mode" in data
    assert "currency" in data
    
    print(f"✓ Freight estimate endpoint works correctly")
    print(f"  - Sea Freight: ${data['sea_freight']}")
    print(f"  - Air Freight: ${data['air_freight']}")
    print(f"  - Recommended Mode: {data['recommended_mode']}")


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Logistics API Router Endpoints")
    print("=" * 70)
    
    try:
        test_risk_analysis_endpoint()
        test_rms_probability_endpoint()
        test_freight_estimate_endpoint()
        
        print("\n" + "=" * 70)
        print("✅ All logistics router endpoints working correctly!")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
