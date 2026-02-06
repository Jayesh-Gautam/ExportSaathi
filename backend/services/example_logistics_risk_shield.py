"""
Example usage of LogisticsRiskShield service.

This script demonstrates how to use the LogisticsRiskShield service
to analyze logistics risks for export shipments.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.logistics_risk_shield import LogisticsRiskShield
from models.logistics import LogisticsRiskRequest
from models.enums import RiskSeverity


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def example_complete_analysis():
    """Example: Complete logistics risk analysis."""
    print_section("Example 1: Complete Logistics Risk Analysis")
    
    service = LogisticsRiskShield()
    
    # Create request for turmeric powder export to USA
    request = LogisticsRiskRequest(
        product_type="Turmeric powder",
        hs_code="0910.30",
        volume=10.0,  # 10 cubic meters
        value=200000.0,  # INR 2 lakh
        destination_country="United States",
        product_description="Organic turmeric powder for food use"
    )
    
    print(f"\nAnalyzing shipment:")
    print(f"  Product: {request.product_type}")
    print(f"  HS Code: {request.hs_code}")
    print(f"  Volume: {request.volume} CBM")
    print(f"  Value: ₹{request.value:,.0f}")
    print(f"  Destination: {request.destination_country}")
    
    # Perform complete analysis
    analysis = service.analyze_risks(request)
    
    # Display results
    print("\n--- LCL vs FCL Comparison ---")
    print(f"Recommendation: {analysis.lcl_fcl_comparison.recommendation}")
    print(f"LCL Cost: ${analysis.lcl_fcl_comparison.lcl.cost:,.2f}")
    print(f"LCL Risk: {analysis.lcl_fcl_comparison.lcl.risk_level}")
    print(f"FCL Cost: ${analysis.lcl_fcl_comparison.fcl.cost:,.2f}")
    print(f"FCL Risk: {analysis.lcl_fcl_comparison.fcl.risk_level}")
    
    print("\n--- RMS Probability ---")
    print(f"Probability: {analysis.rms_probability.probability_percentage:.1f}%")
    print(f"Risk Level: {analysis.rms_probability.risk_level}")
    print(f"Risk Factors: {', '.join(analysis.rms_probability.risk_factors)}")
    if analysis.rms_probability.red_flag_keywords:
        print(f"Red Flag Keywords: {', '.join(analysis.rms_probability.red_flag_keywords)}")
    
    print("\n--- Route Analysis ---")
    print(f"Recommended Route: {analysis.route_analysis.recommended_route}")
    for route in analysis.route_analysis.routes:
        print(f"\n  Route: {route.name}")
        print(f"  Transit Time: {route.transit_time_days} days")
        print(f"  Delay Risk: {route.delay_risk}")
        print(f"  Cost Estimate: ${route.cost_estimate:,.2f}")
        if route.geopolitical_factors:
            print(f"  Geopolitical Factors: {', '.join(route.geopolitical_factors)}")
    
    print("\n--- Freight Estimate ---")
    print(f"Sea Freight: ${analysis.freight_estimate.sea_freight:,.2f}")
    print(f"Air Freight: ${analysis.freight_estimate.air_freight:,.2f}")
    print(f"Recommended Mode: {analysis.freight_estimate.recommended_mode}")
    
    print("\n--- Insurance Recommendation ---")
    print(f"Recommended Coverage: ${analysis.insurance_recommendation.recommended_coverage:,.2f}")
    print(f"Premium Estimate: ${analysis.insurance_recommendation.premium_estimate:,.2f}")
    print(f"Coverage Type: {analysis.insurance_recommendation.coverage_type}")


def example_lcl_vs_fcl():
    """Example: LCL vs FCL comparison."""
    print_section("Example 2: LCL vs FCL Comparison")
    
    service = LogisticsRiskShield()
    
    # Small volume shipment
    print("\nScenario A: Small volume (5 CBM) - Textiles")
    comparison = service.compare_lcl_fcl(volume=5.0, product_type="Textiles")
    print(f"Recommendation: {comparison.recommendation}")
    print(f"LCL Cost: ${comparison.lcl.cost:,.2f}, Risk: {comparison.lcl.risk_level}")
    print(f"FCL Cost: ${comparison.fcl.cost:,.2f}, Risk: {comparison.fcl.risk_level}")
    print(f"LCL Pros: {', '.join(comparison.lcl.pros[:2])}")
    print(f"LCL Cons: {', '.join(comparison.lcl.cons[:2])}")
    
    # Large volume shipment
    print("\nScenario B: Large volume (25 CBM) - Electronics")
    comparison = service.compare_lcl_fcl(volume=25.0, product_type="Electronics")
    print(f"Recommendation: {comparison.recommendation}")
    print(f"LCL Cost: ${comparison.lcl.cost:,.2f}, Risk: {comparison.lcl.risk_level}")
    print(f"FCL Cost: ${comparison.fcl.cost:,.2f}, Risk: {comparison.fcl.risk_level}")
    
    # High-risk product
    print("\nScenario C: Medium volume (15 CBM) - Pharmaceutical")
    comparison = service.compare_lcl_fcl(volume=15.0, product_type="Pharmaceutical")
    print(f"Recommendation: {comparison.recommendation}")
    print(f"LCL Cost: ${comparison.lcl.cost:,.2f}, Risk: {comparison.lcl.risk_level}")
    print(f"FCL Cost: ${comparison.fcl.cost:,.2f}, Risk: {comparison.fcl.risk_level}")
    print("Note: High-risk products recommend FCL at lower volume threshold")


def example_rms_probability():
    """Example: RMS probability estimation."""
    print_section("Example 3: RMS Probability Estimation")
    
    service = LogisticsRiskShield()
    
    # Low-risk product
    print("\nScenario A: Low-risk product (Cotton t-shirts)")
    rms = service.estimate_rms_probability(
        product_type="Textiles",
        hs_code="6109",
        description="Cotton t-shirts for casual wear"
    )
    print(f"RMS Probability: {rms.probability_percentage:.1f}%")
    print(f"Risk Level: {rms.risk_level}")
    print(f"Risk Factors: {rms.risk_factors if rms.risk_factors else 'None'}")
    
    # High-risk product with red flag keywords
    print("\nScenario B: High-risk product (Turmeric powder)")
    rms = service.estimate_rms_probability(
        product_type="Food",
        hs_code="0910.30",
        description="Organic turmeric powder with herbal extracts"
    )
    print(f"RMS Probability: {rms.probability_percentage:.1f}%")
    print(f"Risk Level: {rms.risk_level}")
    print(f"Risk Factors: {', '.join(rms.risk_factors)}")
    print(f"Red Flag Keywords: {', '.join(rms.red_flag_keywords)}")
    print(f"\nMitigation Tips:")
    for tip in rms.mitigation_tips[:3]:
        print(f"  - {tip}")
    
    # Pharmaceutical product
    print("\nScenario C: Pharmaceutical product")
    rms = service.estimate_rms_probability(
        product_type="Pharmaceutical",
        hs_code="3004",
        description="Herbal supplement tablets"
    )
    print(f"RMS Probability: {rms.probability_percentage:.1f}%")
    print(f"Risk Level: {rms.risk_level}")
    print(f"Risk Factors: {', '.join(rms.risk_factors)}")


def example_route_analysis():
    """Example: Route delay prediction."""
    print_section("Example 4: Route Delay Prediction")
    
    service = LogisticsRiskShield()
    
    destinations = ["Germany", "Singapore", "United States", "UAE"]
    
    for destination in destinations:
        print(f"\nDestination: {destination}")
        routes = service.predict_route_delays(destination=destination)
        print(f"Recommended Route: {routes.recommended_route}")
        
        for route in routes.routes:
            print(f"\n  Route: {route.name}")
            print(f"  Transit Time: {route.transit_time_days} days")
            print(f"  Delay Risk: {route.delay_risk}")
            print(f"  Cost: ${route.cost_estimate:,.2f}")
            if route.geopolitical_factors:
                print(f"  Factors: {', '.join(route.geopolitical_factors)}")


def example_freight_estimation():
    """Example: Freight cost estimation."""
    print_section("Example 5: Freight Cost Estimation")
    
    service = LogisticsRiskShield()
    
    # Heavy cargo
    print("\nScenario A: Heavy cargo (10 CBM, 2000 kg)")
    freight = service.estimate_freight_cost(
        destination="United States",
        volume=10.0,
        weight=2000.0
    )
    print(f"Sea Freight: ${freight.sea_freight:,.2f}")
    print(f"Air Freight: ${freight.air_freight:,.2f}")
    print(f"Recommended Mode: {freight.recommended_mode}")
    print(f"Air/Sea Ratio: {freight.air_freight / freight.sea_freight:.1f}x")
    
    # Light but bulky cargo
    print("\nScenario B: Light but bulky cargo (10 CBM, 500 kg)")
    freight = service.estimate_freight_cost(
        destination="Germany",
        volume=10.0,
        weight=500.0
    )
    print(f"Sea Freight: ${freight.sea_freight:,.2f}")
    print(f"Air Freight: ${freight.air_freight:,.2f}")
    print(f"Recommended Mode: {freight.recommended_mode}")
    print(f"Volumetric Weight: {10.0 * 167:.0f} kg (used for air freight)")
    
    # Compare destinations
    print("\nScenario C: Same cargo to different destinations (5 CBM, 1000 kg)")
    destinations = ["Singapore", "Germany", "United States"]
    for dest in destinations:
        freight = service.estimate_freight_cost(
            destination=dest,
            volume=5.0,
            weight=1000.0
        )
        print(f"\n  {dest}:")
        print(f"    Sea: ${freight.sea_freight:,.2f}, Air: ${freight.air_freight:,.2f}")


def example_insurance():
    """Example: Insurance recommendations."""
    print_section("Example 6: Insurance Recommendations")
    
    service = LogisticsRiskShield()
    
    shipment_value = 200000.0
    
    print(f"\nShipment Value: ₹{shipment_value:,.0f}")
    
    for risk_level in [RiskSeverity.LOW, RiskSeverity.MEDIUM, RiskSeverity.HIGH]:
        insurance = service.recommend_insurance(
            shipment_value=shipment_value,
            risk_level=risk_level
        )
        print(f"\n{risk_level.value.upper()} Risk:")
        print(f"  Coverage: ₹{insurance.recommended_coverage:,.2f} (110% of value)")
        print(f"  Premium: ₹{insurance.premium_estimate:,.2f}")
        print(f"  Premium Rate: {(insurance.premium_estimate / insurance.recommended_coverage * 100):.2f}%")
        print(f"  Coverage Type: {insurance.coverage_type}")


def example_red_flag_keywords():
    """Example: Red flag keyword detection."""
    print_section("Example 7: Red Flag Keyword Detection")
    
    service = LogisticsRiskShield()
    
    descriptions = [
        "Cotton t-shirts for casual wear",
        "Organic turmeric powder for food use",
        "Herbal supplement with natural extracts",
        "Chemical compound for industrial use",
        "LED lights for home decoration"
    ]
    
    for description in descriptions:
        keywords = service.detect_red_flag_keywords(description)
        print(f"\nDescription: {description}")
        if keywords:
            print(f"Red Flag Keywords: {', '.join(keywords)}")
            print("⚠️  May trigger higher RMS inspection probability")
        else:
            print("✓ No red flag keywords detected")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  LOGISTICS RISK SHIELD SERVICE - EXAMPLES")
    print("=" * 80)
    
    try:
        example_complete_analysis()
        example_lcl_vs_fcl()
        example_rms_probability()
        example_route_analysis()
        example_freight_estimation()
        example_insurance()
        example_red_flag_keywords()
        
        print("\n" + "=" * 80)
        print("  All examples completed successfully!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
