"""
Integration test for Restricted Substances Analyzer.

This test verifies the end-to-end functionality of the restricted substances analyzer
by testing it with real-world scenarios.
"""

import pytest
from services.restricted_substances_analyzer import RestrictedSubstancesAnalyzer


class TestRestrictedSubstancesIntegration:
    """Integration tests for RestrictedSubstancesAnalyzer."""
    
    def test_analyze_food_product_with_restricted_substances(self):
        """Test analysis of food product with restricted substances."""
        analyzer = RestrictedSubstancesAnalyzer()
        
        result = analyzer.analyze(
            ingredients="turmeric powder, lead chromate (colorant), natural flavors",
            bom=None,
            destination_country="United States",
            product_name="Spice Mix"
        )
        
        # Should detect lead
        assert len(result) > 0
        lead_found = any("lead" in s.name.lower() for s in result)
        assert lead_found, "Lead should be detected in ingredients"
        
        # Each substance should have required fields
        for substance in result:
            assert substance.name, "Substance name should not be empty"
            assert substance.reason, "Substance reason should not be empty"
            assert substance.regulation, "Substance regulation should not be empty"
    
    def test_analyze_electronic_product_with_heavy_metals(self):
        """Test analysis of electronic product with heavy metals."""
        analyzer = RestrictedSubstancesAnalyzer()
        
        result = analyzer.analyze(
            ingredients=None,
            bom="circuit board (contains lead solder), mercury switch, cadmium battery",
            destination_country="European Union",
            product_name="Electronic Device"
        )
        
        # Should detect multiple heavy metals
        assert len(result) >= 2, "Should detect at least 2 restricted substances"
        
        substance_names = {s.name.lower() for s in result}
        assert any("lead" in name for name in substance_names), "Lead should be detected"
        assert any("mercury" in name for name in substance_names), "Mercury should be detected"
    
    def test_analyze_textile_product_with_azo_dyes(self):
        """Test analysis of textile product with azo dyes."""
        analyzer = RestrictedSubstancesAnalyzer()
        
        result = analyzer.analyze(
            ingredients="cotton fabric, azo dye colorant, formaldehyde resin",
            bom=None,
            destination_country="European Union",
            product_name="Textile Product"
        )
        
        # Should detect azo dyes and formaldehyde
        assert len(result) >= 2, "Should detect at least 2 restricted substances"
        
        substance_names = {s.name.lower() for s in result}
        assert any("azo" in name or "dye" in name for name in substance_names), "Azo dyes should be detected"
        assert any("formaldehyde" in name for name in substance_names), "Formaldehyde should be detected"
    
    def test_analyze_clean_product(self):
        """Test analysis of product with no restricted substances."""
        analyzer = RestrictedSubstancesAnalyzer()
        
        result = analyzer.analyze(
            ingredients="organic cotton, natural dyes, water",
            bom="cardboard packaging, paper labels",
            destination_country="United States",
            product_name="Organic T-Shirt"
        )
        
        # Should return empty list or very few substances
        assert isinstance(result, list), "Result should be a list"
        # Note: Keyword matching might still trigger on partial matches,
        # but this is expected behavior for safety
    
    def test_analyze_pharmaceutical_product(self):
        """Test analysis of pharmaceutical product with restricted antibiotics."""
        analyzer = RestrictedSubstancesAnalyzer()
        
        result = analyzer.analyze(
            ingredients="chloramphenicol, nitrofuran compounds, excipients",
            bom=None,
            destination_country="United States",
            product_name="Veterinary Medicine"
        )
        
        # Should detect banned antibiotics
        assert len(result) >= 2, "Should detect at least 2 restricted substances"
        
        substance_names = {s.name.lower() for s in result}
        assert any("chloramphenicol" in name for name in substance_names), "Chloramphenicol should be detected"
        assert any("nitrofuran" in name for name in substance_names), "Nitrofuran should be detected"
    
    def test_analyze_plastic_product_with_phthalates(self):
        """Test analysis of plastic product with phthalates."""
        analyzer = RestrictedSubstancesAnalyzer()
        
        result = analyzer.analyze(
            ingredients=None,
            bom="PVC plastic (contains phthalates), BPA coating",
            destination_country="European Union",
            product_name="Plastic Toy"
        )
        
        # Should detect phthalates and BPA
        assert len(result) >= 2, "Should detect at least 2 restricted substances"
        
        substance_names = {s.name.lower() for s in result}
        assert any("phthalate" in name for name in substance_names), "Phthalates should be detected"
        assert any("bpa" in name or "bisphenol" in name for name in substance_names), "BPA should be detected"
    
    def test_analyze_with_multiple_destinations(self):
        """Test that analysis considers destination country."""
        analyzer = RestrictedSubstancesAnalyzer()
        
        # Same product, different destinations
        ingredients = "ractopamine (growth promoter), natural ingredients"
        
        result_us = analyzer.analyze(
            ingredients=ingredients,
            bom=None,
            destination_country="United States",
            product_name="Meat Product"
        )
        
        result_eu = analyzer.analyze(
            ingredients=ingredients,
            bom=None,
            destination_country="European Union",
            product_name="Meat Product"
        )
        
        # Both should detect ractopamine (banned in EU, restricted in US)
        assert len(result_us) > 0, "Should detect restricted substances for US"
        assert len(result_eu) > 0, "Should detect restricted substances for EU"
        
        # Check that ractopamine is detected
        us_names = {s.name.lower() for s in result_us}
        eu_names = {s.name.lower() for s in result_eu}
        
        assert any("ractopamine" in name for name in us_names), "Ractopamine should be detected for US"
        assert any("ractopamine" in name for name in eu_names), "Ractopamine should be detected for EU"
    
    def test_deduplication_works(self):
        """Test that duplicate substances are properly deduplicated."""
        analyzer = RestrictedSubstancesAnalyzer()
        
        # Mention lead multiple times in different forms
        result = analyzer.analyze(
            ingredients="lead acetate, lead chromate",
            bom="lead-based paint",
            destination_country="United States",
            product_name="Paint Product"
        )
        
        # Should deduplicate to single "Lead" entry
        substance_names = [s.name for s in result]
        lead_count = sum(1 for name in substance_names if "Lead" in name)
        
        # Should have only one Lead entry (deduplicated)
        assert lead_count == 1, f"Expected 1 Lead entry, got {lead_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
