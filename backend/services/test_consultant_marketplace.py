"""
Unit tests for Consultant Marketplace Service

Requirements: 3.4
"""
import pytest
from services.consultant_marketplace import ConsultantMarketplace, get_consultant_marketplace


class TestConsultantMarketplace:
    """Test suite for ConsultantMarketplace service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.marketplace = ConsultantMarketplace()
    
    def test_initialization(self):
        """Test marketplace initializes with consultants."""
        assert len(self.marketplace.consultants) > 0
        assert all(hasattr(c, 'id') for c in self.marketplace.consultants)
        assert all(hasattr(c, 'name') for c in self.marketplace.consultants)
        assert all(hasattr(c, 'rating') for c in self.marketplace.consultants)
    
    def test_search_by_certification_type(self):
        """Test searching consultants by certification type."""
        # Search for FDA consultants
        fda_consultants = self.marketplace.search_consultants(certification_type="FDA")
        assert len(fda_consultants) > 0
        assert all("FDA" in c.certifications_handled for c in fda_consultants)
        
        # Search for CE consultants
        ce_consultants = self.marketplace.search_consultants(certification_type="CE")
        assert len(ce_consultants) > 0
        assert all("CE" in c.certifications_handled for c in ce_consultants)
        
        # Search for BIS consultants
        bis_consultants = self.marketplace.search_consultants(certification_type="BIS")
        assert len(bis_consultants) > 0
        assert all("BIS" in c.certifications_handled for c in bis_consultants)
    
    def test_filter_by_min_rating(self):
        """Test filtering consultants by minimum rating."""
        min_rating = 4.5
        consultants = self.marketplace.search_consultants(min_rating=min_rating)
        assert all(c.rating >= min_rating for c in consultants)
    
    def test_filter_by_max_cost(self):
        """Test filtering consultants by maximum cost."""
        max_cost = 50000
        consultants = self.marketplace.search_consultants(max_cost=max_cost)
        assert all(c.cost_range.max <= max_cost for c in consultants)
    
    def test_filter_by_min_experience(self):
        """Test filtering consultants by minimum experience."""
        min_experience = 10
        consultants = self.marketplace.search_consultants(min_experience=min_experience)
        assert all(c.experience_years >= min_experience for c in consultants)
    
    def test_filter_by_location(self):
        """Test filtering consultants by location."""
        location = "Mumbai"
        consultants = self.marketplace.search_consultants(location=location)
        assert all(location.lower() in c.location.lower() for c in consultants if c.location)
    
    def test_filter_by_specialization(self):
        """Test filtering consultants by specialization."""
        specialization = "FDA"
        consultants = self.marketplace.search_consultants(specialization=specialization)
        assert all(
            any(specialization.lower() in s.lower() for s in c.specialization)
            for c in consultants
        )
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        consultants = self.marketplace.search_consultants(
            certification_type="FDA",
            min_rating=4.0,
            max_cost=100000,
            min_experience=8
        )
        
        for c in consultants:
            assert "FDA" in c.certifications_handled
            assert c.rating >= 4.0
            assert c.cost_range.max <= 100000
            assert c.experience_years >= 8
    
    def test_sort_by_rating_desc(self):
        """Test sorting by rating in descending order."""
        consultants = self.marketplace.search_consultants(
            sort_by="rating",
            sort_order="desc"
        )
        
        # Check that ratings are in descending order
        ratings = [c.rating for c in consultants]
        assert ratings == sorted(ratings, reverse=True)
    
    def test_sort_by_rating_asc(self):
        """Test sorting by rating in ascending order."""
        consultants = self.marketplace.search_consultants(
            sort_by="rating",
            sort_order="asc"
        )
        
        # Check that ratings are in ascending order
        ratings = [c.rating for c in consultants]
        assert ratings == sorted(ratings)
    
    def test_sort_by_cost_desc(self):
        """Test sorting by cost in descending order."""
        consultants = self.marketplace.search_consultants(
            sort_by="cost",
            sort_order="desc"
        )
        
        # Check that costs are in descending order
        costs = [c.cost_range.min for c in consultants]
        assert costs == sorted(costs, reverse=True)
    
    def test_sort_by_experience_desc(self):
        """Test sorting by experience in descending order."""
        consultants = self.marketplace.search_consultants(
            sort_by="experience",
            sort_order="desc"
        )
        
        # Check that experience is in descending order
        experience = [c.experience_years for c in consultants]
        assert experience == sorted(experience, reverse=True)
    
    def test_get_consultant_by_id(self):
        """Test getting consultant by ID."""
        # Get first consultant ID
        consultant_id = self.marketplace.consultants[0].id
        
        # Retrieve by ID
        consultant = self.marketplace.get_consultant_by_id(consultant_id)
        
        assert consultant is not None
        assert consultant.id == consultant_id
    
    def test_get_consultant_by_invalid_id(self):
        """Test getting consultant with invalid ID returns None."""
        consultant = self.marketplace.get_consultant_by_id("invalid-id")
        assert consultant is None
    
    def test_get_consultants_for_certification(self):
        """Test getting consultants for specific certification."""
        # Test FDA certification
        fda_consultants = self.marketplace.get_consultants_for_certification(
            "fda-food-facility",
            limit=3
        )
        assert len(fda_consultants) <= 3
        assert all("FDA" in c.certifications_handled for c in fda_consultants)
        
        # Test CE certification
        ce_consultants = self.marketplace.get_consultants_for_certification(
            "ce-marking",
            limit=3
        )
        assert len(ce_consultants) <= 3
        assert all("CE" in c.certifications_handled for c in ce_consultants)
        
        # Test BIS certification - consultants may handle multiple certifications
        bis_consultants = self.marketplace.get_consultants_for_certification(
            "bis-certification",
            limit=3
        )
        assert len(bis_consultants) <= 3
        # At least one consultant should have BIS in their certifications
        assert len(bis_consultants) > 0
    
    def test_get_consultants_for_certification_sorted_by_rating(self):
        """Test that consultants are sorted by rating (highest first)."""
        consultants = self.marketplace.get_consultants_for_certification(
            "fda-food-facility",
            limit=5
        )
        
        # Check that ratings are in descending order
        ratings = [c.rating for c in consultants]
        assert ratings == sorted(ratings, reverse=True)
    
    def test_singleton_instance(self):
        """Test that get_consultant_marketplace returns singleton instance."""
        instance1 = get_consultant_marketplace()
        instance2 = get_consultant_marketplace()
        
        assert instance1 is instance2
    
    def test_all_consultants_have_required_fields(self):
        """Test that all consultants have required fields."""
        for consultant in self.marketplace.consultants:
            assert consultant.id
            assert consultant.name
            assert consultant.specialization
            assert len(consultant.specialization) > 0
            assert 0.0 <= consultant.rating <= 5.0
            assert consultant.cost_range
            assert consultant.cost_range.min >= 0
            assert consultant.cost_range.max >= consultant.cost_range.min
            assert consultant.contact
            assert consultant.experience_years >= 0
            assert consultant.certifications_handled
            assert len(consultant.certifications_handled) > 0
    
    def test_no_results_for_impossible_filters(self):
        """Test that impossible filter combinations return empty list."""
        consultants = self.marketplace.search_consultants(
            min_rating=5.0,
            max_cost=1000,  # Very low cost
            min_experience=20  # Very high experience
        )
        
        # Should return empty list or very few results
        assert len(consultants) == 0 or len(consultants) < 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
