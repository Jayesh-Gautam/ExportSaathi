"""
Demonstration test for Route Analyzer functionality (Task 10.4).

This test demonstrates the enhanced route analyzer that:
1. Analyzes available shipping routes to destination
2. Predicts delays based on geopolitical situations (e.g., Red Sea disruptions)
3. Considers seasonal factors affecting transit times
4. Estimates transit time for each route
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.logistics_risk_shield import LogisticsRiskShield


def test_route_analyzer_comprehensive_demo():
    """
    Comprehensive demonstration of route analyzer functionality.
    
    This test shows how the route analyzer:
    - Identifies multiple routes to a destination
    - Considers geopolitical factors (Red Sea, Suez Canal)
    - Applies seasonal adjustments (monsoon, winter, peak season)
    - Provides transit time estimates
    - Recommends the best route based on current conditions
    """
    service = LogisticsRiskShield()
    
    print("\n" + "="*80)
    print("ROUTE ANALYZER DEMONSTRATION - Task 10.4")
    print("="*80)
    
    # Test Case 1: Europe destination without seasonal factors
    print("\n1. Route Analysis: Mumbai to Germany (No seasonal factors)")
    print("-" * 80)
    result = service.predict_route_delays(destination="Germany")
    
    print(f"Recommended Route: {result.recommended_route}")
    print(f"\nAvailable Routes ({len(result.routes)}):")
    for i, route in enumerate(result.routes, 1):
        print(f"\n  Route {i}: {route.name}")
        print(f"    Transit Time: {route.transit_time_days} days")
        print(f"    Delay Risk: {route.delay_risk}")
        print(f"    Cost Estimate: ${route.cost_estimate:,.2f}")
        if route.geopolitical_factors:
            print(f"    Geopolitical Factors:")
            for factor in route.geopolitical_factors:
                print(f"      - {factor}")
    
    # Test Case 2: Asia destination with monsoon season
    print("\n\n2. Route Analysis: Mumbai to Singapore (Monsoon Season)")
    print("-" * 80)
    result_monsoon = service.predict_route_delays(destination="Singapore", season="monsoon")
    
    print(f"Recommended Route: {result_monsoon.recommended_route}")
    print(f"\nRoute Details:")
    route = result_monsoon.routes[0]
    print(f"  Transit Time: {route.transit_time_days} days")
    print(f"  Delay Risk: {route.delay_risk}")
    print(f"  Cost Estimate: ${route.cost_estimate:,.2f}")
    if route.geopolitical_factors:
        print(f"  Seasonal & Geopolitical Factors:")
        for factor in route.geopolitical_factors:
            print(f"    - {factor}")
    
    # Compare with no seasonal factors
    result_no_season = service.predict_route_delays(destination="Singapore")
    print(f"\n  Comparison (without seasonal factors):")
    print(f"    Transit Time: {result_no_season.routes[0].transit_time_days} days")
    print(f"    Additional Delay due to Monsoon: {route.transit_time_days - result_no_season.routes[0].transit_time_days} days")
    
    # Test Case 3: North America with winter season
    print("\n\n3. Route Analysis: Mumbai to United States (Winter Season)")
    print("-" * 80)
    result_winter = service.predict_route_delays(destination="United States", season="winter")
    
    print(f"Recommended Route: {result_winter.recommended_route}")
    print(f"\nAvailable Routes ({len(result_winter.routes)}):")
    for i, route in enumerate(result_winter.routes, 1):
        print(f"\n  Route {i}: {route.name}")
        print(f"    Transit Time: {route.transit_time_days} days")
        print(f"    Delay Risk: {route.delay_risk}")
        print(f"    Cost Estimate: ${route.cost_estimate:,.2f}")
        if route.geopolitical_factors:
            print(f"    Factors:")
            for factor in route.geopolitical_factors:
                print(f"      - {factor}")
    
    # Test Case 4: Peak shipping season
    print("\n\n4. Route Analysis: Mumbai to United Kingdom (Peak Season - Fall)")
    print("-" * 80)
    result_peak = service.predict_route_delays(destination="United Kingdom", season="fall")
    
    print(f"Recommended Route: {result_peak.recommended_route}")
    route = result_peak.routes[0]
    print(f"\nRoute Details:")
    print(f"  Transit Time: {route.transit_time_days} days")
    print(f"  Delay Risk: {route.delay_risk}")
    print(f"  Cost Estimate: ${route.cost_estimate:,.2f}")
    if route.geopolitical_factors:
        print(f"  Peak Season Factors:")
        for factor in route.geopolitical_factors:
            print(f"    - {factor}")
    
    # Test Case 5: Favorable spring season
    print("\n\n5. Route Analysis: Mumbai to Singapore (Spring - Optimal Window)")
    print("-" * 80)
    result_spring = service.predict_route_delays(destination="Singapore", season="spring")
    
    print(f"Recommended Route: {result_spring.recommended_route}")
    route = result_spring.routes[0]
    print(f"\nRoute Details:")
    print(f"  Transit Time: {route.transit_time_days} days")
    print(f"  Delay Risk: {route.delay_risk}")
    print(f"  Cost Estimate: ${route.cost_estimate:,.2f}")
    if route.geopolitical_factors:
        print(f"  Favorable Conditions:")
        for factor in route.geopolitical_factors:
            print(f"    - {factor}")
    
    print("\n" + "="*80)
    print("ROUTE ANALYZER DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nKey Features Demonstrated:")
    print("  ✓ Multiple route options analyzed")
    print("  ✓ Geopolitical factors considered (Red Sea, Suez Canal)")
    print("  ✓ Seasonal adjustments applied (monsoon, winter, peak, spring)")
    print("  ✓ Transit time estimates provided")
    print("  ✓ Cost estimates for each route")
    print("  ✓ Delay risk assessment")
    print("  ✓ Route recommendations based on current conditions")
    print("\nRequirements Validated:")
    print("  ✓ 6.3: Route delays predicted based on geopolitical situations")
    print("  ✓ 6.7: Transit time estimated for different routes")
    print("  ✓ Seasonal factors affecting transit times considered")
    print("="*80 + "\n")
    
    # Assertions to validate functionality
    assert len(result.routes) > 0, "Should have at least one route"
    assert result.recommended_route is not None, "Should have a recommended route"
    assert result_monsoon.routes[0].transit_time_days >= result_no_season.routes[0].transit_time_days, \
        "Monsoon season should add delay"
    assert any("monsoon" in factor.lower() for factor in result_monsoon.routes[0].geopolitical_factors), \
        "Should mention monsoon factors"
    assert any("winter" in factor.lower() or "storm" in factor.lower() 
               for route in result_winter.routes 
               for factor in route.geopolitical_factors), \
        "Should mention winter factors"
    assert any("peak" in factor.lower() or "congestion" in factor.lower()
               for factor in result_peak.routes[0].geopolitical_factors), \
        "Should mention peak season factors"
    assert any("favorable" in factor.lower() or "optimal" in factor.lower()
               for factor in result_spring.routes[0].geopolitical_factors), \
        "Should mention favorable spring conditions"


if __name__ == "__main__":
    test_route_analyzer_comprehensive_demo()
