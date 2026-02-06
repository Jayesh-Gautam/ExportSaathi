"""
ComplianceTextAnalyzer Service for ExportSathi

This module provides compliance text analysis capabilities using AWS Comprehend.
It extracts entities, key phrases, and validates compliance-related content from
regulatory documents and export documentation.

Requirements: 12.5
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from config import settings


logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Common entity types in compliance documents"""
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DATE = "DATE"
    QUANTITY = "QUANTITY"
    COMMERCIAL_ITEM = "COMMERCIAL_ITEM"
    PERSON = "PERSON"
    EVENT = "EVENT"
    TITLE = "TITLE"
    OTHER = "OTHER"


class SentimentType(str, Enum):
    """Sentiment types"""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"


@dataclass
class Entity:
    """
    Extracted entity from text
    
    Attributes:
        text: The entity text
        type: Entity type (ORGANIZATION, LOCATION, etc.)
        score: Confidence score (0-1)
        begin_offset: Start position in text
        end_offset: End position in text
    """
    text: str
    type: str
    score: float
    begin_offset: int
    end_offset: int


@dataclass
class KeyPhrase:
    """
    Extracted key phrase from text
    
    Attributes:
        text: The key phrase text
        score: Confidence score (0-1)
        begin_offset: Start position in text
        end_offset: End position in text
    """
    text: str
    score: float
    begin_offset: int
    end_offset: int


@dataclass
class ComplianceTerms:
    """
    Extracted compliance-related terms
    
    Attributes:
        certifications: List of certification names (FDA, CE, REACH, etc.)
        regulations: List of regulation references
        standards: List of standard references (ISO, etc.)
        restricted_substances: List of restricted substance names
        countries: List of country names
        organizations: List of organization names
    """
    certifications: List[str]
    regulations: List[str]
    standards: List[str]
    restricted_substances: List[str]
    countries: List[str]
    organizations: List[str]


@dataclass
class DocumentValidation:
    """
    Document validation result
    
    Attributes:
        is_valid: Whether document passes validation
        compliance_score: Overall compliance score (0-100)
        detected_issues: List of detected compliance issues
        missing_terms: List of expected terms not found
        suggestions: List of improvement suggestions
        entities: List of extracted entities
        key_phrases: List of extracted key phrases
    """
    is_valid: bool
    compliance_score: float
    detected_issues: List[str]
    missing_terms: List[str]
    suggestions: List[str]
    entities: List[Entity]
    key_phrases: List[KeyPhrase]


