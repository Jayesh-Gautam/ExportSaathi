"""
Certification-related data models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from .enums import CertificationType, Priority
from .common import CostRange, GuidanceStep, Source


class Certification(BaseModel):
    """Certification requirement information."""
    id: str = Field(..., description="Unique certification identifier")
    name: str = Field(..., description="Certification name")
    type: CertificationType = Field(..., description="Type of certification")
    mandatory: bool = Field(..., description="Whether certification is mandatory")
    estimated_cost: CostRange = Field(..., description="Estimated cost range")
    estimated_timeline_days: int = Field(..., gt=0, description="Estimated timeline in days")
    priority: Priority = Field(..., description="Priority level")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "fda-food-facility",
                "name": "FDA Food Facility Registration",
                "type": "FDA",
                "mandatory": True,
                "estimated_cost": {
                    "min": 15000,
                    "max": 30000,
                    "currency": "INR"
                },
                "estimated_timeline_days": 30,
                "priority": "high"
            }
        }


class DocumentChecklistItem(BaseModel):
    """Document required for certification."""
    id: str = Field(..., description="Unique document identifier")
    name: str = Field(..., description="Document name")
    description: str = Field(..., description="Document description")
    mandatory: bool = Field(..., description="Whether document is mandatory")
    auto_fill_available: bool = Field(..., description="Whether auto-fill is available")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "company-registration",
                "name": "Company Registration Certificate",
                "description": "Certificate of incorporation or business registration",
                "mandatory": True,
                "auto_fill_available": False
            }
        }


class TestLab(BaseModel):
    """Approved test laboratory information."""
    name: str = Field(..., description="Laboratory name")
    location: str = Field(..., description="Laboratory location")
    contact: str = Field(..., description="Contact information")
    website: str = Field(..., description="Laboratory website")
    accreditation: str = Field(..., description="Accreditation details")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "NABL Accredited Food Testing Lab",
                "location": "Mumbai, Maharashtra",
                "contact": "+91-22-12345678",
                "website": "https://example-lab.com",
                "accreditation": "NABL, FSSAI"
            }
        }


class Consultant(BaseModel):
    """Certification consultant information."""
    name: str = Field(..., description="Consultant name")
    specialization: str = Field(..., description="Area of specialization")
    rating: float = Field(..., ge=0.0, le=5.0, description="Consultant rating")
    cost_range: CostRange = Field(..., description="Consultation cost range")
    contact: str = Field(..., description="Contact information")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Export Compliance Experts",
                "specialization": "FDA and CE certifications",
                "rating": 4.5,
                "cost_range": {
                    "min": 20000,
                    "max": 50000,
                    "currency": "INR"
                },
                "contact": "contact@exportexperts.com"
            }
        }


class Subsidy(BaseModel):
    """Government subsidy information."""
    name: str = Field(..., description="Subsidy scheme name")
    amount: float = Field(..., ge=0, description="Subsidy amount")
    percentage: float = Field(..., ge=0, le=100, description="Subsidy percentage")
    eligibility: str = Field(..., description="Eligibility criteria")
    application_process: str = Field(..., description="How to apply")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ZED Certification Subsidy",
                "amount": 80000,
                "percentage": 80,
                "eligibility": "Micro enterprises only",
                "application_process": "Apply through ZED portal with company registration"
            }
        }


class MockAuditQuestion(BaseModel):
    """Mock audit question for certification preparation."""
    question: str = Field(..., description="Audit question")
    category: str = Field(..., description="Question category")
    tips: str = Field(..., description="Tips for answering")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Describe your quality control process for raw materials",
                "category": "Quality Management",
                "tips": "Mention supplier verification, testing procedures, and documentation"
            }
        }


class CertificationGuidance(BaseModel):
    """Detailed guidance for obtaining a certification."""
    certification_id: str = Field(..., description="Certification identifier")
    name: str = Field(..., description="Certification name")
    why_required: str = Field(..., description="Why this certification is required")
    steps: List[GuidanceStep] = Field(..., description="Step-by-step acquisition process")
    document_checklist: List[DocumentChecklistItem] = Field(..., description="Required documents")
    test_labs: List[TestLab] = Field(default_factory=list, description="Approved test laboratories")
    consultants: List[Consultant] = Field(default_factory=list, description="Available consultants")
    subsidies: List[Subsidy] = Field(default_factory=list, description="Applicable subsidies")
    common_rejection_reasons: List[str] = Field(default_factory=list, description="Common rejection reasons")
    mock_audit_questions: List[MockAuditQuestion] = Field(default_factory=list, description="Mock audit questions")
    estimated_cost: CostRange = Field(..., description="Total estimated cost")
    estimated_timeline: str = Field(..., description="Estimated timeline")
    sources: List[Source] = Field(default_factory=list, description="Source citations")

    class Config:
        json_schema_extra = {
            "example": {
                "certification_id": "fda-food-facility",
                "name": "FDA Food Facility Registration",
                "why_required": "Required for all food facilities that manufacture, process, pack, or hold food for consumption in the United States",
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Create FDA Account",
                        "description": "Register on the FDA Industry Systems portal",
                        "estimated_duration": "1 day"
                    }
                ],
                "document_checklist": [],
                "test_labs": [],
                "consultants": [],
                "subsidies": [],
                "common_rejection_reasons": ["Incomplete facility information", "Invalid DUNS number"],
                "mock_audit_questions": [],
                "estimated_cost": {
                    "min": 15000,
                    "max": 30000,
                    "currency": "INR"
                },
                "estimated_timeline": "30-45 days",
                "sources": []
            }
        }
