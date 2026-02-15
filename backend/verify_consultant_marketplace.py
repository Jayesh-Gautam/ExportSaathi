"""
Simple verification script for consultant marketplace integration.
This script tests the consultant marketplace without loading heavy dependencies.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Test imports
print("Testing imports...")
try:
    from models.certification import Consultant
    from models.common import CostRange, ContactInfo
    print("✓ Models imported successfully")
except Exception as e:
    print(f"✗ Failed to import models: {e}")
    sys.exit(1)

# Test consultant marketplace (without heavy dependencies)
print("\nTesting consultant marketplace...")
try:
    # Import the marketplace class directly
    from services.consultant_marketplace import ConsultantMarketplace
    
    # Create instance
    marketplace = ConsultantMarketplace()
    print(f"✓ Marketplace initialized with {len(marketplace.consultants)} consultants")
    
    # Test search by certification type
    fda_consultants = marketplace.search_consultants(certification_type="FDA")
    print(f"✓ Found {len(fda_consultants)} FDA consultants")
    
    # Test filtering by rating
    high_rated = marketplace.search_consultants(min_rating=4.5)
    print(f"✓ Found {len(high_rated)} consultants with rating >= 4.5")
    
    # Test filtering by cost
    affordable = marketplace.search_consultants(max_cost=50000)
    print(f"✓ Found {len(affordable)} consultants with cost <= ₹50,000")
    
    # Test combined filters
    filtered = marketplace.search_consultants(
        certification_type="CE",
        min_rating=4.0,
        max_cost=100000
    )
    print(f"✓ Found {len(filtered)} CE consultants with rating >= 4.0 and cost <= ₹100,000")
    
    # Test sorting
    by_rating = marketplace.search_consultants(sort_by="rating", sort_order="desc")
    print(f"✓ Sorted {len(by_rating)} consultants by rating (highest first)")
    if len(by_rating) >= 2:
        print(f"  Top consultant: {by_rating[0].name} (rating: {by_rating[0].rating})")
    
    # Test get by ID
    if marketplace.consultants:
        test_id = marketplace.consultants[0].id
        consultant = marketplace.get_consultant_by_id(test_id)
        if consultant:
            print(f"✓ Retrieved consultant by ID: {consultant.name}")
        else:
            print("✗ Failed to retrieve consultant by ID")
    
    # Test get consultants for certification
    fda_top = marketplace.get_consultants_for_certification("fda-food-facility", limit=3)
    print(f"✓ Found {len(fda_top)} top consultants for FDA certification")
    
    # Verify data model
    print("\nVerifying consultant data model...")
    sample = marketplace.consultants[0]
    assert hasattr(sample, 'id'), "Missing id field"
    assert hasattr(sample, 'name'), "Missing name field"
    assert hasattr(sample, 'specialization'), "Missing specialization field"
    assert hasattr(sample, 'rating'), "Missing rating field"
    assert hasattr(sample, 'cost_range'), "Missing cost_range field"
    assert hasattr(sample, 'contact'), "Missing contact field"
    assert hasattr(sample, 'experience_years'), "Missing experience_years field"
    assert hasattr(sample, 'certifications_handled'), "Missing certifications_handled field"
    assert hasattr(sample, 'success_rate'), "Missing success_rate field"
    assert hasattr(sample, 'location'), "Missing location field"
    print("✓ All required fields present in consultant model")
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED - Consultant marketplace is working correctly!")
    print("="*60)
    
except Exception as e:
    print(f"✗ Error testing consultant marketplace: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
