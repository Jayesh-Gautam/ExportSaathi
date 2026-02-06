"""
Unit tests for ComplianceTextAnalyzer service

Tests entity extraction, key phrase extraction, compliance term extraction,
and document validation capabilities.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from compliance_text_analyzer import (
    ComplianceTextAnalyzer,
    Entity,
    KeyPhrase,
    ComplianceTerms,
    DocumentValidation,
    extract_entities_from_text,
    extract_key_phrases_from_text,
    extract_compliance_terms_from_text,
    validate_compliance_document
)


@pytest.fixture
def mock_comprehend_client():
    """Create a mock Comprehend client"""
    with patch('compliance_text_analyzer.boto3.client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def analyzer(mock_comprehend_client):
    """Create ComplianceTextAnalyzer instance with mocked client"""
    with patch('compliance_text_analyzer.settings') as mock_settings:
        mock_settings.AWS_REGION = 'us-east-1'
        mock_settings.AWS_ACCESS_KEY_ID = 'test-key'
        mock_settings.AWS_SECRET_ACCESS_KEY = 'test-secret'
        mock_settings.COMPREHEND_ENABLED = True
        
        analyzer = ComplianceTextAnalyzer()
        analyzer.comprehend_client = mock_comprehend_client
        return analyzer


class TestComplianceTextAnalyzer:
    """Test suite for ComplianceTextAnalyzer"""
    
    def test_initialization_with_comprehend_enabled(self, mock_comprehend_client):
        """Test analyzer initializes correctly when Comprehend is enabled"""
        with patch('compliance_text_analyzer.settings') as mock_settings:
            mock_settings.AWS_REGION = 'us-east-1'
            mock_settings.COMPREHEND_ENABLED = True
            mock_settings.AWS_ACCESS_KEY_ID = None
            mock_settings.AWS_SECRET_ACCESS_KEY = None
            
            analyzer = ComplianceTextAnalyzer()
            
            assert analyzer.comprehend_enabled is True
            assert analyzer.region_name == 'us-east-1'
            assert analyzer.language_code == 'en'
    
    def test_initialization_with_comprehend_disabled(self):
        """Test analyzer handles disabled Comprehend gracefully"""
        with patch('compliance_text_analyzer.settings') as mock_settings:
            mock_settings.COMPREHEND_ENABLED = False
            mock_settings.AWS_REGION = 'us-east-1'
            
            analyzer = ComplianceTextAnalyzer()
            
            assert analyzer.comprehend_enabled is False
            assert analyzer.comprehend_client is None
    
    def test_extract_entities_success(self, analyzer, mock_comprehend_client):
        """Test successful entity extraction"""
        # Mock Comprehend response
        mock_comprehend_client.detect_entities.return_value = {
            'Entities': [
                {
                    'Text': 'FDA',
                    'Type': 'ORGANIZATION',
                    'Score': 0.95,
                    'BeginOffset': 0,
                    'EndOffset': 3
                },
                {
                    'Text': 'United States',
                    'Type': 'LOCATION',
                    'Score': 0.98,
                    'BeginOffset': 20,
                    'EndOffset': 33
                },
                {
                    'Text': 'January 2024',
                    'Type': 'DATE',
                    'Score': 0.92,
                    'BeginOffset': 50,
                    'EndOffset': 62
                }
            ]
        }
        
        text = "FDA approval required for United States export in January 2024"
        entities = analyzer.extract_entities(text)
        
        assert len(entities) == 3
        assert entities[0].text == 'FDA'
        assert entities[0].type == 'ORGANIZATION'
        assert entities[0].score == 0.95
        assert entities[1].text == 'United States'
        assert entities[1].type == 'LOCATION'
        
        mock_comprehend_client.detect_entities.assert_called_once_with(
            Text=text,
            LanguageCode='en'
        )
    
    def test_extract_entities_with_filter(self, analyzer, mock_comprehend_client):
        """Test entity extraction with type filtering"""
        mock_comprehend_client.detect_entities.return_value = {
            'Entities': [
                {'Text': 'FDA', 'Type': 'ORGANIZATION', 'Score': 0.95, 'BeginOffset': 0, 'EndOffset': 3},
                {'Text': 'United States', 'Type': 'LOCATION', 'Score': 0.98, 'BeginOffset': 20, 'EndOffset': 33},
                {'Text': 'January 2024', 'Type': 'DATE', 'Score': 0.92, 'BeginOffset': 50, 'EndOffset': 62}
            ]
        }
        
        text = "FDA approval required for United States export in January 2024"
        entities = analyzer.extract_entities(text, filter_types=['ORGANIZATION', 'LOCATION'])
        
        assert len(entities) == 2
        assert all(e.type in ['ORGANIZATION', 'LOCATION'] for e in entities)
    
    def test_extract_entities_empty_text(self, analyzer):
        """Test entity extraction with empty text raises ValueError"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            analyzer.extract_entities("")
    
    def test_extract_entities_long_text_truncation(self, analyzer, mock_comprehend_client):
        """Test entity extraction truncates long text"""
        mock_comprehend_client.detect_entities.return_value = {'Entities': []}
        
        # Create text longer than 5000 bytes
        long_text = "A" * 6000
        analyzer.extract_entities(long_text)
        
        # Verify truncation occurred
        call_args = mock_comprehend_client.detect_entities.call_args
        assert len(call_args[1]['Text']) < 5000
    
    def test_extract_entities_api_error(self, analyzer, mock_comprehend_client):
        """Test entity extraction handles API errors"""
        mock_comprehend_client.detect_entities.side_effect = ClientError(
            {'Error': {'Code': 'InvalidRequestException', 'Message': 'Invalid request'}},
            'detect_entities'
        )
        
        with pytest.raises(ClientError):
            analyzer.extract_entities("Test text")
    
    def test_extract_entities_disabled_comprehend(self):
        """Test entity extraction returns empty list when Comprehend is disabled"""
        with patch('compliance_text_analyzer.settings') as mock_settings:
            mock_settings.COMPREHEND_ENABLED = False
            mock_settings.AWS_REGION = 'us-east-1'
            
            analyzer = ComplianceTextAnalyzer()
            entities = analyzer.extract_entities("Test text")
            
            assert entities == []
    
    def test_extract_key_phrases_success(self, analyzer, mock_comprehend_client):
        """Test successful key phrase extraction"""
        mock_comprehend_client.detect_key_phrases.return_value = {
            'KeyPhrases': [
                {
                    'Text': 'FDA approval',
                    'Score': 0.95,
                    'BeginOffset': 0,
                    'EndOffset': 12
                },
                {
                    'Text': 'export compliance',
                    'Score': 0.92,
                    'BeginOffset': 30,
                    'EndOffset': 47
                },
                {
                    'Text': 'regulatory requirements',
                    'Score': 0.88,
                    'BeginOffset': 60,
                    'EndOffset': 83
                }
            ]
        }
        
        text = "FDA approval is required for export compliance with regulatory requirements"
        key_phrases = analyzer.extract_key_phrases(text)
        
        assert len(key_phrases) == 3
        assert key_phrases[0].text == 'FDA approval'
        assert key_phrases[0].score == 0.95
        assert key_phrases[1].text == 'export compliance'
        
        mock_comprehend_client.detect_key_phrases.assert_called_once_with(
            Text=text,
            LanguageCode='en'
        )
    
    def test_extract_key_phrases_empty_text(self, analyzer):
        """Test key phrase extraction with empty text raises ValueError"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            analyzer.extract_key_phrases("")
    
    def test_extract_key_phrases_disabled_comprehend(self):
        """Test key phrase extraction returns empty list when Comprehend is disabled"""
        with patch('compliance_text_analyzer.settings') as mock_settings:
            mock_settings.COMPREHEND_ENABLED = False
            mock_settings.AWS_REGION = 'us-east-1'
            
            analyzer = ComplianceTextAnalyzer()
            key_phrases = analyzer.extract_key_phrases("Test text")
            
            assert key_phrases == []
    
    def test_extract_compliance_terms_success(self, analyzer, mock_comprehend_client):
        """Test successful compliance terms extraction"""
        # Mock entity extraction
        mock_comprehend_client.detect_entities.return_value = {
            'Entities': [
                {'Text': 'FDA', 'Type': 'ORGANIZATION', 'Score': 0.95, 'BeginOffset': 0, 'EndOffset': 3},
                {'Text': 'United States', 'Type': 'LOCATION', 'Score': 0.98, 'BeginOffset': 20, 'EndOffset': 33},
                {'Text': 'DGFT', 'Type': 'ORGANIZATION', 'Score': 0.90, 'BeginOffset': 50, 'EndOffset': 54}
            ]
        }
        
        # Mock key phrase extraction
        mock_comprehend_client.detect_key_phrases.return_value = {
            'KeyPhrases': [
                {'Text': 'FDA approval', 'Score': 0.95, 'BeginOffset': 0, 'EndOffset': 12},
                {'Text': 'CE marking', 'Score': 0.92, 'BeginOffset': 20, 'EndOffset': 30},
                {'Text': 'REACH regulation', 'Score': 0.88, 'BeginOffset': 40, 'EndOffset': 56},
                {'Text': 'ISO 9001 standard', 'Score': 0.85, 'BeginOffset': 60, 'EndOffset': 77},
                {'Text': 'lead content', 'Score': 0.80, 'BeginOffset': 80, 'EndOffset': 92}
            ]
        }
        
        text = "FDA approval and CE marking required. REACH regulation and ISO 9001 standard apply. Check lead content."
        compliance_terms = analyzer.extract_compliance_terms(text)
        
        assert isinstance(compliance_terms, ComplianceTerms)
        assert 'FDA' in compliance_terms.certifications or 'FDA approval' in compliance_terms.certifications
        assert 'CE marking' in compliance_terms.certifications
        assert len(compliance_terms.countries) > 0
        assert len(compliance_terms.organizations) > 0
    
    def test_extract_compliance_terms_disabled_comprehend(self):
        """Test compliance terms extraction returns empty result when Comprehend is disabled"""
        with patch('compliance_text_analyzer.settings') as mock_settings:
            mock_settings.COMPREHEND_ENABLED = False
            mock_settings.AWS_REGION = 'us-east-1'
            
            analyzer = ComplianceTextAnalyzer()
            compliance_terms = analyzer.extract_compliance_terms("Test text")
            
            assert compliance_terms.certifications == []
            assert compliance_terms.regulations == []
            assert compliance_terms.standards == []
    
    def test_validate_document_success(self, analyzer, mock_comprehend_client):
        """Test successful document validation"""
        # Mock entity extraction
        mock_comprehend_client.detect_entities.return_value = {
            'Entities': [
                {'Text': 'Acme Corp', 'Type': 'ORGANIZATION', 'Score': 0.95, 'BeginOffset': 0, 'EndOffset': 9},
                {'Text': 'January 15, 2024', 'Type': 'DATE', 'Score': 0.92, 'BeginOffset': 20, 'EndOffset': 36},
                {'Text': '1000 units', 'Type': 'QUANTITY', 'Score': 0.88, 'BeginOffset': 50, 'EndOffset': 60}
            ]
        }
        
        # Mock key phrase extraction
        mock_comprehend_client.detect_key_phrases.return_value = {
            'KeyPhrases': [
                {'Text': 'commercial invoice', 'Score': 0.95, 'BeginOffset': 0, 'EndOffset': 18},
                {'Text': 'product description', 'Score': 0.90, 'BeginOffset': 30, 'EndOffset': 49},
                {'Text': 'total value', 'Score': 0.85, 'BeginOffset': 60, 'EndOffset': 71}
            ]
        }
        
        text = "Commercial invoice from Acme Corp dated January 15, 2024 for 1000 units"
        validation = analyzer.validate_document(text, document_type='invoice')
        
        assert isinstance(validation, DocumentValidation)
        assert validation.compliance_score >= 0
        assert validation.compliance_score <= 100
        assert len(validation.entities) > 0
        assert len(validation.key_phrases) > 0
    
    def test_validate_document_with_required_terms(self, analyzer, mock_comprehend_client):
        """Test document validation with required terms"""
        mock_comprehend_client.detect_entities.return_value = {'Entities': []}
        mock_comprehend_client.detect_key_phrases.return_value = {'KeyPhrases': []}
        
        text = "This document contains FDA approval information"
        required_terms = ['FDA', 'approval', 'certificate']
        
        validation = analyzer.validate_document(text, required_terms=required_terms)
        
        assert 'certificate' in validation.missing_terms
        assert len(validation.detected_issues) > 0
    
    def test_validate_document_invoice_type(self, analyzer, mock_comprehend_client):
        """Test document validation for invoice type"""
        # Mock with minimal entities (missing required ones)
        mock_comprehend_client.detect_entities.return_value = {
            'Entities': [
                {'Text': 'Test', 'Type': 'OTHER', 'Score': 0.5, 'BeginOffset': 0, 'EndOffset': 4}
            ]
        }
        mock_comprehend_client.detect_key_phrases.return_value = {'KeyPhrases': []}
        
        text = "Simple invoice text without proper entities"
        validation = analyzer.validate_document(text, document_type='invoice')
        
        # Should detect missing organization, date, quantity
        assert any('organization' in issue.lower() for issue in validation.detected_issues)
        assert len(validation.suggestions) > 0
    
    def test_validate_document_certification_type(self, analyzer, mock_comprehend_client):
        """Test document validation for certification type"""
        mock_comprehend_client.detect_entities.return_value = {'Entities': []}
        mock_comprehend_client.detect_key_phrases.return_value = {
            'KeyPhrases': [
                {'Text': 'test phrase', 'Score': 0.8, 'BeginOffset': 0, 'EndOffset': 11}
            ]
        }
        
        text = "Certificate document without certification terms"
        validation = analyzer.validate_document(text, document_type='certificate')
        
        # Should detect missing certification terms
        assert any('certification' in issue.lower() for issue in validation.detected_issues)
    
    def test_validate_document_disabled_comprehend(self):
        """Test document validation returns default result when Comprehend is disabled"""
        with patch('compliance_text_analyzer.settings') as mock_settings:
            mock_settings.COMPREHEND_ENABLED = False
            mock_settings.AWS_REGION = 'us-east-1'
            
            analyzer = ComplianceTextAnalyzer()
            validation = analyzer.validate_document("Test text")
            
            assert validation.is_valid is True
            assert validation.compliance_score == 0.0
            assert validation.entities == []
            assert validation.key_phrases == []
    
    def test_detect_sentiment_success(self, analyzer, mock_comprehend_client):
        """Test successful sentiment detection"""
        mock_comprehend_client.detect_sentiment.return_value = {
            'Sentiment': 'POSITIVE',
            'SentimentScore': {
                'Positive': 0.85,
                'Negative': 0.05,
                'Neutral': 0.08,
                'Mixed': 0.02
            }
        }
        
        text = "This is an excellent product with great quality"
        sentiment = analyzer.detect_sentiment(text)
        
        assert sentiment['sentiment'] == 'POSITIVE'
        assert sentiment['scores']['positive'] == 0.85
        assert sentiment['scores']['negative'] == 0.05
        
        mock_comprehend_client.detect_sentiment.assert_called_once_with(
            Text=text,
            LanguageCode='en'
        )
    
    def test_detect_sentiment_negative(self, analyzer, mock_comprehend_client):
        """Test sentiment detection for negative text"""
        mock_comprehend_client.detect_sentiment.return_value = {
            'Sentiment': 'NEGATIVE',
            'SentimentScore': {
                'Positive': 0.05,
                'Negative': 0.88,
                'Neutral': 0.05,
                'Mixed': 0.02
            }
        }
        
        text = "This product failed inspection and was rejected"
        sentiment = analyzer.detect_sentiment(text)
        
        assert sentiment['sentiment'] == 'NEGATIVE'
        assert sentiment['scores']['negative'] > 0.8
    
    def test_detect_sentiment_empty_text(self, analyzer):
        """Test sentiment detection with empty text raises ValueError"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            analyzer.detect_sentiment("")
    
    def test_detect_sentiment_disabled_comprehend(self):
        """Test sentiment detection returns neutral when Comprehend is disabled"""
        with patch('compliance_text_analyzer.settings') as mock_settings:
            mock_settings.COMPREHEND_ENABLED = False
            mock_settings.AWS_REGION = 'us-east-1'
            
            analyzer = ComplianceTextAnalyzer()
            sentiment = analyzer.detect_sentiment("Test text")
            
            assert sentiment['sentiment'] == 'NEUTRAL'
            assert sentiment['scores']['neutral'] == 1.0


