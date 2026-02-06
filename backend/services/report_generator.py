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
from services.restricted_substances_analyzer import RestrictedSubstancesAnalyzer

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
        llm_client: Optional[LLMClient] = None,
        restricted_substances_analyzer: Optional[RestrictedSubstancesAnalyzer] = None
    ):
        """
        Initialize Report Generator.
        
        Args:
            hs_code_predictor: HS code prediction service (creates new if None)
            rag_pipeline: RAG pipeline for document retrieval (uses global if None)
            llm_client: LLM client for generation (creates new if None)
            restricted_substances_analyzer: Restricted substances analyzer (creates new if None)
        """
        self.hs_code_predictor = hs_code_predictor or HSCodePredictor()
        self.rag_pipeline = rag_pipeline or get_rag_pipeline()
        self.llm_client = llm_client or create_llm_client()
        self.restricted_substances_analyzer = restricted_substances_analyzer or RestrictedSubstancesAnalyzer()
        
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
                destination_country=query.destination_country,
                product_name=query.product_name
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
        
        Enhanced Implementation: Uses RAG pipeline to query knowledge base for
        certification requirements, with fallback to rule-based logic.
        
        Args:
            hs_code: Product HS code
            destination_country: Destination country
            product_type: Product type/name
            business_type: Business type (Manufacturing/SaaS/Merchant)
            
        Returns:
            List of required certifications
            
        Requirements: 2.2, 3.8
        """
        certifications = []
        
        try:
            # Use RAG to query knowledge base for certification requirements
            query = f"Required certifications for HS code {hs_code} exporting {product_type} to {destination_country}"
            
            logger.info(f"Querying knowledge base for certifications: {query}")
            documents = self.rag_pipeline.retrieve_documents(query=query, top_k=5)
            
            if documents:
                # Use LLM to extract certification requirements from retrieved documents
                prompt = self._build_certification_prompt(
                    hs_code=hs_code,
                    destination_country=destination_country,
                    product_type=product_type,
                    business_type=business_type,
                    documents=documents
                )
                
                # Generate structured certification list
                response = self.llm_client.generate_structured(
                    prompt=prompt,
                    schema={
                        "type": "object",
                        "properties": {
                            "certifications": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "type": {"type": "string"},
                                        "mandatory": {"type": "boolean"},
                                        "min_cost": {"type": "number"},
                                        "max_cost": {"type": "number"},
                                        "timeline_days": {"type": "number"},
                                        "priority": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                )
                
                # Parse LLM response and create Certification objects
                if response and "certifications" in response:
                    for cert_data in response["certifications"]:
                        cert_type = self._parse_certification_type(cert_data.get("type", "other"))
                        priority = self._parse_priority(cert_data.get("priority", "medium"))
                        
                        certifications.append(Certification(
                            id=cert_data["name"].lower().replace(" ", "-"),
                            name=cert_data["name"],
                            type=cert_type,
                            mandatory=cert_data.get("mandatory", False),
                            estimated_cost=CostRange(
                                min=cert_data.get("min_cost", 10000),
                                max=cert_data.get("max_cost", 50000),
                                currency="INR"
                            ),
                            estimated_timeline_days=cert_data.get("timeline_days", 30),
                            priority=priority
                        ))
                    
                    logger.info(f"RAG-based identification found {len(certifications)} certifications")
        
        except Exception as e:
            logger.warning(f"RAG-based certification identification failed: {e}. Falling back to rule-based logic.")
        
        # Fallback to rule-based logic if RAG fails or returns no results
        if not certifications:
            certifications = self._identify_certifications_rule_based(
                hs_code=hs_code,
                destination_country=destination_country,
                product_type=product_type,
                business_type=business_type
            )
        
        # Always add business-type specific certifications
        certifications.extend(self._add_business_type_certifications(business_type))
        
        # Remove duplicates
        seen_ids = set()
        unique_certifications = []
        for cert in certifications:
            if cert.id not in seen_ids:
                seen_ids.add(cert.id)
                unique_certifications.append(cert)
        
        logger.info(f"Identified {len(unique_certifications)} certifications for {destination_country}")
        return unique_certifications
    
    def _build_certification_prompt(
        self,
        hs_code: str,
        destination_country: str,
        product_type: str,
        business_type: str,
        documents: List[Any]
    ) -> str:
        """Build prompt for LLM to extract certification requirements."""
        context = "\n\n".join([
            f"Document {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(documents[:3])
        ])
        
        return f"""Based on the following regulatory documents, identify ALL required certifications for exporting this product:

