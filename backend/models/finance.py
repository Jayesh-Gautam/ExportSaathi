"""
Finance readiness data models.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import date
from .enums import CashFlowEventType


class WorkingCapitalAnalysis(BaseModel):
    """Working capital requirement analysis."""
    product_cost: float = Field(..., ge=0, description="Product/manufacturing cost")
    certification_costs: float = Field(..., ge=0, description="Certification costs")
    logistics_costs: float = Field(..., ge=0, description="Logistics costs")
    documentation_costs: float = Field(..., ge=0, description="Documentation costs")
    buffer: float = Field(..., ge=0, description="Buffer amount")
    total: float = Field(..., ge=0, description="Total working capital required")
    currency: str = Field(default="INR", description="Currency code")

    @field_validator('total')
    @classmethod
    def validate_total_matches_sum(cls, v: float, info) -> float:
        """Validate that total matches sum of components."""
        data = info.data
        if all(k in data for k in ['product_cost', 'certification_costs', 'logistics_costs', 'documentation_costs', 'buffer']):
            calculated_total = (
                data['product_cost'] + 
                data['certification_costs'] + 
                data['logistics_costs'] + 
                data['documentation_costs'] + 
                data['buffer']
            )
            if abs(v - calculated_total) > 0.01:
                raise ValueError(f'Total ({v}) should match sum of components ({calculated_total})')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "product_cost": 100000,
                "certification_costs": 50000,
                "logistics_costs": 25000,
                "documentation_costs": 10000,
                "buffer": 15000,
                "total": 200000,
                "currency": "INR"
            }
        }


class PreShipmentCredit(BaseModel):
    """Pre-shipment credit eligibility assessment."""
    eligible: bool = Field(..., description="Whether eligible for credit")
    estimated_amount: float = Field(..., ge=0, description="Estimated credit amount")
    interest_rate: float = Field(..., ge=0, description="Interest rate percentage")
    tenure_days: int = Field(..., gt=0, description="Credit tenure in days")
    requirements: List[str] = Field(..., description="Requirements to obtain credit")

    class Config:
        json_schema_extra = {
            "example": {
                "eligible": True,
                "estimated_amount": 150000,
                "interest_rate": 8.5,
                "tenure_days": 90,
                "requirements": [
                    "Valid export order",
                    "Company registration",
                    "Bank account with export credit facility"
                ]
            }
        }


class RoDTEPBenefit(BaseModel):
    """RoDTEP (Remission of Duties and Taxes on Exported Products) benefit."""
    hs_code: str = Field(..., description="HS code")
    rate_percentage: float = Field(..., ge=0, le=100, description="RoDTEP rate percentage")
    estimated_amount: float = Field(..., ge=0, description="Estimated benefit amount")
    currency: str = Field(default="INR", description="Currency code")

    class Config:
        json_schema_extra = {
            "example": {
                "hs_code": "0910.30",
                "rate_percentage": 2.5,
                "estimated_amount": 5000,
                "currency": "INR"
            }
        }


class GSTRefund(BaseModel):
    """GST refund estimation."""
    estimated_amount: float = Field(..., ge=0, description="Estimated refund amount")
    timeline_days: int = Field(..., gt=0, description="Expected timeline in days")
    requirements: List[str] = Field(..., description="Requirements for refund")

    class Config:
        json_schema_extra = {
            "example": {
                "estimated_amount": 18000,
                "timeline_days": 45,
                "requirements": [
                    "GST LUT filed",
                    "Shipping bill filed",
                    "Bank realization certificate"
                ]
            }
        }


class CashFlowEvent(BaseModel):
    """Cash flow event (expense or income)."""
    event_date: date = Field(..., description="Event date", alias="date")
    event_type: CashFlowEventType = Field(..., description="Event type", alias="type")
    category: str = Field(..., description="Event category")
    amount: float = Field(..., description="Amount (positive for income, negative for expense)")
    description: str = Field(..., description="Event description")

    @field_validator('amount')
    @classmethod
    def validate_amount_sign(cls, v: float, info) -> float:
        """Validate amount sign matches event type."""
        # Get event_type from the data being validated
        data = info.data
        if 'event_type' in data:
            if data['event_type'] == CashFlowEventType.EXPENSE and v > 0:
                return -abs(v)  # Make negative for expenses
            elif data['event_type'] == CashFlowEventType.INCOME and v < 0:
                return abs(v)  # Make positive for income
        return v

    model_config = {
        "populate_by_name": True,  # Allow both 'type' and 'event_type'
        "json_schema_extra": {
            "example": {
                "date": "2024-02-01",
                "type": "expense",
                "category": "Certification",
                "amount": -50000,
                "description": "FDA registration fee"
            }
        }
    }


class LiquidityGap(BaseModel):
    """Period of liquidity gap."""
    start_date: date = Field(..., description="Gap start date")
    end_date: date = Field(..., description="Gap end date")
    amount: float = Field(..., description="Gap amount")

    @field_validator('end_date')
    @classmethod
    def validate_end_after_start(cls, v: date, info) -> date:
        """Validate end date is after start date."""
        data = info.data
        if 'start_date' in data and v <= data['start_date']:
            raise ValueError('End date must be after start date')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-02-01",
                "end_date": "2024-03-15",
                "amount": 75000
            }
        }


class CashFlowTimeline(BaseModel):
    """Cash flow timeline with events and liquidity gap."""
    events: List[CashFlowEvent] = Field(..., description="Cash flow events")
    liquidity_gap: LiquidityGap = Field(..., description="Liquidity gap period")

    class Config:
        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "date": "2024-02-01",
                        "type": "expense",
                        "category": "Certification",
                        "amount": -50000,
                        "description": "FDA registration"
                    }
                ],
                "liquidity_gap": {
                    "start_date": "2024-02-01",
                    "end_date": "2024-03-15",
                    "amount": 75000
                }
            }
        }


class CurrencyHedging(BaseModel):
    """Currency hedging recommendations."""
    recommended: bool = Field(..., description="Whether hedging is recommended")
    strategies: List[str] = Field(..., description="Recommended hedging strategies")
    estimated_savings: float = Field(..., ge=0, description="Estimated savings from hedging")

    class Config:
        json_schema_extra = {
            "example": {
                "recommended": True,
                "strategies": [
                    "Forward contract for 50% of order value",
                    "Currency options for remaining 50%"
                ],
                "estimated_savings": 15000
            }
        }


class FinancingOption(BaseModel):
    """Financing option available to the exporter."""
    type: str = Field(..., description="Financing type")
    provider: str = Field(..., description="Financing provider")
    amount: float = Field(..., ge=0, description="Financing amount")
    interest_rate: float = Field(..., ge=0, description="Interest rate percentage")
    tenure: str = Field(..., description="Financing tenure")
    eligibility: str = Field(..., description="Eligibility criteria")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "Pre-shipment credit",
                "provider": "State Bank of India",
                "amount": 150000,
                "interest_rate": 8.5,
                "tenure": "90 days",
                "eligibility": "Valid export order and company registration"
            }
        }


class FinanceAnalysis(BaseModel):
    """Complete finance readiness analysis."""
    report_id: str = Field(..., description="Associated report ID")
    working_capital: WorkingCapitalAnalysis = Field(..., description="Working capital analysis")
    pre_shipment_credit: PreShipmentCredit = Field(..., description="Pre-shipment credit assessment")
    rodtep_benefit: RoDTEPBenefit = Field(..., description="RoDTEP benefit calculation")
    gst_refund: GSTRefund = Field(..., description="GST refund estimation")
    cash_flow_timeline: CashFlowTimeline = Field(..., description="Cash flow timeline")
    currency_hedging: CurrencyHedging = Field(..., description="Currency hedging recommendations")
    financing_options: List[FinancingOption] = Field(..., description="Available financing options")

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "rpt_123e4567",
                "working_capital": {
                    "product_cost": 100000,
                    "certification_costs": 50000,
                    "logistics_costs": 25000,
                    "documentation_costs": 10000,
                    "buffer": 15000,
                    "total": 200000,
                    "currency": "INR"
                },
                "pre_shipment_credit": {
                    "eligible": True,
                    "estimated_amount": 150000,
                    "interest_rate": 8.5,
                    "tenure_days": 90,
                    "requirements": []
                },
                "rodtep_benefit": {
                    "hs_code": "0910.30",
                    "rate_percentage": 2.5,
                    "estimated_amount": 5000,
                    "currency": "INR"
                },
                "gst_refund": {
                    "estimated_amount": 18000,
                    "timeline_days": 45,
                    "requirements": []
                },
                "cash_flow_timeline": {
                    "events": [],
                    "liquidity_gap": {
                        "start_date": "2024-02-01",
                        "end_date": "2024-03-15",
                        "amount": 75000
                    }
                },
                "currency_hedging": {
                    "recommended": True,
                    "strategies": [],
                    "estimated_savings": 15000
                },
                "financing_options": []
            }
        }
