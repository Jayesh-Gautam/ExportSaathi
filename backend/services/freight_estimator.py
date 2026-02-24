"""
Freight Estimator Service for ExportSathi.

This module provides freight cost estimation for different shipping modes:
- Sea freight (based on volume)
- Air freight (based on weight or volumetric weight)
- Route-specific cost adjustments
- Shipping mode recommendations based on urgency and cost
"""
from typing import Dict, Optional
from models.logistics import FreightEstimate
from models.enums import FreightMode


class FreightEstimator:
    """
    Freight Estimator for calculating shipping costs.
    
    This service helps exporters understand freight costs for different
    shipping modes and routes, enabling informed decisions about:
    - Sea freight vs air freight
    - Cost optimization
    - Shipping mode selection based on urgency and budget
    """
    
    def __init__(self):
        """Initialize the Freight Estimator with base rates and mappings."""
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
        
        # Country to region mapping for freight calculation
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
            "Belgium": "Europe",
            "Poland": "Europe",
            "China": "Asia",
            "Japan": "Asia",
            "South Korea": "Asia",
            "Singapore": "Asia",
            "Thailand": "Asia",
            "Vietnam": "Asia",
            "Malaysia": "Asia",
            "Indonesia": "Asia",
            "UAE": "Middle East",
            "Saudi Arabia": "Middle East",
            "Qatar": "Middle East",
            "Oman": "Middle East",
            "Kuwait": "Middle East",
            "South Africa": "Africa",
            "Kenya": "Africa",
            "Nigeria": "Africa",
            "Egypt": "Africa",
            "Morocco": "Africa",
            "Brazil": "South America",
            "Argentina": "South America",
            "Chile": "South America",
            "Colombia": "South America",
            "Peru": "South America",
            "Australia": "Oceania",
            "New Zealand": "Oceania"
        }
        
        # Volumetric weight conversion factor for air freight
        # Standard: 1 CBM = 167 kg for air freight
        self.volumetric_weight_factor = 167
        
        # Cost multiplier threshold for recommending air freight
        # If air freight < sea freight * threshold, recommend air
        self.air_recommendation_threshold = 3.0
    
    def estimate_cost(
        self,
        destination: str,
        volume: float,
        weight: float,
        route: Optional[str] = None,
        urgency: Optional[str] = None
    ) -> FreightEstimate:
        """
        Estimate freight costs for different shipping modes.
        
        This method calculates both sea and air freight costs and recommends
        the most appropriate shipping mode based on cost, urgency, and route.
        
        Args:
            destination: Destination country name
            volume: Shipment volume in cubic meters (CBM)
            weight: Shipment weight in kilograms
            route: Optional specific route (e.g., "via Suez Canal")
            urgency: Optional urgency level ("high", "medium", "low")
            
        Returns:
            FreightEstimate with sea freight, air freight, and recommendation
            
        Example:
            >>> estimator = FreightEstimator()
            >>> estimate = estimator.estimate_cost(
            ...     destination="United States",
            ...     volume=5.0,
            ...     weight=800.0
            ... )
            >>> print(f"Sea: ${estimate.sea_freight}, Air: ${estimate.air_freight}")
        """
        # Determine region from destination country
        region = self._get_region(destination)
        
        # Get base rates for the region
        sea_rate_per_cbm = self.base_freight_rates["sea"].get(region, 80)
        air_rate_per_kg = self.base_freight_rates["air"].get(region, 5.0)
        
        # Apply route-specific adjustments if provided
        if route:
            sea_rate_per_cbm = self._apply_route_adjustment(
                sea_rate_per_cbm, route
            )
        
        # Calculate sea freight (based on volume)
        sea_freight = volume * sea_rate_per_cbm
        
        # Calculate air freight (based on chargeable weight)
        # Chargeable weight is the greater of actual weight or volumetric weight
        volumetric_weight = volume * self.volumetric_weight_factor
        chargeable_weight = max(weight, volumetric_weight)
        air_freight = chargeable_weight * air_rate_per_kg
        
        # Determine recommended shipping mode
        recommended_mode = self._recommend_shipping_mode(
            sea_freight=sea_freight,
            air_freight=air_freight,
            urgency=urgency
        )
        
        return FreightEstimate(
            sea_freight=round(sea_freight, 2),
            air_freight=round(air_freight, 2),
            recommended_mode=recommended_mode,
            currency="USD"
        )
    
    def _get_region(self, destination: str) -> str:
        """
        Get the region for a destination country.
        
        Args:
            destination: Destination country name
            
        Returns:
            Region name (defaults to "Asia" if country not found)
        """
        return self.country_to_region.get(destination, "Asia")
    
    def _apply_route_adjustment(
        self,
        base_rate: float,
        route: str
    ) -> float:
        """
        Apply route-specific cost adjustments.
        
        Different routes have different costs due to distance, canal fees,
        and geopolitical factors.
        
        Args:
            base_rate: Base freight rate per CBM
            route: Route description
            
        Returns:
            Adjusted freight rate
        """
        route_lower = route.lower()
        
        # Cape of Good Hope route is longer and more expensive
        if "cape" in route_lower or "good hope" in route_lower:
            return base_rate * 1.3
        
        # Suez Canal route has canal fees
        elif "suez" in route_lower:
            return base_rate * 1.1
        
        # Red Sea route may have higher insurance costs
        elif "red sea" in route_lower:
            return base_rate * 1.15
        
        # Direct routes are typically cheaper
        elif "direct" in route_lower:
            return base_rate * 0.95
        
        # Default: no adjustment
        return base_rate
    
    def _recommend_shipping_mode(
        self,
        sea_freight: float,
        air_freight: float,
        urgency: Optional[str] = None
    ) -> FreightMode:
        """
        Recommend shipping mode based on cost and urgency.
        
        Recommendation logic:
        1. If urgency is "high", recommend air freight
        2. If air freight < sea freight * threshold, recommend air
        3. Otherwise, recommend sea freight (most cost-effective)
        
        Args:
            sea_freight: Calculated sea freight cost
            air_freight: Calculated air freight cost
            urgency: Optional urgency level ("high", "medium", "low")
            
        Returns:
            Recommended FreightMode (SEA or AIR)
        """
        # High urgency: always recommend air freight
        if urgency and urgency.lower() == "high":
            return FreightMode.AIR
        
        # Cost-based recommendation
        # If air freight is less than 3x sea freight, it may be worth considering
        # for faster delivery (especially for light, high-value goods)
        if air_freight < sea_freight * self.air_recommendation_threshold:
            return FreightMode.AIR
        
        # Default: sea freight is most cost-effective
        return FreightMode.SEA
    
    def calculate_cost_per_unit(
        self,
        total_cost: float,
        units: int
    ) -> float:
        """
        Calculate freight cost per unit.
        
        Useful for understanding the freight cost impact on product pricing.
        
        Args:
            total_cost: Total freight cost
            units: Number of units being shipped
            
        Returns:
            Cost per unit
        """
        if units <= 0:
            return 0.0
        return round(total_cost / units, 2)
    
    def estimate_delivery_time(
        self,
        destination: str,
        mode: FreightMode
    ) -> int:
        """
        Estimate delivery time in days.
        
        Args:
            destination: Destination country
            mode: Shipping mode (SEA or AIR)
            
        Returns:
            Estimated delivery time in days
        """
        region = self._get_region(destination)
        
        # Typical delivery times by region and mode
        delivery_times = {
            "sea": {
                "Asia": 10,
                "Middle East": 7,
                "Europe": 25,
                "North America": 30,
                "Africa": 15,
                "South America": 40,
                "Oceania": 20
            },
            "air": {
                "Asia": 3,
                "Middle East": 2,
                "Europe": 5,
                "North America": 6,
                "Africa": 4,
                "South America": 7,
                "Oceania": 5
            }
        }
        
        mode_key = "sea" if mode == FreightMode.SEA else "air"
        return delivery_times[mode_key].get(region, 15)
