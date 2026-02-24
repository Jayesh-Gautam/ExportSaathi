"""
Unit tests for RMS Predictor Service.
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.rms_predictor import RMSPredictor
from models.enums import RiskSeverity


class TestRMSPredictor:
    """Test suite for RMS Predictor."""
    
    @pytest.fixture
    def predictor(self):
        """Create RMS predictor instance."""
        return RMSPredictor()
    
    def test_low_risk_product(self, predictor):
        """Test prediction for low-risk product."""
        result = predictor.predict_probability(
            product_type="Textile",
            hs_code="6109.10",
            description="100% cotton knitted T-shirts for men"
        )
        
        assert result.probability_percentage >= 0.0
        assert result.probability_percentage <= 100.0
        assert result.risk_level in [RiskSeverity.LOW, RiskSeverity.MEDIUM]
        assert isinstance(result.risk_factors, list)
        assert isinstance(result.mitigation_tips, list)
        assert len(result.mitigation_tips) > 0
    
    def test_high_risk_product_type(self, predictor):
        """Test prediction for high-risk product type."""
        result = predictor.predict_probability(
            product_type="Pharmaceutical",
            hs_code="3004.90",
            description="Medical tablets for therapeutic use"
        )
        
        # High-risk product should have higher probability
        assert result.probability_percentage > 30.0
        assert result.risk_level in [RiskSeverity.MEDIUM, RiskSeverity.HIGH]
        assert any("High-risk product category" in factor for factor in result.risk_factors)
    
    def test_red_flag_keywords_detection(self, predictor):
        """Test detection of red flag keywords."""
        result = predictor.predict_probability(
            product_type="Food",
            hs_code="0910.30",
            description="Organic herbal powder with natural chemical compounds"
        )
        
        # Should detect red flag keywords
        assert len(result.red_flag_keywords) > 0
        assert any(keyword in ["herbal", "organic", "natural", "chemical", "powder"] 
                   for keyword in result.red_flag_keywords)
        assert any("Red flag keywords" in factor for factor in result.risk_factors)
    
    def test_high_risk_hs_code(self, predictor):
        """Test prediction for high-risk HS code."""
        result = predictor.predict_probability(
            product_type="Chemical",
            hs_code="2903.15",  # Organic chemical
            description="Industrial chemical compound"
        )
        
        # High-risk HS code should increase probability
        assert result.probability_percentage > 25.0
        assert any("HS code category" in factor for factor in result.risk_factors)
    
    def test_first_time_exporter(self, predictor):
        """Test prediction for first-time exporter."""
        result = predictor.predict_probability(
            product_type="Textile",
            hs_code="6109.10",
            description="Cotton T-shirts",
            export_history={"is_first_time_exporter": True}
        )
        
        # First-time exporter should increase probability
        assert any("First-time exporter" in factor for factor in result.risk_factors)
        assert any("first" in tip.lower() for tip in result.mitigation_tips)
    
    def test_past_violations(self, predictor):
        """Test prediction with past violations."""
        result = predictor.predict_probability(
            product_type="Textile",
            hs_code="6109.10",
            description="Cotton T-shirts",
            export_history={"past_violations": True}
        )
        
        # Past violations should significantly increase probability
        assert result.probability_percentage > 25.0
        assert any("violation" in factor.lower() for factor in result.risk_factors)
    
    def test_high_value_shipment(self, predictor):
        """Test prediction for high-value shipment."""
        result = predictor.predict_probability(
            product_type="Electronics",
            hs_code="8517.12",
            description="Mobile phones",
            export_history={"high_value_shipment": True}
        )
        
        # High-value shipment should increase probability
        assert any("high-value" in factor.lower() for factor in result.risk_factors)
    
    def test_probability_bounds(self, predictor):
        """Test that probability is always within valid bounds."""
        # Test with maximum risk factors
        result = predictor.predict_probability(
            product_type="Pharmaceutical chemical",
            hs_code="3004.90",
            description="Hazardous toxic pharmaceutical chemical powder drug medicine",
            export_history={
                "is_first_time_exporter": True,
                "past_violations": True,
                "high_value_shipment": True
            }
        )
        
        # Probability should be capped at 95%
        assert result.probability_percentage >= 0.0
        assert result.probability_percentage <= 95.0
    
    def test_risk_level_consistency(self, predictor):
        """Test that risk level matches probability."""
        # Low probability
        result_low = predictor.predict_probability(
            product_type="Textile",
            hs_code="6109.10",
            description="Cotton T-shirts"
        )
        
        if result_low.probability_percentage < 30:
            assert result_low.risk_level == RiskSeverity.LOW
        
        # High probability
        result_high = predictor.predict_probability(
            product_type="Pharmaceutical",
            hs_code="3004.90",
            description="Pharmaceutical drug chemical medicine",
            export_history={"is_first_time_exporter": True}
        )
        
        if result_high.probability_percentage >= 50:
            assert result_high.risk_level == RiskSeverity.HIGH
        elif result_high.probability_percentage >= 30:
            assert result_high.risk_level == RiskSeverity.MEDIUM
    
    def test_mitigation_tips_quality(self, predictor):
        """Test that mitigation tips are relevant and actionable."""
        result = predictor.predict_probability(
            product_type="Food supplement",
            hs_code="0910.30",
            description="Organic herbal powder supplement",
            export_history={"is_first_time_exporter": True}
        )
        
        # Should have multiple mitigation tips
        assert len(result.mitigation_tips) >= 5
        
        # Tips should be unique
        assert len(result.mitigation_tips) == len(set(result.mitigation_tips))
        
        # Should include relevant tips for red flags
        if result.red_flag_keywords:
            assert any("technical" in tip.lower() or "scientific" in tip.lower() 
                      for tip in result.mitigation_tips)
        
        # Should include tips for first-time exporters
        assert any("first" in tip.lower() for tip in result.mitigation_tips)
    
    def test_identify_risk_factors(self, predictor):
        """Test risk factor identification."""
        risk_factors = predictor.identify_risk_factors(
            product_type="Pharmaceutical",
            description="Chemical powder"
        )
        
        assert isinstance(risk_factors, list)
        assert len(risk_factors) > 0
        assert any("High-risk product category" in factor for factor in risk_factors)
        assert any("Red flag keywords" in factor for factor in risk_factors)
    
    def test_vague_description_detection(self, predictor):
        """Test detection of vague descriptions."""
        risk_factors = predictor.identify_risk_factors(
            product_type="Product",
            description="Item"
        )
        
        # Should detect vague description
        assert any("Vague" in factor or "insufficient" in factor for factor in risk_factors)
    
    def test_multiple_red_flags_cap(self, predictor):
        """Test that multiple red flags don't cause excessive probability."""
        result = predictor.predict_probability(
            product_type="Chemical pharmaceutical",
            hs_code="3004.90",
            description="Chemical powder drug medicine pharmaceutical herbal organic natural toxic hazardous"
        )
        
        # Even with many red flags, probability should be capped
        assert result.probability_percentage <= 95.0
        
        # Should detect multiple keywords
        assert len(result.red_flag_keywords) >= 5
    
    def test_experienced_exporter_benefit(self, predictor):
        """Test that experienced exporters with clean record get lower probability."""
        result_experienced = predictor.predict_probability(
            product_type="Textile",
            hs_code="6109.10",
            description="Cotton T-shirts",
            export_history={
                "export_count": 15,
                "past_violations": False
            }
        )
        
        result_first_time = predictor.predict_probability(
            product_type="Textile",
            hs_code="6109.10",
            description="Cotton T-shirts",
            export_history={
                "is_first_time_exporter": True
            }
        )
        
        # Experienced exporter should have lower probability
        assert result_experienced.probability_percentage < result_first_time.probability_percentage
    
    def test_medium_risk_hs_code(self, predictor):
        """Test prediction for medium-risk HS code."""
        result = predictor.predict_probability(
            product_type="Food",
            hs_code="0910.30",  # Spices (medium risk)
            description="Turmeric powder for cooking"
        )
        
        # Should identify medium-risk HS code
        assert any("HS code category" in factor for factor in result.risk_factors)
    
    def test_empty_description(self, predictor):
        """Test handling of empty description."""
        result = predictor.predict_probability(
            product_type="Textile",
            hs_code="6109.10",
            description=""
        )
        
        # Should still return valid result
        assert result.probability_percentage >= 0.0
        assert result.probability_percentage <= 100.0
        assert isinstance(result.mitigation_tips, list)
    
    def test_invalid_hs_code(self, predictor):
        """Test handling of invalid HS code."""
        result = predictor.predict_probability(
            product_type="Textile",
            hs_code="",
            description="Cotton T-shirts"
        )
        
        # Should still return valid result
        assert result.probability_percentage >= 0.0
        assert result.probability_percentage <= 100.0
    
    def test_case_insensitive_keyword_detection(self, predictor):
        """Test that keyword detection is case-insensitive."""
        result1 = predictor.predict_probability(
            product_type="Food",
            hs_code="0910.30",
            description="ORGANIC HERBAL POWDER"
        )
        
        result2 = predictor.predict_probability(
            product_type="Food",
            hs_code="0910.30",
            description="organic herbal powder"
        )
        
        # Should detect keywords regardless of case
        assert len(result1.red_flag_keywords) == len(result2.red_flag_keywords)
        assert result1.probability_percentage == result2.probability_percentage


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
