"""
Export readiness report data models.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from .enums import RiskSeverity, ReportStatus, RejectionSource
from .query import HSCodePrediction
from .certification import Certification, Subsidy
from .action_plan import ActionPlan
from .common import Source


class RestrictedSubstance(BaseModel):
    """Restricted substance information."""
    name: str = Field(..., description="Substance name")
    reason: str = Field(..., description="Reason for restriction")
    regulation: str = Field(..., description="Applicable regulation")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Lead",
                "reason": "Toxic heavy metal",
                "regulation": "EU REACH Annex XVII"
            }
        }


class PastRejection(BaseModel):
    """Past rejection data from FDA or EU databases."""
    product_type: str = Field(..., description="Type of product rejected")
    reason: str = Field(..., description="Reason for rejection")
    source: RejectionSource = Field(..., description="Source of rejection data")
    date: str = Field(..., description="Date of rejection")

    class Config:
        json_schema_extra = {
            "example": {
                "product_type": "Turmeric powder",
                "reason": "Salmonella contamination",
                "source": "FDA",
                "date": "2023-08-15"
            }
        }


class RoadmapStep(BaseModel):
    """Step in the compliance roadmap."""
    step: int = Field(..., ge=1, description="Step number")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    duration_days: int = Field(..., gt=0, description="Duration in days")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies on other steps")

    class Config:
        json_schema_extra = {
            "example": {
                "step": 1,
                "title": "Apply for GST LUT",
                "description": "Submit Letter of Undertaking for GST exemption on exports",
                "duration_days": 7,
                "dependencies": []
            }
        }


class Risk(BaseModel):
    """Risk identified in export process."""
    title: str = Field(..., description="Risk title")
    description: str = Field(..., description="Risk description")
    severity: RiskSeverity = Field(..., description="Risk severity level")
    mitigation: str = Field(..., description="Mitigation strategy")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Contamination Risk",
                "description": "Risk of microbial contamination during processing",
                "severity": "high",
                "mitigation": "Implement HACCP protocols and regular testing"
            }
        }


class TimelinePhase(BaseModel):
    """Phase in the export readiness timeline."""
    phase: str = Field(..., description="Phase name")
    duration_days: int = Field(..., gt=0, description="Duration in days")

    class Config:
        json_schema_extra = {
            "example": {
                "phase": "Certification",
                "duration_days": 30
            }
        }


class Timeline(BaseModel):
    """Overall timeline for export readiness."""
    estimated_days: int = Field(..., gt=0, description="Total estimated days")
    breakdown: List[TimelinePhase] = Field(..., description="Timeline breakdown by phase")

    @field_validator('estimated_days')
    @classmethod
    def validate_estimated_days_matches_breakdown(cls, v: int, info) -> int:
        """Validate that estimated_days matches sum of breakdown."""
        data = info.data
        if 'breakdown' in data and data['breakdown']:
            total = sum(phase.duration_days for phase in data['breakdown'])
            if abs(v - total) > 1:  # Allow 1 day tolerance for rounding
                raise ValueError(f'Estimated days ({v}) should match breakdown total ({total})')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "estimated_days": 60,
                "breakdown": [
                    {"phase": "Documentation", "duration_days": 10},
                    {"phase": "Certification", "duration_days": 30},
                    {"phase": "Logistics Setup", "duration_days": 20}
                ]
            }
        }


class CostBreakdown(BaseModel):
    """Cost breakdown for export readiness."""
    certifications: float = Field(..., ge=0, description="Certification costs")
    documentation: float = Field(..., ge=0, description="Documentation costs")
    logistics: float = Field(..., ge=0, description="Logistics costs")
    total: float = Field(..., ge=0, description="Total cost")
    currency: str = Field(default="INR", description="Currency code")

    @field_validator('total')
    @classmethod
    def validate_total_matches_sum(cls, v: float, info) -> float:
        """Validate that total matches sum of components."""
        data = info.data
        if all(k in data for k in ['certifications', 'documentation', 'logistics']):
            calculated_total = data['certifications'] + data['documentation'] + data['logistics']
            if abs(v - calculated_total) > 0.01:  # Allow small floating point tolerance
                raise ValueError(f'Total ({v}) should match sum of components ({calculated_total})')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "certifications": 50000,
                "documentation": 10000,
                "logistics": 25000,
                "total": 85000,
                "currency": "INR"
            }
        }


class ExportReadinessReport(BaseModel):
    """Complete export readiness report."""
    report_id: str = Field(..., description="Unique report identifier")
    status: ReportStatus = Field(..., description="Report generation status")
    hs_code: HSCodePrediction = Field(..., description="HS code prediction")
    certifications: List[Certification] = Field(..., description="Required certifications")
    restricted_substances: List[RestrictedSubstance] = Field(default_factory=list, description="Restricted substances")
    past_rejections: List[PastRejection] = Field(default_factory=list, description="Past rejection data")
    compliance_roadmap: List[RoadmapStep] = Field(..., description="Compliance roadmap")
    risks: List[Risk] = Field(default_factory=list, description="Identified risks")
    risk_score: int = Field(..., ge=0, le=100, description="Overall risk score")
    timeline: Timeline = Field(..., description="Timeline estimate")
    costs: CostBreakdown = Field(..., description="Cost breakdown")
    subsidies: List[Subsidy] = Field(default_factory=list, description="Applicable subsidies")
    action_plan: ActionPlan = Field(..., description="7-day action plan")
    retrieved_sources: List[Source] = Field(default_factory=list, description="Source citations")
    generated_at: datetime = Field(..., description="Report generation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "rpt_123e4567",
                "status": "completed",
                "hs_code": {
                    "code": "0910.30",
                    "confidence": 92.5,
                    "description": "Turmeric (curcuma)",
                    "alternatives": []
                },
                "certifications": [],
                "restricted_substances": [],
                "past_rejections": [],
                "compliance_roadmap": [],
                "risks": [],
                "risk_score": 35,
                "timeline": {
                    "estimated_days": 60,
                    "breakdown": []
                },
                "costs": {
                    "certifications": 50000,
                    "documentation": 10000,
                    "logistics": 25000,
                    "total": 85000,
                    "currency": "INR"
                },
                "subsidies": [],
                "action_plan": {
                    "days": [],
                    "progress_percentage": 0.0
                },
                "retrieved_sources": [],
                "generated_at": "2024-01-15T10:30:00Z"
            }
        }
