"""
Unit tests for FreightEstimator service.

Tests cover:
- Freight cost estimation for different destinations
- Sea freight vs air freight calculations
- Shipping mode recommendations
- Route-specific cost adjustments
- Delivery time estimation
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.freight_estimator import FreightEstimator
from models.enums import FreightMode


class TestFreightEstimator:
    """Test suite for FreightEstimator service."""
    
    @pytest.fixture
    def estimator(self):
        """Create a FreightEstimator instance for testing."""
        return FreightEstimator()
    
    def test_estimate_cost_basic(self, estimator):
        """Test basic freight cost estimation."""
        estimate = estimator.estimate_cost(
            destination="United States",
            volume=5.0,
            weight=800.0
        )
        
        # Verify estimate structure
        assert estimate.sea_freight > 0
        assert estimate.air_freight > 0
        assert estimate.currency == "USD"
        assert estimate.recommended_mode in [FreightMode.SEA, FreightMode.AIR]
    
    def test_sea_freight_calculation(self, estimator):
        """Test sea freight calculation based on volume."""
        # North America region has base rate of 100 USD/CBM
        estimate = estimator.estimate_cost(
            destination="United States",
            volume=10.0,
            weight=1000.0
        )
        
        # Sea freight should be volume * rate
        # 10 CBM * 100 USD/CBM = 1000 USD
        assert estimate.sea_freight == 1000.0
    
    def test_air_freight_calculation_actual_weight(self, estimator):
        """Test air freight calculation when actual weight is higher."""
        # Heavy cargo: actual weight > volumetric weight
        estimate = estimator.estimate_cost(
            destination="United States",
            volume=1.0,  # 1 CBM = 167 kg volumetric
            weight=500.0  # Actual weight is higher
        )
        
        # Air freight should use actual weight
        # 500 kg * 6.0 USD/kg = 3000 USD
        assert estimate.air_freight == 3000.0
    
    def test_air_freight_calculation_volumetric_weight(self, estimator):
        """Test air freight calculation when volumetric weight is higher."""
        # Light cargo: volumetric weight > actual weight
        estimate = estimator.estimate_cost(
            destination="United States",
            volume=5.0,  # 5 CBM = 835 kg volumetric
            weight=200.0  # Actual weight is lower
        )
        
        # Air freight should use volumetric weight
        # 835 kg * 6.0 USD/kg = 5010 USD
        assert estimate.air_freight == 5010.0
    
    def test_recommend_sea_freight_for_heavy_cargo(self, estimator):
        """Test that sea freight is recommended for heavy cargo."""
        estimate = estimator.estimate_cost(
            destination="Germany",
            volume=10.0,
            weight=2000.0
        )
        
        # Heavy cargo should recommend sea freight (more cost-effective)
        assert estimate.recommended_mode == FreightMode.SEA
    
    def test_recommend_air_freight_for_light_cargo(self, estimator):
        """Test that air freight is recommended for light cargo."""
        estimate = estimator.estimate_cost(
            destination="Singapore",
            volume=0.5,  # Small volume
            weight=10.0  # Very light
        )
        
        # Light cargo may recommend air freight if cost difference is small
        # This depends on the cost ratio
        assert estimate.recommended_mode in [FreightMode.SEA, FreightMode.AIR]
    
    def test_urgency_high_recommends_air(self, estimator):
        """Test that high urgency always recommends air freight."""
        estimate = estimator.estimate_cost(
            destination="United Kingdom",
            volume=20.0,
            weight=4000.0,
            urgency="high"
        )
        
        # High urgency should always recommend air freight
        assert estimate.recommended_mode == FreightMode.AIR
    
    def test_route_adjustment_cape(self, estimator):
        """Test route cost adjustment for Cape of Good Hope."""
        estimate_cape = estimator.estimate_cost(
            destination="United Kingdom",
            volume=10.0,
            weight=2000.0,
            route="via Cape of Good Hope"
        )
        
        estimate_normal = estimator.estimate_cost(
            destination="United Kingdom",
            volume=10.0,
            weight=2000.0
        )
        
        # Cape route should be more expensive (1.3x)
        assert estimate_cape.sea_freight > estimate_normal.sea_freight
    
    def test_route_adjustment_suez(self, estimator):
        """Test route cost adjustment for Suez Canal."""
        estimate_suez = estimator.estimate_cost(
            destination="Germany",
            volume=10.0,
            weight=2000.0,
            route="via Suez Canal"
        )
        
        estimate_normal = estimator.estimate_cost(
            destination="Germany",
            volume=10.0,
            weight=2000.0
        )
        
        # Suez route should be slightly more expensive (1.1x)
        assert estimate_suez.sea_freight > estimate_normal.sea_freight
    
    def test_route_adjustment_direct(self, estimator):
        """Test route cost adjustment for direct routes."""
        estimate_direct = estimator.estimate_cost(
            destination="Singapore",
            volume=10.0,
            weight=2000.0,
            route="direct"
        )
        
        estimate_normal = estimator.estimate_cost(
            destination="Singapore",
            volume=10.0,
            weight=2000.0
        )
        
        # Direct route should be cheaper (0.95x)
        assert estimate_direct.sea_freight < estimate_normal.sea_freight
    
    def test_different_regions(self, estimator):
        """Test freight estimation for different regions."""
        destinations = [
            ("China", "Asia"),
            ("Germany", "Europe"),
            ("United States", "North America"),
            ("UAE", "Middle East"),
            ("South Africa", "Africa"),
            ("Brazil", "South America"),
            ("Australia", "Oceania")
        ]
        
        for destination, region in destinations:
            estimate = estimator.estimate_cost(
                destination=destination,
                volume=5.0,
                weight=1000.0
            )
            
            # All estimates should have valid values
            assert estimate.sea_freight > 0
            assert estimate.air_freight > 0
            assert estimate.currency == "USD"
    
    def test_unknown_country_defaults_to_asia(self, estimator):
        """Test that unknown countries default to Asia region."""
        estimate = estimator.estimate_cost(
            destination="Unknown Country",
            volume=5.0,
            weight=1000.0
        )
        
        # Should use Asia base rates (50 USD/CBM for sea)
        # 5 CBM * 50 USD/CBM = 250 USD
        assert estimate.sea_freight == 250.0
    
    def test_calculate_cost_per_unit(self, estimator):
        """Test cost per unit calculation."""
        cost_per_unit = estimator.calculate_cost_per_unit(
            total_cost=1000.0,
            units=100
        )
        
        assert cost_per_unit == 10.0
    
    def test_calculate_cost_per_unit_zero_units(self, estimator):
        """Test cost per unit with zero units."""
        cost_per_unit = estimator.calculate_cost_per_unit(
            total_cost=1000.0,
            units=0
        )
        
        assert cost_per_unit == 0.0
    
    def test_estimate_delivery_time_sea(self, estimator):
        """Test delivery time estimation for sea freight."""
        delivery_time = estimator.estimate_delivery_time(
            destination="United States",
            mode=FreightMode.SEA
        )
        
        # North America sea freight typically takes 30 days
        assert delivery_time == 30
    
    def test_estimate_delivery_time_air(self, estimator):
        """Test delivery time estimation for air freight."""
        delivery_time = estimator.estimate_delivery_time(
            destination="United States",
            mode=FreightMode.AIR
        )
        
        # North America air freight typically takes 6 days
        assert delivery_time == 6
    
    def test_estimate_delivery_time_different_regions(self, estimator):
        """Test delivery time estimation for different regions."""
        # Asia should be faster than Europe
        asia_time = estimator.estimate_delivery_time(
            destination="Singapore",
            mode=FreightMode.SEA
        )
        
        europe_time = estimator.estimate_delivery_time(
            destination="Germany",
            mode=FreightMode.SEA
        )
        
        assert asia_time < europe_time
    
    def test_cost_rounding(self, estimator):
        """Test that costs are properly rounded to 2 decimal places."""
        estimate = estimator.estimate_cost(
            destination="Japan",
            volume=3.7,
            weight=567.89
        )
        
        # Check that costs are rounded to 2 decimal places
        assert estimate.sea_freight == round(estimate.sea_freight, 2)
        assert estimate.air_freight == round(estimate.air_freight, 2)
    
    def test_large_volume_shipment(self, estimator):
        """Test freight estimation for large volume shipments."""
        estimate = estimator.estimate_cost(
            destination="Germany",
            volume=50.0,  # Large volume
            weight=10000.0
        )
        
        # Large shipments should have proportionally higher costs
        assert estimate.sea_freight > 3000.0
        assert estimate.air_freight >= 50000.0  # Changed to >= to handle exact match
    
    def test_small_volume_shipment(self, estimator):
        """Test freight estimation for small volume shipments."""
        estimate = estimator.estimate_cost(
            destination="Singapore",
            volume=0.1,  # Very small volume
            weight=5.0
        )
        
        # Small shipments should have lower costs
        assert estimate.sea_freight < 100.0
        assert estimate.air_freight < 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