class TestConvenienceFunctions:
    """Test suite for convenience functions"""
    
    @patch('compliance_text_analyzer.ComplianceTextAnalyzer')
    def test_extract_entities_from_text(self, mock_analyzer_class):
        """Test extract_entities_from_text convenience function"""
        mock_instance = Mock()
        mock_instance.extract_entities.return_value = [
            Entity('FDA', 'ORGANIZATION', 0.95, 0, 3)
        ]
        mock_analyzer_class.return_value = mock_instance
        
        result = extract_entities_from_text("FDA approval")
        
        assert len(result) == 1
        assert result[0].text == 'FDA'
        mock_instance.extract_entities.assert_called_once_with("FDA approval", None)
    
    @patch('compliance_text_analyzer.ComplianceTextAnalyzer')
    def test_extract_key_phrases_from_text(self, mock_analyzer_class):
        """Test extract_key_phrases_from_text convenience function"""
        mock_instance = Mock()
        mock_instance.extract_key_phrases.return_value = [
            KeyPhrase('FDA approval', 0.95, 0, 12)
        ]
        mock_analyzer_class.return_value = mock_instance
        
        result = extract_key_phrases_from_text("FDA approval required")
        
        assert len(result) == 1
        assert result[0].text == 'FDA approval'
        mock_instance.extract_key_phrases.assert_called_once_with("FDA approval required")
    
    @patch('compliance_text_analyzer.ComplianceTextAnalyzer')
    def test_extract_compliance_terms_from_text(self, mock_analyzer_class):
        """Test extract_compliance_terms_from_text convenience function"""
        mock_instance = Mock()
        mock_instance.extract_compliance_terms.return_value = ComplianceTerms(
            certifications=['FDA', 'CE'],
            regulations=['REACH'],
            standards=['ISO 9001'],
            restricted_substances=[],
            countries=['United States'],
            organizations=['FDA']
        )
        mock_analyzer_class.return_value = mock_instance
        
        result = extract_compliance_terms_from_text("FDA and CE required")
        
        assert 'FDA' in result.certifications
        assert 'CE' in result.certifications
        mock_instance.extract_compliance_terms.assert_called_once_with("FDA and CE required")
    
    @patch('compliance_text_analyzer.ComplianceTextAnalyzer')
    def test_validate_compliance_document(self, mock_analyzer_class):
        """Test validate_compliance_document convenience function"""
        mock_instance = Mock()
        mock_instance.validate_document.return_value = DocumentValidation(
            is_valid=True,
            compliance_score=85.0,
            detected_issues=[],
            missing_terms=[],
            suggestions=[],
            entities=[],
            key_phrases=[]
        )
        mock_analyzer_class.return_value = mock_instance
        
        result = validate_compliance_document("Test document", required_terms=['FDA'])
        
        assert result.is_valid is True
        assert result.compliance_score == 85.0
        mock_instance.validate_document.assert_called_once_with(
            "Test document", ['FDA'], None
        )


