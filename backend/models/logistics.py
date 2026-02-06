"""
Logistics risk analysis data models.
"""
from pydantic import BaseModel, Field
from typing import List
from .enums import ShippingMode, FreightMode, RiskSeverity


class ShippingOption(BaseModel):
    """Shipping option details (LCL or FCL)."""
    cost: float = Field(..., ge=0, description="Shipping cost")
    risk_level: RiskSeverity = Field(..., description="Risk level")
    pros: List[str] = Field(..., description="Advantages")
    cons: List[str] = Field(..., description="Disadvantages")

    class Config:
        json_schema_extra = {
            "example": {
                "cost": 50000,
                "risk_level": "medium",
                "pros": [
                    "Lower cost for small volumes",
                    "Flexible scheduling"
                ],
                "cons": [
                    "Higher risk of damage",
                    "Longer customs clearance"
                ]
            }
        }


class LCLFCLComparison(BaseModel):
    """Comparison between LCL and FCL shipping options."""
    recommendation: ShippingMode = Field(..., description="Recommended shipping mode")
    lcl: ShippingOption = Field(..., description="LCL option details")
    fcl: ShippingOption = Field(..., description="FCL option details")

    class Config:
        json_schema_extra = {
            "example": {
                "recommendation": "LCL",
                "lcl": {
                    "cost": 50000,
                    "risk_level": "medium",
                    "pros": ["Lower cost"],
                    "cons": ["Higher risk"]
                },
                "fcl": {
                    "cost": 150000,
                    "risk_level": "low",
                    "pros": ["Lower risk"],
                    "cons": ["Higher cost"]
                }
            }
        }


class RMSProbability(BaseModel):
    """RMS (Risk Management System) check probability."""
    probability_percentage: float = Field(..., ge=0.0, le=100.0, description="Probability percentage")
    risk_level: RiskSeverity = Field(..., description="Risk level")
    risk_factors: List[str] = Field(..., description="Identified risk factors")
    red_flag_keywords: List[str] = Field(default_factory=list, description="Red flag keywords detected")
    mitigation_tips: List[str] = Field(..., description="Tips to mitigate RMS risk")

    class Config:
        json_schema_extra = {
            "example": {
                "probability_percentage": 35.5,
                "risk_level": "medium",
                "risk_factors": [
                    "First-time exporter",
                    "High-value shipment",
                    "Sensitive product category"
                ],
                "red_flag_keywords": ["chemical", "powder"],
                "mitigation_tips": [
                    "Provide detailed product documentation",
                    "Use specific product descriptions",
                    "Include test certificates"
                ]
            }
        }


class Route(BaseModel):
    """Shipping route information."""
    name: str = Field(..., description="Route name")
    transit_time_days: int = Field(..., gt=0, description="Transit time in days")
    delay_risk: RiskSeverity = Field(..., description="Delay risk level")
    geopolitical_factors: List[str] = Field(default_factory=list, description="Geopolitical factors")
    cost_estimate: float = Field(..., ge=0, description="Cost estimate")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Mumbai to New York via Suez Canal",
                "transit_time_days": 25,
                "delay_risk": "medium",
                "geopolitical_factors": [
                    "Red Sea tensions may cause delays"
                ],
                "cost_estimate": 75000
            }
        }


class RouteAnalysis(BaseModel):
    """Analysis of available shipping routes."""
    recommended_route: str = Field(..., description="Recommended route name")
    routes: List[Route] = Field(..., description="Available routes")

    class Config:
        json_schema_extra = {
            "example": {
                "recommended_route": "Mumbai to New York via Cape of Good Hope",
                "routes": [
                    {
                        "name": "Mumbai to New York via Suez Canal",
                        "transit_time_days": 25,
                        "delay_risk": "medium",
                        "geopolitical_factors": [],
                        "cost_estimate": 75000
                    }
                ]
            }
        }


class FreightEstimate(BaseModel):
    """Freight cost estimation."""
    sea_freight: float = Field(..., ge=0, description="Sea freight cost")
    air_freight: float = Field(..., ge=0, description="Air freight cost")
    recommended_mode: FreightMode = Field(..., description="Recommended freight mode")
    currency: str = Field(default="USD", description="Currency code")

    class Config:
        json_schema_extra = {
            "example": {
                "sea_freight": 2500,
                "air_freight": 8500,
                "recommended_mode": "sea",
                "currency": "USD"
            }
        }


class InsuranceRecommendation(BaseModel):
    """Insurance coverage recommendation."""
    recommended_coverage: float = Field(..., ge=0, description="Recommended coverage amount")
    premium_estimate: float = Field(..., ge=0, description="Estimated premium")
    coverage_type: str = Field(..., description="Type of coverage")

    class Config:
        json_schema_extra = {
            "example": {
                "recommended_coverage": 250000,
                "premium_estimate": 2500,
                "coverage_type": "All-risk marine cargo insurance"
            }
        }


class LogisticsRiskAnalysis(BaseModel):
    """Complete logistics risk analysis."""
    lcl_fcl_comparison: LCLFCLComparison = Field(..., description="LCL vs FCL comparison")
    rms_probability: RMSProbability = Field(..., description="RMS check probability")
    route_analysis: RouteAnalysis = Field(..., description="Route analysis")
    freight_estimate: FreightEstimate = Field(..., description="Freight cost estimate")
    insurance_recommendation: InsuranceRecommendation = Field(..., description="Insurance recommendation")

    class Config:
        json_schema_extra = {
            "example": {
                "lcl_fcl_comparison": {
                    "recommendation": "LCL",
                    "lcl": {
                        "cost": 50000,
                        "risk_level": "medium",
                        "pros": [],
                        "cons": []
                    },
                    "fcl": {
                        "cost": 150000,
                        "risk_level": "low",
                        "pros": [],
                        "cons": []
                    }
                },
                "rms_probability": {
                    "probability_percentage": 35.5,
                    "risk_level": "medium",
                    "risk_factors": [],
                    "red_flag_keywords": [],
                    "mitigation_tips": []
                },
                "route_analysis": {
                    "recommended_route": "Mumbai to New York",
                    "routes": []
                },
                "freight_estimate": {
                    "sea_freight": 2500,
                    "air_freight": 8500,
                    "recommended_mode": "sea",
                    "currency": "USD"
                },
                "insurance_recommendation": {
                    "recommended_coverage": 250000,
                    "premium_estimate": 2500,
                    "coverage_type": "All-risk marine cargo insurance"
                }
            }
        }


class LogisticsRiskRequest(BaseModel):
    """Request for logistics risk analysis."""
    product_type: str = Field(..., description="Type of product")
    hs_code: str = Field(..., description="HS code")
    volume: float = Field(..., gt=0, description="Shipment volume")
    value: float = Field(..., gt=0, description="Shipment value")
    destination_country: str = Field(..., description="Destination country")
    product_description: str = Field(..., description="Product description")

    class Config:
        json_schema_extra = {
            "example": {
                "product_type": "Turmeric powder",
                "hs_code": "0910.30",
                "volume": 1000.0,
                "value": 200000.0,
                "destination_country": "United States",
                "product_description": "Organic turmeric powder for food use"
            }
        }
