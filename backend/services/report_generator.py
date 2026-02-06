"""
Report Generator Service for ExportSathi

This service orchestrates the generation of comprehensive export readiness reports.
It combines HS code prediction, certification identification, risk analysis, cost estimation,
and action plan generation into a single cohesive report.

CRITICAL MVP TASK: This is a minimal but functional implementation focused on:
1. Using existing HSCodePredictor service
2. Basic certification identification logic
3. Simple but complete report structure
4. Can be called from API endpoints

Requirements: 2.2, 2.5, 2.6, 2.7
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from models.query import QueryInput, HSCodePrediction
from models.report import (
    ExportReadinessReport,
    RestrictedSubstance,
    PastRejection,
    RoadmapStep,
    Risk,
    Timeline,
    TimelinePhase,
    CostBreakdown
)
from models.certification import Certification, Subsidy
from models.action_plan import ActionPlan, DayPlan, Task
from models.common import CostRange, Source
from models.enums import (
    CertificationType,
    Priority,
    RiskSeverity,
    ReportStatus,
    RejectionSource,
    TaskCategory
)
from services.hs_code_predictor import HSCodePredictor
from services.rag_pipeline import RAGPipeline, get_rag_pipeline
from services.llm_client import LLMClient, create_llm_client

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive export readiness reports.
    
    This service orchestrates multiple components to create a complete report:
    1. HS code prediction (via HSCodePredictor)
    2. Certification identification (based on HS code and destination)
    3. Risk analysis (product complexity and historical data)
    4. Cost estimation (certifications, documentation, logistics)
    5. Subsidy identification (ZED, RoDTEP, etc.)
    6. Compliance roadmap generation
    7. 7-day action plan creation
    8. Source citation retrieval
    
    MVP Focus: Minimal but functional implementation that can be extended later.
    
    Requirements: 2.2, 2.5, 2.6, 2.7
    """
    
    def __init__(
        self,
        hs_code_predictor: Optional[HSCodePredictor] = None,
        rag_pipeline: Optional[RAGPipeline] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize Report Generator.
        
        Args:
            hs_code_predictor: HS code prediction service (creates new if None)
            rag_pipeline: RAG pipeline for document retrieval (uses global if None)
            llm_client: LLM client for generation (creates new if None)
        """
        self.hs_code_predictor = hs_code_predictor or HSCodePredictor()
        self.rag_pipeline = rag_pipeline or get_rag_pipeline()
        self.llm_client = llm_client or create_llm_client()
        
        logger.info("ReportGenerator initialized")
    
    def generate_report(
        self,
        query: QueryInput,
        hs_code: Optional[HSCodePrediction] = None
    ) -> ExportReadinessReport:
        """
        Generate comprehensive export readiness report.
        
        This is the main entry point for report generation. It orchestrates:
        1. HS code prediction (if not provided)
        2. Certification identification
        3. Risk analysis
        4. Cost estimation
        5. Compliance roadmap generation
        6. Action plan creation
        
        Args:
            query: User query with product and destination information
            hs_code: Pre-computed HS code prediction (predicts if None)
            
        Returns:
            Complete ExportReadinessReport
            
        Example:
            >>> generator = ReportGenerator()
            >>> query = QueryInput(
            ...     product_name="Organic Turmeric Powder",
            ...     destination_country="United States",
            ...     business_type="Manufacturing",
            ...     company_size="Micro"
            ... )
            >>> report = generator.generate_report(query)
            >>> print(f"Risk Score: {report.risk_score}")
        
        Requirements: 2.2, 2.5, 2.6, 2.7
        """
        logger.info(f"Generating export readiness report for: {query.product_name} -> {query.destination_country}")
        
        try:
            # Generate unique report ID
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            
            # Step 1: Predict HS code if not provided
            if hs_code is None:
                logger.info("Predicting HS code...")
                hs_code = self.hs_code_predictor.predict_hs_code(
                    product_name=query.product_name,
                    image=query.product_image,
                    bom=query.bom,
                    ingredients=query.ingredients,
                    destination_country=query.destination_country
                )
            
            logger.info(f"HS Code: {hs_code.code} (confidence: {hs_code.confidence}%)")
            
            # Step 2: Identify required certifications
            logger.info("Identifying required certifications...")
            certifications = self.identify_certifications(
                hs_code=hs_code.code,
                destination_country=query.destination_country,
                product_type=query.product_name,
                business_type=query.business_type
            )
            
            logger.info(f"Identified {len(certifications)} certifications")
            
            # Step 3: Identify restricted substances (MVP: basic implementation)
            logger.info("Identifying restricted substances...")
            restricted_substances = self.identify_restricted_substances(
                ingredients=query.ingredients,
                bom=query.bom,
                destination_country=query.destination_country
            )
            
            # Step 4: Retrieve past rejection data (MVP: basic implementation)
            logger.info("Retrieving past rejection data...")
            past_rejections = self.retrieve_rejection_reasons(
                product_type=query.product_name,
                destination_country=query.destination_country
            )
            
            # Step 5: Generate compliance roadmap
            logger.info("Generating compliance roadmap...")
            compliance_roadmap = self.generate_compliance_roadmap(
                certifications=certifications,
                query=query
            )
            
            # Step 6: Calculate risk score
            logger.info("Calculating risk score...")
            risk_score, risks = self.calculate_risk_score(
                hs_code=hs_code,
                certifications=certifications,
                restricted_substances=restricted_substances,
                past_rejections=past_rejections
            )
            
            logger.info(f"Risk score: {risk_score}")
            
            # Step 7: Estimate timeline
            logger.info("Estimating timeline...")
            timeline = self.estimate_timeline(
                certifications=certifications,
                compliance_roadmap=compliance_roadmap
            )
            
            # Step 8: Estimate costs
            logger.info("Estimating costs...")
            costs = self.estimate_costs(
                certifications=certifications,
                query=query
            )
            
            # Step 9: Identify applicable subsidies
            logger.info("Identifying subsidies...")
            subsidies = self.identify_subsidies(
                certifications=certifications,
                company_size=query.company_size,
                business_type=query.business_type
            )
            
            # Step 10: Generate 7-day action plan
            logger.info("Generating action plan...")
            action_plan = self.generate_action_plan(
                certifications=certifications,
                compliance_roadmap=compliance_roadmap,
                query=query
            )
            
            # Step 11: Retrieve source citations
            logger.info("Retrieving source citations...")
            sources = self.retrieve_sources(
                query=query,
                hs_code=hs_code.code
            )
            
            # Build complete report
            report = ExportReadinessReport(
                report_id=report_id,
                status=ReportStatus.COMPLETED,
                hs_code=hs_code,
                certifications=certifications,
                restricted_substances=restricted_substances,
                past_rejections=past_rejections,
                compliance_roadmap=compliance_roadmap,
                risks=risks,
                risk_score=risk_score,
                timeline=timeline,
                costs=costs,
                subsidies=subsidies,
                action_plan=action_plan,
                retrieved_sources=sources,
                generated_at=datetime.utcnow()
            )
            
            logger.info(f"Report generation completed: {report_id}")
            return report
        
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            raise
    
    def identify_certifications(
        self,
        hs_code: str,
        destination_country: str,
        product_type: str,
        business_type: str
    ) -> List[Certification]:
        """
        Identify required certifications based on HS code and destination.
        
        MVP Implementation: Basic certification mapping with common certifications.
        This can be enhanced later with RAG-based retrieval from knowledge base.
        
        Args:
            hs_code: Product HS code
            destination_country: Destination country
            product_type: Product type/name
            business_type: Business type (Manufacturing/SaaS/Merchant)
            
        Returns:
            List of required certifications
            
        Requirements: 2.2
        """
        certifications = []
        
        # MVP: Basic certification rules based on destination and product type
        # This is a simplified implementation - can be enhanced with RAG later
        
        # US exports - FDA requirements
        if destination_country.upper() in ["UNITED STATES", "USA", "US"]:
            # Food products (HS codes starting with 01-24)
            if hs_code[:2] in [f"{i:02d}" for i in range(1, 25)]:
                certifications.append(Certification(
                    id="fda-food-facility",
                    name="FDA Food Facility Registration",
                    type=CertificationType.FDA,
                    mandatory=True,
                    estimated_cost=CostRange(min=15000, max=30000, currency="INR"),
                    estimated_timeline_days=30,
                    priority=Priority.HIGH
                ))
        
        # EU exports - CE marking for certain products
        if destination_country.upper() in ["EUROPEAN UNION", "EU", "GERMANY", "FRANCE", "ITALY", "SPAIN"]:
            # Electronics, machinery, toys (simplified check)
            if hs_code[:2] in ["84", "85", "95"]:
                certifications.append(Certification(
                    id="ce-marking",
                    name="CE Marking",
                    type=CertificationType.CE,
                    mandatory=True,
                    estimated_cost=CostRange(min=50000, max=150000, currency="INR"),
                    estimated_timeline_days=60,
                    priority=Priority.HIGH
                ))
        
        # SaaS exports - SOFTEX
        if business_type == "SaaS":
            certifications.append(Certification(
                id="softex",
                name="SOFTEX Declaration",
                type=CertificationType.SOFTEX,
                mandatory=True,
                estimated_cost=CostRange(min=5000, max=10000, currency="INR"),
                estimated_timeline_days=7,
                priority=Priority.HIGH
            ))
        
        # ZED certification - optional but beneficial for manufacturing
        if business_type == "Manufacturing":
            certifications.append(Certification(
                id="zed-certification",
                name="ZED (Zero Defect Zero Effect) Certification",
                type=CertificationType.ZED,
                mandatory=False,
                estimated_cost=CostRange(min=20000, max=100000, currency="INR"),
                estimated_timeline_days=90,
                priority=Priority.MEDIUM
            ))
        
        # BIS certification for certain products
        if hs_code[:2] in ["84", "85"]:  # Electronics and machinery
            certifications.append(Certification(
                id="bis-certification",
                name="BIS (Bureau of Indian Standards) Certification",
                type=CertificationType.BIS,
                mandatory=False,
                estimated_cost=CostRange(min=30000, max=80000, currency="INR"),
                estimated_timeline_days=45,
                priority=Priority.MEDIUM
            ))
        
        logger.info(f"Identified {len(certifications)} certifications for {destination_country}")
        return certifications
    
    def identify_restricted_substances(
        self,
        ingredients: Optional[str],
        bom: Optional[str],
        destination_country: str
    ) -> List[RestrictedSubstance]:
        """
        Identify restricted substances from ingredients/BOM.
        
        MVP Implementation: Basic keyword matching for common restricted substances.
        Can be enhanced with RAG-based retrieval later.
        
        Args:
            ingredients: Product ingredients
            bom: Bill of Materials
            destination_country: Destination country
            
        Returns:
            List of restricted substances
            
        Requirements: 2.3
        """
        restricted = []
        
        # Combine ingredients and BOM for analysis
        content = " ".join(filter(None, [ingredients or "", bom or ""])).lower()
        
        if not content:
            return restricted
        
        # MVP: Basic keyword matching for common restricted substances
        restricted_keywords = {
            "lead": ("Lead", "Toxic heavy metal", "EU REACH Annex XVII"),
            "mercury": ("Mercury", "Toxic heavy metal", "EU REACH Annex XVII"),
            "cadmium": ("Cadmium", "Toxic heavy metal", "EU REACH Annex XVII"),
            "asbestos": ("Asbestos", "Carcinogenic material", "Banned in most countries"),
            "phthalates": ("Phthalates", "Endocrine disruptor", "EU REACH Annex XVII"),
        }
        
        for keyword, (name, reason, regulation) in restricted_keywords.items():
            if keyword in content:
                restricted.append(RestrictedSubstance(
                    name=name,
                    reason=reason,
                    regulation=regulation
                ))
        
        logger.info(f"Identified {len(restricted)} restricted substances")
        return restricted
    
    def retrieve_rejection_reasons(
        self,
        product_type: str,
        destination_country: str
    ) -> List[PastRejection]:
        """
        Retrieve past rejection data from FDA/EU databases.
        
        MVP Implementation: Returns empty list - can be enhanced with actual database queries.
        
        Args:
            product_type: Product type
            destination_country: Destination country
            
        Returns:
            List of past rejections
            
        Requirements: 2.4
        """
        # MVP: Return empty list - this would query FDA refusal database in full implementation
        logger.info("Past rejection retrieval not implemented in MVP")
        return []
    
    def generate_compliance_roadmap(
        self,
        certifications: List[Certification],
        query: QueryInput
    ) -> List[RoadmapStep]:
        """
        Generate compliance roadmap with timeline and dependencies.
        
        Args:
            certifications: Required certifications
            query: User query
            
        Returns:
            List of roadmap steps
            
        Requirements: 2.5
        """
        roadmap = []
        step_num = 1
        
        # Step 1: GST LUT application (always first)
        roadmap.append(RoadmapStep(
            step=step_num,
            title="Apply for GST LUT",
            description="Submit Letter of Undertaking for GST exemption on exports",
            duration_days=7,
            dependencies=[]
        ))
        step_num += 1
        
        # Step 2: HS code confirmation
        roadmap.append(RoadmapStep(
            step=step_num,
            title="Confirm HS Code Classification",
            description="Verify HS code with customs or trade consultant",
            duration_days=3,
            dependencies=[]
        ))
        step_num += 1
        
        # Add certification steps
        for cert in certifications:
            if cert.mandatory:
                roadmap.append(RoadmapStep(
                    step=step_num,
                    title=f"Obtain {cert.name}",
                    description=f"Apply for and obtain {cert.name} certification",
                    duration_days=cert.estimated_timeline_days,
                    dependencies=["Apply for GST LUT"]
                ))
                step_num += 1
        
        # Document preparation
        roadmap.append(RoadmapStep(
            step=step_num,
            title="Prepare Export Documents",
            description="Generate commercial invoice, packing list, and shipping bill",
            duration_days=5,
            dependencies=["Confirm HS Code Classification"]
        ))
        step_num += 1
        
        # Logistics setup
        roadmap.append(RoadmapStep(
            step=step_num,
            title="Setup Logistics",
            description="Select freight forwarder and book shipment",
            duration_days=7,
            dependencies=["Prepare Export Documents"]
        ))
        
        logger.info(f"Generated compliance roadmap with {len(roadmap)} steps")
        return roadmap
    
    def calculate_risk_score(
        self,
        hs_code: HSCodePrediction,
        certifications: List[Certification],
        restricted_substances: List[RestrictedSubstance],
        past_rejections: List[PastRejection]
    ) -> tuple[int, List[Risk]]:
        """
        Calculate risk score (0-100) based on product complexity and historical data.
        
        Args:
            hs_code: HS code prediction
            certifications: Required certifications
            restricted_substances: Restricted substances
            past_rejections: Past rejection data
            
        Returns:
            Tuple of (risk_score, list_of_risks)
            
        Requirements: 2.6
        """
        base_risk = 20  # Base risk for any export
        risks = []
        
        # Factor 1: HS code confidence (lower confidence = higher risk)
        if hs_code.confidence < 70:
            base_risk += 15
            risks.append(Risk(
                title="HS Code Uncertainty",
                description=f"HS code prediction confidence is {hs_code.confidence}%, which may lead to customs issues",
                severity=RiskSeverity.MEDIUM,
                mitigation="Verify HS code with customs broker or trade consultant before shipping"
            ))
        
        # Factor 2: Number of mandatory certifications
        mandatory_certs = [c for c in certifications if c.mandatory]
        if len(mandatory_certs) > 2:
            base_risk += 10
            risks.append(Risk(
                title="Multiple Certifications Required",
                description=f"{len(mandatory_certs)} mandatory certifications needed, increasing complexity",
                severity=RiskSeverity.MEDIUM,
                mitigation="Start certification applications early and consider hiring a consultant"
            ))
        
        # Factor 3: Restricted substances
        if restricted_substances:
            base_risk += 20
            risks.append(Risk(
                title="Restricted Substances Detected",
                description=f"{len(restricted_substances)} restricted substances found in product",
                severity=RiskSeverity.HIGH,
                mitigation="Review product formulation and ensure compliance with destination regulations"
            ))
        
        # Factor 4: Past rejections
        if past_rejections:
            base_risk += 15
            risks.append(Risk(
                title="Historical Rejections",
                description=f"Similar products have been rejected {len(past_rejections)} times",
                severity=RiskSeverity.HIGH,
                mitigation="Study past rejection reasons and implement preventive measures"
            ))
        
        # Cap risk score at 100
        risk_score = min(base_risk, 100)
        
        logger.info(f"Calculated risk score: {risk_score} with {len(risks)} identified risks")
        return risk_score, risks
    
    def estimate_timeline(
        self,
        certifications: List[Certification],
        compliance_roadmap: List[RoadmapStep]
    ) -> Timeline:
        """
        Estimate timeline for export readiness.
        
        Args:
            certifications: Required certifications
            compliance_roadmap: Compliance roadmap
            
        Returns:
            Timeline with breakdown
            
        Requirements: 2.5
        """
        # Calculate total from roadmap
        total_days = sum(step.duration_days for step in compliance_roadmap)
        
        # Create breakdown by phase
        breakdown = [
            TimelinePhase(phase="Documentation", duration_days=10),
            TimelinePhase(phase="Certifications", duration_days=max(
                [c.estimated_timeline_days for c in certifications] if certifications else [0]
            )),
            TimelinePhase(phase="Logistics Setup", duration_days=7)
        ]
        
        # Recalculate total from breakdown
        total_days = sum(phase.duration_days for phase in breakdown)
        
        return Timeline(
            estimated_days=total_days,
            breakdown=breakdown
        )
    
    def estimate_costs(
        self,
        certifications: List[Certification],
        query: QueryInput
    ) -> CostBreakdown:
        """
        Estimate costs for certifications, documentation, and logistics.
        
        Args:
            certifications: Required certifications
            query: User query
            
        Returns:
            Cost breakdown
            
        Requirements: 2.7
        """
        # Sum certification costs (use average of min/max)
        cert_costs = sum(
            (cert.estimated_cost.min + cert.estimated_cost.max) / 2
            for cert in certifications
        )
        
        # Fixed documentation costs (MVP estimate)
        doc_costs = 10000.0
        
        # Logistics costs (MVP estimate based on destination)
        logistics_costs = 25000.0
        
        total = cert_costs + doc_costs + logistics_costs
        
        return CostBreakdown(
            certifications=cert_costs,
            documentation=doc_costs,
            logistics=logistics_costs,
            total=total,
            currency="INR"
        )
    
    def identify_subsidies(
        self,
        certifications: List[Certification],
        company_size: str,
        business_type: str
    ) -> List[Subsidy]:
        """
        Identify applicable subsidies (ZED, RoDTEP, etc.).
        
        Args:
            certifications: Required certifications
            company_size: Company size
            business_type: Business type
            
        Returns:
            List of applicable subsidies
            
        Requirements: 2.7
        """
        subsidies = []
        
        # ZED subsidy for micro enterprises
        if company_size == "Micro":
            zed_cert = next((c for c in certifications if c.type == CertificationType.ZED), None)
            if zed_cert:
                subsidy_amount = (zed_cert.estimated_cost.min + zed_cert.estimated_cost.max) / 2 * 0.8
                subsidies.append(Subsidy(
                    name="ZED Certification Subsidy",
                    amount=subsidy_amount,
                    percentage=80.0,
                    eligibility="Micro enterprises only",
                    application_process="Apply through ZED portal with company registration documents"
                ))
        
        # RoDTEP - applicable to all exporters
        subsidies.append(Subsidy(
            name="RoDTEP (Remission of Duties and Taxes on Exported Products)",
            amount=0.0,  # Calculated based on actual export value
            percentage=1.5,  # Average rate
            eligibility="All exporters",
            application_process="Automatic credit after customs clearance"
        ))
        
        logger.info(f"Identified {len(subsidies)} applicable subsidies")
        return subsidies
    
    def generate_action_plan(
        self,
        certifications: List[Certification],
        compliance_roadmap: List[RoadmapStep],
        query: QueryInput
    ) -> ActionPlan:
        """
        Generate 7-day action plan for export readiness.
        
        Args:
            certifications: Required certifications
            compliance_roadmap: Compliance roadmap
            query: User query
            
        Returns:
            7-day action plan
            
        Requirements: 2.5
        """
        days = []
        
        # Day 1: Documentation setup
        days.append(DayPlan(
            day=1,
            title="Documentation Setup",
            tasks=[
                Task(
                    id="task_gst_lut",
                    title="Apply for GST LUT",
                    description="Submit Letter of Undertaking for GST exemption on exports",
                    category=TaskCategory.DOCUMENTATION,
                    completed=False,
                    estimated_duration="2-3 hours",
                    dependencies=[]
                ),
                Task(
                    id="task_hs_code",
                    title="Confirm HS Code",
                    description="Verify HS code classification with customs broker",
                    category=TaskCategory.DOCUMENTATION,
                    completed=False,
                    estimated_duration="1-2 hours",
                    dependencies=[]
                )
            ]
        ))
        
        # Day 2-3: Certification applications
        cert_tasks = []
        for i, cert in enumerate(certifications[:2]):  # Limit to 2 for MVP
            if cert.mandatory:
                cert_tasks.append(Task(
                    id=f"task_cert_{i}",
                    title=f"Apply for {cert.name}",
                    description=f"Start application process for {cert.name}",
                    category=TaskCategory.CERTIFICATION,
                    completed=False,
                    estimated_duration="3-4 hours",
                    dependencies=[]
                ))
        
        if cert_tasks:
            days.append(DayPlan(
                day=2,
                title="Certification Applications",
                tasks=cert_tasks[:len(cert_tasks)//2 + 1]
            ))
            if len(cert_tasks) > 1:
                days.append(DayPlan(
                    day=3,
                    title="Certification Applications (Continued)",
                    tasks=cert_tasks[len(cert_tasks)//2 + 1:]
                ))
            else:
                days.append(DayPlan(
                    day=3,
                    title="Document Preparation",
                    tasks=[
                        Task(
                            id="task_doc_prep",
                            title="Gather Required Documents",
                            description="Collect all documents needed for certifications",
                            category=TaskCategory.DOCUMENTATION,
                            completed=False,
                            estimated_duration="4-5 hours",
                            dependencies=[]
                        )
                    ]
                ))
        else:
            # No certifications - focus on documentation
            days.append(DayPlan(
                day=2,
                title="Document Preparation",
                tasks=[
                    Task(
                        id="task_invoice",
                        title="Prepare Commercial Invoice",
                        description="Create commercial invoice template",
                        category=TaskCategory.DOCUMENTATION,
                        completed=False,
                        estimated_duration="2-3 hours",
                        dependencies=[]
                    )
                ]
            ))
            days.append(DayPlan(
                day=3,
                title="Document Preparation (Continued)",
                tasks=[
                    Task(
                        id="task_packing",
                        title="Prepare Packing List",
                        description="Create packing list template",
                        category=TaskCategory.DOCUMENTATION,
                        completed=False,
                        estimated_duration="2-3 hours",
                        dependencies=[]
                    )
                ]
            ))
        
        # Day 4-5: More documentation
        days.append(DayPlan(
            day=4,
            title="Export Documentation",
            tasks=[
                Task(
                    id="task_shipping_bill",
                    title="Prepare Shipping Bill",
                    description="Create shipping bill draft",
                    category=TaskCategory.DOCUMENTATION,
                    completed=False,
                    estimated_duration="3-4 hours",
                    dependencies=[]
                )
            ]
        ))
        
        days.append(DayPlan(
            day=5,
            title="Financial Planning",
            tasks=[
                Task(
                    id="task_finance",
                    title="Calculate Working Capital",
                    description="Estimate working capital requirements and explore financing options",
                    category=TaskCategory.FINANCE,
                    completed=False,
                    estimated_duration="2-3 hours",
                    dependencies=[]
                )
            ]
        ))
        
        # Day 6: Logistics
        days.append(DayPlan(
            day=6,
            title="Logistics Planning",
            tasks=[
                Task(
                    id="task_logistics",
                    title="Select Freight Forwarder",
                    description="Research and select freight forwarder for shipment",
                    category=TaskCategory.LOGISTICS,
                    completed=False,
                    estimated_duration="3-4 hours",
                    dependencies=[]
                )
            ]
        ))
        
        # Day 7: Review
        days.append(DayPlan(
            day=7,
            title="Final Review",
            tasks=[
                Task(
                    id="task_review",
                    title="Review Export Readiness",
                    description="Review all documents and certifications, ensure everything is in order",
                    category=TaskCategory.DOCUMENTATION,
                    completed=False,
                    estimated_duration="2-3 hours",
                    dependencies=[]
                )
            ]
        ))
        
        return ActionPlan(
            days=days,
            progress_percentage=0.0
        )
    
    def retrieve_sources(
        self,
        query: QueryInput,
        hs_code: str
    ) -> List[Source]:
        """
        Retrieve and include source citations from knowledge base.
        
        Args:
            query: User query
            hs_code: Product HS code
            
        Returns:
            List of source citations
            
        Requirements: 2.7
        """
        try:
            # Build search query
            search_query = f"{query.product_name} {hs_code} {query.destination_country} export requirements"
            
            # Retrieve documents
            documents = self.rag_pipeline.retrieve_documents(
                query=search_query,
                top_k=3
            )
            
            # Extract sources
            sources = self.rag_pipeline.extract_sources(documents)
            
            # Convert to Source model
            return [
                Source(
                    title=src['title'],
                    source=src['source'],
                    excerpt=src['excerpt'],
                    url=src.get('url'),
                    relevance_score=src['relevance_score']
                )
                for src in sources
            ]
        
        except Exception as e:
            logger.error(f"Error retrieving sources: {e}")
            return []


# Convenience function for quick report generation
def generate_report(query: QueryInput) -> ExportReadinessReport:
    """
    Convenience function to generate export readiness report.
    
    Args:
        query: User query with product and destination information
        
    Returns:
        Complete ExportReadinessReport
    """
    generator = ReportGenerator()
    return generator.generate_report(query)
