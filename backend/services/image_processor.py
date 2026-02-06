"""
ImageProcessor Service for ExportSathi

This module provides image processing and analysis capabilities using AWS Textract.
It extracts text and visual features from product images to assist with HS code prediction
and product identification.

Requirements: 1.2, 12.4
"""
import io
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from PIL import Image

from config import settings


logger = logging.getLogger(__name__)


class ImageFormat(str, Enum):
    """Supported image formats"""
    JPEG = "JPEG"
    PNG = "PNG"
    JPG = "JPG"


@dataclass
class ImageFeatures:
    """
    Extracted features from product image
    
    Attributes:
        text: Extracted text from image (labels, packaging info)
        confidence: Overall confidence score (0-100)
        detected_labels: List of detected labels/objects
        text_blocks: List of text blocks with positions
        key_value_pairs: Extracted key-value pairs (e.g., "Weight: 500g")
        tables: Extracted table data if present
        raw_response: Raw Textract response for advanced processing
    """
    text: str
    confidence: float
    detected_labels: List[str]
    text_blocks: List[Dict[str, Any]]
    key_value_pairs: Dict[str, str]
    tables: List[List[List[str]]]
    raw_response: Dict[str, Any]


@dataclass
class ValidationResult:
    """
    Image validation result
    
    Attributes:
        is_valid: Whether image passes validation
        errors: List of validation errors
        warnings: List of validation warnings
        file_size_mb: Image file size in MB
        dimensions: Image dimensions (width, height)
        format: Image format
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    file_size_mb: float
    dimensions: Tuple[int, int]
    format: str


class ImageProcessor:
    """
    Image processing service using AWS Textract
    
    Provides capabilities for:
    - Text extraction from product images
    - Visual feature analysis
    - Image preprocessing and validation
    - Label and object detection
    
    Requirements: 1.2, 12.4
    """
    
    def __init__(
        self,
        region_name: Optional[str] = None,
        max_image_size_mb: int = None
    ):
        """
        Initialize ImageProcessor
        
        Args:
            region_name: AWS region (defaults to settings)
            max_image_size_mb: Maximum image size in MB (defaults to settings)
        """
        self.region_name = region_name or settings.AWS_REGION
        self.max_image_size_mb = max_image_size_mb or settings.MAX_IMAGE_SIZE_MB
        self.textract_enabled = settings.TEXTRACT_ENABLED
        
        # Initialize AWS Textract client
        if self.textract_enabled:
            try:
                self.textract_client = boto3.client(
                    'textract',
                    region_name=self.region_name,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None
                )
                logger.info(f"Initialized Textract client in region {self.region_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Textract client: {e}")
                self.textract_enabled = False
                self.textract_client = None
        else:
            self.textract_client = None
            logger.warning("Textract is disabled in configuration")
    
    def validate_image(self, image_bytes: bytes) -> ValidationResult:
        """
        Validate image format, size, and quality
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            ValidationResult with validation status and details
            
        Requirements: 1.2
        """
        errors = []
        warnings = []
        
        # Check file size
        file_size_mb = len(image_bytes) / (1024 * 1024)
        if file_size_mb > self.max_image_size_mb:
            errors.append(
                f"Image size ({file_size_mb:.2f} MB) exceeds maximum "
                f"allowed size ({self.max_image_size_mb} MB)"
            )
        
        # Try to open and validate image
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image_format = image.format
            dimensions = image.size
            
            # Check format
            if image_format not in [fmt.value for fmt in ImageFormat]:
                errors.append(
                    f"Unsupported image format: {image_format}. "
                    f"Supported formats: {', '.join([fmt.value for fmt in ImageFormat])}"
                )
            
            # Check dimensions
            width, height = dimensions
            if width < 50 or height < 50:
                errors.append(f"Image dimensions too small: {width}x{height}. Minimum: 50x50")
            
            if width > 10000 or height > 10000:
                warnings.append(
                    f"Large image dimensions: {width}x{height}. "
                    "Processing may be slow."
                )
            
            # Check if image is too small (low quality)
            if width < 300 or height < 300:
                warnings.append(
                    f"Low resolution image: {width}x{height}. "
                    "Text extraction may be less accurate."
                )
            
        except Exception as e:
            errors.append(f"Failed to open image: {str(e)}")
            image_format = "UNKNOWN"
            dimensions = (0, 0)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            file_size_mb=file_size_mb,
            dimensions=dimensions,
            format=image_format
        )
    
    def preprocess_image(self, image_bytes: bytes) -> bytes:
        """
        Preprocess image for better text extraction
        
        Applies:
        - Format conversion to JPEG if needed
        - Compression if image is too large
        - Basic quality enhancements
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Preprocessed image bytes
            
        Requirements: 1.2
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed (for PNG with transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (maintain aspect ratio)
            max_dimension = 4096
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {image.size} to {new_size}")
            
            # Save to bytes with optimization
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            preprocessed_bytes = output.getvalue()
            
            logger.info(
                f"Preprocessed image: {len(image_bytes)} bytes -> "
                f"{len(preprocessed_bytes)} bytes"
            )
            
            return preprocessed_bytes
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            # Return original if preprocessing fails
            return image_bytes
    
    def extract_text(self, image_bytes: bytes) -> str:
        """
        Extract text from product image using AWS Textract
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Extracted text as a single string
            
        Raises:
            ValueError: If Textract is disabled or image is invalid
            ClientError: If AWS Textract API call fails
            
        Requirements: 1.2, 12.4
        """
        if not self.textract_enabled or not self.textract_client:
            logger.warning("Textract is disabled, returning empty text")
            return ""
        
        # Validate image
        validation = self.validate_image(image_bytes)
        if not validation.is_valid:
            raise ValueError(f"Invalid image: {', '.join(validation.errors)}")
        
        # Preprocess image
        processed_bytes = self.preprocess_image(image_bytes)
        
        try:
            # Call Textract detect_document_text API
            response = self.textract_client.detect_document_text(
                Document={'Bytes': processed_bytes}
            )
            
            # Extract text from response
            text_lines = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_lines.append(block.get('Text', ''))
            
            extracted_text = '\n'.join(text_lines)
            logger.info(f"Extracted {len(text_lines)} lines of text from image")
            
            return extracted_text
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Textract API error [{error_code}]: {error_message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during text extraction: {e}")
            raise
    
    def extract_features(self, image_bytes: bytes) -> ImageFeatures:
        """
        Extract comprehensive features from product image
        
        Extracts:
        - Text content (labels, packaging info)
        - Key-value pairs (e.g., "Weight: 500g")
        - Tables (ingredient lists, nutrition facts)
        - Detected labels/objects
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            ImageFeatures object with all extracted features
            
        Raises:
            ValueError: If Textract is disabled or image is invalid
            ClientError: If AWS Textract API call fails
            
        Requirements: 1.2, 12.4
        """
        if not self.textract_enabled or not self.textract_client:
            logger.warning("Textract is disabled, returning empty features")
            return ImageFeatures(
                text="",
                confidence=0.0,
                detected_labels=[],
                text_blocks=[],
                key_value_pairs={},
                tables=[],
                raw_response={}
            )
        
        # Validate image
        validation = self.validate_image(image_bytes)
        if not validation.is_valid:
            raise ValueError(f"Invalid image: {', '.join(validation.errors)}")
        
        # Preprocess image
        processed_bytes = self.preprocess_image(image_bytes)
        
        try:
            # Call Textract analyze_document API for comprehensive analysis
            response = self.textract_client.analyze_document(
                Document={'Bytes': processed_bytes},
                FeatureTypes=['TABLES', 'FORMS']
            )
            
            # Extract text blocks
            text_blocks = []
            text_lines = []
            total_confidence = 0.0
            confidence_count = 0
            
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_lines.append(block.get('Text', ''))
                    text_blocks.append({
                        'text': block.get('Text', ''),
                        'confidence': block.get('Confidence', 0.0),
                        'geometry': block.get('Geometry', {})
                    })
                    if 'Confidence' in block:
                        total_confidence += block['Confidence']
                        confidence_count += 1
            
            # Calculate average confidence
            avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.0
            
            # Extract key-value pairs
            key_value_pairs = self._extract_key_value_pairs(response)
            
            # Extract tables
            tables = self._extract_tables(response)
            
            # Extract detected labels (from text content)
            detected_labels = self._extract_labels(text_lines)
            
            # Combine all text
            extracted_text = '\n'.join(text_lines)
            
            logger.info(
                f"Extracted features: {len(text_lines)} lines, "
                f"{len(key_value_pairs)} key-value pairs, "
                f"{len(tables)} tables, {len(detected_labels)} labels"
            )
            
            return ImageFeatures(
                text=extracted_text,
                confidence=avg_confidence,
                detected_labels=detected_labels,
                text_blocks=text_blocks,
                key_value_pairs=key_value_pairs,
                tables=tables,
                raw_response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Textract API error [{error_code}]: {error_message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during feature extraction: {e}")
            raise
    
    def _extract_key_value_pairs(self, response: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract key-value pairs from Textract response
        
        Args:
            response: Textract analyze_document response
            
        Returns:
            Dictionary of key-value pairs
        """
        key_value_pairs = {}
        
        # Build a map of block IDs to blocks
        block_map = {block['Id']: block for block in response.get('Blocks', [])}
        
        # Find KEY_VALUE_SET blocks
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'KEY_VALUE_SET':
                if 'KEY' in block.get('EntityTypes', []):
                    # This is a key block
                    key_text = self._get_text_from_relationships(block, block_map)
                    
                    # Find associated value
                    value_text = ""
                    for relationship in block.get('Relationships', []):
                        if relationship['Type'] == 'VALUE':
                            for value_id in relationship['Ids']:
                                value_block = block_map.get(value_id)
                                if value_block:
                                    value_text = self._get_text_from_relationships(
                                        value_block, block_map
                                    )
                    
                    if key_text and value_text:
                        key_value_pairs[key_text] = value_text
        
        return key_value_pairs
    
    def _get_text_from_relationships(
        self,
        block: Dict[str, Any],
        block_map: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Get text from a block's child relationships
        
        Args:
            block: Textract block
            block_map: Map of block IDs to blocks
            
        Returns:
            Combined text from child blocks
        """
        text_parts = []
        
        for relationship in block.get('Relationships', []):
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    child_block = block_map.get(child_id)
                    if child_block and child_block['BlockType'] == 'WORD':
                        text_parts.append(child_block.get('Text', ''))
        
        return ' '.join(text_parts)
    
    def _extract_tables(self, response: Dict[str, Any]) -> List[List[List[str]]]:
        """
        Extract tables from Textract response
        
        Args:
            response: Textract analyze_document response
            
        Returns:
            List of tables, where each table is a 2D list of cell values
        """
        tables = []
        
        # Build a map of block IDs to blocks
        block_map = {block['Id']: block for block in response.get('Blocks', [])}
        
        # Find TABLE blocks
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'TABLE':
                table = self._parse_table(block, block_map)
                if table:
                    tables.append(table)
        
        return tables
    
    def _parse_table(
        self,
        table_block: Dict[str, Any],
        block_map: Dict[str, Dict[str, Any]]
    ) -> List[List[str]]:
        """
        Parse a table block into a 2D list
        
        Args:
            table_block: Textract TABLE block
            block_map: Map of block IDs to blocks
            
        Returns:
            2D list representing the table
        """
        # Find all CELL blocks for this table
        cells = []
        for relationship in table_block.get('Relationships', []):
            if relationship['Type'] == 'CHILD':
                for cell_id in relationship['Ids']:
                    cell_block = block_map.get(cell_id)
                    if cell_block and cell_block['BlockType'] == 'CELL':
                        cells.append(cell_block)
        
        if not cells:
            return []
        
        # Determine table dimensions
        max_row = max(cell.get('RowIndex', 0) for cell in cells)
        max_col = max(cell.get('ColumnIndex', 0) for cell in cells)
        
        # Initialize table with empty strings
        table = [['' for _ in range(max_col)] for _ in range(max_row)]
        
        # Fill in cell values
        for cell in cells:
            row_idx = cell.get('RowIndex', 1) - 1  # Convert to 0-indexed
            col_idx = cell.get('ColumnIndex', 1) - 1
            
            # Get cell text
            cell_text = self._get_text_from_relationships(cell, block_map)
            
            if 0 <= row_idx < max_row and 0 <= col_idx < max_col:
                table[row_idx][col_idx] = cell_text
        
        return table
    
    def _extract_labels(self, text_lines: List[str]) -> List[str]:
        """
        Extract potential product labels from text lines
        
        Identifies common label patterns like:
        - Brand names (capitalized words)
        - Product types
        - Certifications (FDA, CE, etc.)
        - Warnings and instructions
        
        Args:
            text_lines: List of text lines from image
            
        Returns:
            List of detected labels
        """
        labels = []
        
        # Common label keywords
        label_keywords = [
            'organic', 'natural', 'certified', 'approved', 'fda', 'ce',
            'made in', 'product of', 'ingredients', 'contains', 'warning',
            'caution', 'net weight', 'net wt', 'volume', 'exp', 'mfg',
            'batch', 'lot', 'halal', 'kosher', 'vegan', 'gluten-free'
        ]
        
        for line in text_lines:
            line_lower = line.lower().strip()
            
            # Check for label keywords
            for keyword in label_keywords:
                if keyword in line_lower:
                    labels.append(line.strip())
                    break
            
            # Check for all-caps text (often labels)
            if line.isupper() and len(line) > 2:
                labels.append(line.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_labels = []
        for label in labels:
            if label not in seen:
                seen.add(label)
                unique_labels.append(label)
        
        return unique_labels[:20]  # Limit to top 20 labels


# Convenience function for quick text extraction
def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Convenience function to extract text from image
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Extracted text
    """
    processor = ImageProcessor()
    return processor.extract_text(image_bytes)


# Convenience function for quick feature extraction
def extract_features_from_image(image_bytes: bytes) -> ImageFeatures:
    """
    Convenience function to extract features from image
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        ImageFeatures object
    """
    processor = ImageProcessor()
    return processor.extract_features(image_bytes)
