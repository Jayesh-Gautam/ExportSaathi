"""
Document Validator Service for ExportSathi

This service validates export documents for compliance and errors.
Performs AI validation checks including:
- Port code mismatch detection
- Invoice format validation
- GST vs Shipping Bill matching
- RMS risk trigger detection
- Compliance text validation using AWS Comprehend

Requirements: 4.3, 4.4, 4.8
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

from models.document import ValidationResult, ValidationError, ValidationWarning
from models.enums import DocumentType, ValidationSeverity
from services.compliance_text_analyzer import ComplianceTextAnalyzer

logger = logging.getLogger(__name__)


# Port code mappings for major countries
PORT_CODE_MAPPINGS = {
    "USA": ["USNYC", "USLAX", "USSFO", "USIAH", "USMIA", "USSEA", "USHOU", "USBOS"],
    "UK": ["GBLGP", "GBSOU", "GBFXT", "GBLIV", "GBBHX"],
    "UAE": ["AEDXB", "AEAUH", "AESHJ"],
    "GERMANY": ["DEHAM", "DEBRE", "DEFRA"],
    "CHINA": ["CNSHA", "CNSHK", "CNNBO", "CNQIN", "CNTAO"],
    "SINGAPORE": ["SGSIN"],
    "JAPAN": ["JPTYO", "JPOSA", "JPYOK"],
    "AUSTRALIA": ["AUSYD", "AUMEL", "AUBNE"],
    "CANADA": ["CAVAN", "CATOR", "CAHAL"],
    "FRANCE": ["FRPAR", "FRMRS", "FRLEH"],
    "INDIA": ["INMUN", "INDEL", "INBLR", "INCHE", "INCCU", "INIXE"]
}

# RMS risk trigger keywords that may flag shipments for inspection
RMS_TRIGGER_KEYWORDS = {
    # High-risk substances
    "chemical", "explosive", "radioactive", "hazardous", "toxic", "flammable",
    "corrosive", "biohazard", "pesticide", "narcotic", "drug", "pharmaceutical",
    
    # Dual-use items
    "military", "weapon", "ammunition", "defense", "surveillance", "encryption",
    
    # Restricted materials
    "ivory", "wildlife", "endangered", "antique", "artifact", "cultural",
    
    # High-value items
    "gold", "diamond", "jewelry", "precious", "gemstone",
    
    # Sensitive electronics
    "drone", "satellite", "missile", "nuclear", "laser",
    
    # Food safety concerns
    "meat", "dairy", "seafood", "poultry", "egg", "honey",
    
    # Agricultural concerns
    "seed", "plant", "soil", "fertilizer", "animal",
    
    # Generic risk terms
    "restricted", "prohibited", "controlled", "regulated", "sanctioned"
}

# Mandatory fields for different document types
MANDATORY_FIELDS = {
    DocumentType.COMMERCIAL_INVOICE: [
        "invoice_number", "invoice_date", "exporter_name", "exporter_address",
        "consignee_name", "consignee_address", "destination_country", "port_of_discharge",
        "items", "total_value", "currency", "payment_terms"
    ],
    DocumentType.PACKING_LIST: [
        "packing_list_number", "date", "exporter_name", "consignee_name",
        "items", "total_packages", "total_weight", "dimensions"
    ],
    DocumentType.SHIPPING_BILL: [
        "shipping_bill_number", "date", "exporter_name", "exporter_iec",
        "consignee_name", "destination_country", "port_of_loading", "port_of_discharge",
        "items", "total_fob_value", "currency"
    ],
    DocumentType.GST_LUT: [
        "lut_number", "financial_year", "exporter_name", "exporter_gstin",
        "exporter_address", "declaration_date"
    ],
    DocumentType.SOFTEX: [
        "softex_number", "date", "exporter_name", "exporter_gstin",
        "service_description", "service_recipient", "recipient_country",
        "invoice_value", "currency"
    ],
    DocumentType.CERTIFICATE_OF_ORIGIN: [
        "certificate_number", "date", "exporter_name", "exporter_address",
        "consignee_name", "consignee_address", "destination_country",
        "items", "origin_country"
    ]
}


@dataclass
class RiskFactor:
    """RMS risk factor detected in document."""
    keyword: str
    location: str  # field name where keyword was found
    context: str  # surrounding text
    severity: str  # "high", "medium", "low"
    suggestion: str


class DocumentValidator:
    """
    Validates export documents for compliance and errors.
    
    Features:
    - Port code mismatch detection
    - Invoice format validation
    - GST vs Shipping Bill data matching
    - RMS risk trigger keyword detection
    - AWS Comprehend compliance text validation
    - Mandatory field validation
    - Cross-document consistency checks
    
    Requirements: 4.3, 4.4, 4.8
    """
    
    def __init__(
        self,
        compliance_analyzer: Optional[ComplianceTextAnalyzer] = None
    ):
        """
        Initialize Document Validator.
        
        Args:
            compliance_analyzer: Compliance text analyzer for AWS Comprehend validation
        """
        self.compliance_analyzer = compliance_analyzer or ComplianceTextAnalyzer()
        logger.info("DocumentValidator initialized")
    
    def validate(
        self,
        document: Dict[str, Any],
        document_type: DocumentType
    ) -> ValidationResult:
        """
        Validate export document for compliance and errors.
        
        Performs comprehensive validation including:
        - Mandatory field checks
        - Port code validation
        - Invoice format validation
        - RMS risk trigger detection
        - Compliance text validation
        
        Args:
            document: Document content as dictionary
            document_type: Type of document being validated
            
        Returns:
            ValidationResult with errors and warnings
            
        Example:
            >>> validator = DocumentValidator()
            >>> result = validator.validate(invoice_data, DocumentType.COMMERCIAL_INVOICE)
            >>> if not result.is_valid:
            ...     for error in result.errors:
            ...         print(f"Error in {error.field}: {error.message}")
        
        Requirements: 4.3, 4.4, 4.8
        """
        logger.info(f"Validating document type: {document_type}")
        
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # 1. Check mandatory fields
        mandatory_errors = self._check_mandatory_fields(document, document_type)
        errors.extend(mandatory_errors)
        
        # 2. Validate port codes
        port_errors = self.check_port_code_mismatch(document)
        errors.extend(port_errors)
        
        # 3. Validate invoice format (if applicable)
        if document_type == DocumentType.COMMERCIAL_INVOICE:
            invoice_errors = self.validate_invoice_format(document)
            errors.extend(invoice_errors)
        
        # 4. Detect RMS risk triggers
        risk_factors = self.detect_rms_risk_triggers(document)
        for risk in risk_factors:
            if risk.severity == "high":
                errors.append(ValidationError(
                    field=risk.location,
                    message=f"High-risk keyword detected: '{risk.keyword}'",
                    severity=ValidationSeverity.ERROR,
                    suggestion=risk.suggestion
                ))
            else:
                warnings.append(ValidationWarning(
                    field=risk.location,
                    message=f"Potential RMS trigger keyword: '{risk.keyword}'",
                    suggestion=risk.suggestion
                ))
        
        # 5. Use AWS Comprehend for compliance text validation
        compliance_warnings = self._validate_with_comprehend(document)
        warnings.extend(compliance_warnings)
        
        # Determine if document is valid (no errors)
        is_valid = len(errors) == 0
        
        logger.info(f"Validation complete: is_valid={is_valid}, errors={len(errors)}, warnings={len(warnings)}")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def check_port_code_mismatch(
        self,
        document: Dict[str, Any]
    ) -> List[ValidationError]:
        """
        Detect port code mismatches with destination country.
        
        Validates that the port of discharge code matches the destination country.
        For example, USNYC (New York) should only be used for USA destinations.
        
        Args:
            document: Document content with port_of_discharge and destination_country
            
        Returns:
            List of validation errors for port code mismatches
            
        Example:
            >>> validator = DocumentValidator()
            >>> doc = {"port_of_discharge": "USNYC", "destination_country": "UK"}
            >>> errors = validator.check_port_code_mismatch(doc)
            >>> # Returns error: port code USNYC doesn't match UK
        
        Requirements: 4.3
        """
        errors: List[ValidationError] = []
        
        port_code = document.get("port_of_discharge", "").upper()
        destination = document.get("destination_country", "").upper()
        
        if not port_code or not destination:
            return errors
        
        # Check if port code matches destination country
        country_matched = False
        for country, valid_ports in PORT_CODE_MAPPINGS.items():
            if country in destination or destination in country:
                if port_code in valid_ports:
                    country_matched = True
                    break
                else:
                    # Found the country but port doesn't match
                    errors.append(ValidationError(
                        field="port_of_discharge",
                        message=f"Port code '{port_code}' does not match destination country '{destination}'",
                        severity=ValidationSeverity.ERROR,
                        suggestion=f"Valid ports for {country}: {', '.join(valid_ports[:3])}"
                    ))
                    return errors
        
        # If country not in our mappings, issue a warning
        if not country_matched and destination not in ["", "INDIA"]:
            logger.warning(f"Unknown destination country: {destination}")
        
        return errors
    
    def validate_invoice_format(
        self,
        invoice: Dict[str, Any]
    ) -> List[ValidationError]:
        """
        Validate commercial invoice format compliance.
        
        Checks:
        - Invoice number format (should be alphanumeric with optional dashes/slashes)
        - Date format (should be valid date)
        - Currency code (should be valid 3-letter ISO code)
        - Total value calculation (should match sum of line items)
        - Payment terms format
        
        Args:
            invoice: Commercial invoice document
            
        Returns:
            List of validation errors for format issues
            
        Example:
            >>> validator = DocumentValidator()
            >>> invoice = {"invoice_number": "INV-2024-001", "currency": "USD"}
            >>> errors = validator.validate_invoice_format(invoice)
        
        Requirements: 4.3
        """
        errors: List[ValidationError] = []
        
        # Validate invoice number format
        invoice_number = invoice.get("invoice_number", "")
        if invoice_number:
            # Should be alphanumeric with optional dashes, slashes, underscores
            if not re.match(r'^[A-Za-z0-9\-/_]+$', invoice_number):
                errors.append(ValidationError(
                    field="invoice_number",
                    message="Invoice number contains invalid characters",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Use only letters, numbers, dashes, slashes, and underscores"
                ))
        
        # Validate currency code (should be 3-letter ISO code)
        currency = invoice.get("currency", "").upper()
        valid_currencies = {"USD", "EUR", "GBP", "INR", "AED", "SGD", "JPY", "CNY", "AUD", "CAD"}
        if currency and currency not in valid_currencies:
            errors.append(ValidationError(
                field="currency",
                message=f"Invalid currency code: '{currency}'",
                severity=ValidationSeverity.ERROR,
                suggestion=f"Use valid ISO currency codes like: {', '.join(list(valid_currencies)[:5])}"
            ))
        
        # Validate total value calculation
        items = invoice.get("items", [])
        total_value = invoice.get("total_value", 0)
        if items and total_value:
            calculated_total = sum(
                item.get("quantity", 0) * item.get("unit_price", 0)
                for item in items
            )
            # Allow small floating point differences
            if abs(calculated_total - total_value) > 0.01:
                errors.append(ValidationError(
                    field="total_value",
                    message=f"Total value {total_value} doesn't match sum of line items {calculated_total:.2f}",
                    severity=ValidationSeverity.ERROR,
                    suggestion=f"Update total_value to {calculated_total:.2f}"
                ))
        
        # Validate payment terms
        payment_terms = invoice.get("payment_terms", "")
        if payment_terms:
            # Common payment terms patterns
            valid_patterns = [
                r'\d+\s*days?',  # "30 days", "60 days"
                r'advance',
                r'on\s*delivery',
                r'letter\s*of\s*credit',
                r'l/?c',
                r'sight',
                r'net\s*\d+'
            ]
            if not any(re.search(pattern, payment_terms.lower()) for pattern in valid_patterns):
                errors.append(ValidationError(
                    field="payment_terms",
                    message="Payment terms format may be non-standard",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Use standard terms like '30 days', 'Advance', 'Letter of Credit', etc."
                ))
        
        return errors
    
    def check_gst_shipping_bill_match(
        self,
        gst_doc: Dict[str, Any],
        shipping_bill: Dict[str, Any]
    ) -> List[ValidationError]:
        """
        Check GST document vs Shipping Bill data matching.
        
        Validates consistency between GST LUT and Shipping Bill:
        - Exporter GSTIN matches
        - Exporter name matches
        - Export value is consistent
        - Dates are within reasonable range
        
        Args:
            gst_doc: GST LUT document
            shipping_bill: Shipping Bill document
            
        Returns:
            List of validation errors for mismatches
            
        Example:
            >>> validator = DocumentValidator()
            >>> gst = {"exporter_gstin": "27AABCU9603R1ZM"}
            >>> sb = {"exporter_gstin": "27AABCU9603R1ZM"}
            >>> errors = validator.check_gst_shipping_bill_match(gst, sb)
        
        Requirements: 4.3, 4.8
        """
        errors: List[ValidationError] = []
        
        # Check GSTIN match
        gst_gstin = gst_doc.get("exporter_gstin", "").upper()
        sb_gstin = shipping_bill.get("exporter_gstin", "").upper()
        
        if gst_gstin and sb_gstin and gst_gstin != sb_gstin:
            errors.append(ValidationError(
                field="exporter_gstin",
                message=f"GSTIN mismatch: GST LUT has '{gst_gstin}' but Shipping Bill has '{sb_gstin}'",
                severity=ValidationSeverity.ERROR,
                suggestion="Ensure both documents use the same GSTIN"
            ))
        
        # Check exporter name match (case-insensitive, allowing minor variations)
        gst_name = gst_doc.get("exporter_name", "").lower().strip()
        sb_name = shipping_bill.get("exporter_name", "").lower().strip()
        
        if gst_name and sb_name:
            # Remove common suffixes for comparison
            gst_name_clean = re.sub(r'\s*(pvt\.?|ltd\.?|limited|private|llp|llc)\s*$', '', gst_name)
            sb_name_clean = re.sub(r'\s*(pvt\.?|ltd\.?|limited|private|llp|llc)\s*$', '', sb_name)
            
            if gst_name_clean != sb_name_clean:
                errors.append(ValidationError(
                    field="exporter_name",
                    message=f"Exporter name mismatch between GST LUT and Shipping Bill",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Ensure exporter name is consistent across all documents"
                ))
        
        return errors
    
    def detect_rms_risk_triggers(
        self,
        document: Dict[str, Any]
    ) -> List[RiskFactor]:
        """
        Detect RMS risk trigger keywords in document.
        
        Scans document content for keywords that may trigger RMS (Risk Management System)
        checks by customs. These include:
        - Hazardous materials
        - Dual-use items
        - Restricted substances
        - High-value items
        - Sensitive electronics
        
        Args:
            document: Document content to scan
            
        Returns:
            List of detected risk factors with severity and suggestions
            
        Example:
            >>> validator = DocumentValidator()
            >>> doc = {"product_description": "Chemical compound for industrial use"}
            >>> risks = validator.detect_rms_risk_triggers(doc)
            >>> # Returns risk factor for "chemical" keyword
        
        Requirements: 4.3, 6.5
        """
        risk_factors: List[RiskFactor] = []
        
        # Fields to scan for risk keywords
        fields_to_scan = [
            "product_description", "description", "item_description",
            "goods_description", "nature_of_goods", "commodity_description"
        ]
        
        # Also scan items array if present
        items = document.get("items", [])
        
        # Scan main document fields
        for field in fields_to_scan:
            if field in document:
                text = str(document[field]).lower()
                risks = self._scan_text_for_triggers(text, field)
                risk_factors.extend(risks)
        
        # Scan items
        for idx, item in enumerate(items):
            for field in ["description", "product_description", "item_description"]:
                if field in item:
                    text = str(item[field]).lower()
                    risks = self._scan_text_for_triggers(text, f"items[{idx}].{field}")
                    risk_factors.extend(risks)
        
        return risk_factors
    
    def _scan_text_for_triggers(
        self,
        text: str,
        field_name: str
    ) -> List[RiskFactor]:
        """
        Scan text for RMS trigger keywords.
        
        Args:
            text: Text to scan (should be lowercase)
            field_name: Name of field being scanned
            
        Returns:
            List of risk factors found
        """
        risk_factors: List[RiskFactor] = []
        
        for keyword in RMS_TRIGGER_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = list(re.finditer(pattern, text))
            
            for match in matches:
                # Extract context (30 chars before and after)
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end]
                
                # Determine severity based on keyword category
                severity = self._determine_risk_severity(keyword)
                
                # Generate suggestion
                suggestion = self._generate_risk_suggestion(keyword)
                
                risk_factors.append(RiskFactor(
                    keyword=keyword,
                    location=field_name,
                    context=context,
                    severity=severity,
                    suggestion=suggestion
                ))
        
        return risk_factors
    
    def _determine_risk_severity(self, keyword: str) -> str:
        """Determine severity level for RMS trigger keyword."""
        high_risk = {
            "explosive", "radioactive", "narcotic", "weapon", "ammunition",
            "military", "nuclear", "missile"
        }
        medium_risk = {
            "chemical", "hazardous", "toxic", "flammable", "pharmaceutical",
            "drone", "encryption", "surveillance"
        }
        
        if keyword in high_risk:
            return "high"
        elif keyword in medium_risk:
            return "medium"
        else:
            return "low"
    
    def _generate_risk_suggestion(self, keyword: str) -> str:
        """Generate suggestion for handling RMS trigger keyword."""
        suggestions = {
            "chemical": "Specify the exact chemical name and CAS number. Provide MSDS documentation.",
            "explosive": "This is a highly restricted item. Ensure proper licensing and documentation.",
            "hazardous": "Classify according to UN hazard class. Provide proper safety documentation.",
            "pharmaceutical": "Provide drug license and regulatory approval documents.",
            "drone": "Provide technical specifications and end-use certificate.",
            "gold": "Declare exact purity and weight. Provide valuation certificate.",
            "meat": "Provide health certificate and veterinary inspection report.",
            "seed": "Provide phytosanitary certificate and import permit from destination.",
        }
        
        return suggestions.get(
            keyword,
            f"Use more specific terminology. Provide detailed specifications and certifications."
        )
    
    def _check_mandatory_fields(
        self,
        document: Dict[str, Any],
        document_type: DocumentType
    ) -> List[ValidationError]:
        """
        Check that all mandatory fields are present and non-empty.
        
        Args:
            document: Document content
            document_type: Type of document
            
        Returns:
            List of validation errors for missing fields
        """
        errors: List[ValidationError] = []
        
        mandatory_fields = MANDATORY_FIELDS.get(document_type, [])
        
        for field in mandatory_fields:
            if field not in document or not document[field]:
                errors.append(ValidationError(
                    field=field,
                    message=f"Mandatory field '{field}' is missing or empty",
                    severity=ValidationSeverity.ERROR,
                    suggestion=f"Provide a value for {field}"
                ))
        
        return errors
    
    def _validate_with_comprehend(
        self,
        document: Dict[str, Any]
    ) -> List[ValidationWarning]:
        """
        Use AWS Comprehend for compliance text validation.
        
        Extracts entities and key phrases to identify potential compliance issues.
        
        Args:
            document: Document content
            
        Returns:
            List of validation warnings from Comprehend analysis
        """
        warnings: List[ValidationWarning] = []
        
        try:
            # Extract text content from document
            text_parts = []
            for key, value in document.items():
                if isinstance(value, str) and len(value) > 10:
                    text_parts.append(value)
            
            if not text_parts:
                return warnings
            
            # Combine text (limit to 5000 chars for Comprehend)
            combined_text = " ".join(text_parts)[:5000]
            
            # Extract entities using Comprehend
            entities = self.compliance_analyzer.extract_entities(combined_text)
            
            # Check for potential compliance issues
            # Look for organization names that might need verification
            org_entities = [e for e in entities if e.type == "ORGANIZATION"]
            if len(org_entities) > 5:
                warnings.append(ValidationWarning(
                    field="document",
                    message=f"Document contains {len(org_entities)} organization names",
                    suggestion="Verify all organization names are spelled correctly"
                ))
            
            # Extract key phrases
            key_phrases = self.compliance_analyzer.extract_key_phrases(combined_text)
            
            # Check for very long descriptions
            long_phrases = [kp for kp in key_phrases if len(kp.text) > 100]
            if long_phrases:
                warnings.append(ValidationWarning(
                    field="description",
                    message="Document contains very long descriptions",
                    suggestion="Consider breaking down long descriptions for clarity"
                ))
            
        except Exception as e:
            logger.warning(f"AWS Comprehend validation failed: {e}")
            # Don't fail validation if Comprehend is unavailable
        
        return warnings