Product: {product_type}
HS Code: {hs_code}
Destination: {destination_country}
Business Type: {business_type}

Regulatory Context:
{context}

For each certification, provide:
1. Full certification name
2. Type (FDA, CE, REACH, BIS, ZED, SOFTEX, or other)
3. Whether it's mandatory or optional
4. Estimated cost range in INR (min and max)
5. Estimated timeline in days
6. Priority (high, medium, or low)

Focus on certifications that are:
- Legally required by the destination country
- Industry-standard for this product type
- Beneficial for market access

Return ONLY certifications that are specifically relevant to this product and destination."""
    
    def _parse_certification_type(self, type_str: str) -> CertificationType:
        """Parse certification type string to enum."""
        type_map = {
            "fda": CertificationType.FDA,
            "ce": CertificationType.CE,
            "reach": CertificationType.REACH,
            "bis": CertificationType.BIS,
            "zed": CertificationType.ZED,
            "softex": CertificationType.SOFTEX,
        }
        return type_map.get(type_str.lower(), CertificationType.OTHER)
    
    def _parse_priority(self, priority_str: str) -> Priority:
        """Parse priority string to enum."""
        priority_map = {
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW,
        }
        return priority_map.get(priority_str.lower(), Priority.MEDIUM)
    
    def _identify_certifications_rule_based(
        self,
        hs_code: str,
        destination_country: str,
        product_type: str,
        business_type: str
    ) -> List[Certification]:
        """
        Rule-based certification identification (fallback method).
        
        This is the original MVP logic, kept as a fallback when RAG is unavailable.
        """
        certifications = []
        
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
            
            # Medical devices and drugs
            if hs_code[:2] in ["30", "90"]:
                certifications.append(Certification(
                    id="fda-medical-device",
                    name="FDA Medical Device Registration",
                    type=CertificationType.FDA,
                    mandatory=True,
                    estimated_cost=CostRange(min=50000, max=200000, currency="INR"),
                    estimated_timeline_days=90,
                    priority=Priority.HIGH
                ))
        
        # EU exports - CE marking for certain products
        if destination_country.upper() in ["EUROPEAN UNION", "EU", "GERMANY", "FRANCE", "ITALY", "SPAIN", "NETHERLANDS", "BELGIUM"]:
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
            
            # REACH for chemicals
            if hs_code[:2] in ["28", "29", "38"]:
                certifications.append(Certification(
                    id="reach-registration",
                    name="REACH Registration",
                    type=CertificationType.REACH,
                    mandatory=True,
                    estimated_cost=CostRange(min=100000, max=500000, currency="INR"),
                    estimated_timeline_days=120,
                    priority=Priority.HIGH
                ))
        
        # BIS certification for certain products to any destination
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
        
        return certifications
    
    def _add_business_type_certifications(self, business_type: str) -> List[Certification]:
        """Add business-type specific certifications."""
        certifications = []
        
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
        
        return certifications
    
    def identify_restricted_substances(
        self,
        ingredients: Optional[str],
        bom: Optional[str],
        destination_country: str,
        product_name: Optional[str] = None
    ) -> List[RestrictedSubstance]:
        """
        Identify restricted substances from ingredients/BOM.
        
        Enhanced Implementation: Uses dedicated RestrictedSubstancesAnalyzer service
        which combines RAG-based retrieval with keyword matching for comprehensive analysis.
        
        Args:
            ingredients: Product ingredients
            bom: Bill of Materials
            destination_country: Destination country
            product_name: Optional product name for context
            
        Returns:
            List of restricted substances
            
        Requirements: 2.3
        """
        return self.restricted_substances_analyzer.analyze(
            ingredients=ingredients,
            bom=bom,
            destination_country=destination_country,
            product_name=product_name
        )
    
    def retrieve_rejection_reasons(
        self,
        product_type: str,
        destination_country: str
    ) -> List[PastRejection]:
        """
        Retrieve past rejection data from FDA/EU databases.
        
        Enhanced Implementation: Uses RAG pipeline to query knowledge base for
        past rejection data from FDA refusal database and EU RASFF, filtered by
        product type and destination country.
        
        Args:
            product_type: Product type
            destination_country: Destination country
            
        Returns:
            List of past rejections with source and date
            
        Requirements: 2.4
        """
        past_rejections = []
        
        try:
            # Determine which rejection databases to query based on destination
            sources_to_query = []
            
            # Query FDA refusal database for US exports
            if destination_country.upper() in ["UNITED STATES", "USA", "US"]:
                sources_to_query.append("FDA")
            
            # Query EU RASFF for EU exports
            eu_countries = [
                "EUROPEAN UNION", "EU", "GERMANY", "FRANCE", "ITALY", "SPAIN",
                "NETHERLANDS", "BELGIUM", "AUSTRIA", "PORTUGAL", "GREECE",
                "SWEDEN", "DENMARK", "FINLAND", "IRELAND", "POLAND", "CZECH REPUBLIC",
                "HUNGARY", "ROMANIA", "BULGARIA", "CROATIA", "SLOVAKIA", "SLOVENIA",
                "LITHUANIA", "LATVIA", "ESTONIA", "LUXEMBOURG", "MALTA", "CYPRUS"
            ]
            if destination_country.upper() in eu_countries:
                sources_to_query.append("EU_RASFF")
            
            # If no specific source, query both for comprehensive results
            if not sources_to_query:
                sources_to_query = ["FDA", "EU_RASFF"]
            
            logger.info(f"Querying rejection databases: {sources_to_query} for {product_type} to {destination_country}")
            
            # Query each relevant source
            for source in sources_to_query:
                # Construct query for rejection data
                query = f"{source} rejection refusal {product_type} import alert contamination"
                
                logger.info(f"Searching {source} database: {query}")
                
                # Retrieve relevant documents from knowledge base
                documents = self.rag_pipeline.retrieve_documents(
                    query=query,
                    top_k=5
                )
                
                if documents:
                    # Use LLM to extract rejection reasons from retrieved documents
                    prompt = self._build_rejection_extraction_prompt(
                        product_type=product_type,
                        destination_country=destination_country,
                        source=source,
                        documents=documents
                    )
                    
                    # Generate structured rejection data
                    response = self.llm_client.generate_structured(
                        prompt=prompt,
                        schema={
                            "type": "object",
                            "properties": {
                                "rejections": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "product_type": {"type": "string"},
                                            "reason": {"type": "string"},
                                            "date": {"type": "string"}
                                        },
                                        "required": ["product_type", "reason", "date"]
                                    }
                                }
                            }
                        }
                    )
                    
                    # Parse LLM response and create PastRejection objects
                    if response and "rejections" in response:
                        for rejection_data in response["rejections"]:
                            # Map source string to enum
                            rejection_source = RejectionSource.FDA if source == "FDA" else RejectionSource.EU_RASFF
                            
                            past_rejections.append(PastRejection(
                                product_type=rejection_data["product_type"],
                                reason=rejection_data["reason"],
                                source=rejection_source,
                                date=rejection_data["date"]
                            ))
                        
                        logger.info(f"Found {len(response['rejections'])} rejections from {source}")
            
            # Limit to most recent/relevant rejections (max 10)
            if len(past_rejections) > 10:
                past_rejections = past_rejections[:10]
            
            logger.info(f"Retrieved {len(past_rejections)} total past rejections")
            
        except Exception as e:
            logger.warning(f"Error retrieving past rejection data: {e}. Returning empty list.")
            # Return empty list on error rather than failing the entire report
            return []
        
        return past_rejections
    
    def _build_rejection_extraction_prompt(
        self,
        product_type: str,
        destination_country: str,
        source: str,
        documents: List[Any]
    ) -> str:
        """Build prompt for LLM to extract past rejection data."""
        context = "\n\n".join([
            f"Document {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(documents[:3])
        ])
        
        return f"""Based on the following {source} regulatory documents, extract past rejection/refusal data for similar products:

