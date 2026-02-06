"""
Example: Past Rejection Data Retrieval

This example demonstrates how the past rejection data retrieval functionality works.
It shows how to query FDA refusal database and EU RASFF for similar products.

Usage:
    python -m services.example_past_rejection_retrieval
"""

import logging
from services.report_generator import ReportGenerator
from models.query import QueryInput, HSCodePrediction
from models.enums import BusinessType, CompanySize

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_us_food_export():
    """Example: Retrieve past rejection data for food export to US."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Past Rejection Data for US Food Export")
    print("="*80)
    
    generator = ReportGenerator()
    
    # Query for turmeric powder to US
    rejections = generator.retrieve_rejection_reasons(
        product_type="Turmeric Powder",
        destination_country="United States"
    )
    
    print(f"\nFound {len(rejections)} past rejections for Turmeric Powder to US:")
    
    for i, rejection in enumerate(rejections, 1):
        print(f"\n{i}. Product: {rejection.product_type}")
        print(f"   Reason: {rejection.reason}")
        print(f"   Source: {rejection.source}")
        print(f"   Date: {rejection.date}")


def example_eu_food_export():
    """Example: Retrieve past rejection data for food export to EU."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Past Rejection Data for EU Food Export")
    print("="*80)
    
    generator = ReportGenerator()
    
    # Query for basmati rice to Germany
    rejections = generator.retrieve_rejection_reasons(
        product_type="Basmati Rice",
        destination_country="Germany"
    )
    
    print(f"\nFound {len(rejections)} past rejections for Basmati Rice to Germany:")
    
    for i, rejection in enumerate(rejections, 1):
        print(f"\n{i}. Product: {rejection.product_type}")
        print(f"   Reason: {rejection.reason}")
        print(f"   Source: {rejection.source}")
        print(f"   Date: {rejection.date}")


def example_full_report_with_rejections():
    """Example: Generate full report including past rejection data."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Full Export Readiness Report with Past Rejections")
    print("="*80)
    
    generator = ReportGenerator()
    
    # Create query for organic turmeric powder to US
    query = QueryInput(
        product_name="Organic Turmeric Powder",
        destination_country="United States",
        business_type=BusinessType.MANUFACTURING,
        company_size=CompanySize.MICRO,
        ingredients="Organic turmeric, natural color",
        bom="Turmeric rhizomes, packaging materials"
    )
    
    # Provide HS code to speed up example
    hs_code = HSCodePrediction(
        code="0910.30",
        confidence=85.0,
        description="Turmeric (curcuma)",
        alternatives=[]
    )
    
    print("\nGenerating export readiness report...")
    report = generator.generate_report(query, hs_code=hs_code)
    
    print(f"\n✓ Report generated: {report.report_id}")
    print(f"✓ Risk Score: {report.risk_score}/100")
    print(f"✓ Certifications Required: {len(report.certifications)}")
    print(f"✓ Past Rejections Found: {len(report.past_rejections)}")
    
    if report.past_rejections:
        print("\nPast Rejection Data:")
        for i, rejection in enumerate(report.past_rejections, 1):
            print(f"\n{i}. {rejection.product_type}")
            print(f"   Reason: {rejection.reason}")
            print(f"   Source: {rejection.source}")
            print(f"   Date: {rejection.date}")
    
    # Show how past rejections affect risk score
    rejection_risks = [r for r in report.risks if "Rejection" in r.title or "Historical" in r.title]
    if rejection_risks:
        print("\nRisks Related to Past Rejections:")
        for risk in rejection_risks:
            print(f"\n• {risk.title} ({risk.severity})")
            print(f"  {risk.description}")
            print(f"  Mitigation: {risk.mitigation}")


def example_multiple_products():
    """Example: Compare rejection data for multiple products."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Compare Rejection Data for Multiple Products")
    print("="*80)
    
    generator = ReportGenerator()
    
    products = [
        ("Turmeric Powder", "United States"),
        ("Basmati Rice", "Germany"),
        ("Cashew Nuts", "United States"),
        ("Black Pepper", "France"),
    ]
    
    print("\nComparing past rejection data across products:\n")
    
    for product, destination in products:
        rejections = generator.retrieve_rejection_reasons(
            product_type=product,
            destination_country=destination
        )
        
        print(f"• {product} → {destination}: {len(rejections)} rejections")
        
        if rejections:
            # Show most common rejection reason
            reasons = [r.reason for r in rejections]
            print(f"  Common issues: {', '.join(set(reasons)[:3])}")


def example_destination_filtering():
    """Example: Show how destination affects database selection."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Destination-Based Database Selection")
    print("="*80)
    
    generator = ReportGenerator()
    
    product = "Spices"
    
    # US destination - queries FDA
    print(f"\nQuerying for '{product}' to United States (FDA database):")
    us_rejections = generator.retrieve_rejection_reasons(
        product_type=product,
        destination_country="United States"
    )
    print(f"Found {len(us_rejections)} rejections")
    if us_rejections:
        print(f"Sources: {set(r.source for r in us_rejections)}")
    
    # EU destination - queries EU RASFF
    print(f"\nQuerying for '{product}' to Germany (EU RASFF database):")
    eu_rejections = generator.retrieve_rejection_reasons(
        product_type=product,
        destination_country="Germany"
    )
    print(f"Found {len(eu_rejections)} rejections")
    if eu_rejections:
        print(f"Sources: {set(r.source for r in eu_rejections)}")
    
    # Other destination - queries both
    print(f"\nQuerying for '{product}' to Japan (both databases):")
    other_rejections = generator.retrieve_rejection_reasons(
        product_type=product,
        destination_country="Japan"
    )
    print(f"Found {len(other_rejections)} rejections")
    if other_rejections:
        print(f"Sources: {set(r.source for r in other_rejections)}")


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("PAST REJECTION DATA RETRIEVAL - EXAMPLES")
    print("="*80)
    print("\nThis demonstrates the implementation of Task 5.5:")
    print("- Query FDA refusal database and EU RASFF")
    print("- Filter by product type and destination country")
    print("- Return rejection reasons with source and date")
    print("- Integrate with risk calculation")
    
    try:
        # Run examples
        example_us_food_export()
        example_eu_food_export()
        example_full_report_with_rejections()
        example_multiple_products()
        example_destination_filtering()
        
        print("\n" + "="*80)
        print("✓ All examples completed successfully!")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
