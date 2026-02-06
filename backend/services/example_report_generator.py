"""
Example usage of Report Generator Service

This script demonstrates how to use the ReportGenerator service to generate
comprehensive export readiness reports.

Run this script to see a complete example of report generation.
"""

import json
from datetime import datetime

from models.query import QueryInput, HSCodePrediction
from models.enums import BusinessType, CompanySize
from services.report_generator import ReportGenerator


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def example_basic_report():
    """Example: Generate basic report with pre-computed HS code."""
    print_section("Example 1: Basic Report Generation")
    
    # Create query
    query = QueryInput(
        product_name="Organic Turmeric Powder",
        destination_country="United States",
        business_type=BusinessType.MANUFACTURING,
        company_size=CompanySize.MICRO,
        ingredients="100% organic turmeric",
        bom="Turmeric rhizomes, paper packaging material"
    )
    
    print(f"\nProduct: {query.product_name}")
    print(f"Destination: {query.destination_country}")
    print(f"Business Type: {query.business_type}")
    print(f"Company Size: {query.company_size}")
    
    # Pre-compute HS code to avoid LLM call in example
    hs_code = HSCodePrediction(
        code="0910.30",
        confidence=92.5,
        description="Turmeric (curcuma)",
        alternatives=[]
    )
    
    # Generate report
    print("\nGenerating report...")
    generator = ReportGenerator()
    report = generator.generate_report(query, hs_code=hs_code)
    
    # Display results
    print(f"\n✅ Report Generated: {report.report_id}")
    print(f"Status: {report.status}")
    print(f"Generated at: {report.generated_at}")
    
    print(f"\n📊 HS Code: {report.hs_code.code} ({report.hs_code.confidence}% confidence)")
    print(f"Description: {report.hs_code.description}")
    
    print(f"\n📋 Certifications Required: {len(report.certifications)}")
    for cert in report.certifications:
        mandatory = "✓ MANDATORY" if cert.mandatory else "○ Optional"
        print(f"  {mandatory} - {cert.name}")
        print(f"    Cost: ₹{cert.estimated_cost.min:,} - ₹{cert.estimated_cost.max:,}")
        print(f"    Timeline: {cert.estimated_timeline_days} days")
        print(f"    Priority: {cert.priority}")
    
    print(f"\n⚠️  Risk Score: {report.risk_score}/100")
    print(f"Identified Risks: {len(report.risks)}")
    for risk in report.risks:
        print(f"  [{risk.severity.upper()}] {risk.title}")
        print(f"    {risk.description}")
        print(f"    Mitigation: {risk.mitigation}")
    
    print(f"\n💰 Cost Breakdown:")
    print(f"  Certifications: ₹{report.costs.certifications:,.2f}")
    print(f"  Documentation: ₹{report.costs.documentation:,.2f}")
    print(f"  Logistics: ₹{report.costs.logistics:,.2f}")
    print(f"  TOTAL: ₹{report.costs.total:,.2f}")
    
    print(f"\n💵 Subsidies Available: {len(report.subsidies)}")
    for subsidy in report.subsidies:
        print(f"  • {subsidy.name}")
        print(f"    Amount: ₹{subsidy.amount:,.2f} ({subsidy.percentage}%)")
        print(f"    Eligibility: {subsidy.eligibility}")
    
    print(f"\n⏱️  Timeline: {report.timeline.estimated_days} days")
    for phase in report.timeline.breakdown:
        print(f"  • {phase.phase}: {phase.duration_days} days")
    
    print(f"\n📅 7-Day Action Plan:")
    for day in report.action_plan.days:
        print(f"  Day {day.day}: {day.title}")
        for task in day.tasks:
            status = "☑" if task.completed else "☐"
            print(f"    {status} {task.title}")
    
    print(f"\n📚 Compliance Roadmap: {len(report.compliance_roadmap)} steps")
    for step in report.compliance_roadmap[:3]:  # Show first 3 steps
        print(f"  {step.step}. {step.title} ({step.duration_days} days)")
    
    print(f"\n📖 Sources Retrieved: {len(report.retrieved_sources)}")
    for source in report.retrieved_sources[:2]:  # Show first 2 sources
        print(f"  • {source.title}")
        if source.relevance_score:
            print(f"    Relevance: {source.relevance_score:.2%}")