Product Type: {product_type}
Destination: {destination_country}
Source Database: {source}

Regulatory Context:
{context}

Extract ALL relevant rejection/refusal cases that are similar to "{product_type}". For each rejection, provide:
1. Specific product type that was rejected (be as specific as possible)
2. Detailed reason for rejection (contamination, labeling issue, restricted substance, etc.)
3. Date of rejection (in YYYY-MM-DD format, or approximate if exact date not available)

Focus on:
- Rejections that are directly relevant to {product_type}
- Recent rejections (within last 2-3 years if available)
- Common patterns or recurring issues
- Specific contamination or compliance violations

If the documents mention "common rejection reasons" or "frequent violations" for this product category, include those as well.

Return ONLY rejections that are specifically documented in the provided context. Do not invent or assume rejection data."""
    
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
        
        Enhanced Implementation: More sophisticated risk calculation with multiple factors.
        
        Args:
            hs_code: HS code prediction
            certifications: Required certifications
            restricted_substances: Restricted substances
            past_rejections: Past rejection data
            
        Returns:
            Tuple of (risk_score, list_of_risks)
            
        Requirements: 2.6
        """
        base_risk = 10  # Base risk for any export
        risks = []
        
        # Factor 1: HS code confidence (lower confidence = higher risk)
        if hs_code.confidence < 50:
            base_risk += 25
            risks.append(Risk(
                title="High HS Code Uncertainty",
                description=f"HS code prediction confidence is only {hs_code.confidence}%, which may lead to serious customs issues and delays",
                severity=RiskSeverity.HIGH,
                mitigation="URGENT: Consult with customs broker or trade consultant to verify HS code before proceeding. Incorrect HS code can result in shipment rejection or penalties."
            ))
        elif hs_code.confidence < 70:
            base_risk += 15
            risks.append(Risk(
                title="HS Code Uncertainty",
                description=f"HS code prediction confidence is {hs_code.confidence}%, which may lead to customs issues",
                severity=RiskSeverity.MEDIUM,
                mitigation="Verify HS code with customs broker or trade consultant before shipping. Consider getting a binding ruling from customs."
            ))
        elif hs_code.confidence < 85:
            base_risk += 5
            risks.append(Risk(
                title="Minor HS Code Uncertainty",
                description=f"HS code prediction confidence is {hs_code.confidence}%. While likely correct, verification is recommended.",
                severity=RiskSeverity.LOW,
                mitigation="Double-check HS code classification with product specifications and customs guidelines."
            ))
        
        # Factor 2: Number and complexity of certifications
        mandatory_certs = [c for c in certifications if c.mandatory]
        high_priority_certs = [c for c in certifications if c.priority == Priority.HIGH]
        
        if len(mandatory_certs) >= 4:
            base_risk += 20
            risks.append(Risk(
                title="High Certification Complexity",
                description=f"{len(mandatory_certs)} mandatory certifications required, significantly increasing complexity and timeline",
                severity=RiskSeverity.HIGH,
                mitigation="Start all certification applications immediately. Consider hiring a specialized consultant to manage the certification process. Budget for 3-6 months timeline."
            ))
        elif len(mandatory_certs) >= 2:
            base_risk += 12
            risks.append(Risk(
                title="Multiple Certifications Required",
                description=f"{len(mandatory_certs)} mandatory certifications needed, increasing complexity",
                severity=RiskSeverity.MEDIUM,
                mitigation="Start certification applications early and track deadlines carefully. Consider hiring a consultant for complex certifications like FDA or CE."
            ))
        elif len(mandatory_certs) == 1:
            base_risk += 5
            risks.append(Risk(
                title="Certification Required",
                description=f"1 mandatory certification needed: {mandatory_certs[0].name}",
                severity=RiskSeverity.LOW,
                mitigation=f"Allocate {mandatory_certs[0].estimated_timeline_days} days for certification process. Ensure all documentation is prepared in advance."
            ))
        
        # Factor 3: High-priority certifications (FDA, CE, REACH)
        if len(high_priority_certs) > 0:
            high_priority_names = [c.name for c in high_priority_certs]
            base_risk += 10
            risks.append(Risk(
                title="High-Priority Certifications Required",
                description=f"Critical certifications required: {', '.join(high_priority_names)}. These are strictly enforced at customs.",
                severity=RiskSeverity.HIGH,
                mitigation="Prioritize these certifications above all others. Non-compliance will result in shipment rejection at destination port."
            ))
        
        # Factor 4: Restricted substances
        if len(restricted_substances) >= 3:
            base_risk += 30
            substance_names = [s.name for s in restricted_substances]
            risks.append(Risk(
                title="Multiple Restricted Substances Detected",
                description=f"{len(restricted_substances)} restricted substances found: {', '.join(substance_names)}. This is a critical compliance issue.",
                severity=RiskSeverity.HIGH,
                mitigation="URGENT: Reformulate product to remove restricted substances OR obtain special permits/exemptions. Current formulation will be rejected at customs."
            ))
        elif len(restricted_substances) > 0:
            base_risk += 20
            substance_names = [s.name for s in restricted_substances]
            risks.append(Risk(
                title="Restricted Substances Detected",
                description=f"{len(restricted_substances)} restricted substance(s) found: {', '.join(substance_names)}",
                severity=RiskSeverity.HIGH,
                mitigation="Review product formulation immediately. Ensure compliance with destination regulations or obtain necessary permits. Document compliance evidence."
            ))
        
        # Factor 5: Past rejections
        if len(past_rejections) >= 3:
            base_risk += 25
            risks.append(Risk(
                title="High Historical Rejection Rate",
                description=f"Similar products have been rejected {len(past_rejections)} times in the past",
                severity=RiskSeverity.HIGH,
                mitigation="Study all past rejection reasons in detail. Implement preventive measures for each issue. Consider pre-shipment inspection by third-party."
            ))
        elif len(past_rejections) > 0:
            base_risk += 15
            risks.append(Risk(
                title="Historical Rejections",
                description=f"Similar products have been rejected {len(past_rejections)} time(s)",
                severity=RiskSeverity.MEDIUM,
                mitigation="Review past rejection reasons and ensure your product addresses those issues. Document compliance measures."
            ))
        
        # Factor 6: Certification cost burden
        total_cert_cost = sum(
            (cert.estimated_cost.min + cert.estimated_cost.max) / 2
            for cert in certifications
        )
        if total_cert_cost > 200000:
            base_risk += 10
            risks.append(Risk(
                title="High Certification Costs",
                description=f"Total certification costs estimated at ₹{total_cert_cost:,.0f}, which may strain working capital",
                severity=RiskSeverity.MEDIUM,
                mitigation="Explore government subsidies (ZED offers 80% subsidy for micro enterprises). Consider pre-shipment credit from banks. Budget for 3-6 month timeline."
            ))
        
        # Factor 7: Long certification timelines
        max_timeline = max([c.estimated_timeline_days for c in certifications]) if certifications else 0
        if max_timeline > 90:
            base_risk += 8
            risks.append(Risk(
                title="Extended Certification Timeline",
                description=f"Longest certification requires {max_timeline} days, delaying export readiness",
                severity=RiskSeverity.MEDIUM,
                mitigation="Start certification process immediately. Plan cash flow for extended timeline. Consider parallel processing of multiple certifications."
            ))
        
        # Add general export risks if no specific risks identified
        if not risks:
            risks.append(Risk(
                title="Standard Export Compliance",
                description="Product appears to have standard export requirements with no major red flags",
                severity=RiskSeverity.LOW,
                mitigation="Follow standard export procedures. Ensure all documentation is accurate and complete. Verify HS code classification."
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
