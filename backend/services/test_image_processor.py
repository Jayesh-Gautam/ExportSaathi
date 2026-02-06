"""
Unit tests for ImageProcessor service

Tests image processing, validation, and AWS Textract integration.
"""
import io
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from image_processor import (
    ImageProcessor,
    ImageFeatures,
    ValidationResult,
    ImageFormat,
    extract_text_from_image,
    extract_features_from_image
)


# Test fixtures

@pytest.fixture
def sample_image_bytes():
    """Create a sample JPEG image for testing"""
    img = Image.new('RGB', (800, 600), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()


@pytest.fixture
def sample_png_image_bytes():
    """Create a sample PNG image for testing"""
    img = Image.new('RGBA', (800, 600), color=(255, 255, 255, 255))
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture
def large_image_bytes():
    """Create a large image that exceeds size limits"""
    img = Image.new('RGB', (5000, 5000), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=100)
    return buffer.getvalue()


@pytest.fixture
def small_image_bytes():
    """Create a very small image"""
    img = Image.new('RGB', (30, 30), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()


@pytest.fixture
def mock_textract_response():
    """Mock Textract detect_document_text response"""
    return {
        'Blocks': [
            {
                'BlockType': 'LINE',
                'Text': 'Product Name: Organic Tea',
                'Confidence': 99.5
            },
            {
                'BlockType': 'LINE',
                'Text': 'Net Weight: 500g',
                'Confidence': 98.2
            },
            {
                'BlockType': 'LINE',
                'Text': 'Made in India',
                'Confidence': 97.8
            }
        ]
    }


@pytest.fixture
def mock_textract_analyze_response():
    """Mock Textract analyze_document response with forms and tables"""
    return {
        'Blocks': [
            {
                'Id': 'line1',
                'BlockType': 'LINE',
                'Text': 'Product Name: Organic Tea',
                'Confidence': 99.5,
                'Geometry': {}
            },
            {
                'Id': 'line2',
                'BlockType': 'LINE',
                'Text': 'Net Weight: 500g',
                'Confidence': 98.2,
                'Geometry': {}
            },
            {
                'Id': 'key1',
                'BlockType': 'KEY_VALUE_SET',
                'EntityTypes': ['KEY'],
                'Relationships': [
                    {'Type': 'CHILD', 'Ids': ['word1']},
                    {'Type': 'VALUE', 'Ids': ['value1']}
                ]
            },
            {
                'Id': 'word1',
                'BlockType': 'WORD',
                'Text': 'Weight'
            },
            {
                'Id': 'value1',
                'BlockType': 'KEY_VALUE_SET',
                'EntityTypes': ['VALUE'],
                'Relationships': [
                    {'Type': 'CHILD', 'Ids': ['word2']}
                ]
            },
            {
                'Id': 'word2',
                'BlockType': 'WORD',
                'Text': '500g'
            },
            {
                'Id': 'table1',
                'BlockType': 'TABLE',
                'Relationships': [
                    {'Type': 'CHILD', 'Ids': ['cell1', 'cell2']}
                ]
            },
            {
                'Id': 'cell1',
                'BlockType': 'CELL',
                'RowIndex': 1,
                'ColumnIndex': 1,
                'Relationships': [
                    {'Type': 'CHILD', 'Ids': ['word3']}
                ]
            },
            {
                'Id': 'word3',
                'BlockType': 'WORD',
                'Text': 'Ingredient'
            },
            {
                'Id': 'cell2',
                'BlockType': 'CELL',
                'RowIndex': 1,
                'ColumnIndex': 2,
                'Relationships': [
                    {'Type': 'CHILD', 'Ids': ['word4']}
                ]
            },
            {
                'Id': 'word4',
                'BlockType': 'WORD',
                'Text': 'Tea Leaves'
            }
        ]
    }


@pytest.fixture
def image_processor():
    """Create ImageProcessor instance with mocked Textract"""
    with patch('image_processor.boto3.client') as mock_boto:
        mock_client = Mock()
        mock_boto.return_value = mock_client
        processor = ImageProcessor()
        processor.textract_client = mock_client
        processor.textract_enabled = True
        return processor


# Test ImageProcessor initialization

def test_image_processor_initialization():
    """Test ImageProcessor initializes correctly"""
    with patch('image_processor.boto3.client') as mock_boto:
        processor = ImageProcessor()
        assert processor.region_name is not None
        assert processor.max_image_size_mb > 0


def test_image_processor_with_custom_settings():
    """Test ImageProcessor with custom settings"""
    with patch('image_processor.boto3.client'):
        processor = ImageProcessor(
            region_name='us-west-2',
            max_image_size_mb=5
        )
        assert processor.region_name == 'us-west-2'
        assert processor.max_image_size_mb == 5


# Test image validation

def test_validate_image_success(image_processor, sample_image_bytes):
    """Test successful image validation"""
    result = image_processor.validate_image(sample_image_bytes)
    
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.file_size_mb > 0
    assert result.dimensions == (800, 600)
    assert result.format == 'JPEG'


def test_validate_image_too_large(image_processor):
    """Test validation fails for oversized image"""
    # Create an image with random noise that won't compress well
    import random
    img = Image.new('RGB', (4000, 4000))
    pixels = img.load()
    # Fill with random pixels (doesn't compress well)
    for i in range(4000):
        for j in range(4000):
            pixels[i, j] = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=100)
    large_bytes = buffer.getvalue()
    
    # Verify it's actually large
    file_size_mb = len(large_bytes) / (1024 * 1024)
    
    # If we still can't create a large enough image, just test with a mock
    if file_size_mb <= 10:
        # Create fake large bytes
        large_bytes = b'x' * (11 * 1024 * 1024)  # 11 MB of data
    
    result = image_processor.validate_image(large_bytes)
    
    assert result.is_valid is False
    assert any('exceeds maximum' in error for error in result.errors)


def test_validate_image_too_small(image_processor, small_image_bytes):
    """Test validation fails for undersized image"""
    result = image_processor.validate_image(small_image_bytes)
    
    assert result.is_valid is False
    assert any('too small' in error for error in result.errors)


def test_validate_image_invalid_format(image_processor):
    """Test validation fails for invalid image data"""
    invalid_bytes = b'not an image'
    result = image_processor.validate_image(invalid_bytes)
    
    assert result.is_valid is False
    assert any('Failed to open image' in error for error in result.errors)


def test_validate_image_png_format(image_processor, sample_png_image_bytes):
    """Test validation succeeds for PNG format"""
    result = image_processor.validate_image(sample_png_image_bytes)
    
    assert result.is_valid is True
    assert result.format == 'PNG'


# Test image preprocessing

def test_preprocess_image_jpeg(image_processor, sample_image_bytes):
    """Test preprocessing JPEG image"""
    processed = image_processor.preprocess_image(sample_image_bytes)
    
    assert isinstance(processed, bytes)
    assert len(processed) > 0
    
    # Verify it's still a valid image
    img = Image.open(io.BytesIO(processed))
    assert img.format == 'JPEG'
    assert img.mode == 'RGB'


def test_preprocess_image_png_to_jpeg(image_processor, sample_png_image_bytes):
    """Test preprocessing converts PNG to JPEG"""
    processed = image_processor.preprocess_image(sample_png_image_bytes)
    
    # Verify conversion to JPEG
    img = Image.open(io.BytesIO(processed))
    assert img.format == 'JPEG'
    assert img.mode == 'RGB'


def test_preprocess_image_resize_large(image_processor):
    """Test preprocessing resizes very large images"""
    # Create a very large image
    large_img = Image.new('RGB', (6000, 6000), color='white')
    buffer = io.BytesIO()
    large_img.save(buffer, format='JPEG')
    large_bytes = buffer.getvalue()
    
    processed = image_processor.preprocess_image(large_bytes)
    
    # Verify image was resized
    img = Image.open(io.BytesIO(processed))
    assert max(img.size) <= 4096


def test_preprocess_image_handles_rgba(image_processor):
    """Test preprocessing handles RGBA images with transparency"""
    # Create RGBA image with transparency
    img = Image.new('RGBA', (800, 600), color=(255, 0, 0, 128))
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    rgba_bytes = buffer.getvalue()
    
    processed = image_processor.preprocess_image(rgba_bytes)
    
    # Verify conversion to RGB
    result_img = Image.open(io.BytesIO(processed))
    assert result_img.mode == 'RGB'


# Test text extraction

def test_extract_text_success(image_processor, sample_image_bytes, mock_textract_response):
    """Test successful text extraction"""
    image_processor.textract_client.detect_document_text.return_value = mock_textract_response
    
    text = image_processor.extract_text(sample_image_bytes)
    
    assert 'Organic Tea' in text
    assert 'Net Weight: 500g' in text
    assert 'Made in India' in text
    image_processor.textract_client.detect_document_text.assert_called_once()


def test_extract_text_empty_response(image_processor, sample_image_bytes):
    """Test text extraction with empty Textract response"""
    image_processor.textract_client.detect_document_text.return_value = {'Blocks': []}
    
    text = image_processor.extract_text(sample_image_bytes)
    
    assert text == ''


def test_extract_text_invalid_image(image_processor):
    """Test text extraction fails with invalid image"""
    invalid_bytes = b'not an image'
    
    with pytest.raises(ValueError, match='Invalid image'):
        image_processor.extract_text(invalid_bytes)


def test_extract_text_textract_disabled():
    """Test text extraction when Textract is disabled"""
    with patch('image_processor.settings') as mock_settings:
        mock_settings.TEXTRACT_ENABLED = False
        mock_settings.AWS_REGION = 'us-east-1'
        mock_settings.MAX_IMAGE_SIZE_MB = 10
        
        processor = ImageProcessor()
        
        # Create valid image
        img = Image.new('RGB', (800, 600), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        text = processor.extract_text(image_bytes)
        assert text == ''


def test_extract_text_client_error(image_processor, sample_image_bytes):
    """Test text extraction handles AWS ClientError"""
    from botocore.exceptions import ClientError
    
    error_response = {
        'Error': {
            'Code': 'InvalidParameterException',
            'Message': 'Invalid image format'
        }
    }
    image_processor.textract_client.detect_document_text.side_effect = ClientError(
        error_response, 'DetectDocumentText'
    )
    
    with pytest.raises(ClientError):
        image_processor.extract_text(sample_image_bytes)


# Test feature extraction

def test_extract_features_success(
    image_processor,
    sample_image_bytes,
    mock_textract_analyze_response
):
    """Test successful feature extraction"""
    image_processor.textract_client.analyze_document.return_value = mock_textract_analyze_response
    
    features = image_processor.extract_features(sample_image_bytes)
    
    assert isinstance(features, ImageFeatures)
    assert 'Organic Tea' in features.text
    assert features.confidence > 0
    assert len(features.text_blocks) > 0
    assert len(features.key_value_pairs) > 0
    assert 'Weight' in features.key_value_pairs
    assert features.key_value_pairs['Weight'] == '500g'
    assert len(features.tables) > 0
    assert len(features.detected_labels) > 0
    image_processor.textract_client.analyze_document.assert_called_once()


def test_extract_features_empty_response(image_processor, sample_image_bytes):
    """Test feature extraction with empty response"""
    image_processor.textract_client.analyze_document.return_value = {'Blocks': []}
    
    features = image_processor.extract_features(sample_image_bytes)
    
    assert features.text == ''
    assert features.confidence == 0.0
    assert len(features.text_blocks) == 0
    assert len(features.key_value_pairs) == 0
    assert len(features.tables) == 0


def test_extract_features_invalid_image(image_processor):
    """Test feature extraction fails with invalid image"""
    invalid_bytes = b'not an image'
    
    with pytest.raises(ValueError, match='Invalid image'):
        image_processor.extract_features(invalid_bytes)


def test_extract_features_textract_disabled():
    """Test feature extraction when Textract is disabled"""
    with patch('image_processor.settings') as mock_settings:
        mock_settings.TEXTRACT_ENABLED = False
        mock_settings.AWS_REGION = 'us-east-1'
        mock_settings.MAX_IMAGE_SIZE_MB = 10
        
        processor = ImageProcessor()
        
        # Create valid image
        img = Image.new('RGB', (800, 600), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        features = processor.extract_features(image_bytes)
        assert features.text == ''
        assert features.confidence == 0.0


# Test helper methods

def test_extract_key_value_pairs(image_processor, mock_textract_analyze_response):
    """Test key-value pair extraction"""
    pairs = image_processor._extract_key_value_pairs(mock_textract_analyze_response)
    
    assert isinstance(pairs, dict)
    assert 'Weight' in pairs
    assert pairs['Weight'] == '500g'


def test_extract_tables(image_processor, mock_textract_analyze_response):
    """Test table extraction"""
    tables = image_processor._extract_tables(mock_textract_analyze_response)
    
    assert isinstance(tables, list)
    assert len(tables) > 0
    assert isinstance(tables[0], list)
    assert tables[0][0][0] == 'Ingredient'
    assert tables[0][0][1] == 'Tea Leaves'


def test_extract_labels(image_processor):
    """Test label extraction from text lines"""
    text_lines = [
        'ORGANIC CERTIFIED',
        'Product Name: Tea',
        'Made in India',
        'FDA Approved',
        'Net Weight: 500g',
        'Contains: Tea Leaves'
    ]
    
    labels = image_processor._extract_labels(text_lines)
    
    assert isinstance(labels, list)
    assert 'ORGANIC CERTIFIED' in labels
    assert any('fda' in label.lower() for label in labels)
    assert any('made in' in label.lower() for label in labels)


def test_extract_labels_deduplication(image_processor):
    """Test label extraction removes duplicates"""
    text_lines = [
        'ORGANIC',
        'ORGANIC',
        'Made in India',
        'Made in India'
    ]
    
    labels = image_processor._extract_labels(text_lines)
    
    # Should have only unique labels
    assert len(labels) == len(set(labels))


def test_extract_labels_limit(image_processor):
    """Test label extraction limits to 20 labels"""
    text_lines = [f'LABEL {i}' for i in range(50)]
    
    labels = image_processor._extract_labels(text_lines)
    
    assert len(labels) <= 20


# Test convenience functions

def test_extract_text_from_image_convenience(sample_image_bytes, mock_textract_response):
    """Test convenience function for text extraction"""
    with patch('image_processor.boto3.client') as mock_boto:
        mock_client = Mock()
        mock_client.detect_document_text.return_value = mock_textract_response
        mock_boto.return_value = mock_client
        
        with patch('image_processor.settings') as mock_settings:
            mock_settings.TEXTRACT_ENABLED = True
            mock_settings.AWS_REGION = 'us-east-1'
            mock_settings.MAX_IMAGE_SIZE_MB = 10
            mock_settings.AWS_ACCESS_KEY_ID = None
            mock_settings.AWS_SECRET_ACCESS_KEY = None
            
            text = extract_text_from_image(sample_image_bytes)
            
            assert 'Organic Tea' in text


def test_extract_features_from_image_convenience(
    sample_image_bytes,
    mock_textract_analyze_response
):
    """Test convenience function for feature extraction"""
    with patch('image_processor.boto3.client') as mock_boto:
        mock_client = Mock()
        mock_client.analyze_document.return_value = mock_textract_analyze_response
        mock_boto.return_value = mock_client
        
        with patch('image_processor.settings') as mock_settings:
            mock_settings.TEXTRACT_ENABLED = True
            mock_settings.AWS_REGION = 'us-east-1'
            mock_settings.MAX_IMAGE_SIZE_MB = 10
            mock_settings.AWS_ACCESS_KEY_ID = None
            mock_settings.AWS_SECRET_ACCESS_KEY = None
            
            features = extract_features_from_image(sample_image_bytes)
            
            assert isinstance(features, ImageFeatures)
            assert 'Organic Tea' in features.text


# Integration-style tests

def test_full_workflow_text_extraction(image_processor, sample_image_bytes, mock_textract_response):
    """Test complete workflow: validate -> preprocess -> extract text"""
    image_processor.textract_client.detect_document_text.return_value = mock_textract_response
    
    # Validate
    validation = image_processor.validate_image(sample_image_bytes)
    assert validation.is_valid
    
    # Preprocess
    processed = image_processor.preprocess_image(sample_image_bytes)
    assert len(processed) > 0
    
    # Extract text
    text = image_processor.extract_text(sample_image_bytes)
    assert len(text) > 0


def test_full_workflow_feature_extraction(
    image_processor,
    sample_image_bytes,
    mock_textract_analyze_response
):
    """Test complete workflow: validate -> preprocess -> extract features"""
    image_processor.textract_client.analyze_document.return_value = mock_textract_analyze_response
    
    # Validate
    validation = image_processor.validate_image(sample_image_bytes)
    assert validation.is_valid
    
    # Preprocess
    processed = image_processor.preprocess_image(sample_image_bytes)
    assert len(processed) > 0
    
    # Extract features
    features = image_processor.extract_features(sample_image_bytes)
    assert len(features.text) > 0
    assert len(features.text_blocks) > 0


# Edge cases

def test_extract_text_with_no_text_blocks(image_processor, sample_image_bytes):
    """Test text extraction when image has no text"""
    image_processor.textract_client.detect_document_text.return_value = {
        'Blocks': [
            {'BlockType': 'PAGE', 'Id': 'page1'}
        ]
    }
    
    text = image_processor.extract_text(sample_image_bytes)
    assert text == ''


def test_extract_features_with_partial_data(image_processor, sample_image_bytes):
    """Test feature extraction with incomplete Textract response"""
    partial_response = {
        'Blocks': [
            {
                'Id': 'line1',
                'BlockType': 'LINE',
                'Text': 'Partial Data',
                'Confidence': 95.0,
                'Geometry': {}
            }
        ]
    }
    image_processor.textract_client.analyze_document.return_value = partial_response
    
    features = image_processor.extract_features(sample_image_bytes)
    
    assert features.text == 'Partial Data'
    assert features.confidence == 95.0
    assert len(features.key_value_pairs) == 0
    assert len(features.tables) == 0


def test_preprocess_image_error_handling(image_processor):
    """Test preprocessing handles corrupted image gracefully"""
    # Partially corrupted image data
    corrupted_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * 100
    
    # Should return original bytes if preprocessing fails
    result = image_processor.preprocess_image(corrupted_bytes)
    assert result == corrupted_bytes
