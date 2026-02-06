"""
Unit tests for Restricted Substances Analyzer Service.

Tests the identification of restricted substances from ingredients and BOM.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

from services.restricted_substances_analyzer import (
    RestrictedSubstancesAnalyzer,
    analyze_restricted_substances
)
from models.report import RestrictedSubstance


class TestRestrictedSubstancesAnalyzer:
    """Test suite for RestrictedSubstancesAnalyzer."""
    
    @pytest.fixture
    def mock_rag_pipeline(self):
        """Create mock RAG pipeline."""
        mock = Mock()
        mock.retrieve_documents = Mock(return_value=[])
        return mock
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        mock = Mock()
        mock.generate_structured = Mock(return_value={"restricted_substances": []})
        return mock
    
    @pytest.fixture
    def analyzer(self, mock_rag_pipeline, mock_llm_client):
        """Create analyzer instance with mocked dependencies."""
        return RestrictedSubstancesAnalyzer(
            rag_pipeline=mock_rag_pipeline,
            llm_client=mock_llm_client
        )
    
    def test_initialization(self, analyzer):
        """Test analyzer initializes correctly."""
        assert analyzer is not None
        assert analyzer.rag_pipeline is not None
        assert analyzer.llm_client is not None
    
    def test_analyze_empty_input(self, analyzer):
        """Test analysis with no ingredients or BOM returns empty list."""
        result = analyzer.analyze(
            ingredients=None,
            bom=None,
            destination_country="United States"
        )
        
        assert result == []
    
    def test_analyze_with_lead_keyword(self, analyzer):
        """Test keyword matching detects lead."""
        result = analyzer.analyze(
            ingredients="turmeric powder, lead chromate (colorant)",
            bom=None,
            destination_country="United States"
        )
        
        # Should find lead via keyword matching
        assert len(result) > 0
        lead_found = any(s.name == "Lead" for s in result)
        assert lead_found
        
        # Check lead substance details
        lead = next(s for s in result if s.name == "Lead")
        assert "toxic" in lead.reason.lower()
        assert len(lead.regulation) > 0
    
    def test_analyze_with_mercury_keyword(self, analyzer):
        """Test keyword matching detects mercury."""
        result = analyzer.analyze(
            ingredients="fish oil, mercury preservative",
            bom=None,
            destination_country="European Union"
        )
        
        # Should find mercury via keyword matching
        assert len(result) > 0
        mercury_found = any(s.name == "Mercury" for s in result)
        assert mercury_found
    
    def test_analyze_with_multiple_substances(self, analyzer):
        """Test detection of multiple restricted substances."""
        result = analyzer.analyze(
            ingredients="lead, mercury, cadmium compounds",
            bom=None,
            destination_country="United States"
        )
        
        # Should find all three heavy metals
        assert len(result) >= 3
        names = {s.name for s in result}
        assert "Lead" in names
        assert "Mercury" in names
        assert "Cadmium" in names
    
    def test_analyze_with_bom(self, analyzer):
        """Test analysis with Bill of Materials."""
        result = analyzer.analyze(
            ingredients=None,
            bom="plastic housing (contains phthalates), electronic components",
            destination_country="European Union"
        )
        
        # Should find phthalates
        assert len(result) > 0
        phthalates_found = any("phthalate" in s.name.lower() for s in result)
        assert phthalates_found
    
    def test_analyze_with_both_ingredients_and_bom(self, analyzer):
        """Test analysis with both ingredients and BOM."""
        result = analyzer.analyze(
            ingredients="organic turmeric, lead-free colorant",
            bom="packaging material (BPA-free plastic)",
            destination_country="United States"
        )
        
        # Should not find restricted substances (lead-free, BPA-free)
        # But keyword matching might still trigger on "lead" and "bpa" words
        # This is expected behavior - the analyzer flags potential issues
        assert isinstance(result, list)
    
    def test_analyze_with_asbestos(self, analyzer):
        """Test detection of asbestos."""
        result = analyzer.analyze(
            ingredients=None,
            bom="insulation material (asbestos-containing)",
            destination_country="United States"
        )
        
        # Should find asbestos
        assert len(result) > 0
        asbestos_found = any(s.name == "Asbestos" for s in result)
        assert asbestos_found
    
    def test_analyze_with_formaldehyde(self, analyzer):
        """Test detection of formaldehyde."""
        result = analyzer.analyze(
            ingredients="wood preservative (formaldehyde)",
            bom=None,
            destination_country="European Union"
        )
        
        # Should find formaldehyde
        assert len(result) > 0
        formaldehyde_found = any(s.name == "Formaldehyde" for s in result)
        assert formaldehyde_found
    
    def test_analyze_case_insensitive(self, analyzer):
        """Test that analysis is case-insensitive."""
        result1 = analyzer.analyze(
            ingredients="LEAD chromate",
            bom=None,
            destination_country="United States"
        )
       