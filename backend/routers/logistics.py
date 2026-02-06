"""
Logistics API Router
Handles logistics risk analysis, RMS probability, and freight estimation

This router implements the core API endpoints for logistics risk analysis.
It provides:
1. POST /api/logistics/risk-analysis - Comprehensive logistics risk analysis
2. POST /api/logistics/rms-probability - Calculate RMS check probability
3. POST /api/logistics/freight-estimate - Estimate freight costs

Requirements: 8.1
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional
import logging

from models.logistics import (
    LogisticsRiskAnalysis,
    LogisticsRiskRequest,
    RMSProbability,
    FreightEstimate
)
from services.logistics_risk_shield import LogisticsRiskShield
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class RMSProbabilityRequest(BaseModel):
    """Request model for RMS probability calculation."""
    product_type: str = Field(..., min_length=1, max_length=200, description="Type of product")
    hs_code: str = Field(..., min_length=4, max_length=20, description="HS code")
    product_description: str = Field(..., min_length=1, max_length=1000, description="Product description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_type": "Turmeric powder",
                "hs_code": "0910.30",
                "product_description": "Organic turmeric powder for food use"
            }
        }


class FreightEstimateRequest(BaseModel):
    """Request model for freight cost estimation."""
    destination_country: str = Field(..., min_length=1, max_length=100, description="Destination country")
    volume: float = Field(..., gt=0, description="Shipment volume in cubic meters (CBM)")
    weight: float = Field(..., gt=0, description="Shipment weight in kilograms")
    
    class Config:
        json_schema_extra = {
            "example": {
                "destination_country": "United States",
                "volume": 10.0,
                "weight": 2000.0
            }
        }


@router.post("/risk-analysis", response_model=LogisticsRiskAnalysis)
async def analyze_logistics_risks(request: LogisticsRiskRequest):
    """
    Perform comprehensive logistics risk analysis.
    
    This endpoint analyzes logistics risks for export shipments including:
    - LCL vs FCL comparison based on volume and product type
    - RMS (Risk Management System) probability estimation
    - Route delay prediction based on geopolitical factors
    - Freight cost estimation for sea and air modes
    - Insurance coverage recommendations
    
    **Request Body:**
    - product_type: Type of product being shipped (required)
    - hs_code: Harmonized System code (required)
    - volume: Shipment volume in cubic meters (required, must be positive)
    - value: Shipment value in USD (required, must be positive)
    - destination_country: Destination country name (required)
    - product_description: Detailed product description (required)
    
    **Returns:**
    - LogisticsRiskAnalysis with all risk components and recommendations
    
    **Errors:**
    - 400: Invalid request data
    - 422: Validation error
    - 500: Internal server error during analysis
    
    **Example:**
    ```json
    {
        "product_type": "Turmeric powder",
        "hs_code": "0910.30",
        "volume": 10.0,
        "value": 20000.0,
        "destination_country": "United States",
        "product_description": "Organic turmeric powder for food use"
    }
    ```
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Analyzing logistics risks for {request.product_type} to {request.destination_country}")
        
        # Validate and clean inputs
        if not request.product_type.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product type cannot be empty"
            )
        
        if not request.hs_code.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HS code cannot be empty"
            )
        
        if not request.destination_country.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Destination country cannot be empty"
            )
        
        if not request.product_description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product description cannot be empty"
            )
        
        # Perform logistics risk analysis using LogisticsRiskShield service
        logger.info("Calling LogisticsRiskShield service...")
        service = LogisticsRiskShield()
        analysis = service.analyze_risks(request)
        
        logger.info(
            f"Logistics risk analysis completed: "
            f"RMS probability={analysis.rms_probability.probability_percentage}%, "
            f"Recommended mode={analysis.lcl_fcl_comparison.recommendation}"
        )
        
        return analysis
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as e:
        # Validation errors
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error analyzing logistics risks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while analyzing logistics risks. Please try again later."
        )


