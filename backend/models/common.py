"""
Common data models used across ExportSathi.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class CostRange(BaseModel):
    """Cost range with min and max values."""
    min: float = Field(..., ge=0, description="Minimum cost")
    max: float = Field(..., ge=0, description="Maximum cost")
    currency: str = Field(default="INR", description="Currency code")

    class Config:
        json_schema_extra = {
            "example": {
                "min": 5000,
                "max": 25000,
                "currency": "INR"
            }
        }


class Source(BaseModel):
    """Source citation for retrieved documents."""
    title: str = Field(..., description="Title of the source document")
    source: Optional[str] = Field(None, description="Source type or organization")
    excerpt: Optional[str] = Field(None, description="Relevant excerpt from the source")
    url: Optional[str] = Field(None, description="URL to the source document")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "DGFT Export Policy 2023",
                "source": "DGFT",
                "excerpt": "All exports require proper HS code classification...",
                "url": "https://dgft.gov.in/policy",
                "relevance_score": 0.95
            }
        }


class GuidanceStep(BaseModel):
    """Step in a guidance or certification process."""
    step_number: int = Field(..., ge=1, description="Step sequence number")
    title: Optional[str] = Field(None, description="Step title")
    description: str = Field(..., description="Detailed description of the step")
    estimated_duration: str = Field(..., description="Estimated time to complete")

    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "title": "Submit Application",
                "description": "Complete and submit the FDA registration form online",
                "estimated_duration": "2-3 days"
            }
        }
