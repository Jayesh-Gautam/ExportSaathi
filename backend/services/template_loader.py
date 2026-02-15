"""
Template Loader for Export Documents

Loads and manages India-specific document templates from JSON files.
Provides template validation and metadata extraction.

Requirements: 4.2, 4.6
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from models.enums import DocumentType

logger = logging.getLogger(__name__)


class TemplateLoader:
    """
    Loads and manages document templates from JSON files.
    
    Features:
    - Load templates from JSON files
    - Extract template metadata
    - Validate template structure
    - Cache loaded templates for performance
    
    Requirements: 4.2, 4.6
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template loader.
        
        Args:
            templates_dir: Directory containing template JSON files (defaults to ./templates)
        """
        if templates_dir is None:
            # Default to templates directory relative to this file
            templates_dir = Path(__file__).parent / "templates"
        
        self.templates_dir = Path(templates_dir)
        self._template_cache: Dict[DocumentType, Dict[str, Any]] = {}
        
        # Template file mapping
        self.template_files = {
            DocumentType.COMMERCIAL_INVOICE: "commercial_invoice.json",
            DocumentType.PACKING_LIST: "packing_list.json",
            DocumentType.SHIPPING_BILL: "shipping_bill.json",
            DocumentType.GST_LUT: "gst_lut.json",
            DocumentType.SOFTEX: "softex.json",
            DocumentType.CERTIFICATE_OF_ORIGIN: "certificate_of_origin.json"
        }
        
        logger.info(f"TemplateLoader initialized with templates_dir: {self.templates_dir}")
    
    def load_template(self, document_type: DocumentType) -> Dict[str, Any]:
        """
        Load template for specified document type.
        
        Args:
            document_type: Type of document
            
        Returns:
            Template dictionary
            
        Raises:
            FileNotFoundError: If template file not found
            ValueError: If template is invalid
        """
        # Check cache first
        if document_type in self._template_cache:
            logger.debug(f"Returning cached template for {document_type}")
            return self._template_cache[document_type].copy()
        
        # Get template filename
        filename = self.template_files.get(document_type)
        if not filename:
            raise ValueError(f"No template file defined for document type: {document_type}")
        
        # Load template from file
        template_path = self.templates_dir / filename
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        logger.info(f"Loading template from {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            # Validate template structure
            self._validate_template(template, document_type)
            
            # Cache template
            self._template_cache[document_type] = template
            
            logger.info(f"Template loaded successfully for {document_type}")
            return template.copy()
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in template file {template_path}: {e}")
            raise ValueError(f"Invalid JSON in template file: {e}")
        except Exception as e:
            logger.error(f"Error loading template {template_path}: {e}")
            raise
    
    def get_template_info(self, document_type: DocumentType) -> Dict[str, Any]:
        """
        Get template metadata without loading full template.
        
        Args:
            document_type: Type of document
            
        Returns:
            Template info dictionary
        """
        template = self.load_template(document_type)
        return template.get("_template_info", {})
    
    def get_mandatory_fields(self, document_type: DocumentType) -> List[str]:
        """
        Get list of mandatory fields for document type.
        
        Args:
            document_type: Type of document
            
        Returns:
            List of mandatory field paths (dot notation)
        """
        template_info = self.get_template_info(document_type)
        return template_info.get("mandatory_fields", [])
    
    def get_template_version(self, document_type: DocumentType) -> str:
        """
        Get template version.
        
        Args:
            document_type: Type of document
            
        Returns:
            Version string
        """
        template_info = self.get_template_info(document_type)
        return template_info.get("version", "unknown")
    
    def get_compliance_info(self, document_type: DocumentType) -> str:
        """
        Get compliance information for template.
        
        Args:
            document_type: Type of document
            
        Returns:
            Compliance information string
        """
        template_info = self.get_template_info(document_type)
        return template_info.get("compliance", "")
    
    def list_available_templates(self) -> List[DocumentType]:
        """
        List all available document templates.
        
        Returns:
            List of document types with available templates
        """
        available = []
        for doc_type, filename in self.template_files.items():
            template_path = self.templates_dir / filename
            if template_path.exists():
                available.append(doc_type)
        return available
    
    def _validate_template(self, template: Dict[str, Any], document_type: DocumentType) -> None:
        """
        Validate template structure.
        
        Args:
            template: Template dictionary
            document_type: Type of document
            
        Raises:
            ValueError: If template is invalid
        """
        # Check for _template_info
        if "_template_info" not in template:
            raise ValueError(f"Template missing _template_info section: {document_type}")
        
        template_info = template["_template_info"]
        
        # Check required metadata fields
        required_metadata = ["name", "version", "compliance", "description", "mandatory_fields"]
        for field in required_metadata:
            if field not in template_info:
                logger.warning(f"Template {document_type} missing metadata field: {field}")
        
        # Validate mandatory_fields is a list
        if "mandatory_fields" in template_info:
            if not isinstance(template_info["mandatory_fields"], list):
                raise ValueError(f"Template {document_type}: mandatory_fields must be a list")
        
        logger.debug(f"Template validation passed for {document_type}")
    
    def clear_cache(self) -> None:
        """Clear template cache."""
        self._template_cache.clear()
        logger.info("Template cache cleared")
    
    def reload_template(self, document_type: DocumentType) -> Dict[str, Any]:
        """
        Reload template from file (bypass cache).
        
        Args:
            document_type: Type of document
            
        Returns:
            Reloaded template dictionary
        """
        # Remove from cache
        if document_type in self._template_cache:
            del self._template_cache[document_type]
        
        # Load fresh from file
        return self.load_template(document_type)


# Global singleton instance
_template_loader: Optional[TemplateLoader] = None


def get_template_loader(templates_dir: Optional[Path] = None) -> TemplateLoader:
    """
    Get the global template loader instance.
    
    Args:
        templates_dir: Optional custom templates directory
        
    Returns:
        Global TemplateLoader instance
    """
    global _template_loader
    if _template_loader is None:
        _template_loader = TemplateLoader(templates_dir=templates_dir)
    return _template_loader
