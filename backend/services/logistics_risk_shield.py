"""
Logistics Risk Shield Service for ExportSathi.

This module provides comprehensive logistics risk analysis including:
- LCL vs FCL comparison based on volume and product type
- RMS (Risk Management System) probability estimation
- Route delay prediction based on geopolitical factors
- Freight cost estimation for different routes and modes
- Insurance coverage recommendations
- Red flag keyword detection
"""
from typing import List, Dict, Optional
from datetime import date
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.logistics import (
    LogisticsRiskAnalysis,
    LCLFCLComparison,
    ShippingOption,
    RMSProbability,
    RouteAnalysis,
    Route,
    FreightEstimate,
    InsuranceRecommendation,
    LogisticsRiskRequest
)
from models.enums import ShippingMode, FreightMode, RiskSeverity


class LogisticsRiskShield:
    """
    Logistics Risk Shield for analyzing shipping risks and providing recommendations.
    
    This service helps exporters make informed decisions about:
    - Container load options (LCL vs FCL)
    - Customs inspection probability (RMS)
    - Shipping routes and delays
    - Freight costs
    - Insurance coverage
    """
    
    def __init__(self):
        """Initialize the Logistics Risk Shield."""
        # FCL container capacity in cubic meters
        self.fcl_capacity_cbm = 33.0  # Standard 20ft container
        
        # RMS risk keywords database
        self.rms_red_flag_keywords = [
            "chemical", "powder", "liquid", "explosive", "flammable",
            "hazardous", "toxic", "radioactive", "weapon", "drug",
            "pharmaceutical", "medicine", "supplement", "herbal",
            "ayurvedic", "organic", "natural", "extract", "oil"
        ]
        
        # Product type risk factors
        self.high_risk_product_types = [
            "food", "beverage", "cosmetic", "pharmaceutical", "chemical",
            "supplement", "herbal", "ayurvedic", "medical device"
        ]
        
        # Geopolitical risk database (simplified)
        self.geopolitical_risks = {
            "Red Sea": {
                "risk_level": RiskSeverity.HIGH,
                "factors": [
                    "Ongoing tensions in Red Sea region",
                    "Potential for shipping disruptions",
                    "Increased insurance premiums"
                ],
                "delay_days": 10
            },
            "Suez Canal": {
                "risk_level": RiskSeverity.MEDIUM,
                "factors": [
                    "Congestion during peak seasons",
                    "Occasional blockages"
                ],
                "delay_days": 3
            },
            "Panama Canal": {
                "risk_level": RiskSeverity.LOW,
                "factors": [
                    "Water level restrictions during dry season"
                ],
                "delay_days": 2
            }
        }
        
        # Base freight rates (USD per CBM for sea, USD per kg for air)
        self.base_freight_rates = {
            "sea": {
                "Asia": 50,
                "Europe": 80,
                "North America": 100,
                "Middle East": 60,
                "Africa": 70,
                "South America": 110,
                "Oceania": 90
            },
            "air": {
                "Asia": 3.5,
                "Europe": 5.0,
                "North America": 6.0,
                "Middle East": 4.5,
                "Africa": 5.5,
                "South America": 7.0,
                "Oceania": 6.5
            }
        }
        
        # Country to region mapping
        self.country_to_region = {
            "United States": "North America",
            "Canada": "North America",
            "Mexico": "North America",
            "United Kingdom": "Europe",
            "Germany": "Europe",
            "France": "Europe",
            "Italy": "Europe",
            "Spain": "Europe",
            "Netherlands": "Europe",
            "China": "Asia",
            "Japan": "Asia",
            "South Korea": "Asia",
            "Singapore": "Asia",
            "Thailand": "Asia",
            "Vietnam": "Asia",
            "UAE": "Middle East",
            "Saudi Arabia": "Middle East",
            "Qatar": "Middle East",
            "South Africa": "Africa",
            "Kenya": "Africa",
            "Nigeria": "Africa",
            "Brazil": "South America",
            "Argentina": "South America",
            "Chile": "South America",
            "Australia": "Oceania",
            "New Zealand": "Oceania"
        }
    
    def analyze_risks(self, request: LogisticsRiskRequest) -> LogisticsRiskAnalysis:
        """
        Perform comprehensive logistics risk analysis.
        
        This is the main method that orchestrates all logistics risk assessments.
        
        Args:
            request: LogisticsRiskRequest with shipment details
            
        Returns:
            LogisticsRiskAnalysis with all components
        """
        # Compare LCL vs FCL options
        lcl_fcl_comparison = self.compare_lcl_fcl(
            volume=request.volume,
            product_type=request.product_type
        )
        
        # Estimate RMS probability
        rms_probability = self.estimate_rms_probability(
            product_type=request.product_type,
            hs_code=request.hs_code,
            description=request.product_description
        )
        
        # Analyze routes
        route_analysis = self.predict_route_delays(
            destination=request.destination_country
        )
        
        # Estimate freight costs
        freight_estimate = self.estimate_freight_cost(
            destination=request.destination_country,
            volume=request.volume,
            weight=request.volume * 200  # Assume 200 kg/CBM density
        )
        
        # Recommend insurance
        insurance_recommendation = self.recommend_insurance(
            shipment_value=request.value,
            risk_level=rms_probability.risk_level
        )
        
        return LogisticsRiskAnalysis(
            lcl_fcl_comparison=lcl_fcl_comparison,
            rms_probability=rms_probability,
            route_analysis=route_analysis,
            freight_estimate=freight_estimate,
            insurance_recommendation=insurance_recommendation
        )
    
    def compare_lcl_fcl(
        self,
        volume: float,
        product_type: str
    ) -> LCLFCLComparison:
        """
        Compare LCL (Less than Container Load) vs FCL (Full Container Load) options.
        
        Args:
            volume: Shipment volume in cubic meters (CBM)
            product_type: Type of product being shipped
            
        Returns:
            LCLFCLComparison with recommendation and details
        """
        # Calculate FCL utilization percentage
        fcl_utilization = (volume / self.fcl_capacity_cbm) * 100
        
        # Determine if product is high-risk
        is_high_risk = any(
            risk_type.lower() in product_type.lower()
            for risk_type in self.high_risk_product_types
        )
        
        # LCL cost calculation (higher per-CBM rate)
        lcl_cost_per_cbm = 150  # USD per CBM
        lcl_total_cost = volume * lcl_cost_per_cbm
        
        # FCL cost calculation (fixed container cost)
        fcl_container_cost = 3000  # USD for 20ft container
        fcl_total_cost = fcl_container_cost
        
        # LCL pros and cons
        lcl_pros = [
            "Lower cost for small volumes",
            "Flexible scheduling",
            "No need to fill entire container",
            "Pay only for space used"
        ]
        
        lcl_cons = [
            "Higher risk of damage due to multiple handling",
            "Longer customs clearance time",
            "Shared container with other shipments",
            "Higher per-CBM cost for larger volumes",
            "Risk of contamination from other cargo"
        ]
        
        # Add high-risk specific cons
        if is_high_risk:
            lcl_cons.append("Higher RMS inspection probability for shared containers")
            lcl_cons.append("Potential delays if other cargo in container is flagged")
        
        # FCL pros and cons
        fcl_pros = [
            "Lower risk of damage (dedicated container)",
            "Faster customs clearance",
            "Better for high-value or fragile goods",
            "Lower per-CBM cost for larger volumes",
            "No contamination risk from other cargo"
        ]
        
        fcl_cons = [
            "Higher upfront cost",
            "Need sufficient volume to justify",
            "Less flexible scheduling",
            "Wasted space if container not full"
        ]
        
        # Determine risk levels
        # LCL has higher risk due to multiple handling and shared container
        lcl_risk = RiskSeverity.MEDIUM if not is_high_risk else RiskSeverity.HIGH
        fcl_risk = RiskSeverity.LOW
        
        # Make recommendation based on volume and product type
        if fcl_utilization >= 60:
            # If container is 60%+ full, FCL is usually better
            recommendation = ShippingMode.FCL
        elif is_high_risk and fcl_utilization >= 40:
            # For high-risk products, recommend FCL at lower threshold
            recommendation = ShippingMode.FCL
        else:
            # For small volumes, LCL is more cost-effective
            recommendation = ShippingMode.LCL
        
        # Create shipping options
        lcl_option = ShippingOption(
            cost=lcl_total_cost,
            risk_level=lcl_risk,
            pros=lcl_pros,
            cons=lcl_cons
        )
        
        fcl_option = ShippingOption(
            cost=fcl_total_cost,
            risk_level=fcl_risk,
            pros=fcl_pros,
            cons=fcl_cons
        )
        
        return LCLFCLComparison(
            recommendation=recommendation,
            lcl=lcl_option,
            fcl=fcl_option
        )
    
    def estimate_rms_probability(
        self,
        product_type: str,
        hs_code: str,
        description: str
    ) -> RMSProbability:
        """
        Estimate RMS (Risk Management System) check probability.
        
        RMS is the customs screening system that flags shipments for physical inspection.
        
        Args:
            product_type: Type of product
            hs_code: Harmonized System code
            description: Product description
            
        Returns:
            RMSProbability with percentage, risk factors, and mitigation tips
        """
        # Base probability: 15% (average RMS check rate)
        probability = 15.0
        
        # Risk factors identified
        risk_factors: List[str] = []
        
        # Detected red flag keywords
        red_flag_keywords: List[str] = []
        
        # Check for high-risk product types
        is_high_risk_product = any(
            risk_type.lower() in product_type.lower()
            for risk_type in self.high_risk_product_types
        )
        
        if is_high_risk_product:
            probability += 20.0
            risk_factors.append(f"High-risk product category: {product_type}")
        
        # Check for red flag keywords in description
        description_lower = description.lower()
        for keyword in self.rms_red_flag_keywords:
            if keyword in description_lower:
                red_flag_keywords.append(keyword)
        
        if red_flag_keywords:
            probability += len(red_flag_keywords) * 5.0
            risk_factors.append(f"Red flag keywords detected: {', '.join(red_flag_keywords)}")
        
        # Check HS code risk (certain HS codes are high-risk)
        high_risk_hs_prefixes = ["29", "30", "33", "38"]  # Chemicals, pharma, cosmetics
        hs_prefix = hs_code[:2] if len(hs_code) >= 2 else ""
        
        if hs_prefix in high_risk_hs_prefixes:
            probability += 15.0
            risk_factors.append(f"High-risk HS code category: {hs_prefix}")
        
        # Cap probability at 95%
        probability = min(probability, 95.0)
        
        # Determine risk level
        if probability >= 50:
            risk_level = RiskSeverity.HIGH
        elif probability >= 30:
            risk_level = RiskSeverity.MEDIUM
        else:
            risk_level = RiskSeverity.LOW
        
        # Generate mitigation tips
        mitigation_tips = [
            "Provide detailed and accurate product documentation",
            "Use specific product descriptions (avoid vague terms)",
            "Include test certificates and quality reports",
            "Ensure all documents are consistent and error-free",
            "Declare correct HS code and product classification"
        ]
        
        if red_flag_keywords:
            mitigation_tips.append(
                "Avoid using red flag keywords; use technical/scientific names instead"
            )
        
        if is_high_risk_product:
            mitigation_tips.append(
                "Obtain pre-clearance certifications (FDA, FSSAI, etc.) before shipping"
            )
            mitigation_tips.append(
                "Work with experienced customs broker familiar with your product category"
            )
        
        return RMSProbability(
            probability_percentage=probability,
            risk_level=risk_level,
            risk_factors=risk_factors,
            red_flag_keywords=red_flag_keywords,
            mitigation_tips=mitigation_tips
        )
    
    def predict_route_delays(
        self,
        destination: str,
        season: Optional[str] = None
    ) -> RouteAnalysis:
        """
        Predict route delays based on geopolitical factors and seasonal conditions.
        
        Args:
            destination: Destination country
            season: Optional season (defaults to current)
            
        Returns:
            RouteAnalysis with available routes and recommendations
        """
        # Determine region
        region = self.country_to_region.get(destination, "Asia")
        
        # Define available routes based on destination
        routes: List[Route] = []
        
        if region in ["Europe", "North America"]:
            # Route 1: Via Suez Canal (traditional route)
            suez_risk = self.geopolitical_risks.get("Suez Canal", {})
            routes.append(Route(
                name=f"Mumbai to {destination} via Suez Canal",
                transit_time_days=25 + suez_risk.get("delay_days", 0),
                delay_risk=suez_risk.get("risk_level", RiskSeverity.MEDIUM),
                geopolitical_factors=suez_risk.get("factors", []),
                cost_estimate=self._estimate_route_cost(region, "suez")
            ))
            
            # Route 2: Via Cape of Good Hope (alternative route)
            routes.append(Route(
                name=f"Mumbai to {destination} via Cape of Good Hope",
                transit_time_days=35,
                delay_risk=RiskSeverity.LOW,
                geopolitical_factors=["Longer route but avoids Red Sea tensions"],
                cost_estimate=self._estimate_route_cost(region, "cape")
            ))
            
            # Check for Red Sea risks
            red_sea_risk = self.geopolitical_risks.get("Red Sea", {})
            if red_sea_risk.get("risk_level") == RiskSeverity.HIGH:
                # Recommend Cape route if Red Sea is high risk
                recommended_route = f"Mumbai to {destination} via Cape of Good Hope"
            else:
                # Recommend Suez route (faster)
                recommended_route = f"Mumbai to {destination} via Suez Canal"
        
        elif region == "Asia":
            # Direct route for Asian destinations
            routes.append(Route(
                name=f"Mumbai to {destination} (Direct)",
                transit_time_days=10,
                delay_risk=RiskSeverity.LOW,
                geopolitical_factors=[],
                cost_estimate=self._estimate_route_cost(region, "direct")
            ))
            recommended_route = f"Mumbai to {destination} (Direct)"
        
        elif region == "Middle East":
            # Direct route through Arabian Sea
            routes.append(Route(
                name=f"Mumbai to {destination} via Arabian Sea",
                transit_time_days=7,
                delay_risk=RiskSeverity.LOW,
                geopolitical_factors=[],
                cost_estimate=self._estimate_route_cost(region, "direct")
            ))
            recommended_route = f"Mumbai to {destination} via Arabian Sea"
        
        elif region == "Africa":
            # Route via East Africa
            routes.append(Route(
                name=f"Mumbai to {destination} via East Africa",
                transit_time_days=15,
                delay_risk=RiskSeverity.MEDIUM,
                geopolitical_factors=["Port congestion in some African ports"],
                cost_estimate=self._estimate_route_cost(region, "direct")
            ))
            recommended_route = f"Mumbai to {destination} via East Africa"
        
        elif region == "South America":
            # Route via Cape of Good Hope
            routes.append(Route(
                name=f"Mumbai to {destination} via Cape of Good Hope",
                transit_time_days=40,
                delay_risk=RiskSeverity.MEDIUM,
                geopolitical_factors=["Long transit time", "Weather delays possible"],
                cost_estimate=self._estimate_route_cost(region, "cape")
            ))
            recommended_route = f"Mumbai to {destination} via Cape of Good Hope"
        
        elif region == "Oceania":
            # Direct route through Southeast Asia
            routes.append(Route(
                name=f"Mumbai to {destination} via Southeast Asia",
                transit_time_days=20,
                delay_risk=RiskSeverity.LOW,
                geopolitical_factors=[],
                cost_estimate=self._estimate_route_cost(region, "direct")
            ))
            recommended_route = f"Mumbai to {destination} via Southeast Asia"
        
        else:
            # Default route
            routes.append(Route(
                name=f"Mumbai to {destination}",
                transit_time_days=25,
                delay_risk=RiskSeverity.MEDIUM,
                geopolitical_factors=[],
                cost_estimate=self._estimate_route_cost("Asia", "direct")
            ))
            recommended_route = f"Mumbai to {destination}"
        
        return RouteAnalysis(
            recommended_route=recommended_route,
            routes=routes
        )
    
    def estimate_freight_cost(
        self,
        destination: str,
        volume: float,
        weight: float
    ) -> FreightEstimate:
        """
        Estimate freight costs for different shipping modes.
        
        Args:
            destination: Destination country
            volume: Shipment volume in cubic meters (CBM)
            weight: Shipment weight in kilograms
            
        Returns:
            FreightEstimate with sea and air freight costs
        """
        # Determine region
        region = self.country_to_region.get(destination, "Asia")
        
        # Get base rates
        sea_rate_per_cbm = self.base_freight_rates["sea"].get(region, 80)
        air_rate_per_kg = self.base_freight_rates["air"].get(region, 5.0)
        
        # Calculate sea freight (based on volume)
        sea_freight = volume * sea_rate_per_cbm
        
        # Calculate air freight (based on weight or volumetric weight, whichever is higher)
        # Volumetric weight = volume (CBM) * 167 (conversion factor for air freight)
        volumetric_weight = volume * 167
        chargeable_weight = max(weight, volumetric_weight)
        air_freight = chargeable_weight * air_rate_per_kg
        
        # Determine recommended mode
        # Generally, sea freight is recommended unless:
        # 1. Air freight is less than 3x sea freight (very light cargo)
        # 2. Urgent delivery required (not considered here)
        if air_freight < sea_freight * 3:
            recommended_mode = FreightMode.AIR
        else:
            recommended_mode = FreightMode.SEA
        
        return FreightEstimate(
            sea_freight=sea_freight,
            air_freight=air_freight,
            recommended_mode=recommended_mode,
            currency="USD"
        )
    
    def recommend_insurance(
        self,
        shipment_value: float,
        risk_level: RiskSeverity
    ) -> InsuranceRecommendation:
        """
        Recommend insurance coverage based on shipment value and risk level.
        
        Args:
            shipment_value: Total shipment value
            risk_level: Risk level assessment
            
        Returns:
            InsuranceRecommendation with coverage and premium
        """
        # Recommended coverage: 110% of shipment value (standard practice)
        recommended_coverage = shipment_value * 1.10
        
        # Premium calculation based on risk level
        # Low risk: 0.3% of coverage
        # Medium risk: 0.5% of coverage
        # High risk: 0.8% of coverage
        premium_rates = {
            RiskSeverity.LOW: 0.003,
            RiskSeverity.MEDIUM: 0.005,
            RiskSeverity.HIGH: 0.008
        }
        
        premium_rate = premium_rates.get(risk_level, 0.005)
        premium_estimate = recommended_coverage * premium_rate
        
        # Determine coverage type based on risk level
        if risk_level == RiskSeverity.HIGH:
            coverage_type = "All-risk marine cargo insurance with extended coverage"
        elif risk_level == RiskSeverity.MEDIUM:
            coverage_type = "All-risk marine cargo insurance"
        else:
            coverage_type = "Institute Cargo Clauses (A) - All risks"
        
        return InsuranceRecommendation(
            recommended_coverage=recommended_coverage,
            premium_estimate=premium_estimate,
            coverage_type=coverage_type
        )
    
    def detect_red_flag_keywords(self, description: str) -> List[str]:
        """
        Detect red flag keywords in product description that may trigger RMS checks.
        
        Args:
            description: Product description text
            
        Returns:
            List of detected red flag keywords
        """
        description_lower = description.lower()
        detected_keywords = []
        
        for keyword in self.rms_red_flag_keywords:
            if keyword in description_lower:
                detected_keywords.append(keyword)
        
        return detected_keywords
    
    def _estimate_route_cost(self, region: str, route_type: str) -> float:
        """
        Estimate route cost based on region and route type.
        
        Args:
            region: Destination region
            route_type: Type of route (suez, cape, direct)
            
        Returns:
            Estimated cost in USD
        """
        base_cost = self.base_freight_rates["sea"].get(region, 80) * 20  # 20 CBM container
        
        # Adjust based on route type
        if route_type == "cape":
            # Cape route is longer, costs more
            return base_cost * 1.3
        elif route_type == "suez":
            # Suez route is standard
            return base_cost
        else:  # direct
            # Direct routes may be cheaper
            return base_cost * 0.9