class TestEdgeCases:
    """Test suite for edge cases and error handling"""
    
    def test_entity_extraction_with_special_characters(self, analyzer, mock_comprehend_client):
        """Test entity extraction handles special characters"""
        mock_comprehend_client.detect_entities.return_value = {'Entities': []}
        
        text = "Test @#$% special !@# characters"
        entities = analyzer.extract_entities(text)
        
        assert isinstance(entities, list)
    
    def test_key_phrase_extraction_with_unicode(self, analyzer, mock_comprehend_client):
        """Test key phrase extraction handles unicode characters"""
        mock_comprehend_client.detect_key_phrases.return_value = {'KeyPhrases': []}
        
        text = "Test with unicode: café, naïve, résumé"
        key_phrases = analyzer.extract_key_phrases(text)
        
        assert isinstance(key_phrases, list)
    
    def test_compliance_terms_extraction_error_handling(self, analyzer, mock_comprehend_client):
        """Test compliance terms extraction handles errors gracefully"""
        mock_comprehend_client.detect_entities.side_effect = Exception("API Error")
        
        text = "Test text"
        compliance_terms = analyzer.extract_compliance_terms(text)
        
        # Should return empty result instead of raising
        assert compliance_terms.certifications == []
        assert compliance_terms.regulations == []
    
    def test_document_validation_error_handling(self, analyzer, mock_comprehend_client):
        """Test document validation handles errors gracefully"""
        mock_comprehend_client.detect_entities.side_effect = Exception("API Error")
        
        text = "Test document"
        validation = analyzer.validate_document(text)
        
        # Should return failed validation instead of raising
        assert validation.is_valid is False
        assert validation.compliance_score == 0.0
        assert len(validation.detected_issues) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
