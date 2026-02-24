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
from services.rms_predictor import RMSPredictor
from services.freight_estimator import FreightEstimator


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
        # Initialize RMS Predictor
        self.rms_predictor = RMSPredictor()
        
        # Initialize Freight Estimator
        self.freight_estimator = FreightEstimator()
        
        # FCL container capacity in cubic meters
        self.fcl_capacity_cbm = 33.0  # Standard 20ft container
        
        # Product type risk factors (used for LCL/FCL comparison)
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
        description: str,
        export_history: Optional[dict] = None
    ) -> RMSProbability:
        """
        Estimate RMS (Risk Management System) check probability.
        
        RMS is the customs screening system that flags shipments for physical inspection.
        This method delegates to the RMSPredictor service for detailed analysis.
        
        Args:
            product_type: Type of product
            hs_code: Harmonized System code
            description: Product description
            export_history: Optional export history data
            
        Returns:
            RMSProbability with percentage, risk factors, and mitigation tips
        """
        # Delegate to RMSPredictor service
        return self.rms_predictor.predict_probability(
            product_type=product_type,
            hs_code=hs_code,
            description=description,
            export_history=export_history
        )
    
    def predict_route_delays(
        self,
        destination: str,
        season: Optional[str] = None
    ) -> RouteAnalysis:
        """
        Predict route delays based on geopolitical factors and seasonal conditions.
        
        This method analyzes available shipping routes to the destination country,
        considering:
        - Geopolitical situations (e.g., Red Sea disruptions, Suez Canal congestion)
        - Seasonal factors (monsoon season, winter storms, peak shipping periods)
        - Transit times for each route
        - Cost estimates for different routes
        
        Args:
            destination: Destination country
            season: Optional season (winter, spring, summer, fall/monsoon)
                    If not provided, no seasonal adjustments are applied
            
        Returns:
            RouteAnalysis with available routes and recommendations
        """
        # Determine region using FreightEstimator's mapping
        region = self.freight_estimator._get_region(destination)
        
        # Determine seasonal delay factors
        seasonal_delay = self._get_seasonal_delay(region, season) if season else 0
        seasonal_factors = self._get_seasonal_factors(region, season) if season else []
        
        # Define available routes based on destination
        routes: List[Route] = []
        
        if region in ["Europe", "North America"]:
            # Route 1: Via Suez Canal (traditional route)
            suez_risk = self.geopolitical_risks.get("Suez Canal", {})
            suez_factors = suez_risk.get("factors", []).copy()
            suez_factors.extend(seasonal_factors)
            
            routes.append(Route(
                name=f"Mumbai to {destination} via Suez Canal",
                transit_time_days=25 + suez_risk.get("delay_days", 0) + seasonal_delay,
                delay_risk=suez_risk.get("risk_level", RiskSeverity.MEDIUM),
                geopolitical_factors=suez_factors,
                cost_estimate=self._estimate_route_cost(region, "suez")
            ))
            
            # Route 2: Via Cape of Good Hope (alternative route)
            cape_factors = ["Longer route but avoids Red Sea tensions"]
            cape_factors.extend(seasonal_factors)
            
            routes.append(Route(
                name=f"Mumbai to {destination} via Cape of Good Hope",
                transit_time_days=35 + seasonal_delay,
                delay_risk=RiskSeverity.LOW,
                geopolitical_factors=cape_factors,
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
            asia_factors = seasonal_factors.copy() if seasonal_factors else []
            
            routes.append(Route(
                name=f"Mumbai to {destination} (Direct)",
                transit_time_days=10 + seasonal_delay,
                delay_risk=RiskSeverity.LOW,
                geopolitical_factors=asia_factors,
                cost_estimate=self._estimate_route_cost(region, "direct")
            ))
            recommended_route = f"Mumbai to {destination} (Direct)"
        
        elif region == "Middle East":
            # Direct route through Arabian Sea
            middle_east_factors = seasonal_factors.copy() if seasonal_factors else []
            
            routes.append(Route(
                name=f"Mumbai to {destination} via Arabian Sea",
                transit_time_days=7 + seasonal_delay,
                delay_risk=RiskSeverity.LOW,
                geopolitical_factors=middle_east_factors,
                cost_estimate=self._estimate_route_cost(region, "direct")
            ))
            recommended_route = f"Mumbai to {destination} via Arabian Sea"
        
        elif region == "Africa":
            # Route via East Africa
            africa_factors = ["Port congestion in some African ports"]
            africa_factors.extend(seasonal_factors)
            
            routes.append(Route(
                name=f"Mumbai to {destination} via East Africa",
                transit_time_days=15 + seasonal_delay,
                delay_risk=RiskSeverity.MEDIUM,
                geopolitical_factors=africa_factors,
                cost_estimate=self._estimate_route_cost(region, "direct")
            ))
            recommended_route = f"Mumbai to {destination} via East Africa"
        
        elif region == "South America":
            # Route via Cape of Good Hope
            sa_factors = ["Long transit time", "Weather delays possible"]
            sa_factors.extend(seasonal_factors)
            
            routes.append(Route(
                name=f"Mumbai to {destination} via Cape of Good Hope",
                transit_time_days=40 + seasonal_delay,
                delay_risk=RiskSeverity.MEDIUM,
                geopolitical_factors=sa_factors,
                cost_estimate=self._estimate_route_cost(region, "cape")
            ))
            recommended_route = f"Mumbai to {destination} via Cape of Good Hope"
        
        elif region == "Oceania":
            # Direct route through Southeast Asia
            oceania_factors = seasonal_factors.copy() if seasonal_factors else []
            
            routes.append(Route(
                name=f"Mumbai to {destination} via Southeast Asia",
                transit_time_days=20 + seasonal_delay,
                delay_risk=RiskSeverity.LOW,
                geopolitical_factors=oceania_factors,
                cost_estimate=self._estimate_route_cost(region, "direct")
            ))
            recommended_route = f"Mumbai to {destination} via Southeast Asia"
        
        else:
            # Default route
            default_factors = seasonal_factors.copy() if seasonal_factors else []
            
            routes.append(Route(
                name=f"Mumbai to {destination}",
                transit_time_days=25 + seasonal_delay,
                delay_risk=RiskSeverity.MEDIUM,
                geopolitical_factors=default_factors,
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
        weight: float,
        route: Optional[str] = None,
        urgency: Optional[str] = None
    ) -> FreightEstimate:
        """
        Estimate freight costs for different shipping modes.
        
        This method delegates to the FreightEstimator service for detailed
        cost calculations and shipping mode recommendations.
        
        Args:
            destination: Destination country
            volume: Shipment volume in cubic meters (CBM)
            weight: Shipment weight in kilograms
            route: Optional specific route for cost adjustments
            urgency: Optional urgency level for mode recommendation
            
        Returns:
            FreightEstimate with sea and air freight costs
        """
        # Delegate to FreightEstimator service
        return self.freight_estimator.estimate_cost(
            destination=destination,
            volume=volume,
            weight=weight,
            route=route,
            urgency=urgency
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
        
        This method delegates to the RMSPredictor service.
        
        Args:
            description: Product description text
            
        Returns:
            List of detected red flag keywords
        """
        # Delegate to RMSPredictor service
        return self.rms_predictor._detect_red_flag_keywords(description)
    
    
    def _get_seasonal_delay(self, region: str, season: Optional[str]) -> int:
        """
        Calculate seasonal delay in days based on region and season.
        
        Args:
            region: Destination region
            season: Season (winter, spring, summer, fall/monsoon)
            
        Returns:
            Additional delay days due to seasonal factors
        """
        if not season:
            return 0
        
        season_lower = season.lower()
        
        # Monsoon season (June-September) affects Indian Ocean routes
        if season_lower in ["monsoon", "fall"]:
            if region in ["Asia", "Middle East", "Africa"]:
                return 3  # Monsoon affects routes from India
            elif region in ["Europe", "North America"]:
                return 2  # Indirect effect on longer routes
        
        # Winter storms (December-February) affect North Atlantic and North Pacific
        elif season_lower == "winter":
            if region in ["North America", "Europe"]:
                return 4  # Winter storms can cause significant delays
            elif region == "Oceania":
                return 2  # Southern hemisphere summer, but some weather effects
        
        # Peak shipping season (September-November) causes port congestion
        elif season_lower in ["fall", "autumn"]:
            # Peak season affects all routes due to increased volume
            return 2
        
        # Spring and summer are generally favorable
        elif season_lower in ["spring", "summer"]:
            return 0
        
        return 0
    
    def _get_seasonal_factors(self, region: str, season: Optional[str]) -> List[str]:
        """
        Get seasonal factors affecting shipping routes.
        
        Args:
            region: Destination region
            season: Season (winter, spring, summer, fall/monsoon)
            
        Returns:
            List of seasonal factors to consider
        """
        if not season:
            return []
        
        factors = []
        season_lower = season.lower()
        
        # Monsoon season (June-September)
        if season_lower in ["monsoon", "fall"]:
            if region in ["Asia", "Middle East", "Africa"]:
                factors.append("Monsoon season may cause delays in Indian Ocean routes")
                factors.append("Increased port congestion during monsoon")
            elif region in ["Europe", "North America"]:
                factors.append("Monsoon season may affect departure schedules from India")
        
        # Winter storms (December-February)
        elif season_lower == "winter":
            if region in ["North America", "Europe"]:
                factors.append("Winter storms in North Atlantic can cause delays")
                factors.append("Ice conditions may affect northern ports")
            elif region == "Oceania":
                factors.append("Cyclone season in Pacific (December-April)")
        
        # Peak shipping season (September-November)
        elif season_lower in ["fall", "autumn"]:
            factors.append("Peak shipping season - expect port congestion")
            factors.append("Longer wait times for vessel space")
            factors.append("Holiday season rush may affect schedules")
        
        # Spring (March-May)
        elif season_lower == "spring":
            factors.append("Favorable weather conditions for shipping")
            if region in ["Asia", "Middle East"]:
                factors.append("Pre-monsoon period - optimal shipping window")
        
        # Summer (June-August)
        elif season_lower == "summer":
            if region in ["Europe", "North America"]:
                factors.append("Peak vacation season may affect port operations")
            else:
                factors.append("Generally favorable shipping conditions")
        
        return factors
    
    def _estimate_route_cost(self, region: str, route_type: str) -> float:
        """
        Estimate route cost based on region and route type.
        
        Args:
            region: Destination region
            route_type: Type of route (suez, cape, direct)
            
        Returns:
            Estimated cost in USD
        """
        # Use FreightEstimator's base rates
        base_cost = self.freight_estimator.base_freight_rates["sea"].get(region, 80) * 20  # 20 CBM container
        
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