class ComplianceTextAnalyzer:
    """
    Compliance text analysis service using AWS Comprehend
    
    Provides capabilities for:
    - Entity extraction for compliance terms (certifications, regulations, substances)
    - Key phrase extraction from regulatory documents
    - Document validation for compliance requirements
    - Sentiment analysis for risk assessment
    
    Requirements: 12.5
    """
    
    def __init__(
        self,
        region_name: Optional[str] = None,
        language_code: str = "en"
    ):
        """
        Initialize ComplianceTextAnalyzer
        
        Args:
            region_name: AWS region (defaults to settings)
            language_code: Language code for text analysis (default: "en")
        """
        self.region_name = region_name or settings.AWS_REGION
        self.language_code = language_code
        self.comprehend_enabled = settings.COMPREHEND_ENABLED
        
        # Initialize AWS Comprehend client
        if self.comprehend_enabled:
            try:
                self.comprehend_client = boto3.client(
                    'comprehend',
                    region_name=self.region_name,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None
                )
                logger.info(f"Initialized Comprehend client in region {self.region_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Comprehend client: {e}")
                self.comprehend_enabled = False
                self.comprehend_client = None
        else:
            self.comprehend_client = None
            logger.warning("Comprehend is disabled in configuration")
        
        # Compliance-related keywords for filtering
        self.certification_keywords = [
            'fda', 'ce', 'reach', 'bis', 'zed', 'softex', 'iso', 'haccp',
            'gmp', 'fssai', 'halal', 'kosher', 'organic', 'epa', 'rohs'
        ]
        
        self.regulation_keywords = [
            'dgft', 'customs', 'gst', 'igst', 'rodtep', 'meis', 'seis',
            'regulation', 'directive', 'act', 'rule', 'policy', 'schedule'
        ]
        
        self.restricted_substance_keywords = [
            'lead', 'mercury', 'cadmium', 'arsenic', 'pesticide', 'antibiotic',
            'hormone', 'preservative', 'additive', 'colorant', 'banned', 'prohibited'
        ]
    
    def extract_entities(
        self,
        text: str,
        filter_types: Optional[List[str]] = None
    ) -> List[Entity]:
        """
        Extract entities from text using AWS Comprehend
        
        Args:
            text: Input text to analyze
            filter_types: Optional list of entity types to filter (e.g., ["ORGANIZATION", "LOCATION"])
            
        Returns:
            List of Entity objects
            
        Raises:
            ValueError: If Comprehend is disabled or text is invalid
            ClientError: If AWS Comprehend API call fails
            
        Requirements: 12.5
        """
        if not self.comprehend_enabled or not self.comprehend_client:
            logger.warning("Comprehend is disabled, returning empty entities")
            return []
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # AWS Comprehend has a 5000 byte limit for detect_entities
        if len(text.encode('utf-8')) > 5000:
            logger.warning(f"Text too long ({len(text)} chars), truncating to 5000 bytes")
            # Truncate to approximately 5000 bytes (conservative estimate)
            text = text[:4000]
        
        try:
            # Call Comprehend detect_entities API
            response = self.comprehend_client.detect_entities(
                Text=text,
                LanguageCode=self.language_code
            )
            
            # Parse entities
            entities = []
            for entity_data in response.get('Entities', []):
                entity = Entity(
                    text=entity_data.get('Text', ''),
                    type=entity_data.get('Type', 'OTHER'),
                    score=entity_data.get('Score', 0.0),
                    begin_offset=entity_data.get('BeginOffset', 0),
                    end_offset=entity_data.get('EndOffset', 0)
                )
                
                # Apply filter if specified
                if filter_types is None or entity.type in filter_types:
                    entities.append(entity)
            
            logger.info(f"Extracted {len(entities)} entities from text")
            return entities
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Comprehend API error [{error_code}]: {error_message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during entity extraction: {e}")
            raise
    
    def extract_key_phrases(self, text: str) -> List[KeyPhrase]:
        """
        Extract key phrases from text using AWS Comprehend
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of KeyPhrase objects
            
        Raises:
            ValueError: If Comprehend is disabled or text is invalid
            ClientError: If AWS Comprehend API call fails
            
        Requirements: 12.5
        """
        if not self.comprehend_enabled or not self.comprehend_client:
            logger.warning("Comprehend is disabled, returning empty key phrases")
            return []
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # AWS Comprehend has a 5000 byte limit for detect_key_phrases
        if len(text.encode('utf-8')) > 5000:
            logger.warning(f"Text too long ({len(text)} chars), truncating to 5000 bytes")
            text = text[:4000]
        
        try:
            # Call Comprehend detect_key_phrases API
            response = self.comprehend_client.detect_key_phrases(
                Text=text,
                LanguageCode=self.language_code
            )
            
            # Parse key phrases
            key_phrases = []
            for phrase_data in response.get('KeyPhrases', []):
                key_phrase = KeyPhrase(
                    text=phrase_data.get('Text', ''),
                    score=phrase_data.get('Score', 0.0),
                    begin_offset=phrase_data.get('BeginOffset', 0),
                    end_offset=phrase_data.get('EndOffset', 0)
                )
                key_phrases.append(key_phrase)
            
            logger.info(f"Extracted {len(key_phrases)} key phrases from text")
            return key_phrases
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Comprehend API error [{error_code}]: {error_message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during key phrase extraction: {e}")
            raise
    
    def extract_compliance_terms(self, text: str) -> ComplianceTerms:
        """
        Extract compliance-related terms from text
        
        Combines entity extraction and key phrase extraction to identify:
        - Certifications (FDA, CE, REACH, etc.)
        - Regulations and standards
        - Restricted substances
        - Countries and organizations
        
        Args:
            text: Input text to analyze
            
        Returns:
            ComplianceTerms object with categorized terms
            
        Requirements: 12.5
        """
        if not self.comprehend_enabled or not self.comprehend_client:
            logger.warning("Comprehend is disabled, returning empty compliance terms")
            return ComplianceTerms(
                certifications=[],
                regulations=[],
                standards=[],
                restricted_substances=[],
                countries=[],
                organizations=[]
            )
        
        try:
            # Extract entities and key phrases
            entities = self.extract_entities(text)
            key_phrases = self.extract_key_phrases(text)
            
            # Categorize terms
            certifications = []
            regulations = []
            standards = []
            restricted_substances = []
            countries = []
            organizations = []
            
            # Process entities
            for entity in entities:
                entity_text_lower = entity.text.lower()
                
                if entity.type == "LOCATION":
                    countries.append(entity.text)
                elif entity.type == "ORGANIZATION":
                    organizations.append(entity.text)
                
                # Check for certifications
                for cert_keyword in self.certification_keywords:
                    if cert_keyword in entity_text_lower:
                        certifications.append(entity.text)
                        break
            
            # Process key phrases
            for phrase in key_phrases:
                phrase_text_lower = phrase.text.lower()
                
                # Check for certifications
                for cert_keyword in self.certification_keywords:
                    if cert_keyword in phrase_text_lower:
                        certifications.append(phrase.text)
                        break
                
                # Check for regulations
                for reg_keyword in self.regulation_keywords:
                    if reg_keyword in phrase_text_lower:
                        regulations.append(phrase.text)
                        break
                
                # Check for standards (ISO, etc.)
                if 'iso' in phrase_text_lower or 'standard' in phrase_text_lower:
                    standards.append(phrase.text)
                
                # Check for restricted substances
                for substance_keyword in self.restricted_substance_keywords:
                    if substance_keyword in phrase_text_lower:
                        restricted_substances.append(phrase.text)
                        break
            
            # Remove duplicates while preserving order
            certifications = list(dict.fromkeys(certifications))
            regulations = list(dict.fromkeys(regulations))
            standards = list(dict.fromkeys(standards))
            restricted_substances = list(dict.fromkeys(restricted_substances))
            countries = list(dict.fromkeys(countries))
            organizations = list(dict.fromkeys(organizations))
            
            logger.info(
                f"Extracted compliance terms: {len(certifications)} certifications, "
                f"{len(regulations)} regulations, {len(standards)} standards, "
                f"{len(restricted_substances)} restricted substances"
            )
            
            return ComplianceTerms(
                certifications=certifications,
                regulations=regulations,
                standards=standards,
                restricted_substances=restricted_substances,
                countries=countries,
                organizations=organizations
            )
            
        except Exception as e:
            logger.error(f"Error extracting compliance terms: {e}")
            # Return empty result on error
            return ComplianceTerms(
                certifications=[],
                regulations=[],
                standards=[],
                restricted_substances=[],
                countries=[],
                organizations=[]
            )
    
    def validate_document(
        self,
        text: str,
        required_terms: Optional[List[str]] = None,
        document_type: Optional[str] = None
    ) -> DocumentValidation:
        """
        Validate document for compliance requirements
        
        Checks for:
        - Presence of required compliance terms
        - Proper entity mentions (organizations, locations, dates)
        - Key phrase coverage
        - Overall compliance score
        
        Args:
            text: Document text to validate
            required_terms: Optional list of terms that must be present
            document_type: Optional document type for specific validation rules
            
        Returns:
            DocumentValidation object with validation results
            
        Requirements: 12.5
        """
        if not self.comprehend_enabled or not self.comprehend_client:
            logger.warning("Comprehend is disabled, returning default validation")
            return DocumentValidation(
                is_valid=True,
                compliance_score=0.0,
                detected_issues=[],
                missing_terms=[],
                suggestions=[],
                entities=[],
                key_phrases=[]
            )
        
        try:
            # Extract entities and key phrases
            entities = self.extract_entities(text)
            key_phrases = self.extract_key_phrases(text)
            
            detected_issues = []
            missing_terms = []
            suggestions = []
            
            # Check for required terms
            if required_terms:
                text_lower = text.lower()
                for term in required_terms:
                    if term.lower() not in text_lower:
                        missing_terms.append(term)
                        detected_issues.append(f"Required term '{term}' not found in document")
            
            # Validate based on document type
            if document_type:
                if document_type.lower() in ['invoice', 'commercial_invoice']:
                    # Check for essential invoice entities
                    has_organization = any(e.type == "ORGANIZATION" for e in entities)
                    has_date = any(e.type == "DATE" for e in entities)
                    has_quantity = any(e.type == "QUANTITY" for e in entities)
                    
                    if not has_organization:
                        detected_issues.append("No organization/company name detected")
                        suggestions.append("Ensure buyer and seller names are clearly mentioned")
                    
                    if not has_date:
                        detected_issues.append("No date detected")
                        suggestions.append("Include invoice date and shipment date")
                    
                    if not has_quantity:
                        detected_issues.append("No quantity information detected")
                        suggestions.append("Include product quantities and values")
                
                elif document_type.lower() in ['certificate', 'certification']:
                    # Check for certification-specific terms
                    has_cert_terms = any(
                        any(keyword in phrase.text.lower() for keyword in self.certification_keywords)
                        for phrase in key_phrases
                    )
                    
                    if not has_cert_terms:
                        detected_issues.append("No certification terms detected")
                        suggestions.append("Ensure certification type and standards are mentioned")
            
            # Calculate compliance score
            # Base score starts at 100, deduct points for issues
            compliance_score = 100.0
            
            # Deduct for missing required terms
            if required_terms:
                missing_ratio = len(missing_terms) / len(required_terms)
                compliance_score -= missing_ratio * 30  # Up to 30 points
            
            # Deduct for detected issues
            compliance_score -= min(len(detected_issues) * 10, 40)  # Up to 40 points
            
            # Bonus for good entity coverage
            if len(entities) >= 5:
                compliance_score += 10
            
            # Bonus for good key phrase coverage
            if len(key_phrases) >= 10:
                compliance_score += 10
            
            # Ensure score is in valid range
            compliance_score = max(0.0, min(100.0, compliance_score))
            
            # Determine if valid (score >= 70)
            is_valid = compliance_score >= 70.0 and len(missing_terms) == 0
            
            logger.info(
                f"Document validation: score={compliance_score:.1f}, "
                f"issues={len(detected_issues)}, missing_terms={len(missing_terms)}"
            )
            
            return DocumentValidation(
                is_valid=is_valid,
                compliance_score=compliance_score,
                detected_issues=detected_issues,
                missing_terms=missing_terms,
                suggestions=suggestions,
                entities=entities,
                key_phrases=key_phrases
            )
            
        except Exception as e:
            logger.error(f"Error validating document: {e}")
            # Return failed validation on error
            return DocumentValidation(
                is_valid=False,
                compliance_score=0.0,
                detected_issues=[f"Validation error: {str(e)}"],
                missing_terms=[],
                suggestions=["Please check document format and try again"],
                entities=[],
                key_phrases=[]
            )
    
    def detect_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Detect sentiment in text (useful for analyzing rejection reasons, feedback)
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with sentiment type and scores
            
        Requirements: 12.5
        """
        if not self.comprehend_enabled or not self.comprehend_client:
            logger.warning("Comprehend is disabled, returning neutral sentiment")
            return {
                'sentiment': 'NEUTRAL',
                'scores': {
                    'positive': 0.0,
                    'negative': 0.0,
                    'neutral': 1.0,
                    'mixed': 0.0
                }
            }
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # AWS Comprehend has a 5000 byte limit
        if len(text.encode('utf-8')) > 5000:
            text = text[:4000]
        
        try:
            response = self.comprehend_client.detect_sentiment(
                Text=text,
                LanguageCode=self.language_code
            )
            
            sentiment = response.get('Sentiment', 'NEUTRAL')
            sentiment_scores = response.get('SentimentScore', {})
            
            return {
                'sentiment': sentiment,
                'scores': {
                    'positive': sentiment_scores.get('Positive', 0.0),
                    'negative': sentiment_scores.get('Negative', 0.0),
                    'neutral': sentiment_scores.get('Neutral', 0.0),
                    'mixed': sentiment_scores.get('Mixed', 0.0)
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Comprehend API error [{error_code}]: {error_message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during sentiment detection: {e}")
            raise


# Convenience functions

def extract_entities_from_text(text: str, filter_types: Optional[List[str]] = None) -> List[Entity]:
    """
    Convenience function to extract entities from text
    
    Args:
        text: Input text
        filter_types: Optional entity types to filter
        
    Returns:
        List of Entity objects
    """
    analyzer = ComplianceTextAnalyzer()
    return analyzer.extract_entities(text, filter_types)


def extract_key_phrases_from_text(text: str) -> List[KeyPhrase]:
    """
    Convenience function to extract key phrases from text
    
    Args:
        text: Input text
        
    Returns:
        List of KeyPhrase objects
    """
    analyzer = ComplianceTextAnalyzer()
    return analyzer.extract_key_phrases(text)


def extract_compliance_terms_from_text(text: str) -> ComplianceTerms:
    """
    Convenience function to extract compliance terms from text
    
    Args:
        text: Input text
        
    Returns:
        ComplianceTerms object
    """
    analyzer = ComplianceTextAnalyzer()
    return analyzer.extract_compliance_terms(text)


def validate_compliance_document(
    text: str,
    required_terms: Optional[List[str]] = None,
    document_type: Optional[str] = None
) -> DocumentValidation:
    """
    Convenience function to validate compliance document
    
    Args:
        text: Document text
        required_terms: Optional required terms
        document_type: Optional document type
        
    Returns:
        DocumentValidation object
    """
    analyzer = ComplianceTextAnalyzer()
    return analyzer.validate_document(text, required_terms, document_type)
