"""
Unit tests for Report Generator Service

Tests the core functionality of the ReportGenerator service including:
- Report generation
- Certification identification
- Risk calculation
- Cost estimation
- Action plan generation
"""

import pytest
from datetime import datetime

from models.query import QueryInput, HSCodePrediction, HSCodeAlternative
from models.enums import BusinessType, CompanySize, ReportStatus
from services.report_generator import ReportGenerator, generate_report


class TestReportGenerator:
    """Test suite for ReportGenerator service."""
    
    def test_report_generator_initialization(self):
        """Test that ReportGenerator initializes correctly."""
        generator = ReportGenerator()
        
        assert generator is not None
        assert generator.hs_code_predictor is not None
        assert generator.rag_pipeline is not None
        assert generator.llm_client is not None
    
    def test_generate_report_basic(self):
        """Test basic report generation with minimal input."""
        generator = ReportGenerator()
        
        query = QueryInput(
            product_name="Organic Turmeric Powder",
            destination_country="United States",
            business_type=BusinessType.MANUFACTURING,
            company_size=CompanySize.MICRO
        )
        
        # Provide pre-computed HS code to avoid LLM call
        hs_code = HSCodePrediction(
            code="0910.30",
            confidence=85.0,
            description="Turmeric (curcuma)",
            alternatives=[]
        )
        
        report = generator.generate_report(query, hs_code=hs_code)
        
        # Verify report structure
        assert report is not None
        assert report.report_id.startswith("rpt_")
        assert report.status == ReportStatus.COMPLETED
        assert report.hs_code.code == "0910.30"
        assert isinstance(report.certifications, list)
        assert isinstance(report.risks, list)
        assert 0 <= report.risk_score <= 100
        assert report.timeline.estimated_days > 0
        assert report.costs.total > 0
        assert len(report.action_plan.days) == 7
        assert isinstance(report.generated_at, datetime)
    
    def test_identify_certifications_us_food(self):
        """Test certification identification for US food exports."""
        generator = ReportGenerator()
        
        certifications = generator.identify_certifications(
            hs_code="0910.30",  # Turmeric - food product
            destination_country="United States",
            product_type="Turmeric Powder",
            business_type="Manufacturing"
        )
        
        # Should include FDA certification for food
        assert len(certifications) > 0
        fda_cert = next((c for c in certifications if c.type.value == "FDA"), None)
        assert fda_cert is not None
        assert fda_cert.mandatory is True
    
    def test_identify_certifications_eu_electronics(self):
        """Test certification identification for EU electronics exports."""
        generator = ReportGenerator()
        
        certifications = generator.identify_certifications(
            hs_code="8517.62",  # Electronics
            destination_country="Germany",
            product_type="Wireless Router",
            business_type="Manufacturing"
        )
        
        # Should include CE marking for electronics
        assert len(certifications) > 0
        ce_cert = next((c for c in certifications if c.type.value == "CE"), None)
        assert ce_cert is not None
        assert ce_cert.mandatory is True
    
    def test_identify_certifications_saas(self):
        """Test certification identification for SaaS exports."""
        generator = ReportGenerator()
        
        certifications = generator.identify_certifications(
            hs_code="0000.00",  # Not applicable for SaaS
            destination_country="United States",
            product_type="Cloud Software",
            business_type="SaaS"
        )
        
        # Should include SOFTEX for SaaS
        assert len(certifications) > 0
        softex_cert = next((c for c in certifications if c.type.value == "SOFTEX"), None)
        assert softex_cert is not None
        assert softex_cert.mandatory is True
    
    def test_identify_restricted_substances(self):
        """Test restricted substance identification."""
        generator = ReportGenerator()
        
        # Test with lead in ingredients
        substances = generator.identify_restricted_substances(
            ingredients="Lead oxide, zinc oxide",
            bom="Lead-based paint, plastic housing",
            destination_country="European Union"
        )
        
        assert len(substances) > 0
        lead_substance = next((s for s in substances if "Lead" in s.name), None)
        assert lead_substance is not None
        assert "toxic" in lead_substance.reason.lower()
    
    def test_identify_restricted_substances_clean(self):
        """Test with no restricted substances."""
        generator = ReportGenerator()
        
        substances = generator.identify_restricted_substances(
            ingredients="Organic turmeric, natural color",
            bom="Paper packaging, cotton bags",
            destination_country="United States"
        )
        
        # Should find no restricted substances
        assert len(substances) == 0
    
    def test_calculate_risk_score_low_confidence(self):
        """Test risk score calculation with low HS code confidence."""
        generator = ReportGenerator()
        
        hs_code = HSCodePrediction(
            code="0910.30",
            confidence=50.0,  # Low confidence
            description="Turmeric",
            alternatives=[]
        )
        
        risk_score, risks = generator.calculate_risk_score(
            hs_code=hs_code,
            certifications=[],
            restricted_substances=[],
            past_rejections=[]
        )
        
        # Should have elevated risk due to low confidence
        assert risk_score > 20
        assert len(risks) > 0
        assert any("HS Code" in risk.title for risk in risks)
    
    def test_calculate_risk_score_restricted_substances(self):
        """Test risk score calculation with restricted substances."""
        generator = ReportGenerator()
        
        from models.report import RestrictedSubstance
        
        hs_code = HSCodePrediction(
            code="0910.30",
            confidence=90.0,
            description="Turmeric",
            alternatives=[]
        )
        
        restricted = [
            RestrictedSubstance(
                name="Lead",
                reason="Toxic heavy metal",
                regulation="EU REACH"
            )
        ]
        
        risk_score, risks = generator.calculate_risk_score(
            hs_code=hs_code,
            certifications=[],
            restricted_substances=restricted,
            past_rejections=[]
        )
        
        # Should have elevated risk due to restricted substances
        assert risk_score > 30
        assert len(risks) > 0
        assert any("Restricted" in risk.title for risk in risks)
    
    def test_estimate_costs(self):
        """Test cost estimation."""
        generator = ReportGenerator()
        
        from models.certification import Certification
        from models.common import CostRange
        from models.enums import CertificationType, Priority
        
        certifications = [
            Certification(
                id="test-cert",
                name="Test Certification",
                type=CertificationType.FDA,
                mandatory=True,
                estimated_cost=CostRange(min=10000, max=20000, currency="INR"),
                estimated_timeline_days=30,
                priority=Priority.HIGH
            )
        ]
        
        query = QueryInput(
            product_name="Test Product",
            destination_country="US",
            business_type=BusinessType.MANUFACTURING,
            company_size=CompanySize.MICRO
        )
        
        costs = generator.estimate_costs(certifications, query)
        
        assert costs.certifications > 0
        assert costs.documentation > 0
        assert costs.logistics > 0
        assert costs.total == costs.certifications + costs.documentation + costs.logistics
        assert costs.currency == "INR"
    
    def test_identify_subsidies_micro_enterprise(self):
        """Test subsidy identification for micro enterprises."""
        generator = ReportGenerator()
        
        from models.certification import Certification
        from models.common import CostRange
        from models.enums import CertificationType, Priority
        
        certifications = [
            Certification(
                id="zed-cert",
                name="ZED Certification",
                type=CertificationType.ZED,
                mandatory=False,
                estimated_cost=CostRange(min=20000, max=100000, currency="INR"),
                estimated_timeline_days=90,
                priority=Priority.MEDIUM
            )
        ]
        
        subsidies = generator.identify_subsidies(
            certifications=certifications,
            company_size="Micro",
            business_type="Manufacturing"
        )
        
        # Should include ZED subsidy for micro enterprises
        assert len(subsidies) > 0
        zed_subsidy = next((s for s in subsidies if "ZED" in s.name), None)
        assert zed_subsidy is not None
        assert zed_subsidy.percentage == 80.0
    
    def test_generate_action_plan(self):
        """Test 7-day action plan generation."""
        generator = ReportGenerator()
        
        query = QueryInput(
            product_name="Test Product",
            destination_country="US",
            business_type=BusinessType.MANUFACTURING,
            company_size=CompanySize.MICRO
        )
        
        action_plan = generator.generate_action_plan(
            certifications=[],
            compliance_roadmap=[],
            query=query
        )
        
        # Verify action plan structure
        assert len(action_plan.days) == 7
        assert action_plan.progress_percentage == 0.0
        
        # Verify each day has tasks
        for day in action_plan.days:
            assert 1 <= day.day <= 7
            assert len(day.tasks) > 0
            assert day.title is not None
        
        # Verify day 1 includes GST LUT
        day1 = action_plan.days[0]
        assert any("GST" in task.title for task in day1.tasks)
    
    def test_generate_compliance_roadmap(self):
        """Test compliance roadmap generation."""
        generator = ReportGenerator()
        
        from models.certification import Certification
        from models.common import CostRange
        from models.enums import CertificationType, Priority
        
        certifications = [
            Certification(
                id="test-cert",
                name="Test Certification",
                type=CertificationType.FDA,
                mandatory=True,
                estimated_cost=CostRange(min=10000, max=20000, currency="INR"),
                estimated_timeline_days=30,
                priority=Priority.HIGH
            )
        ]
        
        query = QueryInput(
            product_name="Test Product",
            destination_country="US",
            business_type=BusinessType.MANUFACTURING,
            company_size=CompanySize.MICRO
        )
        
        roadmap = generator.generate_compliance_roadmap(certifications, query)
        
        # Verify roadmap structure
        assert len(roadmap) > 0
        
        # Verify steps are numbered sequentially
        for i, step in enumerate(roadmap, 1):
            assert step.step == i
            assert step.duration_days > 0
        
        # Verify GST LUT is first step
        assert "GST" in roadmap[0].title
    
    def test_estimate_timeline(self):
        """Test timeline estimation."""
        generator = ReportGenerator()
        
        from models.certification import Certification
        from models.common import CostRange
        from models.enums import CertificationType, Priority
        from models.report import RoadmapStep
        
        certifications = [
            Certification(
                id="test-cert",
                name="Test Certification",
                type=CertificationType.FDA,
                mandatory=True,
                estimated_cost=CostRange(min=10000, max=20000, currency="INR"),
                estimated_timeline_days=30,
                priority=Priority.HIGH
            )
        ]
        
        roadmap = [
            RoadmapStep(
                step=1,
                title="Step 1",
                description="Test step",
                duration_days=10,
                dependencies=[]
            )
        ]
        
        timeline = generator.estimate_timeline(certifications, roadmap)
        
        assert timeline.estimated_days > 0
        assert len(timeline.breakdown) > 0
        
        # Verify breakdown sums to total
        breakdown_total = sum(phase.duration_days for phase in timeline.breakdown)
        assert timeline.estimated_days == breakdown_total
    
    def test_convenience_function(self):
        """Test convenience function for report generation."""
        query = QueryInput(
            product_name="Test Product",
            destination_country="United States",
            business_type=BusinessType.MANUFACTURING,
            company_size=CompanySize.MICRO
        )
        
        # This will call the full pipeline including HS code prediction
        # In a real test, we'd mock the LLM calls
        # For now, just verify the function exists and has correct signature
        assert callable(generate_report)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
