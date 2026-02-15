"""
RoDTEP Calculator Service for ExportSathi.

This service calculates RoDTEP (Remission of Duties and Taxes on Exported Products)
benefits for exporters based on HS codes and destination countries.

RoDTEP is a government scheme that reimburses exporters for embedded taxes
(central, state, and local) that are not refunded through other mechanisms.
"""
from typing import Dict, Optional
import logging

from models.finance import RoDTEPBenefit

logger = logging.getLogger(__name__)


class RoDTEPCalculator:
    """
    Calculator for RoDTEP (Remission of Duties and Taxes on Exported Products) benefits.
    
    This service loads RoDTEP schedules from the knowledge base and calculates
    benefit amounts based on HS codes and destination countries.
    """
    
    def __init__(self):
        """
        Initialize the RoDTEP Calculator.
        
        In production, this would load official RoDTEP schedules from:
        - DGFT RoDTEP schedule notifications
        - Knowledge base documents
        - Database with regularly updated rates
        """
        # RoDTEP rates database (simplified - in production, load from official schedules)
        # Rates are in percentage of FOB value
        # Store both with and without dots for flexible matching
        self.rodtep_rates: Dict[str, float] = {
            # Agricultural products
            "091030": 2.5,       # Turmeric
            "091020": 2.3,       # Saffron
            "091091": 2.4,       # Curry powder
            "0910": 2.3,         # Spices (general)
            
            # Textiles and garments
            "6109": 4.3,         # T-shirts, cotton
            "6110": 4.1,         # Sweaters, pullovers
            "6203": 4.2,         # Men's suits, trousers
            "6204": 4.2,         # Women's suits, dresses
            "61": 4.0,           # Knitted garments (general)
            "62": 3.9,           # Woven garments (general)
            
            # Electronics and LED lights
            "9405": 3.8,         # LED lights and lamps
            "8541": 3.5,         # LED diodes
            "8539": 3.6,         # Electric lamps
            "94": 3.5,           # Furniture and lighting (general)
            
            # Beauty and cosmetics
            "3304": 2.1,         # Beauty/makeup products
            "3305": 2.0,         # Hair care products
            "3307": 1.9,         # Perfumes and toiletries
            "33": 2.0,           # Cosmetics (general)
            
            # Leather products
            "4202": 3.2,         # Leather bags and cases
            "6403": 3.4,         # Leather footwear
            "42": 3.1,           # Leather goods (general)
            
            # Toys and games
            "9503": 2.8,         # Toys
            "95": 2.7,           # Toys and sports goods (general)
            
            # Chemicals
            "2933": 1.8,         # Organic chemicals
            "3004": 1.7,         # Pharmaceutical products
            "29": 1.6,           # Chemicals (general)
            
            # Engineering goods
            "8481": 3.0,         # Taps, valves, fittings
            "7326": 2.9,         # Iron/steel articles
            "84": 2.8,           # Machinery (general)
            
            # Default rate for products not in schedule
            "default": 1.5
        }
        
        logger.info(f"RoDTEP Calculator initialized with {len(self.rodtep_rates)} rate entries")
    
    def get_rodtep_rate(self, hs_code: str) -> float:
        """
        Get RoDTEP rate percentage for a given HS code.
        
        Uses hierarchical matching:
        1. Exact HS code match (e.g., "091030")
        2. 4-digit prefix match (e.g., "0910")
        3. 2-digit chapter match (e.g., "09")
        4. Default rate
        
        Args:
            hs_code: Harmonized System code (with or without dots)
            
        Returns:
            RoDTEP rate as percentage of FOB value
        """
        # Clean HS code: remove dots, spaces, and convert to uppercase
        clean_code = hs_code.replace(".", "").replace(" ", "").upper()
        
        # Try exact match first (with cleaned code)
        if clean_code in self.rodtep_rates:
            rate = self.rodtep_rates[clean_code]
            logger.debug(f"Exact match for HS code {hs_code}: {rate}%")
            return rate
        
        # Try 4-digit prefix match
        if len(clean_code) >= 4:
            prefix_4 = clean_code[:4]
            if prefix_4 in self.rodtep_rates:
                rate = self.rodtep_rates[prefix_4]
                logger.debug(f"4-digit prefix match for HS code {hs_code} ({prefix_4}): {rate}%")
                return rate
        
        # Try 2-digit chapter match
        if len(clean_code) >= 2:
            chapter = clean_code[:2]
            if chapter in self.rodtep_rates:
                rate = self.rodtep_rates[chapter]
                logger.debug(f"2-digit chapter match for HS code {hs_code} ({chapter}): {rate}%")
                return rate
        
        # Use default rate
        rate = self.rodtep_rates["default"]
        logger.debug(f"Using default rate for HS code {hs_code}: {rate}%")
        return rate
    
    def calculate_benefit(
        self,
        hs_code: str,
        destination: str,
        fob_value: float
    ) -> RoDTEPBenefit:
        """
        Calculate RoDTEP benefit amount.
        
        The benefit is calculated as:
        RoDTEP Amount = FOB Value × (RoDTEP Rate / 100)
        
        Args:
            hs_code: Harmonized System code
            destination: Destination country (for future country-specific rates)
            fob_value: FOB (Free on Board) value in INR
            
        Returns:
            RoDTEPBenefit with HS code, rate percentage, and estimated amount
            
        Raises:
            ValueError: If FOB value is negative or zero
        """
        # Validate inputs
        if fob_value <= 0:
            raise ValueError(f"FOB value must be positive, got: {fob_value}")
        
        if not hs_code or not hs_code.strip():
            raise ValueError("HS code cannot be empty")
        
        # Get RoDTEP rate for HS code
        rate_percentage = self.get_rodtep_rate(hs_code)
        
        # Calculate benefit amount
        estimated_amount = fob_value * (rate_percentage / 100)
        
        logger.info(
            f"RoDTEP calculated for HS {hs_code} to {destination}: "
            f"{rate_percentage}% of ₹{fob_value:,.2f} = ₹{estimated_amount:,.2f}"
        )
        
        return RoDTEPBenefit(
            hs_code=hs_code,
            rate_percentage=rate_percentage,
            estimated_amount=estimated_amount,
            currency="INR"
        )
    
    def load_rodtep_schedules(self, schedules_data: Dict[str, float]) -> None:
        """
        Load RoDTEP schedules from external source.
        
        This method allows updating the RoDTEP rates from:
        - Knowledge base documents
        - Database
        - DGFT notifications
        
        Args:
            schedules_data: Dictionary mapping HS codes to rate percentages
        """
        if not schedules_data:
            logger.warning("Empty schedules data provided")
            return
        
        # Update rates
        self.rodtep_rates.update(schedules_data)
        logger.info(f"Loaded {len(schedules_data)} RoDTEP rate entries")
    
    def get_all_rates(self) -> Dict[str, float]:
        """
        Get all RoDTEP rates.
        
        Returns:
            Dictionary mapping HS codes to rate percentages
        """
        return self.rodtep_rates.copy()
