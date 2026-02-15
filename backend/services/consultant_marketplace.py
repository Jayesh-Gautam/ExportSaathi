"""
Consultant Marketplace Service for ExportSathi

This service provides search and filter functionality for finding consultants
who can help with certification acquisition.

Requirements: 3.4
"""

import logging
from typing import List, Optional, Dict, Any
from models.certification import Consultant
from models.common import CostRange, ContactInfo

logger = logging.getLogger(__name__)


class ConsultantMarketplace:
    """
    Service for searching and filtering consultants.
    
    Provides functionality to:
    1. Search consultants by certification type
    2. Filter by rating, cost range, experience, and location
    3. Sort by rating, cost, or experience
    
    Requirements: 3.4
    """
    
    def __init__(self):
        """Initialize Consultant Marketplace with sample data."""
        self.consultants = self._load_consultants()
        logger.info(f"ConsultantMarketplace initialized with {len(self.consultants)} consultants")
    
    def _load_consultants(self) -> List[Consultant]:
        """Load consultant data. In production, this would come from a database."""
        return [
            # FDA Consultants
            Consultant(
                id="cons-fda-1",
                name="FDA Compliance Experts India",
                specialization=["FDA Registration", "Food Safety", "FSVP"],
                rating=4.5,
                cost_range=CostRange(min=25000, max=75000, currency="INR"),
                contact=ContactInfo(
                    email="info@fdacompliance.in",
                    phone="+91-98765-43210",
                    website="https://www.fdacompliance.in"
                ),
                experience_years=10,
                certifications_handled=["FDA", "FSSAI", "HACCP"],
                success_rate=95.0,
                location="Mumbai, India"
            ),
            Consultant(
                id="cons-fda-2",
                name="Global Export Consultants",
                specialization=["FDA", "Export Compliance", "Documentation"],
                rating=4.3,
                cost_range=CostRange(min=30000, max=80000, currency="INR"),
                contact=ContactInfo(
                    email="contact@globalexport.com",
                    phone="+91-98765-12345",
                    website="https://www.globalexport.com"
                ),
                experience_years=8,
                certifications_handled=["FDA", "CE", "ISO"],
                success_rate=92.0,
                location="Delhi, India"
            ),
            Consultant(
                id="cons-fda-3",
                name="US Market Access Advisors",
                specialization=["FDA", "US Customs", "Labeling"],
                rating=4.7,
                cost_range=CostRange(min=40000, max=100000, currency="INR"),
                contact=ContactInfo(
                    email="info@usmarketaccess.com",
                    phone="+91-98765-99999",
                    website="https://www.usmarketaccess.com"
                ),
                experience_years=15,
                certifications_handled=["FDA", "USDA", "EPA"],
                success_rate=97.0,
                location="Bangalore, India"
            ),
            
            # CE Marking Consultants
            Consultant(
                id="cons-ce-1",
                name="CE Marking Consultants India",
                specialization=["CE Marking", "EU Compliance", "Technical Files"],
                rating=4.6,
                cost_range=CostRange(min=40000, max=120000, currency="INR"),
                contact=ContactInfo(
                    email="info@cemarking.in",
                    phone="+91-98765-67890",
                    website="https://www.cemarking.in"
                ),
                experience_years=12,
                certifications_handled=["CE", "REACH", "RoHS"],
                success_rate=94.0,
                location="Pune, India"
            ),
            Consultant(
                id="cons-ce-2",
                name="EU Compliance Partners",
                specialization=["CE", "REACH", "RoHS", "WEEE"],
                rating=4.4,
                cost_range=CostRange(min=50000, max=150000, currency="INR"),
                contact=ContactInfo(
                    email="contact@eucompliance.com",
                    phone="+91-98765-11111",
                    website="https://www.eucompliance.com"
                ),
                experience_years=15,
                certifications_handled=["CE", "REACH", "RoHS", "WEEE", "ATEX"],
                success_rate=96.0,
                location="Mumbai, India"
            ),
            Consultant(
                id="cons-ce-3",
                name="European Market Specialists",
                specialization=["CE Marking", "Product Safety", "EMC Testing"],
                rating=4.2,
                cost_range=CostRange(min=35000, max=90000, currency="INR"),
                contact=ContactInfo(
                    email="info@eumarketspecialists.com",
                    phone="+91-98765-33333",
                    website="https://www.eumarketspecialists.com"
                ),
                experience_years=9,
                certifications_handled=["CE", "LVD", "EMC"],
                success_rate=91.0,
                location="Chennai, India"
            ),
            
            # BIS Consultants
            Consultant(
                id="cons-bis-1",
                name="BIS Certification Consultants",
                specialization=["BIS", "ISI Mark", "CRS"],
                rating=4.7,
                cost_range=CostRange(min=20000, max=60000, currency="INR"),
                contact=ContactInfo(
                    email="info@bisconsultants.in",
                    phone="+91-98765-22222",
                    website="https://www.bisconsultants.in"
                ),
                experience_years=10,
                certifications_handled=["BIS", "ISI", "Hallmark"],
                success_rate=96.0,
                location="Delhi, India"
            ),
            Consultant(
                id="cons-bis-2",
                name="Indian Standards Experts",
                specialization=["BIS", "Quality Certification", "Factory Audits"],
                rating=4.5,
                cost_range=CostRange(min=25000, max=70000, currency="INR"),
                contact=ContactInfo(
                    email="contact@indianstandards.com",
                    phone="+91-98765-44444",
                    website="https://www.indianstandards.com"
                ),
                experience_years=12,
                certifications_handled=["BIS", "ISO", "NABL"],
                success_rate=94.0,
                location="Mumbai, India"
            ),
            
            # Multi-certification Consultants
            Consultant(
                id="cons-multi-1",
                name="Global Certification Partners",
                specialization=["FDA", "CE", "BIS", "ISO", "Export Compliance"],
                rating=4.8,
                cost_range=CostRange(min=50000, max=150000, currency="INR"),
                contact=ContactInfo(
                    email="info@globalcertpartners.com",
                    phone="+91-98765-55555",
                    website="https://www.globalcertpartners.com"
                ),
                experience_years=18,
                certifications_handled=["FDA", "CE", "BIS", "ISO", "REACH", "RoHS"],
                success_rate=98.0,
                location="Bangalore, India"
            ),
            Consultant(
                id="cons-multi-2",
                name="Export Ready Consultants",
                specialization=["Certification", "Documentation", "Logistics"],
                rating=4.4,
                cost_range=CostRange(min=30000, max=90000, currency="INR"),
                contact=ContactInfo(
                    email="info@exportready.in",
                    phone="+91-98765-66666",
                    website="https://www.exportready.in"
                ),
                experience_years=11,
                certifications_handled=["FDA", "CE", "BIS", "SOFTEX"],
                success_rate=93.0,
                location="Hyderabad, India"
            ),
            
            # SOFTEX Consultants
            Consultant(
                id="cons-softex-1",
                name="SOFTEX Filing Experts",
                specialization=["SOFTEX", "STPI", "SaaS Export"],
                rating=4.6,
                cost_range=CostRange(min=10000, max=30000, currency="INR"),
                contact=ContactInfo(
                    email="info@softexexperts.com",
                    phone="+91-98765-77777",
                    website="https://www.softexexperts.com"
                ),
                experience_years=7,
                certifications_handled=["SOFTEX", "STPI", "SEZ"],
                success_rate=95.0,
                location="Bangalore, India"
            ),
            
            # ZED Consultants
            Consultant(
                id="cons-zed-1",
                name="ZED Certification Advisors",
                specialization=["ZED", "Quality Management", "MSME Support"],
                rating=4.5,
                cost_range=CostRange(min=15000, max=50000, currency="INR"),
                contact=ContactInfo(
                    email="info@zedadvisors.in",
                    phone="+91-98765-88888",
                    website="https://www.zedadvisors.in"
                ),
                experience_years=8,
                certifications_handled=["ZED", "ISO", "5S"],
                success_rate=94.0,
                location="Pune, India"
            )
        ]
    
    def search_consultants(
        self,
        certification_type: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_cost: Optional[float] = None,
        min_experience: Optional[int] = None,
        location: Optional[str] = None,
        specialization: Optional[str] = None,
        sort_by: str = "rating",
        sort_order: str = "desc"
    ) -> List[Consultant]:
        """
        Search and filter consultants based on criteria.
        
        Args:
            certification_type: Filter by certification type (e.g., "FDA", "CE", "BIS")
            min_rating: Minimum rating (0-5)
            max_cost: Maximum cost (filters by cost_range.max)
            min_experience: Minimum years of experience
            location: Filter by location (partial match)
            specialization: Filter by specialization (partial match)
            sort_by: Sort field ("rating", "cost", "experience")
            sort_order: Sort order ("asc" or "desc")
            
        Returns:
            List of matching consultants
            
        Requirements: 3.4
        """
        logger.info(f"Searching consultants with filters: cert={certification_type}, "
                   f"rating>={min_rating}, cost<={max_cost}, exp>={min_experience}, "
                   f"location={location}, spec={specialization}")
        
        filtered = self.consultants.copy()
        
        # Filter by certification type
        if certification_type:
            cert_upper = certification_type.upper()
            filtered = [
                c for c in filtered
                if any(cert_upper in cert.upper() for cert in c.certifications_handled)
            ]
        
        # Filter by minimum rating
        if min_rating is not None:
            filtered = [c for c in filtered if c.rating >= min_rating]
        
        # Filter by maximum cost
        if max_cost is not None:
            filtered = [c for c in filtered if c.cost_range.max <= max_cost]
        
        # Filter by minimum experience
        if min_experience is not None:
            filtered = [c for c in filtered if c.experience_years >= min_experience]
        
        # Filter by location
        if location:
            location_lower = location.lower()
            filtered = [
                c for c in filtered
                if c.location and location_lower in c.location.lower()
            ]
        
        # Filter by specialization
        if specialization:
            spec_lower = specialization.lower()
            filtered = [
                c for c in filtered
                if any(spec_lower in s.lower() for s in c.specialization)
            ]
        
        # Sort results
        if sort_by == "rating":
            filtered.sort(key=lambda c: c.rating, reverse=(sort_order == "desc"))
        elif sort_by == "cost":
            filtered.sort(key=lambda c: c.cost_range.min, reverse=(sort_order == "desc"))
        elif sort_by == "experience":
            filtered.sort(key=lambda c: c.experience_years, reverse=(sort_order == "desc"))
        
        logger.info(f"Found {len(filtered)} consultants matching criteria")
        return filtered
    
    def get_consultant_by_id(self, consultant_id: str) -> Optional[Consultant]:
        """
        Get consultant by ID.
        
        Args:
            consultant_id: Consultant identifier
            
        Returns:
            Consultant if found, None otherwise
        """
        for consultant in self.consultants:
            if consultant.id == consultant_id:
                return consultant
        return None
    
    def get_consultants_for_certification(
        self,
        certification_id: str,
        limit: int = 5
    ) -> List[Consultant]:
        """
        Get top consultants for a specific certification.
        
        Args:
            certification_id: Certification identifier (e.g., "fda-food-facility")
            limit: Maximum number of consultants to return
            
        Returns:
            List of top-rated consultants for the certification
            
        Requirements: 3.4
        """
        # Extract certification type from ID
        cert_type = None
        if "fda" in certification_id.lower():
            cert_type = "FDA"
        elif "ce" in certification_id.lower():
            cert_type = "CE"
        elif "bis" in certification_id.lower():
            cert_type = "BIS"
        elif "zed" in certification_id.lower():
            cert_type = "ZED"
        elif "softex" in certification_id.lower():
            cert_type = "SOFTEX"
        
        # Search with certification type filter and sort by rating
        consultants = self.search_consultants(
            certification_type=cert_type,
            sort_by="rating",
            sort_order="desc"
        )
        
        return consultants[:limit]


# Singleton instance
_marketplace_instance: Optional[ConsultantMarketplace] = None


def get_consultant_marketplace() -> ConsultantMarketplace:
    """Get or create singleton ConsultantMarketplace instance."""
    global _marketplace_instance
    if _marketplace_instance is None:
        _marketplace_instance = ConsultantMarketplace()
    return _marketplace_instance
