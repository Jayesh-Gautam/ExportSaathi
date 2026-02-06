"""
User and profile data models.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re
from .enums import BusinessType, CompanySize


class UserProfile(BaseModel):
    """User profile information."""
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    business_type: BusinessType = Field(..., description="Type of business")
    company_size: CompanySize = Field(..., description="Size of the company")
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    monthly_volume: Optional[float] = Field(None, gt=0, description="Monthly export volume")
    created_at: datetime = Field(..., description="Account creation timestamp")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "business_type": "Manufacturing",
                "company_size": "Small",
                "company_name": "ABC Exports Pvt Ltd",
                "monthly_volume": 50000.0,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class UserMetrics(BaseModel):
    """User success metrics and analytics."""
    user_id: str = Field(..., description="Unique user identifier")
    reports_generated: int = Field(default=0, ge=0, description="Number of reports generated")
    certifications_completed: int = Field(default=0, ge=0, description="Number of certifications completed")
    exports_completed: int = Field(default=0, ge=0, description="Number of successful exports")
    cost_savings: float = Field(default=0.0, ge=0, description="Total cost savings in INR")
    timeline_savings: float = Field(default=0.0, ge=0, description="Timeline savings in days")
    success_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="Success rate percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "reports_generated": 5,
                "certifications_completed": 2,
                "exports_completed": 3,
                "cost_savings": 150000.0,
                "timeline_savings": 45.0,
                "success_rate": 85.5
            }
        }
