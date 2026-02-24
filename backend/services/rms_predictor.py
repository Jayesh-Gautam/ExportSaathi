"""
RMS Predictor Service for ExportSathi.

This module provides RMS (Risk Management System) probability prediction
to help exporters understand the likelihood of customs inspection.

RMS is the customs screening system that flags shipments for physical inspection
based on various risk factors including product type, HS code, description,
and historical data.
"""
from typing import List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.logistics import RMSProbability
from models.enums import RiskSeverity


class RMSPredictor:
    """
    RMS Predictor for estimating customs inspection probability.
    
    This service analyzes product information to predict the likelihood
    of RMS (Risk Management System) checks and provides mitigation strategies.
    """
    
    def __init__(self, knowledge_base=None):
        """
        Initialize the RMS Predictor.
        
        Args:
            knowledge_base: Optional knowledge base for retrieving customs RMS rules
        """
        self.knowledge_base = knowledge_base
        
        # RMS red flag keywords database
        # These keywords in product descriptions may trigger customs scrutiny
        self.rms_red_flag_keywords = [
            # Chemical and hazardous materials
            "chemical", "powder", "liquid", "explosive", "flammable",
            "hazardous", "toxic", "radioactive", "corrosive", "oxidizing",
            
            # Weapons and controlled items
            "weapon", "gun", "ammunition", "knife", "blade",
            
            # Pharmaceuticals and drugs
            "drug", "pharmaceutical", "medicine", "supplement", "tablet",
            "capsule", "injection", "vaccine", "antibiotic",
            
            # Herbal and natural products
            "herbal", "ayurvedic", "organic", "natural", "extract",
            "oil", "essence", "tincture", "botanical",
            
            # Dual-use items
            "dual-use", "military", "strategic", "encryption",
            
            # Food safety concerns
            "raw", "unpasteurized", "fermented", "live culture",
            
            # High-value items
            "gold", "silver", "diamond", "precious", "jewelry",
            
            # Electronics and technology
            "battery", "lithium", "electronic", "semiconductor",
            
            # Agricultural products
            "seed", "plant", "soil", "pesticide", "fertilizer"
        ]
        
        # High-risk product types that attract more scrutiny
        self.high_risk_product_types = [
            "food", "beverage", "cosmetic", "pharmaceutical", "chemical",
            "supplement", "herbal", "ayurvedic", "medical device",
            "electronics", "battery", "agricultural", "textile",
            "jewelry", "precious metal", "dual-use technology"
        ]
        
        # High-risk HS code prefixes (first 2 digits)
        # These categories are subject to more stringent customs checks
        self.high_risk_hs_prefixes = {
            "29": "Organic chemicals",
            "30": "Pharmaceutical products",
            "33": "Essential oils and cosmetics",
            "38": "Miscellaneous chemical products",
            "84": "Nuclear reactors and machinery",
            "85": "Electrical machinery and equipment",
            "90": "Optical, medical instruments",
            "93": "Arms and ammunition"
        }
        
        # Medium-risk HS code prefixes
        self.medium_risk_hs_prefixes = {
            "04": "Dairy products",
            "07": "Edible vegetables",
            "08": "Edible fruits and nuts",
            "09": "Coffee, tea, spices",
            "10": "Cereals",
            "15": "Animal or vegetable fats and oils",
            "16": "Preparations of meat or fish",
            "17": "Sugars and sugar confectionery",
            "18": "Cocoa and cocoa preparations",
            "19": "Preparations of cereals",
            "20": "Preparations of vegetables or fruits",
            "21": "Miscellaneous edible preparations",
            "22": "Beverages and vinegar",
            "61": "Knitted apparel",
            "62": "Woven apparel",
            "63": "Textile articles",
            "71": "Precious stones and metals"
        }
    
    def predict_probability(
        self,
        product_type: str,
        hs_code: str,
        description: str,
        export_history: Optional[dict] = None
    ) -> RMSProbability:
        """
        Predict RMS check probability for a shipment.
        
        This method analyzes multiple risk factors to estimate the likelihood
        of customs inspection and provides actionable mitigation strategies.
        
        Args:
            product_type: Type of product being exported
            hs_code: Harmonized System code
            description: Detailed product description
            export_history: Optional export history data (first-time exporter, past issues, etc.)
            
        Returns:
            RMSProbability with percentage, risk factors, and mitigation tips
        """
        # Base probability: 15% (average RMS check rate in India)
        probability = 15.0
        
        # Risk factors identified
        risk_factors: List[str] = []
        
        # Detected red flag keywords
        red_flag_keywords: List[str] = []
        
        # 1. Check for high-risk product types
        is_high_risk_product = self._is_high_risk_product(product_type)
        if is_high_risk_product:
            probability += 20.0
            risk_factors.append(f"High-risk product category: {product_type}")
        
        # 2. Check for red flag keywords in description
        detected_keywords = self._detect_red_flag_keywords(description)
        if detected_keywords:
            red_flag_keywords = detected_keywords
            # Each keyword adds 5% to probability
            keyword_risk = min(len(detected_keywords) * 5.0, 25.0)  # Cap at 25%
            probability += keyword_risk
            risk_factors.append(
                f"Red flag keywords detected: {', '.join(detected_keywords[:3])}"
                + (f" and {len(detected_keywords) - 3} more" if len(detected_keywords) > 3 else "")
            )
        
        # 3. Check HS code risk level
        hs_risk_level, hs_category = self._assess_hs_code_risk(hs_code)
        if hs_risk_level == "high":
            probability += 15.0
            risk_factors.append(f"High-risk HS code category: {hs_category}")
        elif hs_risk_level == "medium":
            probability += 8.0
            risk_factors.append(f"Medium-risk HS code category: {hs_category}")
        
        # 4. Check export history
        if export_history:
            history_risk = self._assess_export_history(export_history)
            probability += history_risk
            if history_risk > 0:
                if export_history.get("is_first_time_exporter"):
                    risk_factors.append("First-time exporter (higher scrutiny)")
                if export_history.get("past_violations"):
                    risk_factors.append("Past compliance violations on record")
                if export_history.get("high_value_shipment"):
                    risk_factors.append("High-value shipment (>$50,000)")
        
        # 5. Load customs RMS rules from knowledge base if available
        if self.knowledge_base:
            kb_risk_factors = self._retrieve_rms_rules_from_kb(
                product_type, hs_code, description
            )
            if kb_risk_factors:
                probability += kb_risk_factors["additional_probability"]
                risk_factors.extend(kb_risk_factors["factors"])
        
        # Cap probability at 95% (never 100% certain)
        probability = min(probability, 95.0)
        
        # Determine risk level based on probability
        risk_level = self._determine_risk_level(probability)
        
        # Generate mitigation tips
        mitigation_tips = self._generate_mitigation_tips(
            risk_level=risk_level,
            has_red_flags=len(red_flag_keywords) > 0,
            is_high_risk_product=is_high_risk_product,
            is_first_time=export_history.get("is_first_time_exporter", False) if export_history else False
        )
        
        return RMSProbability(
            probability_percentage=round(probability, 1),
            risk_level=risk_level,
            risk_factors=risk_factors,
            red_flag_keywords=red_flag_keywords,
            mitigation_tips=mitigation_tips
        )
    
    def identify_risk_factors(
        self,
        product_type: str,
        description: str
    ) -> List[str]:
        """
        Identify specific risk factors in product information.
        
        Args:
            product_type: Type of product
            description: Product description
            
        Returns:
            List of identified risk factors
        """
        risk_factors = []
        
        # Check product type
        if self._is_high_risk_product(product_type):
            risk_factors.append(f"High-risk product category: {product_type}")
        
        # Check for red flag keywords
        keywords = self._detect_red_flag_keywords(description)
        if keywords:
            risk_factors.append(f"Red flag keywords: {', '.join(keywords)}")
        
        # Check for vague descriptions
        if len(description.split()) < 5:
            risk_factors.append("Vague or insufficient product description")
        
        # Check for multiple product types in one description
        if "and" in description.lower() or "," in description:
            word_count = len([w for w in description.split() if len(w) > 3])
            if word_count > 15:
                risk_factors.append("Complex multi-component product description")
        
        return risk_factors
    
    def _is_high_risk_product(self, product_type: str) -> bool:
        """Check if product type is high-risk."""
        product_type_lower = product_type.lower()
        return any(
            risk_type.lower() in product_type_lower
            for risk_type in self.high_risk_product_types
        )
    
    def _detect_red_flag_keywords(self, description: str) -> List[str]:
        """Detect red flag keywords in product description."""
        description_lower = description.lower()
        detected = []
        
        for keyword in self.rms_red_flag_keywords:
            if keyword in description_lower:
                detected.append(keyword)
        
        return detected
    
    def _assess_hs_code_risk(self, hs_code: str) -> tuple[str, str]:
        """
        Assess risk level based on HS code.
        
        Returns:
            Tuple of (risk_level, category_description)
        """
        if not hs_code or len(hs_code) < 2:
            return ("unknown", "Invalid HS code")
        
        hs_prefix = hs_code[:2]
        
        if hs_prefix in self.high_risk_hs_prefixes:
            return ("high", self.high_risk_hs_prefixes[hs_prefix])
        elif hs_prefix in self.medium_risk_hs_prefixes:
            return ("medium", self.medium_risk_hs_prefixes[hs_prefix])
        else:
            return ("low", "Standard product category")
    
    def _assess_export_history(self, export_history: dict) -> float:
        """
        Assess risk based on export history.
        
        Returns:
            Additional probability percentage to add
        """
        additional_risk = 0.0
        
        # First-time exporter
        if export_history.get("is_first_time_exporter"):
            additional_risk += 10.0
        
        # Past violations
        if export_history.get("past_violations"):
            additional_risk += 15.0
        
        # High-value shipment
        if export_history.get("high_value_shipment"):
            additional_risk += 5.0
        
        # Frequent exporter with clean record (reduces risk)
        if export_history.get("export_count", 0) > 10 and not export_history.get("past_violations"):
            additional_risk -= 5.0
        
        return additional_risk
    
    def _retrieve_rms_rules_from_kb(
        self,
        product_type: str,
        hs_code: str,
        description: str
    ) -> Optional[dict]:
        """
        Retrieve customs RMS rules from knowledge base.
        
        This method queries the knowledge base for specific RMS rules
        related to the product being exported.
        
        Returns:
            Dictionary with additional_probability and factors, or None
        """
        # TODO: Implement knowledge base retrieval when RAG pipeline is integrated
        # For now, return None
        # 
        # Example implementation:
        # query = f"RMS customs rules for {product_type} HS code {hs_code}"
        # documents = self.knowledge_base.retrieve_documents(query, top_k=3)
        # 
        # Parse documents to extract:
        # - Additional risk factors
        # - Specific regulations
        # - Historical inspection rates
        
        return None
    
    def _determine_risk_level(self, probability: float) -> RiskSeverity:
        """Determine risk level based on probability percentage."""
        if probability >= 50:
            return RiskSeverity.HIGH
        elif probability >= 30:
            return RiskSeverity.MEDIUM
        else:
            return RiskSeverity.LOW
    
    def _generate_mitigation_tips(
        self,
        risk_level: RiskSeverity,
        has_red_flags: bool,
        is_high_risk_product: bool,
        is_first_time: bool
    ) -> List[str]:
        """
        Generate actionable mitigation tips based on risk factors.
        
        Args:
            risk_level: Overall risk level
            has_red_flags: Whether red flag keywords were detected
            is_high_risk_product: Whether product is high-risk category
            is_first_time: Whether this is a first-time exporter
            
        Returns:
            List of mitigation tips
        """
        tips = []
        
        # Universal tips (always applicable)
        tips.extend([
            "Provide detailed and accurate product documentation",
            "Ensure all documents are consistent and error-free",
            "Declare correct HS code and product classification",
            "Include complete ingredient/component list with percentages"
        ])
        
        # Red flag keyword tips
        if has_red_flags:
            tips.extend([
                "Use technical/scientific names instead of generic terms",
                "Avoid using red flag keywords; be specific and precise",
                "Provide Material Safety Data Sheets (MSDS) if applicable"
            ])
        
        # High-risk product tips
        if is_high_risk_product:
            tips.extend([
                "Obtain pre-clearance certifications (FDA, FSSAI, BIS, etc.) before shipping",
                "Include test certificates and quality reports from accredited labs",
                "Work with experienced customs broker familiar with your product category",
                "Consider pre-shipment inspection by authorized agencies"
            ])
        
        # First-time exporter tips
        if is_first_time:
            tips.extend([
                "Register with relevant export promotion councils",
                "Attend customs facilitation workshops for first-time exporters",
                "Consider using a customs house agent (CHA) for first few shipments",
                "Start with smaller shipments to build export track record"
            ])
        
        # Risk-level specific tips
        if risk_level == RiskSeverity.HIGH:
            tips.extend([
                "Consider voluntary pre-inspection to identify issues early",
                "Maintain comprehensive documentation trail for audit",
                "Budget extra time for potential customs delays (3-5 days)",
                "Ensure product packaging clearly displays all required information"
            ])
        elif risk_level == RiskSeverity.MEDIUM:
            tips.extend([
                "Double-check all documentation before submission",
                "Keep digital copies of all certificates and permits",
                "Budget buffer time for potential inspection (1-2 days)"
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tips = []
        for tip in tips:
            if tip not in seen:
                seen.add(tip)
                unique_tips.append(tip)
        
        return unique_tips


# Example usage
if __name__ == "__main__":
    # Create predictor instance
    predictor = RMSPredictor()
    
    # Example 1: Low-risk product
    print("Example 1: Low-risk product (Cotton T-shirts)")
    print("-" * 60)
    result1 = predictor.predict_probability(
        product_type="Textile",
        hs_code="6109.10",
        description="100% cotton knitted T-shirts for men, crew neck, short sleeves"
    )
    print(f"Probability: {result1.probability_percentage}%")
    print(f"Risk Level: {result1.risk_level}")
    print(f"Risk Factors: {result1.risk_factors}")
    print(f"Mitigation Tips: {result1.mitigation_tips[:3]}")
    print()
    
    # Example 2: High-risk product
    print("Example 2: High-risk product (Turmeric powder)")
    print("-" * 60)
    result2 = predictor.predict_probability(
        product_type="Food supplement",
        hs_code="0910.30",
        description="Organic turmeric powder, natural herbal supplement for health",
        export_history={"is_first_time_exporter": True}
    )
    print(f"Probability: {result2.probability_percentage}%")
    print(f"Risk Level: {result2.risk_level}")
    print(f"Risk Factors: {result2.risk_factors}")
    print(f"Red Flag Keywords: {result2.red_flag_keywords}")
    print(f"Mitigation Tips: {result2.mitigation_tips[:5]}")
    print()
    
    # Example 3: Very high-risk product
    print("Example 3: Very high-risk product (Pharmaceutical)")
    print("-" * 60)
    result3 = predictor.predict_probability(
        product_type="Pharmaceutical",
        hs_code="3004.90",
        description="Pharmaceutical tablets containing chemical compounds for medical use",
        export_history={
            "is_first_time_exporter": True,
            "high_value_shipment": True
        }
    )
    print(f"Probability: {result3.probability_percentage}%")
    print(f"Risk Level: {result3.risk_level}")
    print(f"Risk Factors: {result3.risk_factors}")
    print(f"Red Flag Keywords: {result3.red_flag_keywords}")
    print(f"Mitigation Tips: {result3.mitigation_tips[:5]}")
