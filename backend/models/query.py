"""
Query input and HS code prediction models.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from .enums import BusinessType, CompanySize


class QueryInput(BaseModel):
    """Input data for export readiness query."""
    product_name: str = Field(..., min_length=1, max_length=200, description="Product name")
    product_image: Optional[bytes] = Field(None, description="Product image binary data")
    ingredients: Optional[str] = Field(None, max_length=2000, description="Product ingredients")
    bom: Optional[str] = Field(None, max_length=2000, description="Bill of Materials")
    destination_country: str = Field(..., min_length=1, max_length=100, description="Destination country")
    business_type: BusinessType = Field(..., description="Type of business")
    company_size: CompanySize = Field(..., description="Size of the company")
    monthly_volume: Optional[float] = Field(None, gt=0, description="Monthly export volume")
    price_range: Optional[str] = Field(None, description="Price range of the product")
    payment_mode: Optional[str] = Field(None, description="Preferred payment mode")

    @field_validator('product_name')
    @classmethod
    def validate_product_name(cls, v: str) -> str:
        """Validate product name is not empty after stripping."""
        if not v.strip():
            raise ValueError('Product name cannot be empty or whitespace only')
        return v.strip()

    @field_validator('destination_country')
    @classmethod
    def validate_destination_country(cls, v: str) -> str:
        """Validate destination country is not empty after stripping."""
        if not v.strip():
            raise ValueError('Destination country cannot be empty or whitespace only')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Organic Turmeric Powder",
                "ingredients": "100% organic turmeric",
                "bom": "Turmeric rhizomes, packaging material",
                "destination_country": "United States",
                "business_type": "Manufacturing",
                "company_size": "Small",
                "monthly_volume": 1000.0,
                "price_range": "500-1000 INR/kg",
                "payment_mode": "LC"
            }
        }


class HSCodeAlternative(BaseModel):
    """Alternative HS code prediction."""
    code: str = Field(..., description="HS code")
    confidence: float = Field(..., ge=0.0, le=100.0, description="Confidence percentage")
    description: str = Field(..., description="HS code description")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "0910.30",
                "confidence": 65.5,
                "description": "Turmeric (curcuma)"
            }
        }


class HSCodePrediction(BaseModel):
    """HS code prediction with confidence and alternatives."""
    code: str = Field(..., description="Predicted HS code")
    confidence: float = Field(..., ge=0.0, le=100.0, description="Confidence percentage")
    description: str = Field(..., description="HS code description")
    alternatives: List[HSCodeAlternative] = Field(default_factory=list, description="Alternative HS codes")

    @field_validator('alternatives')
    @classmethod
    def validate_alternatives_sorted(cls, v: List[HSCodeAlternative]) -> List[HSCodeAlternative]:
        """Ensure alternatives are sorted by confidence descending."""
        if v:
            sorted_alternatives = sorted(v, key=lambda x: x.confidence, reverse=True)
            return sorted_alternatives
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "code": "0910.30",
                "confidence": 92.5,
                "description": "Turmeric (curcuma)",
                "alternatives": [
                    {
                        "code": "0910.99",
                        "confidence": 65.0,
                        "description": "Other spices"
                    }
                ]
            }
        }


class ImageFeatures(BaseModel):
    """Features extracted from product image."""
    extracted_text: str = Field(..., description="Text extracted from image")
    visual_features: dict = Field(..., description="Visual features from image analysis")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")

    class Config:
        json_schema_extra = {
            "example": {
                "extracted_text": "Organic Turmeric 100g",
                "visual_features": {
                    "color": "yellow-orange",
                    "texture": "powder",
                    "packaging": "sealed bag"
                },
                "confidence": 0.89
            }
        }
