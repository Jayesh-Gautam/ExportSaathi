"""
Integration test for past rejection data retrieval

This test verifies that the past rejection retrieval functionality works
end-to-end with the RAG pipeline and knowledge base.
"""

import pytest
import logging

from models.query import QueryInput, HSCodePrediction
from models.enums import BusinessType, CompanySize, RejectionSource
from services.report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPastRejectionIntegration:
    """Integration tests for past rejection data retrieval."""
    
    def test_full_report_with_rejection_data_us(self):
        """Test full report generation includes past rejection data for US exports."""
        generator = ReportGenerator()
        
        # Create query for food product to US (likely to have FDA rejection data)
        query = QueryInput(
            product_name="Turmeric Powder",
            destination_country="United States",
            business_type=BusinessType.MANUFACTURING,
            company_size=CompanySize.MICRO,
            ingredients="Organic turmeric, natural color"
        )
        
        # Provide HS code to avoid LLM call
        hs_code = HSCodePrediction(
            code="0910.30",
            confidence=85.0,
            description="Turmeric (curcuma)",
            alternatives=[]
        )
        
        # Generate full report
        report = generator.generate_report(query, hs_code=hs_code)
        
        # Verify report structure
        assert report is not None
        assert report.report_id is not None
        
        # Verify past rejections are included
        assert hasattr(report, 'past_rejections')
        assert isinstance(report.past_rejections, list)
        
        # Log results
        logger.info(f"Report generated with {len(report.past_rejections)} past rejections")
        
        # If rejections found, verify structure
        for rejection in report.past_rejections:
            logger.info(f"  - {rejection.product_type}: {rejection.reason} ({rejection.source}, {rejection.date})")
            assert rejection.product_type is not None
            assert rejection.reason is not None
            assert rejection.source in [RejectionSource.FDA, RejectionSource.EU_RASFF, RejectionSource.OTHER]
            assert rejection.date is not None
        
        # Verify risk score considers past rejections
        if len(report.past_rejections) > 0:
            # Risk score should be elevated if rejections found
            assert report.risk_score > 10
            # Should have a risk related to historical rejections
            rejection_risks = [r for r in report.risks if "Rejection" in r.title or "Historical" in r.title]
            assert len(rejection_risks) > 0
    
    def test_full_report_with_rejection_data_eu(self):
        """Test full report generation includes past rejection data for EU exports."""
        generator = ReportGenerator()
        
        # Create query for food product to EU (likely to have RASFF data)
        query = QueryInput(
            product_name="Basmati Rice",
            destination_country="Germany",
            business_type=BusinessType.MANUFACTURING,
            company_size=CompanySize.SMALL,
            ingredients="Basmati rice"
        )
        
        # Provide HS code to avoid LLM call
        hs_code = HSCodePrediction(
            code="1006.30",
            confidence=90.0,
            description="Semi-milled or wholly milled rice",
            alternatives=[]
        )
        
        # Generate full report
        report = generator.generate_report(query, hs_code=hs_code)
        
        # Verify report structure
        assert report is not None
        assert report.report_id is not None
        
        # Verify past rejections are included
        assert hasattr(report, 'past_rejections')
        assert isinstance(report.past_rejections, list)
        
        # Log results
        logger.info(f"Report generated with {len(report.past_rejections)} past rejections")
        
        # If rejections found, verify structure
        for rejection in report.past_rejections:
            logger.info(f"  - {rejection.product_type}: {rejection.reason} ({rejection.source}, {rejection.date})")
            assert rejection.product_type is not None
            assert rejection.reason is not None
            assert rejection.source in [RejectionSource.FDA, RejectionSource.EU_RASFF, RejectionSource.OTHER]
            assert rejection.date is not None
    
    def test_rejection_retrieval_with_various_products(self):
        """Test rejection retrieval works for various product types."""
        generator = ReportGenerator()
        
        test_cases = [
            ("Turmeric Powder", "United States"),
            ("Basmati Rice", "Germany"),
            ("Cashew Nuts", "United States"),
            ("Black Pepper", "France"),
            ("Dried Mango", "United Kingdom"),
        ]
        
        for product_type, destination in test_cases:
            logger.info(f"\nTesting: {product_type} -> {destination}")
            
            rejections = generator.retrieve_rejection_reasons(
                product_type=product_type,
                destination_country=destination
            )
            
            # Should return a list (may be empty)
            assert isinstance(rejections, list)
            
            # Log results
            logger.info(f"  Found {len(rejections)} past rejections")
            
            # Verify structure if rejections found
            for rejection in rejections:
                assert rejection.product_type is not None
                assert rejection.reason is not None
                assert rejection.source in [RejectionSource.FDA, RejectionSource.EU_RASFF, RejectionSource.OTHER]
                assert rejection.date is not None
    
    def test_rejection_data_filters_by_destination(self):
        """Test that rejection data is filtered appropriately by destination."""
        generator = ReportGenerator()
        
        # Test US destination - should query FDA
        us_rejections = generator.retrieve_rejection_reasons(
            product_type="Spices",
            destination_country="United States"
        )
        
        # If rejections found for US, they should be from FDA
        for rejection in us_rejections:
            if rejection.source != RejectionSource.OTHER:
                assert rejection.source == RejectionSource.FDA
        
        # Test EU destination - should query EU RASFF
        eu_rejections = generator.retrieve_rejection_reasons(
            product_type="Spices",
            destination_country="Germany"
        )
        
        # If rejections found for EU, they should be from EU_RASFF
        for rejection in eu_rejections:
            if rejection.source != RejectionSource.OTHER:
                assert rejection.source == RejectionSource.EU_RASFF
        
        logger.info(f"US rejections: {len(us_rejections)}, EU rejections: {len(eu_rejections)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