def example_saas_export():
    """Example: Generate report for SaaS export."""
    print_section("Example 2: SaaS Export Report")
    
    query = QueryInput(
        product_name="Cloud-based CRM Software",
        destination_country="United Kingdom",
        business_type=BusinessType.SAAS,
        company_size=CompanySize.SMALL,
        monthly_volume=100,
        price_range="$50-$200 per user/month"
    )
    
    print(f"\nProduct: {query.product_name}")
    print(f"Destination: {query.destination_country}")
    print(f"Business Type: {query.business_type}")
    
    # For SaaS, HS code is not applicable
    hs_code = HSCodePrediction(
        code="0000.00",
        confidence=100.0,
        description="Software as a Service (not applicable)",
        alternatives=[]
    )
    
    print("\nGenerating report...")
    generator = ReportGenerator()
    report = generator.generate_report(query, hs_code=hs_code)
    
    print(f"\n✅ Report Generated: {report.report_id}")
    
    print(f"\n📋 Certifications Required: {len(report.certifications)}")
    for cert in report.certifications:
        print(f"  • {cert.name} ({cert.type})")
        if cert.type.value == "SOFTEX":
            print(f"    ⭐ SOFTEX is mandatory for SaaS exports from India")
    
    print(f"\n⚠️  Risk Score: {report.risk_score}/100")
    print(f"💰 Total Cost: ₹{report.costs.total:,.2f}")
    print(f"⏱️  Timeline: {report.timeline.estimated_days} days")


def example_eu_electronics():
    """Example: Generate report for EU electronics export."""
    print_section("Example 3: EU Electronics Export")
    
    query = QueryInput(
        product_name="Wireless Bluetooth Speaker",
        destination_country="Germany",
        business_type=BusinessType.MANUFACTURING,
        company_size=CompanySize.MEDIUM,
        bom="PCB, battery, speaker driver, plastic housing",
        monthly_volume=1000
    )
    
    print(f"\nProduct: {query.product_name}")
    print(f"Destination: {query.destination_country}")
    
    # Electronics HS code
    hs_code = HSCodePrediction(
        code="8518.21",
        confidence=88.0,
        description="Loudspeakers, single",
        alternatives=[]
    )
    
    print("\nGenerating report...")
    generator = ReportGenerator()
    report = generator.generate_report(query, hs_code=hs_code)
    
    print(f"\n✅ Report Generated: {report.report_id}")
    
    print(f"\n📋 Certifications Required: {len(report.certifications)}")
    for cert in report.certifications:
        print(f"  • {cert.name} ({cert.type})")
        if cert.type.value == "CE":
            print(f"    ⭐ CE Marking is mandatory for electronics in EU")
            print(f"    Cost: ₹{cert.estimated_cost.min:,} - ₹{cert.estimated_cost.max:,}")
    
    print(f"\n⚠️  Risk Score: {report.risk_score}/100")
    print(f"💰 Total Cost: ₹{report.costs.total:,.2f}")


def example_json_export():
    """Example: Export report as JSON."""
    print_section("Example 4: JSON Export")
    
    query = QueryInput(
        product_name="Organic Tea",
        destination_country="United States",
        business_type=BusinessType.MANUFACTURING,
        company_size=CompanySize.MICRO
    )
    
    hs_code = HSCodePrediction(
        code="0902.10",
        confidence=95.0,
        description="Green tea",
        alternatives=[]
    )
    
    generator = ReportGenerator()
    report = generator.generate_report(query, hs_code=hs_code)
    
    # Convert to JSON
    report_json = report.model_dump_json(indent=2)
    
    print("\nReport JSON (first 1000 characters):")
    print(report_json[:1000] + "...")
    
    # Save to file
    filename = f"report_{report.report_id}.json"
    with open(filename, 'w') as f:
        f.write(report_json)
    
    print(f"\n✅ Full report saved to: {filename}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  REPORT GENERATOR SERVICE - EXAMPLES")
    print("=" * 80)
    print("\nThis script demonstrates the Report Generator Service capabilities.")
    print("It generates export readiness reports for different scenarios.")
    
    try:
        # Example 1: Basic report
        example_basic_report()
        
        # Example 2: SaaS export
        example_saas_export()
        
        # Example 3: EU electronics
        example_eu_electronics()
        
        # Example 4: JSON export
        example_json_export()
        
        print("\n" + "=" * 80)
        print("  ✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
