"""
Document Generator Service for ExportSathi

This service generates export documents with India-specific templates.
Supports: commercial invoice, packing list, shipping bill, GST LUT, SOFTEX, certificate of origin.
Auto-fills templates with user data from reports and profiles.
Generates documents in PDF and editable formats.

Requirements: 4.1, 4.2, 4.5
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from io import BytesIO

from models.document import (
    GeneratedDocument,
    ValidationResult,
    ValidationError,
    ValidationWarning,
    DocumentGenerationRequest
)
from models.enums import DocumentType, ValidationSeverity
from services.compliance_text_analyzer import ComplianceTextAnalyzer
from services.document_validator import DocumentValidator
from services.template_loader import TemplateLoader, get_template_loader

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """
    Generates export documents with India-specific templates.
    
    Features:
    - Support for 6 document types (commercial invoice, packing list, shipping bill, GST LUT, SOFTEX, certificate of origin)
    - India-specific templates compliant with DGFT and customs requirements
    - Auto-fill with user data from reports and profiles
    - AI validation for compliance
    - PDF and editable format generation
    
    Requirements: 4.1, 4.2, 4.5
    """
    
    def __init__(
        self,
        compliance_analyzer: Optional[ComplianceTextAnalyzer] = None,
        document_validator: Optional[DocumentValidator] = None,
        template_loader: Optional[TemplateLoader] = None
    ):
        """
        Initialize Document Generator.
        
        Args:
            compliance_analyzer: Compliance text analyzer for validation (creates new if None)
            document_validator: Document validator for comprehensive validation (creates new if None)
            template_loader: Template loader for loading JSON templates (creates new if None)
        """
        self.compliance_analyzer = compliance_analyzer or ComplianceTextAnalyzer()
        self.document_validator = document_validator or DocumentValidator(
            compliance_analyzer=self.compliance_analyzer
        )
        self.template_loader = template_loader or get_template_loader()
        logger.info("DocumentGenerator initialized with DocumentValidator and TemplateLoader")

    
    def generate_document(
        self,
        document_type: DocumentType,
        report_data: Dict[str, Any],
        user_data: Dict[str, Any],
        custom_data: Optional[Dict[str, Any]] = None
    ) -> GeneratedDocument:
        """
        Generate export document with auto-filled template.
        
        This is the main entry point for document generation. It:
        1. Selects appropriate India-specific template
        2. Auto-fills template with user data
        3. Validates document for compliance
        4. Generates PDF and editable formats
        
        Args:
            document_type: Type of document to generate
            report_data: Data from export readiness report
            user_data: User profile and business data
            custom_data: Optional custom fields to override defaults
            
        Returns:
            GeneratedDocument with content, validation results, and download URLs
            
        Example:
            >>> generator = DocumentGenerator()
            >>> doc = generator.generate_document(
            ...     document_type=DocumentType.COMMERCIAL_INVOICE,
            ...     report_data=report_dict,
            ...     user_data=user_dict
            ... )
            >>> print(f"Document ID: {doc.document_id}")
            >>> print(f"Valid: {doc.validation_results.is_valid}")
        
        Requirements: 4.1, 4.2, 4.5
        """
        logger.info(f"Generating document: {document_type}")
        
        try:
            # Generate unique document ID
            document_id = f"doc_{uuid.uuid4().hex[:12]}"
            
            # Step 1: Get India-specific template
            template = self._get_template(document_type)
            
            # Step 2: Auto-fill template with data
            content = self._auto_fill_template(
                template=template,
                document_type=document_type,
                report_data=report_data,
                user_data=user_data,
                custom_data=custom_data or {}
            )
            
            # Step 3: Validate document
            validation_results = self._validate_document(
                document_type=document_type,
                content=content,
                report_data=report_data
            )
            
            # Step 4: Generate PDF and editable formats
            pdf_url = self._generate_pdf(document_id, content, document_type)
            editable_url = self._generate_editable(document_id, content, document_type)
            
            # Build document response
            document = GeneratedDocument(
                document_id=document_id,
                document_type=document_type,
                content=content,
                validation_results=validation_results,
                pdf_url=pdf_url,
                editable_url=editable_url,
                generated_at=datetime.utcnow()
            )
            
            logger.info(f"Document generated successfully: {document_id}")
            return document
        
        except Exception as e:
            logger.error(f"Error generating document: {e}", exc_info=True)
            raise

    
    def _get_template(self, document_type: DocumentType) -> Dict[str, Any]:
        """
        Get India-specific template for document type.
        
        Templates are loaded from JSON files and are compliant with DGFT and customs requirements.
        
        Args:
            document_type: Type of document
            
        Returns:
            Template structure with required fields
        """
        try:
            # Load template from JSON file using TemplateLoader
            template = self.template_loader.load_template(document_type)
            
            # Remove _template_info from the template (metadata only)
            if "_template_info" in template:
                template = {k: v for k, v in template.items() if k != "_template_info"}
            
            return template
        except Exception as e:
            logger.error(f"Error loading template for {document_type}: {e}")
            # Fallback to hardcoded templates if JSON loading fails
            logger.warning(f"Falling back to hardcoded template for {document_type}")
            return self._get_fallback_template(document_type)
    
    def _get_fallback_template(self, document_type: DocumentType) -> Dict[str, Any]:
        """
        Get fallback hardcoded template if JSON loading fails.
        
        Args:
            document_type: Type of document
            
        Returns:
            Template structure with required fields
        """
        templates = {
            DocumentType.COMMERCIAL_INVOICE: self._get_commercial_invoice_template(),
            DocumentType.PACKING_LIST: self._get_packing_list_template(),
            DocumentType.SHIPPING_BILL: self._get_shipping_bill_template(),
            DocumentType.GST_LUT: self._get_gst_lut_template(),
            DocumentType.SOFTEX: self._get_softex_template(),
            DocumentType.CERTIFICATE_OF_ORIGIN: self._get_certificate_of_origin_template()
        }
        
        template = templates.get(document_type)
        if not template:
            raise ValueError(f"Unsupported document type: {document_type}")
        
        return template
    
    def _get_commercial_invoice_template(self) -> Dict[str, Any]:
        """India-specific commercial invoice template."""
        return {
            "invoice_number": "",
            "invoice_date": "",
            "exporter": {
                "name": "",
                "address": "",
                "city": "",
                "state": "",
                "country": "India",
                "pin_code": "",
                "gstin": "",
                "iec_code": "",
                "pan": "",
                "email": "",
                "phone": ""
            },
            "consignee": {
                "name": "",
                "address": "",
                "city": "",
                "state": "",
                "country": "",
                "postal_code": "",
                "tax_id": ""
            },
            "buyer": {
                "name": "",
                "address": "",
                "city": "",
                "country": ""
            },
            "shipment_details": {
                "port_of_loading": "",
                "port_of_discharge": "",
                "country_of_origin": "India",
                "country_of_final_destination": "",
                "terms_of_delivery": "FOB",  # FOB, CIF, CFR, etc.
                "mode_of_transport": "Sea"
            },
            "items": [],
            "totals": {
                "subtotal": 0.0,
                "freight": 0.0,
                "insurance": 0.0,
                "total": 0.0,
                "currency": "USD"
            },
            "payment_terms": "",
            "bank_details": {
                "bank_name": "",
                "branch": "",
                "account_number": "",
                "swift_code": "",
                "ifsc_code": ""
            },
            "declaration": "We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct."
        }

    
    def _get_packing_list_template(self) -> Dict[str, Any]:
        """India-specific packing list template."""
        return {
            "packing_list_number": "",
            "date": "",
            "invoice_number": "",
            "exporter": {
                "name": "",
                "address": "",
                "city": "",
                "country": "India"
            },
            "consignee": {
                "name": "",
                "address": "",
                "city": "",
                "country": ""
            },
            "shipment_details": {
                "port_of_loading": "",
                "port_of_discharge": "",
                "vessel_name": "",
                "container_number": ""
            },
            "packages": [],
            "totals": {
                "total_packages": 0,
                "total_gross_weight_kg": 0.0,
                "total_net_weight_kg": 0.0,
                "total_volume_cbm": 0.0
            }
        }
    
    def _get_shipping_bill_template(self) -> Dict[str, Any]:
        """India-specific shipping bill template (customs declaration)."""
        return {
            "shipping_bill_number": "",
            "shipping_bill_date": "",
            "exporter": {
                "name": "",
                "address": "",
                "iec_code": "",
                "gstin": "",
                "ad_code": ""  # Authorized Dealer Code
            },
            "consignee": {
                "name": "",
                "address": "",
                "country": ""
            },
            "port_of_loading": "",
            "port_of_discharge": "",
            "country_of_final_destination": "",
            "nature_of_transaction": "Export",
            "items": [],
            "totals": {
                "fob_value_inr": 0.0,
                "freight_inr": 0.0,
                "insurance_inr": 0.0,
                "total_invoice_value_inr": 0.0,
                "fob_value_foreign": 0.0,
                "currency": "USD"
            },
            "exchange_rate": 0.0,
            "rodtep_claim": {
                "eligible": False,
                "rate_percentage": 0.0,
                "amount_inr": 0.0
            },
            "declaration": "I/We hereby declare that the particulars given above are true and correct."
        }

    
    def _get_gst_lut_template(self) -> Dict[str, Any]:
        """India-specific GST LUT (Letter of Undertaking) template."""
        return {
            "lut_number": "",
            "financial_year": "",
            "date": "",
            "exporter": {
                "name": "",
                "address": "",
                "gstin": "",
                "pan": "",
                "iec_code": ""
            },
            "jurisdictional_officer": {
                "designation": "Assistant/Deputy Commissioner",
                "office": "",
                "address": ""
            },
            "undertaking": {
                "export_without_payment_of_igst": True,
                "comply_with_provisions": True,
                "furnish_required_documents": True,
                "accept_consequences_of_contravention": True
            },
            "declaration": "I/We hereby solemnly affirm and declare that the information given herein above is true and correct to the best of my/our knowledge and belief and nothing has been concealed therefrom.",
            "authorized_signatory": {
                "name": "",
                "designation": "",
                "date": ""
            }
        }
    
    def _get_softex_template(self) -> Dict[str, Any]:
        """India-specific SOFTEX declaration template for software/service exports."""
        return {
            "softex_number": "",
            "date": "",
            "exporter": {
                "name": "",
                "address": "",
                "city": "",
                "state": "",
                "pin_code": "",
                "iec_code": "",
                "gstin": "",
                "pan": "",
                "stpi_registration": ""  # STPI/SEZ registration if applicable
            },
            "buyer": {
                "name": "",
                "address": "",
                "country": ""
            },
            "service_details": {
                "description": "",
                "service_category": "",  # Software Development, IT Services, Consulting, etc.
                "contract_number": "",
                "contract_date": "",
                "delivery_mode": "Electronic"  # Electronic, Physical Media, etc.
            },
            "invoice_details": {
                "invoice_number": "",
                "invoice_date": "",
                "invoice_value": 0.0,
                "currency": "USD"
            },
            "payment_details": {
                "mode": "Wire Transfer",
                "bank_name": "",
                "swift_code": "",
                "expected_realization_date": ""
            },
            "declaration": "I/We hereby declare that the software/services mentioned above have been exported and the particulars given are true and correct."
        }

    
    def _get_certificate_of_origin_template(self) -> Dict[str, Any]:
        """India-specific certificate of origin template."""
        return {
            "certificate_number": "",
            "date": "",
            "exporter": {
                "name": "",
                "address": "",
                "city": "",
                "state": "",
                "country": "India"
            },
            "consignee": {
                "name": "",
                "address": "",
                "city": "",
                "country": ""
            },
            "transport_details": {
                "vessel_name": "",
                "port_of_loading": "",
                "port_of_discharge": "",
                "country_of_origin": "India",
                "country_of_destination": ""
            },
            "goods": [],
            "declaration": "The undersigned hereby declares that the above details and statement are correct; that all the goods were produced in India and that they comply with the origin requirements specified for those goods.",
            "issuing_authority": {
                "name": "Export Inspection Council of India / Chamber of Commerce",
                "place": "",
                "date": "",
                "signature": "",
                "stamp": ""
            }
        }

    
    def _auto_fill_template(
        self,
        template: Dict[str, Any],
        document_type: DocumentType,
        report_data: Dict[str, Any],
        user_data: Dict[str, Any],
        custom_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Auto-fill template with user data from reports and profiles.
        
        Args:
            template: Document template
            document_type: Type of document
            report_data: Data from export readiness report
            user_data: User profile and business data
            custom_data: Custom fields to override defaults
            
        Returns:
            Filled template
        """
        # Start with template
        content = template.copy()
        
        # Auto-fill based on document type (lowest priority)
        if document_type == DocumentType.COMMERCIAL_INVOICE:
            content = self._fill_commercial_invoice(content, report_data, user_data)
        elif document_type == DocumentType.PACKING_LIST:
            content = self._fill_packing_list(content, report_data, user_data)
        elif document_type == DocumentType.SHIPPING_BILL:
            content = self._fill_shipping_bill(content, report_data, user_data)
        elif document_type == DocumentType.GST_LUT:
            content = self._fill_gst_lut(content, report_data, user_data)
        elif document_type == DocumentType.SOFTEX:
            content = self._fill_softex(content, report_data, user_data)
        elif document_type == DocumentType.CERTIFICATE_OF_ORIGIN:
            content = self._fill_certificate_of_origin(content, report_data, user_data)
        
        # Apply custom data last (highest priority - overrides auto-fill)
        content = self._deep_update(content, custom_data)
        
        return content
    
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep update dictionary (recursive merge)."""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_update(result[key], value)
            else:
                result[key] = value
        return result

    
    def _fill_commercial_invoice(
        self,
        content: Dict[str, Any],
        report_data: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill commercial invoice with data."""
        # Generate invoice number if not provided
        if not content.get("invoice_number"):
            content["invoice_number"] = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Set invoice date
        if not content.get("invoice_date"):
            content["invoice_date"] = datetime.now().strftime("%Y-%m-%d")
        
        # Fill exporter details from user data
        if user_data:
            exporter = content.get("exporter", {})
            exporter["name"] = user_data.get("company_name", "")
            exporter["address"] = user_data.get("address", "")
            exporter["city"] = user_data.get("city", "")
            exporter["state"] = user_data.get("state", "")
            exporter["pin_code"] = user_data.get("pin_code", "")
            exporter["gstin"] = user_data.get("gstin", "")
            exporter["iec_code"] = user_data.get("iec_code", "")
            exporter["pan"] = user_data.get("pan", "")
            exporter["email"] = user_data.get("email", "")
            exporter["phone"] = user_data.get("phone", "")
            content["exporter"] = exporter
        
        # Fill destination from report data
        if report_data:
            destination = report_data.get("destination_country", "")
            if destination:
                content["consignee"]["country"] = destination
                content["buyer"]["country"] = destination
                content["shipment_details"]["country_of_final_destination"] = destination
        
        return content
    
    def _fill_packing_list(
        self,
        content: Dict[str, Any],
        report_data: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill packing list with data."""
        # Generate packing list number
        if not content.get("packing_list_number"):
            content["packing_list_number"] = f"PL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Set date
        if not content.get("date"):
            content["date"] = datetime.now().strftime("%Y-%m-%d")
        
        # Fill exporter details
        if user_data:
            exporter = content.get("exporter", {})
            exporter["name"] = user_data.get("company_name", "")
            exporter["address"] = user_data.get("address", "")
            exporter["city"] = user_data.get("city", "")
            content["exporter"] = exporter
        
        # Fill destination
        if report_data:
            destination = report_data.get("destination_country", "")
            if destination:
                content["consignee"]["country"] = destination
        
        return content

    
    def _fill_shipping_bill(
        self,
        content: Dict[str, Any],
        report_data: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill shipping bill with data."""
        # Generate shipping bill number
        if not content.get("shipping_bill_number"):
            content["shipping_bill_number"] = f"SB-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Set date
        if not content.get("shipping_bill_date"):
            content["shipping_bill_date"] = datetime.now().strftime("%Y-%m-%d")
        
        # Fill exporter details
        if user_data:
            exporter = content.get("exporter", {})
            exporter["name"] = user_data.get("company_name", "")
            exporter["address"] = user_data.get("address", "")
            exporter["iec_code"] = user_data.get("iec_code", "")
            exporter["gstin"] = user_data.get("gstin", "")
            exporter["ad_code"] = user_data.get("ad_code", "")
            content["exporter"] = exporter
        
        # Fill destination
        if report_data:
            destination = report_data.get("destination_country", "")
            if destination:
                content["consignee"]["country"] = destination
                content["country_of_final_destination"] = destination
        
        return content
    
    def _fill_gst_lut(
        self,
        content: Dict[str, Any],
        report_data: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill GST LUT with data."""
        # Generate LUT number
        if not content.get("lut_number"):
            content["lut_number"] = f"LUT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Set financial year and date
        if not content.get("financial_year"):
            year = datetime.now().year
            month = datetime.now().month
            if month >= 4:
                content["financial_year"] = f"{year}-{year+1}"
            else:
                content["financial_year"] = f"{year-1}-{year}"
        
        if not content.get("date"):
            content["date"] = datetime.now().strftime("%Y-%m-%d")
        
        # Fill exporter details
        if user_data:
            exporter = content.get("exporter", {})
            exporter["name"] = user_data.get("company_name", "")
            exporter["address"] = user_data.get("address", "")
            exporter["gstin"] = user_data.get("gstin", "")
            exporter["pan"] = user_data.get("pan", "")
            exporter["iec_code"] = user_data.get("iec_code", "")
            content["exporter"] = exporter
        
        return content

    
    def _fill_softex(
        self,
        content: Dict[str, Any],
        report_data: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill SOFTEX declaration with data."""
        # Generate SOFTEX number
        if not content.get("softex_number"):
            content["softex_number"] = f"SOFTEX-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Set date
        if not content.get("date"):
            content["date"] = datetime.now().strftime("%Y-%m-%d")
        
        # Fill exporter details
        if user_data:
            exporter = content.get("exporter", {})
            exporter["name"] = user_data.get("company_name", "")
            exporter["address"] = user_data.get("address", "")
            exporter["city"] = user_data.get("city", "")
            exporter["state"] = user_data.get("state", "")
            exporter["pin_code"] = user_data.get("pin_code", "")
            exporter["iec_code"] = user_data.get("iec_code", "")
            exporter["gstin"] = user_data.get("gstin", "")
            exporter["pan"] = user_data.get("pan", "")
            exporter["stpi_registration"] = user_data.get("stpi_registration", "")
            content["exporter"] = exporter
        
        # Fill destination
        if report_data:
            destination = report_data.get("destination_country", "")
            if destination:
                content["buyer"]["country"] = destination
        
        return content
    
    def _fill_certificate_of_origin(
        self,
        content: Dict[str, Any],
        report_data: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill certificate of origin with data."""
        # Generate certificate number
        if not content.get("certificate_number"):
            content["certificate_number"] = f"COO-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Set date
        if not content.get("date"):
            content["date"] = datetime.now().strftime("%Y-%m-%d")
        
        # Fill exporter details
        if user_data:
            exporter = content.get("exporter", {})
            exporter["name"] = user_data.get("company_name", "")
            exporter["address"] = user_data.get("address", "")
            exporter["city"] = user_data.get("city", "")
            exporter["state"] = user_data.get("state", "")
            content["exporter"] = exporter
        
        # Fill destination
        if report_data:
            destination = report_data.get("destination_country", "")
            if destination:
                content["consignee"]["country"] = destination
                content["transport_details"]["country_of_destination"] = destination
        
        return content

    
    def _validate_document(
        self,
        document_type: DocumentType,
        content: Dict[str, Any],
        report_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate document for compliance using DocumentValidator service.
        
        Performs comprehensive AI validation checks including:
        - Port code mismatch detection
        - Invoice format validation
        - GST vs Shipping Bill matching
        - RMS risk trigger detection
        - AWS Comprehend compliance text validation
        - Mandatory field validation
        
        Args:
            document_type: Type of document
            content: Document content
            report_data: Report data for cross-validation
            
        Returns:
            ValidationResult with errors and warnings
            
        Requirements: 4.3, 4.4, 4.8
        """
        logger.info(f"Validating document using DocumentValidator: {document_type}")
        
        # Use DocumentValidator service for comprehensive validation
        validation_result = self.document_validator.validate(
            document=content,
            document_type=document_type
        )
        
        # Add any additional document-specific validations
        additional_errors = []
        additional_warnings = []
        
        # Document-specific validations
        if document_type == DocumentType.COMMERCIAL_INVOICE:
            additional_errors.extend(self._validate_commercial_invoice(content, report_data))
        elif document_type == DocumentType.SHIPPING_BILL:
            additional_errors.extend(self._validate_shipping_bill(content, report_data))
        elif document_type == DocumentType.GST_LUT:
            additional_errors.extend(self._validate_gst_lut(content))
        
        # Combine results
        all_errors = validation_result.errors + additional_errors
        all_warnings = validation_result.warnings + additional_warnings
        
        is_valid = len(all_errors) == 0
        
        logger.info(f"Validation complete: is_valid={is_valid}, errors={len(all_errors)}, warnings={len(all_warnings)}")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings
        )
    
    def _validate_required_fields(
        self,
        document_type: DocumentType,
        content: Dict[str, Any]
    ) -> List[ValidationError]:
        """Validate that required fields are filled."""
        errors = []
        
        # Define required fields per document type
        required_fields = {
            DocumentType.COMMERCIAL_INVOICE: [
                ("invoice_number", "Invoice number is required"),
                ("invoice_date", "Invoice date is required"),
                ("exporter.name", "Exporter name is required"),
                ("consignee.name", "Consignee name is required")
            ],
            DocumentType.PACKING_LIST: [
                ("packing_list_number", "Packing list number is required"),
                ("date", "Date is required"),
                ("exporter.name", "Exporter name is required")
            ],
            DocumentType.SHIPPING_BILL: [
                ("shipping_bill_number", "Shipping bill number is required"),
                ("exporter.iec_code", "IEC code is required"),
                ("exporter.gstin", "GSTIN is required")
            ],
            DocumentType.GST_LUT: [
                ("exporter.gstin", "GSTIN is required"),
                ("exporter.pan", "PAN is required"),
                ("financial_year", "Financial year is required")
            ],
            DocumentType.SOFTEX: [
                ("softex_number", "SOFTEX number is required"),
                ("exporter.iec_code", "IEC code is required"),
                ("service_details.description", "Service description is required")
            ],
            DocumentType.CERTIFICATE_OF_ORIGIN: [
                ("certificate_number", "Certificate number is required"),
                ("exporter.name", "Exporter name is required")
            ]
        }
        
        fields = required_fields.get(document_type, [])
        for field_path, message in fields:
            if not self._get_nested_value(content, field_path):
                errors.append(ValidationError(
                    field=field_path,
                    message=message,
                    severity=ValidationSeverity.ERROR,
                    suggestion=f"Please provide {field_path}"
                ))
        
        return errors

    
    def _validate_commercial_invoice(
        self,
        content: Dict[str, Any],
        report_data: Dict[str, Any]
    ) -> List[ValidationError]:
        """Validate commercial invoice specific fields."""
        errors = []
        
        # Validate GSTIN format (15 characters)
        gstin = content.get("exporter", {}).get("gstin", "")
        if gstin and len(gstin) != 15:
            errors.append(ValidationError(
                field="exporter.gstin",
                message="GSTIN must be 15 characters",
                severity=ValidationSeverity.ERROR,
                suggestion="Verify GSTIN format: 2 digits (state) + 10 digits (PAN) + 1 digit (entity) + 1 letter (Z) + 1 check digit"
            ))
        
        # Validate IEC code format (10 characters)
        iec = content.get("exporter", {}).get("iec_code", "")
        if iec and len(iec) != 10:
            errors.append(ValidationError(
                field="exporter.iec_code",
                message="IEC code must be 10 characters",
                severity=ValidationSeverity.ERROR,
                suggestion="Verify IEC code format"
            ))
        
        # Validate totals
        totals = content.get("totals", {})
        if totals.get("total", 0) <= 0:
            errors.append(ValidationError(
                field="totals.total",
                message="Invoice total must be greater than zero",
                severity=ValidationSeverity.ERROR,
                suggestion="Add items to the invoice"
            ))
        
        return errors
    
    def _validate_shipping_bill(
        self,
        content: Dict[str, Any],
        report_data: Dict[str, Any]
    ) -> List[ValidationError]:
        """Validate shipping bill specific fields."""
        errors = []
        
        # Validate IEC code
        iec = content.get("exporter", {}).get("iec_code", "")
        if not iec or len(iec) != 10:
            errors.append(ValidationError(
                field="exporter.iec_code",
                message="Valid IEC code is required for shipping bill",
                severity=ValidationSeverity.ERROR,
                suggestion="IEC code must be 10 characters"
            ))
        
        # Validate GSTIN
        gstin = content.get("exporter", {}).get("gstin", "")
        if not gstin or len(gstin) != 15:
            errors.append(ValidationError(
                field="exporter.gstin",
                message="Valid GSTIN is required for shipping bill",
                severity=ValidationSeverity.ERROR,
                suggestion="GSTIN must be 15 characters"
            ))
        
        return errors
    
    def _validate_gst_lut(
        self,
        content: Dict[str, Any]
    ) -> List[ValidationError]:
        """Validate GST LUT specific fields."""
        errors = []
        
        # Validate GSTIN
        gstin = content.get("exporter", {}).get("gstin", "")
        if not gstin or len(gstin) != 15:
            errors.append(ValidationError(
                field="exporter.gstin",
                message="Valid GSTIN is required for LUT",
                severity=ValidationSeverity.ERROR,
                suggestion="GSTIN must be 15 characters"
            ))
        
        # Validate PAN
        pan = content.get("exporter", {}).get("pan", "")
        if not pan or len(pan) != 10:
            errors.append(ValidationError(
                field="exporter.pan",
                message="Valid PAN is required for LUT",
                severity=ValidationSeverity.ERROR,
                suggestion="PAN must be 10 characters"
            ))
        
        return errors

    
    def _validate_port_codes(
        self,
        content: Dict[str, Any]
    ) -> List[ValidationError]:
        """Validate port codes match destination country."""
        errors = []
        
        # Get port of discharge and destination country
        port_of_discharge = None
        destination_country = None
        
        # Extract from different document structures
        if "shipment_details" in content:
            port_of_discharge = content["shipment_details"].get("port_of_discharge", "")
            destination_country = content["shipment_details"].get("country_of_final_destination", "")
        elif "port_of_discharge" in content:
            port_of_discharge = content.get("port_of_discharge", "")
            destination_country = content.get("country_of_final_destination", "")
        
        if port_of_discharge and destination_country:
            # Basic port code validation (simplified)
            port_upper = port_of_discharge.upper()
            country_upper = destination_country.upper()
            
            # Check for obvious mismatches
            if "US" in country_upper or "UNITED STATES" in country_upper:
                if not any(code in port_upper for code in ["US", "NEW YORK", "LOS ANGELES", "MIAMI", "HOUSTON"]):
                    errors.append(ValidationError(
                        field="port_of_discharge",
                        message="Port code may not match destination country (USA)",
                        severity=ValidationSeverity.WARNING,
                        suggestion="Verify port code for USA destination"
                    ))
        
        return errors
    
    def _check_rms_triggers(
        self,
        content: Dict[str, Any]
    ) -> List[ValidationWarning]:
        """Check for RMS risk trigger keywords in product descriptions."""
        warnings = []
        
        # RMS trigger keywords (simplified list)
        trigger_keywords = [
            "chemical", "drug", "medicine", "pharmaceutical",
            "weapon", "explosive", "radioactive", "hazardous",
            "dual-use", "military", "restricted"
        ]
        
        # Check product descriptions in items
        items = content.get("items", [])
        for i, item in enumerate(items):
            description = item.get("description", "").lower()
            for keyword in trigger_keywords:
                if keyword in description:
                    warnings.append(ValidationWarning(
                        field=f"items[{i}].description",
                        message=f"Product description contains potential RMS trigger keyword: '{keyword}'",
                        suggestion="Consider using more specific terminology or be prepared for customs inspection"
                    ))
                    break  # Only warn once per item
        
        return warnings
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested dictionary value using dot notation."""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    
    def _generate_pdf(
        self,
        document_id: str,
        content: Dict[str, Any],
        document_type: DocumentType
    ) -> str:
        """
        Generate PDF version of document.
        
        In production, this would use a PDF generation library like ReportLab
        or WeasyPrint. For MVP, we return a placeholder URL.
        
        Args:
            document_id: Document ID
            content: Document content
            document_type: Type of document
            
        Returns:
            URL to PDF file
        """
        # MVP: Return placeholder URL
        # In production: Generate actual PDF and upload to S3
        pdf_url = f"https://exportsathi-docs.s3.amazonaws.com/{document_id}.pdf"
        
        logger.info(f"PDF generated (placeholder): {pdf_url}")
        return pdf_url
    
    def _generate_editable(
        self,
        document_id: str,
        content: Dict[str, Any],
        document_type: DocumentType
    ) -> str:
        """
        Generate editable version of document (DOCX/XLSX).
        
        In production, this would use python-docx or openpyxl.
        For MVP, we return a placeholder URL.
        
        Args:
            document_id: Document ID
            content: Document content
            document_type: Type of document
            
        Returns:
            URL to editable file
        """
        # MVP: Return placeholder URL
        # In production: Generate actual DOCX/XLSX and upload to S3
        editable_url = f"https://exportsathi-docs.s3.amazonaws.com/{document_id}.docx"
        
        logger.info(f"Editable document generated (placeholder): {editable_url}")
        return editable_url


# Global singleton instance
_document_generator: Optional[DocumentGenerator] = None


def get_document_generator(
    compliance_analyzer: Optional[ComplianceTextAnalyzer] = None
) -> DocumentGenerator:
    """
    Get the global document generator instance.
    
    Returns:
        Global DocumentGenerator instance
    """
    global _document_generator
    if _document_generator is None:
        _document_generator = DocumentGenerator(
            compliance_analyzer=compliance_analyzer
        )
    return _document_generator
