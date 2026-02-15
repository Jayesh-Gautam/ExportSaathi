"""
Certification Solver Service for ExportSathi

This service provides detailed guidance for obtaining required certifications.
It generates step-by-step roadmaps, document checklists, test lab information,
consultant recommendations, subsidy details, and mock audit questions.

Requirements: 3.1, 3.2, 3.4, 3.5, 3.6
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.certification import (
    Certification,
    CertificationGuidance,
    DocumentChecklistItem as Document,
    TestLab,
    Consultant,
    Subsidy,
    MockAuditQuestion
)
from models.common import GuidanceStep as CertRoadmapStep
from models.enums import CertificationType, Priority
from models.common import CostRange, ContactInfo
from services.rag_pipeline import RAGPipeline, get_rag_pipeline
from services.llm_client import LLMClient, create_llm_client
from services.consultant_marketplace import get_consultant_marketplace

logger = logging.getLogger(__name__)


class CertificationSolver:
    """
    Generates detailed certification acquisition guidance.
    
    This service helps users navigate the certification process by providing:
    1. Step-by-step acquisition roadmap
    2. Document checklists with mandatory/optional flags
    3. Approved test labs with contact information
    4. Consultant marketplace recommendations
    5. Government subsidy information
    6. Mock audit questions for preparation
    
    Requirements: 3.1, 3.2, 3.4, 3.5, 3.6
    """
    
    def __init__(
        self,
        rag_pipeline: Optional[RAGPipeline] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """Initialize Certification Solver."""
        self.rag_pipeline = rag_pipeline or get_rag_pipeline()
        self.llm_client = llm_client or create_llm_client()
        logger.info("CertificationSolver initialized")

    def generate_guidance(
        self,
        certification_id: str,
        product_type: str,
        destination: str,
        company_size: str = "Small"
    ) -> CertificationGuidance:
        """
        Generate comprehensive certification guidance.
        
        Args:
            certification_id: Certification identifier
            product_type: Product type/name
            destination: Destination country
            company_size: Company size for subsidy eligibility
            
        Returns:
            Complete CertificationGuidance
            
        Requirements: 3.1, 3.2, 3.4, 3.5, 3.6
        """
        logger.info(f"Generating guidance for certification: {certification_id}")
        
        try:
            # Retrieve certification-specific documents
            query = f"{certification_id} certification requirements {product_type} {destination}"
            documents = self.rag_pipeline.retrieve_documents(query=query, top_k=5)
            
            # Generate roadmap
            roadmap = self.generate_roadmap(certification_id, product_type, documents)
            
            # Generate document checklist
            document_checklist = self.get_document_checklist(certification_id, product_type)
            
            # Find test labs
            test_labs = self.find_test_labs(certification_id, "India")
            
            # Find consultants
            consultants = self.find_consultants(certification_id)
            
            # Get subsidies
            subsidies = self.get_subsidies(certification_id, company_size)
            
            # Generate mock audit questions
            mock_questions = self.generate_mock_audit_questions(certification_id, product_type)
            
            # Get common rejection reasons
            rejection_reasons = self.get_rejection_reasons(certification_id, documents)
            
            guidance = CertificationGuidance(
                certification_id=certification_id,
                why_required=self._get_why_required(certification_id, destination),
                roadmap=roadmap,
                document_checklist=document_checklist,
                test_labs=test_labs,
                consultants=consultants,
                subsidies=subsidies,
                common_rejection_reasons=rejection_reasons,
                mock_audit_questions=mock_questions,
                estimated_cost=self._get_estimated_cost(certification_id),
                estimated_timeline_days=self._get_estimated_timeline(certification_id)
            )
            
            logger.info(f"Generated guidance for {certification_id}")
            return guidance
            
        except Exception as e:
            logger.error(f"Error generating guidance: {e}", exc_info=True)
            raise

    def generate_roadmap(
        self,
        certification_id: str,
        product_type: str,
        documents: List[Any]
    ) -> List[CertRoadmapStep]:
        """Generate step-by-step acquisition roadmap."""
        # MVP: Rule-based roadmap generation
        roadmap = []
        
        if "fda" in certification_id.lower():
            roadmap = [
                CertRoadmapStep(
                    step=1,
                    title="Register with FDA",
                    description="Create FDA account and register your facility",
                    duration_days=7,
                    dependencies=[]
                ),
                CertRoadmapStep(
                    step=2,
                    title="Prepare Documentation",
                    description="Gather all required documents including product specifications, manufacturing process, quality control procedures",
                    duration_days=14,
                    dependencies=["Register with FDA"]
                ),
                CertRoadmapStep(
                    step=3,
                    title="Submit Application",
                    description="Submit FDA application with all supporting documents",
                    duration_days=3,
                    dependencies=["Prepare Documentation"]
                ),
                CertRoadmapStep(
                    step=4,
                    title="FDA Review",
                    description="Wait for FDA review and respond to any queries",
                    duration_days=30,
                    dependencies=["Submit Application"]
                ),
                CertRoadmapStep(
                    step=5,
                    title="Receive Approval",
                    description="Receive FDA approval and registration number",
                    duration_days=7,
                    dependencies=["FDA Review"]
                )
            ]
        elif "ce" in certification_id.lower():
            roadmap = [
                CertRoadmapStep(
                    step=1,
                    title="Identify Applicable Directives",
                    description="Determine which EU directives apply to your product",
                    duration_days=5,
                    dependencies=[]
                ),
                CertRoadmapStep(
                    step=2,
                    title="Conduct Conformity Assessment",
                    description="Perform conformity assessment according to applicable directives",
                    duration_days=30,
                    dependencies=["Identify Applicable Directives"]
                ),
                CertRoadmapStep(
                    step=3,
                    title="Prepare Technical Documentation",
                    description="Compile technical file with test reports, risk assessments, and declarations",
                    duration_days=14,
                    dependencies=["Conduct Conformity Assessment"]
                ),
                CertRoadmapStep(
                    step=4,
                    title="Issue Declaration of Conformity",
                    description="Create and sign Declaration of Conformity",
                    duration_days=3,
                    dependencies=["Prepare Technical Documentation"]
                ),
                CertRoadmapStep(
                    step=5,
                    title="Affix CE Marking",
                    description="Apply CE marking to product and packaging",
                    duration_days=7,
                    dependencies=["Issue Declaration of Conformity"]
                )
            ]
        elif "bis" in certification_id.lower():
            roadmap = [
                CertRoadmapStep(
                    step=1,
                    title="Apply for BIS License",
                    description="Submit application to BIS with company and product details",
                    duration_days=7,
                    dependencies=[]
                ),
                CertRoadmapStep(
                    step=2,
                    title="Factory Inspection",
                    description="BIS conducts factory inspection to verify manufacturing capabilities",
                    duration_days=21,
                    dependencies=["Apply for BIS License"]
                ),
                CertRoadmapStep(
                    step=3,
                    title="Product Testing",
                    description="Submit samples for testing at BIS-approved lab",
                    duration_days=14,
                    dependencies=["Factory Inspection"]
                ),
                CertRoadmapStep(
                    step=4,
                    title="Receive License",
                    description="Receive BIS license and registration number",
                    duration_days=7,
                    dependencies=["Product Testing"]
                )
            ]
        else:
            # Generic roadmap
            roadmap = [
                CertRoadmapStep(
                    step=1,
                    title="Research Requirements",
                    description="Understand certification requirements and standards",
                    duration_days=5,
                    dependencies=[]
                ),
                CertRoadmapStep(
                    step=2,
                    title="Prepare Documentation",
                    description="Gather all required documents and information",
                    duration_days=14,
                    dependencies=["Research Requirements"]
                ),
                CertRoadmapStep(
                    step=3,
                    title="Submit Application",
                    description="Submit certification application",
                    duration_days=3,
                    dependencies=["Prepare Documentation"]
                ),
                CertRoadmapStep(
                    step=4,
                    title="Review and Approval",
                    description="Wait for review and approval",
                    duration_days=30,
                    dependencies=["Submit Application"]
                )
            ]
        
        return roadmap

    def get_document_checklist(
        self,
        certification_id: str,
        product_type: str
    ) -> List[Document]:
        """Generate document checklist for certification."""
        documents = []
        
        if "fda" in certification_id.lower():
            documents = [
                Document(
                    id="fda-doc-1",
                    name="FDA Registration Form",
                    description="Complete FDA facility registration form",
                    mandatory=True,
                    auto_fill_available=True
                ),
                Document(
                    id="fda-doc-2",
                    name="Product Specifications",
                    description="Detailed product specifications including ingredients, composition, and intended use",
                    mandatory=True,
                    auto_fill_available=False
                ),
                Document(
                    id="fda-doc-3",
                    name="Manufacturing Process Description",
                    description="Step-by-step description of manufacturing process",
                    mandatory=True,
                    auto_fill_available=False
                ),
                Document(
                    id="fda-doc-4",
                    name="Quality Control Procedures",
                    description="Quality control and testing procedures",
                    mandatory=True,
                    auto_fill_available=False
                ),
                Document(
                    id="fda-doc-5",
                    name="Labeling Samples",
                    description="Product labeling samples showing all required information",
                    mandatory=True,
                    auto_fill_available=False
                )
            ]
        elif "ce" in certification_id.lower():
            documents = [
                Document(
                    id="ce-doc-1",
                    name="Technical File",
                    description="Complete technical documentation file",
                    mandatory=True,
                    auto_fill_available=False
                ),
                Document(
                    id="ce-doc-2",
                    name="Test Reports",
                    description="Test reports from accredited laboratory",
                    mandatory=True,
                    auto_fill_available=False
                ),
                Document(
                    id="ce-doc-3",
                    name="Risk Assessment",
                    description="Product risk assessment documentation",
                    mandatory=True,
                    auto_fill_available=False
                ),
                Document(
                    id="ce-doc-4",
                    name="Declaration of Conformity",
                    description="Signed Declaration of Conformity",
                    mandatory=True,
                    auto_fill_available=True
                ),
                Document(
                    id="ce-doc-5",
                    name="User Manual",
                    description="Product user manual in applicable languages",
                    mandatory=True,
                    auto_fill_available=False
                )
            ]
        elif "bis" in certification_id.lower():
            documents = [
                Document(
                    id="bis-doc-1",
                    name="BIS Application Form",
                    description="Completed BIS license application form",
                    mandatory=True,
                    auto_fill_available=True
                ),
                Document(
                    id="bis-doc-2",
                    name="Company Registration Certificate",
                    description="Certificate of incorporation or registration",
                    mandatory=True,
                    auto_fill_available=False
                ),
                Document(
                    id="bis-doc-3",
                    name="Product Specifications",
                    description="Detailed product specifications and standards compliance",
                    mandatory=True,
                    auto_fill_available=False
                ),
                Document(
                    id="bis-doc-4",
                    name="Factory Layout",
                    description="Factory layout and manufacturing process flow",
                    mandatory=True,
                    auto_fill_available=False
                ),
                Document(
                    id="bis-doc-5",
                    name="Test Reports",
                    description="Test reports from BIS-approved laboratory",
                    mandatory=True,
                    auto_fill_available=False
                )
            ]
        else:
            # Generic checklist
            documents = [
                Document(
                    id="gen-doc-1",
                    name="Application Form",
                    description="Completed certification application form",
                    mandatory=True,
                    auto_fill_available=True
                ),
                Document(
                    id="gen-doc-2",
                    name="Company Documents",
                    description="Company registration and business documents",
                    mandatory=True,
                    auto_fill_available=False
                ),
                Document(
                    id="gen-doc-3",
                    name="Product Information",
                    description="Detailed product specifications and documentation",
                    mandatory=True,
                    auto_fill_available=False
                )
            ]
        
        return documents

    def find_test_labs(
        self,
        certification_id: str,
        location: str = "India"
    ) -> List[TestLab]:
        """Find approved test labs for certification."""
        test_labs = []
        
        if "fda" in certification_id.lower():
            test_labs = [
                TestLab(
                    id="lab-fda-1",
                    name="SGS India Pvt Ltd",
                    accreditation="ISO 17025, FDA Recognized",
                    location="Mumbai, Delhi, Bangalore",
                    contact=ContactInfo(
                        email="india.food@sgs.com",
                        phone="+91-22-6122-8888",
                        website="https://www.sgs.com/en-in"
                    ),
                    specialization=["Food Testing", "FDA Compliance"]
                ),
                TestLab(
                    id="lab-fda-2",
                    name="Intertek India Pvt Ltd",
                    accreditation="ISO 17025, FDA Recognized",
                    location="Mumbai, Chennai, Hyderabad",
                    contact=ContactInfo(
                        email="food.india@intertek.com",
                        phone="+91-22-6602-3000",
                        website="https://www.intertek.com/food/"
                    ),
                    specialization=["Food Safety", "FDA Testing"]
                )
            ]
        elif "ce" in certification_id.lower():
            test_labs = [
                TestLab(
                    id="lab-ce-1",
                    name="TUV India Pvt Ltd",
                    accreditation="ISO 17025, Notified Body",
                    location="Bangalore, Pune, Delhi",
                    contact=ContactInfo(
                        email="info@tuv-nord.com",
                        phone="+91-80-4147-1000",
                        website="https://www.tuv-nord.com/in"
                    ),
                    specialization=["CE Marking", "Product Safety"]
                ),
                TestLab(
                    id="lab-ce-2",
                    name="Bureau Veritas India",
                    accreditation="ISO 17025, Notified Body",
                    location="Mumbai, Delhi, Chennai",
                    contact=ContactInfo(
                        email="india.cps@bureauveritas.com",
                        phone="+91-22-6274-2000",
                        website="https://www.bureauveritas.co.in"
                    ),
                    specialization=["CE Testing", "EMC Testing"]
                )
            ]
        elif "bis" in certification_id.lower():
            test_labs = [
                TestLab(
                    id="lab-bis-1",
                    name="NABL Accredited Lab - Delhi",
                    accreditation="NABL, BIS Approved",
                    location="Delhi",
                    contact=ContactInfo(
                        email="info@nabllabs.com",
                        phone="+91-11-2345-6789",
                        website="https://www.nabl-india.org"
                    ),
                    specialization=["BIS Testing", "Product Certification"]
                ),
                TestLab(
                    id="lab-bis-2",
                    name="CPRI - Central Power Research Institute",
                    accreditation="NABL, BIS Approved",
                    location="Bangalore",
                    contact=ContactInfo(
                        email="cpri@cpri.in",
                        phone="+91-80-2838-0311",
                        website="https://www.cpri.in"
                    ),
                    specialization=["Electrical Testing", "BIS Certification"]
                )
            ]
        
        return test_labs

    def find_consultants(
        self,
        certification_id: str
    ) -> List[Consultant]:
        """Find consultants for certification assistance using the marketplace."""
        marketplace = get_consultant_marketplace()
        return marketplace.get_consultants_for_certification(certification_id, limit=5)

    def get_subsidies(
        self,
        certification_id: str,
        company_size: str
    ) -> List[Subsidy]:
        """Get applicable subsidies for certification."""
        subsidies = []
        
        # ZED subsidy for micro enterprises
        if "zed" in certification_id.lower() and company_size == "Micro":
            subsidies.append(Subsidy(
                name="ZED Certification Subsidy for Micro Enterprises",
                amount=0.0,  # Percentage-based
                percentage=80.0,
                eligibility="Micro enterprises (investment < ₹1 crore, turnover < ₹5 crore)",
                application_process="Apply through ZED portal (https://zed.msme.gov.in) with Udyam registration and company documents"
            ))
        elif "zed" in certification_id.lower() and company_size == "Small":
            subsidies.append(Subsidy(
                name="ZED Certification Subsidy for Small Enterprises",
                amount=0.0,
                percentage=60.0,
                eligibility="Small enterprises (investment < ₹10 crore, turnover < ₹50 crore)",
                application_process="Apply through ZED portal (https://zed.msme.gov.in) with Udyam registration and company documents"
            ))
        
        # Quality certification subsidies
        if any(cert_type in certification_id.lower() for cert_type in ["iso", "bis", "ce", "fda"]):
            subsidies.append(Subsidy(
                name="Quality Certification Subsidy (State-specific)",
                amount=25000.0,
                percentage=50.0,
                eligibility="MSMEs registered in participating states",
                application_process="Check with state MSME department for eligibility and application process"
            ))
        
        return subsidies
    
    def generate_mock_audit_questions(
        self,
        certification_id: str,
        product_type: str
    ) -> List[MockAuditQuestion]:
        """Generate mock audit questions for certification preparation."""
        questions = []
        
        if "fda" in certification_id.lower():
            questions = [
                MockAuditQuestion(
                    question="Describe your facility's sanitation procedures and frequency.",
                    category="Facility Management",
                    importance="High"
                ),
                MockAuditQuestion(
                    question="How do you ensure traceability of raw materials from supplier to finished product?",
                    category="Quality Control",
                    importance="High"
                ),
                MockAuditQuestion(
                    question="What is your process for handling customer complaints and product recalls?",
                    category="Quality Management",
                    importance="High"
                ),
                MockAuditQuestion(
                    question="Describe your employee training program for food safety and hygiene.",
                    category="Personnel",
                    importance="Medium"
                ),
                MockAuditQuestion(
                    question="How do you verify that your suppliers meet FDA requirements?",
                    category="Supply Chain",
                    importance="Medium"
                )
            ]
        elif "ce" in certification_id.lower():
            questions = [
                MockAuditQuestion(
                    question="Which EU directives apply to your product and how did you determine this?",
                    category="Compliance",
                    importance="High"
                ),
                MockAuditQuestion(
                    question="Describe the conformity assessment procedure you followed.",
                    category="Assessment",
                    importance="High"
                ),
                MockAuditQuestion(
                    question="How do you ensure your product continues to meet CE requirements during production?",
                    category="Quality Control",
                    importance="High"
                ),
                MockAuditQuestion(
                    question="What risk assessment methodology did you use for your product?",
                    category="Risk Management",
                    importance="Medium"
                ),
                MockAuditQuestion(
                    question="How do you maintain and update your technical documentation?",
                    category="Documentation",
                    importance="Medium"
                )
            ]
        elif "bis" in certification_id.lower():
            questions = [
                MockAuditQuestion(
                    question="Describe your quality control testing procedures and frequency.",
                    category="Quality Control",
                    importance="High"
                ),
                MockAuditQuestion(
                    question="How do you ensure compliance with Indian Standards (IS) specifications?",
                    category="Compliance",
                    importance="High"
                ),
                MockAuditQuestion(
                    question="What is your process for handling non-conforming products?",
                    category="Quality Management",
                    importance="High"
                ),
                MockAuditQuestion(
                    question="Describe your calibration and maintenance program for testing equipment.",
                    category="Equipment",
                    importance="Medium"
                ),
                MockAuditQuestion(
                    question="How do you train employees on quality standards and procedures?",
                    category="Personnel",
                    importance="Medium"
                )
            ]
        
        return questions

    def get_rejection_reasons(
        self,
        certification_id: str,
        documents: List[Any]
    ) -> List[str]:
        """Get common rejection reasons for certification."""
        # MVP: Rule-based rejection reasons
        rejection_reasons = []
        
        if "fda" in certification_id.lower():
            rejection_reasons = [
                "Incomplete or inaccurate product labeling",
                "Insufficient documentation of manufacturing process",
                "Lack of proper quality control procedures",
                "Failure to register facility with FDA",
                "Non-compliance with Good Manufacturing Practices (GMP)",
                "Inadequate traceability systems",
                "Missing or expired test reports"
            ]
        elif "ce" in certification_id.lower():
            rejection_reasons = [
                "Incomplete technical documentation",
                "Incorrect or missing Declaration of Conformity",
                "Test reports from non-accredited laboratories",
                "Inadequate risk assessment",
                "Non-compliance with applicable EU directives",
                "Missing or incorrect CE marking on product",
                "Insufficient user documentation"
            ]
        elif "bis" in certification_id.lower():
            rejection_reasons = [
                "Product does not meet Indian Standards specifications",
                "Inadequate factory quality control systems",
                "Incomplete application documentation",
                "Failed product testing at BIS-approved lab",
                "Non-compliance with factory inspection requirements",
                "Missing or incorrect product marking",
                "Insufficient production capacity"
            ]
        else:
            rejection_reasons = [
                "Incomplete application documentation",
                "Non-compliance with certification standards",
                "Inadequate quality management systems",
                "Failed product testing",
                "Insufficient evidence of compliance"
            ]
        
        return rejection_reasons
    
    def _get_why_required(self, certification_id: str, destination: str) -> str:
        """Get explanation of why certification is required."""
        if "fda" in certification_id.lower():
            return f"FDA registration is mandatory for exporting food products to the United States. The FDA requires all foreign food facilities that manufacture, process, pack, or hold food for consumption in the US to register with the FDA."
        elif "ce" in certification_id.lower():
            return f"CE marking is mandatory for products sold in the European Economic Area (EEA). It indicates that the product complies with EU safety, health, and environmental protection requirements."
        elif "bis" in certification_id.lower():
            return f"BIS certification is required for certain products under the Compulsory Registration Scheme (CRS) in India. It ensures products meet Indian quality and safety standards."
        elif "zed" in certification_id.lower():
            return "ZED (Zero Defect Zero Effect) certification helps MSMEs adopt quality management systems and environmental practices. It's optional but provides significant subsidies and improves market competitiveness."
        elif "softex" in certification_id.lower():
            return "SOFTEX declaration is mandatory for exporting software and IT services from India. It's required for claiming benefits under the Software Technology Parks of India (STPI) scheme."
        else:
            return f"This certification is required for exporting to {destination} to ensure product compliance with local regulations and standards."
    
    def _get_estimated_cost(self, certification_id: str) -> CostRange:
        """Get estimated cost for certification."""
        if "fda" in certification_id.lower():
            return CostRange(min=15000, max=30000, currency="INR")
        elif "ce" in certification_id.lower():
            return CostRange(min=50000, max=150000, currency="INR")
        elif "bis" in certification_id.lower():
            return CostRange(min=30000, max=80000, currency="INR")
        elif "zed" in certification_id.lower():
            return CostRange(min=20000, max=100000, currency="INR")
        elif "softex" in certification_id.lower():
            return CostRange(min=5000, max=10000, currency="INR")
        else:
            return CostRange(min=10000, max=50000, currency="INR")
    
    def _get_estimated_timeline(self, certification_id: str) -> int:
        """Get estimated timeline for certification in days."""
        if "fda" in certification_id.lower():
            return 60
        elif "ce" in certification_id.lower():
            return 90
        elif "bis" in certification_id.lower():
            return 60
        elif "zed" in certification_id.lower():
            return 90
        elif "softex" in certification_id.lower():
            return 7
        else:
            return 45


# Convenience function
def generate_certification_guidance(
    certification_id: str,
    product_type: str,
    destination: str,
    company_size: str = "Small"
) -> CertificationGuidance:
    """
    Convenience function to generate certification guidance.
    
    Args:
        certification_id: Certification identifier
        product_type: Product type/name
        destination: Destination country
        company_size: Company size for subsidy eligibility
        
    Returns:
        Complete CertificationGuidance
    """
    solver = CertificationSolver()
    return solver.generate_guidance(certification_id, product_type, destination, company_size)