@router.post("/rms-probability", response_model=RMSProbability)
async def calculate_rms_probability(request: RMSProbabilityRequest):
    """
    Calculate RMS (Risk Management System) check probability.
    
    This endpoint estimates the probability that a shipment will be flagged by
    customs RMS for physical inspection. It analyzes:
    - Product type risk factors
    - HS code risk category
    - Red flag keywords in product description
    - Historical inspection patterns
    
    **Request Body:**
    - product_type: Type of product (required)
    - hs_code: Harmonized System code (required)
    - product_description: Detailed product description (required)
    
    **Returns:**
    - RMSProbability with percentage, risk level, factors, and mitigation tips
    
    **Errors:**
    - 400: Invalid request data
    - 422: Validation error
    - 500: Internal server error during calculation
    
    **Example:**
    ```json
    {
        "product_type": "Turmeric powder",
        "hs_code": "0910.30",
        "product_description": "Organic turmeric powder for food use"
    }
    ```
    
    **Response:**
    ```json
    {
        "probability_percentage": 35.5,
        "risk_level": "medium",
        "risk_factors": [
            "High-risk product category: Turmeric powder",
            "Red flag keywords detected: powder, organic"
        ],
        "red_flag_keywords": ["powder", "organic"],
        "mitigation_tips": [
            "Provide detailed and accurate product documentation",
            "Use specific product descriptions (avoid vague terms)",
            "Include test certificates and quality reports"
        ]
    }
    ```
    
    Requirements: 8.1
    """
    try:
        logger.info(f"Calculating RMS probability for {request.product_type}, HS code: {request.hs_code}")
        
        # Validate inputs
        if not request.product_type.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product type cannot be empty"
            )
        
        if not request.hs_code.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HS code cannot be empty"
            )
        
        if not request.product_description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product description cannot be empty"
            )
        
        # Calculate RMS probability using LogisticsRiskShield service
        logger.info("Calling LogisticsRiskShield RMS probability estimator...")
        service = LogisticsRiskShield()
        rms_probability = service.estimate_rms_probability(
            product_type=request.product_type.strip(),
            hs_code=request.hs_code.strip(),
            description=request.product_description.strip()
        )
        
        logger.info(
            f"RMS probability calculated: {rms_probability.probability_percentage}%, "
            f"risk level: {rms_probability.risk_level}"
        )
        
        return rms_probability
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as e:
        # Validation errors
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error calculating RMS probability: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while calculating RMS probability. Please try again later."
        )


@router.post("/freight-estimate", response_model=FreightEstimate)
async def estimate_freight(request: FreightEstimateRequest):
    """
    Estimate freight costs for sea and air shipping modes.
    
    This endpoint calculates freight costs for different shipping modes based on:
    - Destination country and region
    - Shipment volume (for sea freight)
    - Shipment weight (for air freight)
    - Volumetric weight calculation for air freight
    
    **Request Body:**
    - destination_country: Destination country name (required)
    - volume: Shipment volume in cubic meters/CBM (required, must be positive)
    - weight: Shipment weight in kilograms (required, must be positive)
    
    **Returns:**
    - FreightEstimate with sea freight, air freight, and recommended mode
    
    **Errors:**
    - 400: Invalid request data
    - 422: Validation error
    - 500: Internal server error during estimation
    
    **Example:**
    ```json
    {
        "destination_country": "United States",
        "volume": 10.0,
        "weight": 2000.0
    }
    ```
    
    **Response:**
    ```json
    {
        "sea_freight": 1000.0,
        "air_freight": 12000.0,
        "recommended_mode": "sea",
        "currency": "USD"
    }
    ```
    
    **Notes:**
    - Sea freight is calculated based on volume (CBM)
    - Air freight is calculated based on chargeable weight (higher of actual weight or volumetric weight)
    - Volumetric weight = volume (CBM) × 167 kg/CBM
    - Recommended mode is typically sea freight unless air freight is less than 3x sea freight cost
    
    Requirements: 8.1
    """
    try:
        logger.info(
            f"Estimating freight costs to {request.destination_country}, "
            f"volume: {request.volume} CBM, weight: {request.weight} kg"
        )
        
        # Validate inputs
        if not request.destination_country.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Destination country cannot be empty"
            )
        
        if request.volume <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Volume must be greater than 0"
            )
        
        if request.weight <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weight must be greater than 0"
            )
        
        # Estimate freight costs using LogisticsRiskShield service
        logger.info("Calling LogisticsRiskShield freight estimator...")
        service = LogisticsRiskShield()
        freight_estimate = service.estimate_freight_cost(
            destination=request.destination_country.strip(),
            volume=request.volume,
            weight=request.weight
        )
        
        logger.info(
            f"Freight estimate calculated: "
            f"Sea=${freight_estimate.sea_freight:.2f}, "
            f"Air=${freight_estimate.air_freight:.2f}, "
            f"Recommended={freight_estimate.recommended_mode}"
        )
        
        return freight_estimate
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as e:
        # Validation errors
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error estimating freight costs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while estimating freight costs. Please try again later."
        )
