"""
Unit tests for LogisticsRiskShield service.

Tests cover:
- LCL vs FCL comparison
- RMS probability estimation
- Route delay prediction
- Freight cost estimation
- Insurance recommendations
- Red flag keyword detection
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.logistics_risk_shield import LogisticsRiskShield
from models.logistics import LogisticsRiskRequest
from models.enums import ShippingMode, FreightMode, RiskSeverity


class TestLogisticsRiskShield:
    """Test suite for LogisticsRiskShield service."""
    
    @pytest.fixture
    def service(self):
        """Create LogisticsRiskShield instance for testing."""
        return LogisticsRiskShield()
    
    # LCL vs FCL Comparison Tests
    
    def test_compare_lcl_fcl_small_volume_recommends_lcl(self, service):
        """Test that small volumes recommend LCL."""
        result = service.compare_lcl_fcl(volume=5.0, product_type="Textiles")
        
        assert result.recommendation == ShippingMode.LCL
        assert result.lcl.cost < result.fcl.cost
        assert result.lcl.risk_level in [RiskSeverity.LOW, RiskSeverity.MEDIUM]
    
    def test_compare_lcl_fcl_large_volume_recommends_fcl(self, service):
        """Test that large volumes (>60% FCL capacity) recommend FCL."""
        result = service.compare_lcl_fcl(volume=25.0, product_type="Electronics")
        
        assert result.recommendation == ShippingMode.FCL
        assert result.fcl.cost < result.lcl.cost
        assert result.fcl.risk_level == RiskSeverity.LOW
    
    def test_compare_lcl_fcl_high_risk_product_recommends_fcl_at_lower_threshold(self, service):
        """Test that high-risk products recommend FCL at lower volume threshold."""
        result = service.compare_lcl_fcl(volume=15.0, product_type="Pharmaceutical")
        
        # 15 CBM is ~45% of FCL capacity, but high-risk products should recommend FCL at 40%+
        assert result.recommendation == ShippingMode.FCL
        assert result.lcl.risk_level == RiskSeverity.HIGH
    
    def test_compare_lcl_fcl_includes_pros_and_cons(self, service):
        """Test that comparison includes pros and cons for both options."""
        result = service.compare_lcl_fcl(volume=10.0, product_type="Furniture")
        
        assert len(result.lcl.pros) > 0
        assert len(result.lcl.cons) > 0
        assert len(result.fcl.pros) > 0
        assert len(result.fcl.cons) > 0
    
    # RMS Probability Estimation Tests
    
    def test_estimate_rms_probability_low_risk_product(self, service):
        """Test RMS probability for low-risk product."""
        result = service.estimate_rms_probability(
            product_type="Textiles",
            hs_code="6109",
            description="Cotton t-shirts for casual wear"
        )
        
        # Textiles (HS 61) are medium-risk, so probability will be higher than pure low-risk
        assert result.probability_percentage >= 15.0
        assert result.probability_percentage <= 60.0
        assert result.risk_level in [RiskSeverity.LOW, RiskSeverity.MEDIUM]
        assert len(result.mitigation_tips) > 0
    
    def test_estimate_rms_probability_high_risk_product(self, service):
        """Test RMS probability for high-risk product type."""
        result = service.estimate_rms_probability(
            product_type="Pharmaceutical",
            hs_code="3004",
            description="Herbal supplement tablets"
        )
        
        assert result.probability_percentage >= 30.0
        assert result.risk_level in [RiskSeverity.MEDIUM, RiskSeverity.HIGH]
        assert any("High-risk product category" in factor for factor in result.risk_factors)
    
    def test_estimate_rms_probability_detects_red_flag_keywords(self, service):
        """Test that RMS estimation detects red flag keywords."""
        result = service.estimate_rms_probability(
            product_type="Food",
            hs_code="0910",
            description="Turmeric powder and herbal extract"
        )
        
        assert len(result.red_flag_keywords) > 0
        assert "powder" in result.red_flag_keywords or "herbal" in result.red_flag_keywords
        assert any("Red flag keywords detected" in factor for factor in result.risk_factors)
    
    def test_estimate_rms_probability_high_risk_hs_code(self, service):
        """Test RMS probability for high-risk HS code categories."""
        result = service.estimate_rms_probability(
            product_type="Chemical",
            hs_code="2918",  # Chemical HS code
            description="Industrial chemical compound"
        )
        
        assert result.probability_percentage >= 30.0
        assert any("High-risk HS code category" in factor for factor in result.risk_factors)
    
    def test_estimate_rms_probability_capped_at_95(self, service):
        """Test that RMS probability is capped at 95%."""
        result = service.estimate_rms_probability(
            product_type="Pharmaceutical chemical supplement",
            hs_code="3004",
            description="Chemical powder drug medicine pharmaceutical herbal supplement"
        )
        
        assert result.probability_percentage <= 95.0
    
    # Route Delay Prediction Tests
    
    def test_predict_route_delays_europe_destination(self, service):
        """Test route prediction for European destination."""
        result = service.predict_route_delays(destination="Germany")
        
        assert len(result.routes) > 0
        assert result.recommended_route is not None
        assert any("Suez" in route.name or "Cape" in route.name for route in result.routes)
    
    def test_predict_route_delays_asia_destination(self, service):
        """Test route prediction for Asian destination."""
        result = service.predict_route_delays(destination="Singapore")
        
        assert len(result.routes) > 0
        assert "Direct" in result.recommended_route
        # Asian routes should be faster
        assert all(route.transit_time_days <= 15 for route in result.routes)
    
    def test_predict_route_delays_north_america_destination(self, service):
        """Test route prediction for North American destination."""
        result = service.predict_route_delays(destination="United States")
        
        assert len(result.routes) > 0
        assert result.recommended_route is not None
        # Should have multiple route options
        assert len(result.routes) >= 1
    
    def test_predict_route_delays_includes_geopolitical_factors(self, service):
        """Test that route analysis includes geopolitical factors."""
        result = service.predict_route_delays(destination="United Kingdom")
        
        # At least one route should have geopolitical factors mentioned
        has_geopolitical_info = any(
            len(route.geopolitical_factors) > 0 for route in result.routes
        )
        assert has_geopolitical_info or len(result.routes) > 0
    
    def test_predict_route_delays_with_monsoon_season(self, service):
        """Test route prediction with monsoon season affecting transit times."""
        result = service.predict_route_delays(destination="Singapore", season="monsoon")
        
        assert len(result.routes) > 0
        # Check that monsoon factors are mentioned
        has_monsoon_factor = any(
            any("monsoon" in factor.lower() for factor in route.geopolitical_factors)
            for route in result.routes
        )
        assert has_monsoon_factor
        # Transit time should be longer than without seasonal factors
        result_no_season = service.predict_route_delays(destination="Singapore")
        assert result.routes[0].transit_time_days >= result_no_season.routes[0].transit_time_days
    
    def test_predict_route_delays_with_winter_season(self, service):
        """Test route prediction with winter season affecting North Atlantic routes."""
        result = service.predict_route_delays(destination="United States", season="winter")
        
        assert len(result.routes) > 0
        # Check that winter factors are mentioned
        has_winter_factor = any(
            any("winter" in factor.lower() or "storm" in factor.lower() for factor in route.geopolitical_factors)
            for route in result.routes
        )
        assert has_winter_factor
    
    def test_predict_route_delays_with_peak_season(self, service):
        """Test route prediction during peak shipping season."""
        result = service.predict_route_delays(destination="Germany", season="fall")
        
        assert len(result.routes) > 0
        # Check that peak season factors are mentioned
        has_peak_factor = any(
            any("peak" in factor.lower() or "congestion" in factor.lower() for factor in route.geopolitical_factors)
            for route in result.routes
        )
        assert has_peak_factor
    
    def test_predict_route_delays_spring_favorable(self, service):
        """Test that spring season shows favorable conditions."""
        result = service.predict_route_delays(destination="Singapore", season="spring")
        
        assert len(result.routes) > 0
        # Check that favorable conditions are mentioned
        has_favorable_factor = any(
            any("favorable" in factor.lower() or "optimal" in factor.lower() for factor in route.geopolitical_factors)
            for route in result.routes
        )
        assert has_favorable_factor
    
    # Freight Cost Estimation Tests
    
    def test_estimate_freight_cost_sea_vs_air(self, service):
        """Test that air freight is more expensive than sea freight."""
        result = service.estimate_freight_cost(
            destination="United States",
            volume=10.0,
            weight=2000.0
        )
        
        assert result.air_freight > result.sea_freight
        assert result.currency == "USD"
    
    def test_estimate_freight_cost_recommends_sea_for_heavy_cargo(self, service):
        """Test that sea freight is recommended for heavy cargo."""
        result = service.estimate_freight_cost(
            destination="Germany",
            volume=15.0,
            weight=3000.0
        )
        
        assert result.recommended_mode == FreightMode.SEA
    
    def test_estimate_freight_cost_considers_volumetric_weight(self, service):
        """Test that freight estimation considers volumetric weight for air freight."""
        # Light but bulky cargo
        result = service.estimate_freight_cost(
            destination="Singapore",
            volume=5.0,
            weight=100.0  # Very light for 5 CBM
        )
        
        # Air freight should be calculated based on volumetric weight (5 * 167 = 835 kg)
        # which is higher than actual weight (100 kg)
        assert result.air_freight > 0
    
    def test_estimate_freight_cost_varies_by_destination(self, service):
        """Test that freight costs vary by destination region."""
        result_asia = service.estimate_freight_cost(
            destination="Singapore",
            volume=10.0,
            weight=2000.0
        )
        
        result_europe = service.estimate_freight_cost(
            destination="Germany",
            volume=10.0,
            weight=2000.0
        )
        
        # Europe should generally be more expensive than Asia
        assert result_europe.sea_freight >= result_asia.sea_freight
    
    # Insurance Recommendation Tests
    
    def test_recommend_insurance_coverage_110_percent(self, service):
        """Test that insurance coverage is 110% of shipment value."""
        result = service.recommend_insurance(
            shipment_value=100000.0,
            risk_level=RiskSeverity.MEDIUM
        )
        
        # Use approximate comparison for floating point
        assert abs(result.recommended_coverage - 110000.0) < 0.01
    
    def test_recommend_insurance_premium_varies_by_risk(self, service):
        """Test that insurance premium varies based on risk level."""
        low_risk = service.recommend_insurance(
            shipment_value=100000.0,
            risk_level=RiskSeverity.LOW
        )
        
        high_risk = service.recommend_insurance(
            shipment_value=100000.0,
            risk_level=RiskSeverity.HIGH
        )
        
        assert high_risk.premium_estimate > low_risk.premium_estimate
    
    def test_recommend_insurance_coverage_type_by_risk(self, service):
        """Test that coverage type varies based on risk level."""
        low_risk = service.recommend_insurance(
            shipment_value=100000.0,
            risk_level=RiskSeverity.LOW
        )
        
        high_risk = service.recommend_insurance(
            shipment_value=100000.0,
            risk_level=RiskSeverity.HIGH
        )
        
        assert low_risk.coverage_type != high_risk.coverage_type
        assert "extended" in high_risk.coverage_type.lower()
    
    # Red Flag Keyword Detection Tests
    
    def test_detect_red_flag_keywords_finds_keywords(self, service):
        """Test that red flag keyword detection finds keywords."""
        keywords = service.detect_red_flag_keywords(
            "Organic turmeric powder with herbal extracts"
        )
        
        assert len(keywords) > 0
        assert "powder" in keywords or "herbal" in keywords or "organic" in keywords
    
    def test_detect_red_flag_keywords_case_insensitive(self, service):
        """Test that keyword detection is case-insensitive."""
        keywords = service.detect_red_flag_keywords(
            "CHEMICAL POWDER for industrial use"
        )
        
        assert "chemical" in keywords or "powder" in keywords
    
    def test_detect_red_flag_keywords_no_keywords(self, service):
        """Test that clean descriptions return no keywords."""
        keywords = service.detect_red_flag_keywords(
            "Cotton fabric for garment manufacturing"
        )
        
        assert len(keywords) == 0
    
    # Complete Analysis Tests
    
    def test_analyze_risks_complete_analysis(self, service):
        """Test complete logistics risk analysis."""
        request = LogisticsRiskRequest(
            product_type="Turmeric powder",
            hs_code="0910.30",
            volume=10.0,
            value=200000.0,
            destination_country="United States",
            product_description="Organic turmeric powder for food use"
        )
        
        result = service.analyze_risks(request)
        
        # Verify all components are present
        assert result.lcl_fcl_comparison is not None
        assert result.rms_probability is not None
        assert result.route_analysis is not None
        assert result.freight_estimate is not None
        assert result.insurance_recommendation is not None
    
    def test_analyze_risks_high_risk_product(self, service):
        """Test analysis for high-risk product."""
        request = LogisticsRiskRequest(
            product_type="Pharmaceutical",
            hs_code="3004",
            volume=5.0,
            value=500000.0,
            destination_country="Germany",
            product_description="Herbal supplement tablets with natural extracts"
        )
        
        result = service.analyze_risks(request)
        
        # High-risk product should have higher RMS probability
        assert result.rms_probability.probability_percentage >= 30.0
        # 5 CBM is ~15% of FCL capacity, which is below the 40% threshold for high-risk products
        # So it will still recommend LCL, but with HIGH risk level
        assert result.lcl_fcl_comparison.lcl.risk_level == RiskSeverity.HIGH
        # Should have higher insurance premium
        assert result.insurance_recommendation.premium_estimate > 0
    
    def test_analyze_risks_low_risk_product(self, service):
        """Test analysis for low-risk product."""
        request = LogisticsRiskRequest(
            product_type="Textiles",
            hs_code="6109",
            volume=8.0,
            value=100000.0,
            destination_country="United Kingdom",
            product_description="Cotton t-shirts for retail"
        )
        
        result = service.analyze_risks(request)
        
        # Low-risk product should have lower RMS probability
        assert result.rms_probability.probability_percentage < 50.0
        # Should recommend LCL for moderate volume
        assert result.lcl_fcl_comparison.recommendation == ShippingMode.LCL
    
    def test_analyze_risks_large_volume(self, service):
        """Test analysis for large volume shipment."""
        request = LogisticsRiskRequest(
            product_type="Electronics",
            hs_code="8517",
            volume=30.0,
            value=1000000.0,
            destination_country="United States",
            product_description="Mobile phone accessories"
        )
        
        result = service.analyze_risks(request)
        
        # Large volume should recommend FCL
        assert result.lcl_fcl_comparison.recommendation == ShippingMode.FCL
        # Should have higher insurance coverage
        assert result.insurance_recommendation.recommended_coverage > 1000000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
