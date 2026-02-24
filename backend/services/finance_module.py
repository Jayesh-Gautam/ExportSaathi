"""
Finance Module Service for ExportSathi.

This module provides comprehensive finance readiness analysis including:
- Working capital calculation
- Pre-shipment credit eligibility assessment
- RoDTEP benefit calculation
- GST refund estimation
- Cash flow timeline generation
- Liquidity gap identification
- Financing options and bank referrals
"""
from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import directly from models file to avoid __init__.py issues
from database.models import Report as DBReport
from models.finance import (
    WorkingCapitalAnalysis,
    PreShipmentCredit,
    RoDTEPBenefit,
    GSTRefund,
    CashFlowEvent,
    CashFlowTimeline,
    LiquidityGap,
    CurrencyHedging,
    FinancingOption,
    FinanceAnalysis
)
from models.enums import CashFlowEventType, CompanySize
from models.report import ExportReadinessReport
from services.rodtep_calculator import RoDTEPCalculator
import json


class FinanceModule:
    """
    Finance Module for calculating working capital, credit eligibility,
    RoDTEP benefits, and generating cash flow timelines.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize the Finance Module.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        
        # Initialize RoDTEP calculator
        self.rodtep_calculator = RoDTEPCalculator()
        
        # Pre-shipment credit rates by company size
        self.credit_rates = {
            CompanySize.MICRO: {"rate": 7.5, "max_percentage": 80},
            CompanySize.SMALL: {"rate": 8.0, "max_percentage": 75},
            CompanySize.MEDIUM: {"rate": 8.5, "max_percentage": 70}
        }
    
    def calculate_working_capital(self, report_id: str) -> WorkingCapitalAnalysis:
        """
        Calculate total working capital requirements.
        
        Includes:
        - Product/manufacturing cost
        - Certification costs
        - Logistics costs
        - Documentation costs
        - Buffer (15% of total)
        
        Args:
            report_id: Report identifier
            
        Returns:
            WorkingCapitalAnalysis with breakdown and total
            
        Raises:
            ValueError: If report not found
        """
        # Retrieve report from database
        report = self.db.query(DBReport).filter(DBReport.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Parse report data
        report_data = report.report_data
        
        # Extract costs from report
        # Product cost: estimate based on monthly volume and price range
        product_cost = self._estimate_product_cost(
            report.monthly_volume,
            report.price_range
        )
        
        # Certification costs from report
        certification_costs = float(report_data.get("costs", {}).get("certifications", 0))
        
        # Logistics costs from report
        logistics_costs = float(report_data.get("costs", {}).get("logistics", 0))
        
        # Documentation costs from report
        documentation_costs = float(report_data.get("costs", {}).get("documentation", 0))
        
        # Calculate subtotal
        subtotal = product_cost + certification_costs + logistics_costs + documentation_costs
        
        # Buffer: 15% of subtotal for contingencies
        buffer = subtotal * 0.15
        
        # Total working capital
        total = subtotal + buffer
        
        return WorkingCapitalAnalysis(
            product_cost=product_cost,
            certification_costs=certification_costs,
            logistics_costs=logistics_costs,
            documentation_costs=documentation_costs,
            buffer=buffer,
            total=total,
            currency="INR"
        )
    
    def assess_credit_eligibility(
        self,
        report_id: str,
        order_value: Optional[float] = None,
        has_banking_relationship: bool = False,
        export_history_months: int = 0
    ) -> PreShipmentCredit:
        """
        Assess pre-shipment credit eligibility based on company profile.
        
        Considers:
        - Company size (Micro/Small/Medium)
        - Order value
        - Banking relationships (existing export credit facility)
        - Export history
        
        Args:
            report_id: Report identifier
            order_value: Optional order value (uses working capital if not provided)
            has_banking_relationship: Whether company has existing banking relationship
            export_history_months: Number of months of export history (0 for first-time exporters)
            
        Returns:
            PreShipmentCredit with eligibility and terms
            
        Raises:
            ValueError: If report not found
        """
        # Retrieve report from database
        report = self.db.query(DBReport).filter(DBReport.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Get company size
        company_size = CompanySize(report.company_size)
        
        # Calculate working capital if order value not provided
        if order_value is None:
            working_capital = self.calculate_working_capital(report_id)
            order_value = working_capital.total
        
        # Get base credit parameters for company size
        credit_params = self.credit_rates.get(company_size, self.credit_rates[CompanySize.SMALL])
        
        # Base interest rate and max percentage
        base_interest_rate = credit_params["rate"]
        max_percentage = credit_params["max_percentage"]
        
        # Adjust interest rate based on banking relationship
        # Existing banking relationship can reduce interest rate by 0.5-1%
        interest_rate_adjustment = 0.0
        if has_banking_relationship:
            interest_rate_adjustment = -0.5
        
        # Adjust based on export history
        # Established exporters (12+ months) get better rates
        if export_history_months >= 12:
            interest_rate_adjustment -= 0.5
        elif export_history_months >= 6:
            interest_rate_adjustment -= 0.25
        
        # Final interest rate (minimum 6.5%)
        interest_rate = max(6.5, base_interest_rate + interest_rate_adjustment)
        
        # Adjust credit percentage based on relationship and history
        percentage_adjustment = 0
        if has_banking_relationship:
            percentage_adjustment += 5  # 5% more credit
        if export_history_months >= 12:
            percentage_adjustment += 5  # Another 5% for established exporters
        
        # Final credit percentage (capped at 90%)
        final_percentage = min(90, max_percentage + percentage_adjustment)
        
        # Calculate eligible credit amount
        estimated_amount = order_value * (final_percentage / 100)
        
        # Tenure: typically 90-180 days for pre-shipment credit
        # Longer tenure for established exporters
        tenure_days = 90
        if export_history_months >= 12:
            tenure_days = 120
        elif export_history_months >= 6:
            tenure_days = 105
        
        # Eligibility criteria
        # First-time exporters with small orders may face challenges
        eligible = True
        if order_value < 50000 and export_history_months == 0:
            eligible = False  # Too small for most banks
        
        # Build requirements list
        requirements = [
            "Valid export order or Letter of Credit (LC)",
            "Company registration documents (GST, IEC)",
            "Bank account with export credit facility",
            "KYC documents of directors",
            "Last 6 months bank statements"
        ]
        
        # Additional requirements for larger companies
        if company_size == CompanySize.MEDIUM:
            requirements.append("Audited financial statements for last 2 years")
        
        # Additional requirements for first-time exporters
        if export_history_months == 0:
            requirements.append("Business plan and export strategy document")
            requirements.append("Collateral or personal guarantee may be required")
        
        # Reduced requirements for established banking relationships
        if has_banking_relationship and export_history_months >= 12:
            requirements.append("Note: Simplified documentation for existing customers")
        
        return PreShipmentCredit(
            eligible=eligible,
            estimated_amount=estimated_amount,
            interest_rate=interest_rate,
            tenure_days=tenure_days,
            requirements=requirements
        )
    
    def calculate_rodtep_benefit(
        self,
        hs_code: str,
        destination: str,
        fob_value: float
    ) -> RoDTEPBenefit:
        """
        Calculate RoDTEP (Remission of Duties and Taxes on Exported Products) benefit.
        
        Uses the RoDTEPCalculator service to calculate benefits based on
        official RoDTEP schedules.
        
        Args:
            hs_code: Harmonized System code
            destination: Destination country
            fob_value: FOB (Free on Board) value of export
            
        Returns:
            RoDTEPBenefit with rate and estimated amount
        """
        # Use RoDTEPCalculator service
        return self.rodtep_calculator.calculate_benefit(
            hs_code=hs_code,
            destination=destination,
            fob_value=fob_value
        )
    
    def estimate_gst_refund(
        self,
        export_value: float,
        gst_paid: Optional[float] = None
    ) -> GSTRefund:
        """
        Estimate GST refund timeline and amount.
        
        Args:
            export_value: Export value
            gst_paid: GST paid on inputs (estimated if not provided)
            
        Returns:
            GSTRefund with amount and timeline
        """
        # If GST paid not provided, estimate at 18% of export value
        if gst_paid is None:
            gst_paid = export_value * 0.18
        
        # GST refund timeline: typically 30-60 days
        timeline_days = 45
        
        requirements = [
            "GST LUT (Letter of Undertaking) filed",
            "Shipping bill filed with customs",
            "Bank realization certificate (BRC)",
            "Invoice and packing list",
            "GST returns filed (GSTR-1, GSTR-3B)"
        ]
        
        return GSTRefund(
            estimated_amount=gst_paid,
            timeline_days=timeline_days,
            requirements=requirements
        )
    
    def generate_cash_flow_timeline(self, report_id: str) -> CashFlowTimeline:
        """
        Generate cash flow timeline with expense and income events.
        
        Identifies liquidity gap periods where expenses exceed income.
        
        Args:
            report_id: Report identifier
            
        Returns:
            CashFlowTimeline with events and liquidity gap
            
        Raises:
            ValueError: If report not found
        """
        # Retrieve report from database
        report = self.db.query(DBReport).filter(DBReport.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Parse report data
        report_data = report.report_data
        
        # Calculate working capital
        working_capital = self.calculate_working_capital(report_id)
        
        # Start date: today
        start_date = date.today()
        
        # Generate cash flow events
        events: List[CashFlowEvent] = []
        
        # Day 1-7: Documentation costs
        events.append(CashFlowEvent(
            event_date=start_date + timedelta(days=3),
            event_type=CashFlowEventType.EXPENSE,
            category="Documentation",
            amount=-working_capital.documentation_costs,
            description="Export documentation preparation (invoices, packing lists, GST LUT)"
        ))
        
        # Day 7-30: Certification costs (staggered)
        cert_costs = working_capital.certification_costs
        if cert_costs > 0:
            # Split certification costs into application and testing
            events.append(CashFlowEvent(
                event_date=start_date + timedelta(days=7),
                event_type=CashFlowEventType.EXPENSE,
                category="Certification",
                amount=-(cert_costs * 0.3),
                description="Certification application fees"
            ))
            events.append(CashFlowEvent(
                event_date=start_date + timedelta(days=21),
                event_type=CashFlowEventType.EXPENSE,
                category="Certification",
                amount=-(cert_costs * 0.7),
                description="Certification testing and audit fees"
            ))
        
        # Day 30-45: Product/manufacturing costs
        events.append(CashFlowEvent(
            event_date=start_date + timedelta(days=35),
            event_type=CashFlowEventType.EXPENSE,
            category="Production",
            amount=-working_capital.product_cost,
            description="Product manufacturing/procurement costs"
        ))
        
        # Day 45-60: Logistics costs
        events.append(CashFlowEvent(
            event_date=start_date + timedelta(days=50),
            event_type=CashFlowEventType.EXPENSE,
            category="Logistics",
            amount=-working_capital.logistics_costs,
            description="Freight, insurance, and shipping costs"
        ))
        
        # Day 60: Shipment departure
        # No cash flow event, but milestone
        
        # Day 75-90: Customer payment (income)
        # Assume payment terms: 30 days after shipment
        customer_payment = working_capital.total * 1.2  # Assume 20% margin
        events.append(CashFlowEvent(
            event_date=start_date + timedelta(days=90),
            event_type=CashFlowEventType.INCOME,
            category="Customer Payment",
            amount=customer_payment,
            description="Customer payment received"
        ))
        
        # Day 105: RoDTEP benefit (income)
        hs_code = report.hs_code or "default"
        rodtep = self.calculate_rodtep_benefit(
            hs_code=hs_code,
            destination=report.destination_country,
            fob_value=customer_payment
        )
        events.append(CashFlowEvent(
            event_date=start_date + timedelta(days=105),
            event_type=CashFlowEventType.INCOME,
            category="RoDTEP Benefit",
            amount=rodtep.estimated_amount,
            description=f"RoDTEP benefit at {rodtep.rate_percentage}% rate"
        ))
        
        # Day 120: GST refund (income)
        gst_refund = self.estimate_gst_refund(customer_payment)
        events.append(CashFlowEvent(
            event_date=start_date + timedelta(days=120),
            event_type=CashFlowEventType.INCOME,
            category="GST Refund",
            amount=gst_refund.estimated_amount,
            description="GST refund received"
        ))
        
        # Sort events by date
        events.sort(key=lambda e: e.event_date)
        
        # Identify liquidity gap
        # Gap starts from first expense and ends when cumulative cash flow becomes positive
        liquidity_gap = self._identify_liquidity_gap(events, start_date)
        
        return CashFlowTimeline(
            events=events,
            liquidity_gap=liquidity_gap
        )
    
    def _identify_liquidity_gap(
        self,
        events: List[CashFlowEvent],
        start_date: date
    ) -> LiquidityGap:
        """
        Identify the liquidity gap period from cash flow events.
        
        Args:
            events: List of cash flow events
            start_date: Start date for analysis
            
        Returns:
            LiquidityGap with start date, end date, and amount
        """
        # Calculate cumulative cash flow
        cumulative = 0.0
        max_negative = 0.0
        gap_start = start_date
        gap_end = start_date
        
        for event in events:
            cumulative += event.amount
            
            if cumulative < 0:
                # Still in negative territory
                if cumulative < max_negative:
                    max_negative = cumulative
                gap_end = event.event_date
            elif cumulative >= 0 and max_negative < 0:
                # Just became positive - gap ends
                break
        
        # Gap amount is the maximum negative cumulative cash flow
        gap_amount = abs(max_negative)
        
        return LiquidityGap(
            start_date=gap_start,
            end_date=gap_end,
            amount=gap_amount
        )
    
    def suggest_financing_options(
        self,
        report_id: str,
        liquidity_gap: float
    ) -> List[FinancingOption]:
        """
        Suggest financing options based on liquidity gap and company profile.
        
        Args:
            report_id: Report identifier
            liquidity_gap: Liquidity gap amount
            
        Returns:
            List of FinancingOption
            
        Raises:
            ValueError: If report not found
        """
        # Retrieve report from database
        report = self.db.query(DBReport).filter(DBReport.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        company_size = CompanySize(report.company_size)
        
        options: List[FinancingOption] = []
        
        # Option 1: Pre-shipment credit
        credit = self.assess_credit_eligibility(report_id, liquidity_gap)
        if credit.eligible:
            options.append(FinancingOption(
                type="Pre-shipment credit",
                provider="State Bank of India / HDFC Bank / ICICI Bank",
                amount=credit.estimated_amount,
                interest_rate=credit.interest_rate,
                tenure="90 days",
                eligibility="Valid export order, company registration, bank account"
            ))
        
        # Option 2: Export credit guarantee (for micro/small enterprises)
        if company_size in [CompanySize.MICRO, CompanySize.SMALL]:
            options.append(FinancingOption(
                type="Export Credit Guarantee",
                provider="Export Credit Guarantee Corporation (ECGC)",
                amount=liquidity_gap * 0.9,  # 90% coverage
                interest_rate=0.0,  # Guarantee, not loan
                tenure="Up to 180 days",
                eligibility="MSME registration, export order"
            ))
        
        # Option 3: Working capital loan
        options.append(FinancingOption(
            type="Working capital loan",
            provider="Public/Private sector banks",
            amount=liquidity_gap,
            interest_rate=9.5,
            tenure="12 months",
            eligibility="Business vintage of 2+ years, financial statements"
        ))
        
        # Option 4: Invoice discounting (if customer is creditworthy)
        options.append(FinancingOption(
            type="Invoice discounting",
            provider="Banks / NBFCs / Fintech platforms",
            amount=liquidity_gap * 0.8,  # 80% of invoice value
            interest_rate=10.5,
            tenure="30-90 days",
            eligibility="Valid invoice, creditworthy buyer"
        ))
        
        # Option 5: Government schemes (for micro enterprises)
        if company_size == CompanySize.MICRO:
            options.append(FinancingOption(
                type="MUDRA loan (Tarun category)",
                provider="Banks under MUDRA scheme",
                amount=min(liquidity_gap, 1000000),  # Max 10 lakh
                interest_rate=8.0,
                tenure="Up to 5 years",
                eligibility="Micro enterprise, business plan"
            ))
        
        return options
    
    def generate_currency_hedging_advice(
        self,
        export_value: float,
        destination: str
    ) -> CurrencyHedging:
        """
        Generate currency hedging recommendations based on order value.
        
        Provides tailored hedging strategies including forward contracts and options
        to manage foreign exchange risk. Estimates potential savings from hedging
        based on typical currency volatility.
        
        Args:
            export_value: Export value in INR
            destination: Destination country
            
        Returns:
            CurrencyHedging with recommendations, strategies, and estimated savings
        """
        # Determine if hedging is recommended based on export value
        # Typically recommended for exports > 10 lakh INR
        recommended = export_value > 1000000
        
        strategies = []
        estimated_savings = 0.0
        
        if recommended:
            # For large exports, provide comprehensive hedging strategies
            strategies = [
                "Forward contract: Lock in exchange rate for 50-70% of order value to protect against adverse currency movements",
                "Currency options: Use options for remaining 30-50% to benefit from favorable rate movements while limiting downside risk",
                "Natural hedging: Match foreign currency receivables with payables (e.g., import raw materials in same currency)",
                "Layered hedging: Stagger forward contracts at different rates to average out exchange rate risk",
                "Consult with bank's treasury department for customized hedging solutions based on your risk appetite"
            ]
            
            # Estimate savings: assume 2-3% protection against adverse currency movement
            # Based on typical INR volatility of 3-5% annually
            estimated_savings = export_value * 0.025
            
            # Add value-specific recommendations
            if export_value > 5000000:  # > 50 lakh
                strategies.append(
                    "Consider structured products: Participate in favorable movements while protecting downside (consult forex advisor)"
                )
                # Higher savings potential for larger orders
                estimated_savings = export_value * 0.03
        else:
            # For smaller exports, provide basic monitoring strategies
            strategies = [
                "Monitor exchange rates regularly using bank apps or forex platforms",
                "Consider hedging when order value exceeds ₹10 lakh to protect margins",
                "Maintain foreign currency account for natural hedging of future transactions",
                "Build currency risk buffer into pricing (add 2-3% margin for forex volatility)"
            ]
            # No estimated savings for small exports as hedging costs may exceed benefits
            estimated_savings = 0.0
        
        return CurrencyHedging(
            recommended=recommended,
            strategies=strategies,
            estimated_savings=estimated_savings
        )
    
    def get_bank_referral_programs(self, company_size: CompanySize) -> List[dict]:
        """
        Get bank referral programs for export financing.
        
        Args:
            company_size: Company size classification
            
        Returns:
            List of bank referral programs
        """
        programs = [
            {
                "bank": "State Bank of India",
                "program": "SBI Export Credit",
                "features": [
                    "Pre-shipment and post-shipment credit",
                    "Competitive interest rates",
                    "Quick processing for MSMEs"
                ],
                "contact": "1800-425-3800",
                "website": "https://sbi.co.in/export-credit"
            },
            {
                "bank": "HDFC Bank",
                "program": "HDFC Export Finance",
                "features": [
                    "Customized export credit solutions",
                    "Foreign exchange advisory",
                    "Digital banking for exporters"
                ],
                "contact": "1800-202-6161",
                "website": "https://hdfcbank.com/export-finance"
            },
            {
                "bank": "ICICI Bank",
                "program": "ICICI Trade Finance",
                "features": [
                    "End-to-end export solutions",
                    "Letter of credit services",
                    "Export bill discounting"
                ],
                "contact": "1860-120-7777",
                "website": "https://icicibank.com/trade-finance"
            }
        ]
        
        # Add MSME-specific programs
        if company_size in [CompanySize.MICRO, CompanySize.SMALL]:
            programs.append({
                "bank": "SIDBI",
                "program": "SIDBI MSME Export Finance",
                "features": [
                    "Specialized MSME export financing",
                    "Subsidized interest rates",
                    "Capacity building support"
                ],
                "contact": "1800-102-7800",
                "website": "https://sidbi.in/export-finance"
            })
        
        return programs
    
    def _estimate_product_cost(
        self,
        monthly_volume: Optional[int],
        price_range: Optional[str]
    ) -> float:
        """
        Estimate product cost based on monthly volume and price range.
        
        Args:
            monthly_volume: Monthly export volume
            price_range: Price range string
            
        Returns:
            Estimated product cost
        """
        # Default cost if no data available
        default_cost = 100000.0
        
        if monthly_volume is None:
            return default_cost
        
        # Parse price range to get average price
        if price_range:
            # Expected format: "₹1000-₹5000" or "1000-5000"
            try:
                # Remove currency symbols and split
                price_range_clean = price_range.replace("₹", "").replace("$", "").strip()
                if "-" in price_range_clean:
                    parts = price_range_clean.split("-")
                    min_price = float(parts[0].strip())
                    max_price = float(parts[1].strip())
                    avg_price = (min_price + max_price) / 2
                else:
                    avg_price = float(price_range_clean)
                
                # Product cost = monthly volume * average price
                return monthly_volume * avg_price
            except (ValueError, IndexError):
                pass
        
        # Fallback: estimate based on monthly volume
        # Assume average unit price of ₹1000
        return monthly_volume * 1000.0 if monthly_volume else default_cost
    
    def generate_complete_analysis(self, report_id: str) -> FinanceAnalysis:
        """
        Generate complete finance readiness analysis.
        
        This is the main method that orchestrates all finance calculations.
        
        Args:
            report_id: Report identifier
            
        Returns:
            FinanceAnalysis with all components
            
        Raises:
            ValueError: If report not found
        """
        # Retrieve report from database
        report = self.db.query(DBReport).filter(DBReport.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Calculate working capital
        working_capital = self.calculate_working_capital(report_id)
        
        # Assess pre-shipment credit eligibility
        # Use default values for optional parameters (first-time exporter, no banking relationship)
        pre_shipment_credit = self.assess_credit_eligibility(
            report_id=report_id,
            has_banking_relationship=False,
            export_history_months=0
        )
        
        # Calculate RoDTEP benefit
        hs_code = report.hs_code or "default"
        fob_value = working_capital.total * 1.2  # Assume 20% margin
        rodtep_benefit = self.calculate_rodtep_benefit(
            hs_code=hs_code,
            destination=report.destination_country,
            fob_value=fob_value
        )
        
        # Estimate GST refund
        gst_refund = self.estimate_gst_refund(fob_value)
        
        # Generate cash flow timeline
        cash_flow_timeline = self.generate_cash_flow_timeline(report_id)
        
        # Generate currency hedging advice
        currency_hedging = self.generate_currency_hedging_advice(
            export_value=fob_value,
            destination=report.destination_country
        )
        
        # Suggest financing options
        financing_options = self.suggest_financing_options(
            report_id=report_id,
            liquidity_gap=cash_flow_timeline.liquidity_gap.amount
        )
        
        return FinanceAnalysis(
            report_id=report_id,
            working_capital=working_capital,
            pre_shipment_credit=pre_shipment_credit,
            rodtep_benefit=rodtep_benefit,
            gst_refund=gst_refund,
            cash_flow_timeline=cash_flow_timeline,
            currency_hedging=currency_hedging,
            financing_options=financing_options
        )
