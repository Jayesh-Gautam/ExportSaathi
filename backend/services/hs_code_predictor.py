"""
HS Code Predictor Service for ExportSathi

This module provides HS code prediction from product images, descriptions, and BOM.
It combines image feature extraction, semantic search for similar products, and LLM
inference to predict the most appropriate HS code with confidence scoring.

Requirements: 2.1, 2.8
"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import json

import numpy as np

from models.query import HSCodePrediction, HSCodeAlternative, ImageFeatures as ImageFeaturesModel
from models.internal import Document
from services.image_processor import ImageProcessor, ImageFeatures as ImageProcessorFeatures
from services.embeddings import EmbeddingService, get_embedding_service
from services.vector_store import VectorStore, get_vector_store
from services.llm_client import LLMClient, create_llm_client
from config import settings


logger = logging.getLogger(__name__)


@dataclass
class ProductFeatures:
    """
    Combined features for HS code prediction
    
    Attributes:
        product_name: Product name
        description: Product description text
        bom: Bill of Materials
        ingredients: Product ingredients
        image_text: Text extracted from product image
        image_labels: Labels detected in image
        visual_features: Visual characteristics from image
        combined_text: All text features combined
    """
    product_name: str
    description: str
    bom: Optional[str]
    ingredients: Optional[str]
    image_text: Optional[str]
    image_labels: Optional[List[str]]
    visual_features: Optional[Dict[str, Any]]
    combined_text: str


class HSCodePredictor:
    """
    Predicts HS codes from product information using multi-modal analysis.
    
    The predictor combines:
    1. Image feature extraction using AWS Textract
    2. Text analysis from product description and BOM
    3. Semantic search for similar products with known HS codes
    4. LLM-based prediction with confidence scoring
    
    Features:
    - Multi-modal product analysis (image + text)
    - Semantic similarity search for known products
    - Confidence-based prediction with alternatives
    - Returns alternatives when confidence < 70%
    
    Requirements: 2.1, 2.8
    """
    
    def __init__(
        self,
        image_processor: Optional[ImageProcessor] = None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
        llm_client: Optional[LLMClient] = None,
        confidence_threshold: float = 70.0,
        num_similar_products: int = 5
    ):
        """
        Initialize HS Code Predictor
        
        Args:
            image_processor: Service for image processing (creates new if None)
            embedding_service: Service for embeddings (uses global if None)
            vector_store: Vector store for product search (uses global if None)
            llm_client: LLM client for prediction (creates new if None)
            confidence_threshold: Threshold for returning alternatives (default 70%)
            num_similar_products: Number of similar products to retrieve
        """
        self.image_processor = image_processor or ImageProcessor()
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or get_vector_store()
        self.llm_client = llm_client or create_llm_client()
        self.confidence_threshold = confidence_threshold
        self.num_similar_products = num_similar_products
        
        logger.info(
            f"HSCodePredictor initialized with confidence_threshold={confidence_threshold}, "
            f"num_similar_products={num_similar_products}"
        )
    
    def predict_hs_code(
        self,
        product_name: str,
        image: Optional[bytes] = None,
        bom: Optional[str] = None,
        ingredients: Optional[str] = None,
        destination_country: Optional[str] = None
    ) -> HSCodePrediction:
        """
        Predict HS code from product information.
        
        This method:
        1. Extracts features from product image (if provided)
        2. Combines image features with text description and BOM
        3. Queries vector store for similar products with known HS codes
        4. Uses LLM to predict HS code based on all available information
        5. Returns prediction with confidence score and alternatives
        
        Args:
            product_name: Name of the product
            image: Product image bytes (optional)
            bom: Bill of Materials (optional)
            ingredients: Product ingredients (optional)
            destination_country: Destination country for context (optional)
            
        Returns:
            HSCodePrediction with code, confidence, description, and alternatives
            
        Example:
            >>> predictor = HSCodePredictor()
            >>> prediction = predictor.predict_hs_code(
            ...     product_name="Organic Turmeric Powder",
            ...     ingredients="100% organic turmeric",
            ...     bom="Turmeric rhizomes, packaging material"
            ... )
            >>> print(f"HS Code: {prediction.code} (confidence: {prediction.confidence}%)")
        
        Requirements: 2.1, 2.8
        """
        logger.info(f"Predicting HS code for product: {product_name}")
        
        try:
            # Step 1: Extract image features if image provided
            image_features = None
            if image:
                logger.info("Extracting features from product image")
                image_features = self.extract_image_features(image)
            
            # Step 2: Combine all product features
            product_features = self._combine_features(
                product_name=product_name,
                bom=bom,
                ingredients=ingredients,
                image_features=image_features
            )
            
            logger.info(f"Combined product features: {len(product_features.combined_text)} chars")
            
            # Step 3: Find similar products with known HS codes
            similar_products = self.find_similar_products(
                features=product_features,
                destination_country=destination_country
            )
            
            logger.info(f"Found {len(similar_products)} similar products")
            
            # Step 4: Use LLM to predict HS code
            prediction = self._predict_with_llm(
                product_features=product_features,
                similar_products=similar_products,
                destination_country=destination_country
            )
            
            logger.info(
                f"Predicted HS code: {prediction.code} "
                f"(confidence: {prediction.confidence}%)"
            )
            
            # Step 5: Add alternatives if confidence is low
            if prediction.confidence < self.confidence_threshold:
                logger.info(
                    f"Confidence {prediction.confidence}% below threshold "
                    f"{self.confidence_threshold}%, including alternatives"
                )
                # Alternatives are already included from LLM response
            
            return prediction
        
        except Exception as e:
            logger.error(f"Error predicting HS code: {e}", exc_info=True)
            # Return a low-confidence prediction on error
            return HSCodePrediction(
                code="0000.00",
                confidence=0.0,
                description="Unable to predict HS code due to error",
                alternatives=[]
            )
    
    def extract_image_features(self, image: bytes) -> ImageProcessorFeatures:
        """
        Extract features from product image using Textract.
        
        Extracts:
        - Text content (labels, packaging info)
        - Key-value pairs (e.g., "Weight: 500g")
        - Tables (ingredient lists, nutrition facts)
        - Detected labels/objects
        
        Args:
            image: Product image bytes
            
        Returns:
            ImageFeatures object with extracted features
            
        Raises:
            ValueError: If image is invalid
            Exception: If Textract processing fails
        
        Requirements: 2.1
        """
        try:
            logger.debug("Extracting image features using Textract")
            features = self.image_processor.extract_features(image)
            
            logger.info(
                f"Extracted image features: {len(features.text)} chars text, "
                f"{len(features.detected_labels)} labels, "
                f"{len(features.key_value_pairs)} key-value pairs"
            )
            
            return features
        
        except Exception as e:
            logger.error(f"Failed to extract image features: {e}")
            # Return empty features on error rather than failing completely
            return ImageProcessorFeatures(
                text="",
                confidence=0.0,
                detected_labels=[],
                text_blocks=[],
                key_value_pairs={},
                tables=[],
                raw_response={}
            )
    
    def find_similar_products(
        self,
        features: ProductFeatures,
        destination_country: Optional[str] = None
    ) -> List[Document]:
        """
        Find similar products with known HS codes using semantic search.
        
        Queries the vector store for products similar to the input based on:
        - Product name and description
        - Ingredients and BOM
        - Image-extracted text and labels
        
        Args:
            features: Combined product features
            destination_country: Optional country filter
            
        Returns:
            List of similar product documents with HS codes
        
        Requirements: 2.1
        """
        try:
            # Create search query from combined features
            search_query = features.combined_text
            
            # Generate embedding for search
            query_embedding = self.embedding_service.embed_query(search_query)
            
            # Build metadata filters
            filters = {}
            if destination_country:
                filters['country'] = destination_country
            
            # Add filter for documents with HS codes
            filters['has_hs_code'] = True
            
            # Search vector store
            similar_docs = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=self.num_similar_products,
                filters=filters if filters else None
            )
            
            logger.info(f"Retrieved {len(similar_docs)} similar products from vector store")
            
            return similar_docs
        
        except Exception as e:
            logger.error(f"Error finding similar products: {e}", exc_info=True)
            return []
    
    def _combine_features(
        self,
        product_name: str,
        bom: Optional[str],
        ingredients: Optional[str],
        image_features: Optional[ImageProcessorFeatures]
    ) -> ProductFeatures:
        """
        Combine all product features into a unified representation.
        
        Args:
            product_name: Product name
            bom: Bill of Materials
            ingredients: Product ingredients
            image_features: Extracted image features
            
        Returns:
            ProductFeatures object with combined information
        """
        # Extract image information
        image_text = None
        image_labels = None
        visual_features = None
        
        if image_features:
            image_text = image_features.text
            image_labels = image_features.detected_labels
            
            # Extract visual features from key-value pairs
            visual_features = {
                'key_value_pairs': image_features.key_value_pairs,
                'confidence': image_features.confidence
            }
        
        # Build combined text for embedding and LLM
        text_parts = [f"Product: {product_name}"]
        
        if ingredients:
            text_parts.append(f"Ingredients: {ingredients}")
        
        if bom:
            text_parts.append(f"Bill of Materials: {bom}")
        
        if image_text:
            text_parts.append(f"Image Text: {image_text}")
        
        if image_labels:
            text_parts.append(f"Image Labels: {', '.join(image_labels)}")
        
        combined_text = "\n".join(text_parts)
        
        return ProductFeatures(
            product_name=product_name,
            description=product_name,  # Use product name as description
            bom=bom,
            ingredients=ingredients,
            image_text=image_text,
            image_labels=image_labels,
            visual_features=visual_features,
            combined_text=combined_text
        )
    
    def _predict_with_llm(
        self,
        product_features: ProductFeatures,
        similar_products: List[Document],
        destination_country: Optional[str]
    ) -> HSCodePrediction:
        """
        Use LLM to predict HS code based on product features and similar products.
        
        Args:
            product_features: Combined product features
            similar_products: Similar products with known HS codes
            destination_country: Destination country for context
            
        Returns:
            HSCodePrediction with code, confidence, and alternatives
        """
        # Build context from similar products
        similar_products_context = self._build_similar_products_context(similar_products)
        
        # Build prompt for LLM
        prompt = self._build_prediction_prompt(
            product_features=product_features,
            similar_products_context=similar_products_context,
            destination_country=destination_country
        )
        
        # System prompt for HS code prediction
        system_prompt = """You are an expert in international trade and HS code classification. 
Your task is to predict the most appropriate Harmonized System (HS) code for products based on their description, 
ingredients, bill of materials, and similar products.

HS codes are 6-digit international product classification codes used for customs and trade.
The first 2 digits represent the chapter, the next 2 represent the heading, and the last 2 represent the subheading.

Provide your prediction with:
1. The most likely HS code (6 digits in format XX.XX or XXXX.XX)
2. A confidence percentage (0-100)
3. A brief description of what the HS code covers
4. Up to 3 alternative HS codes if confidence is below 70%

Be conservative with confidence scores. Only give high confidence (>80%) when you are very certain.
Consider the product's material composition, intended use, and processing level."""
        
        try:
            # Define JSON schema for structured response
            response_schema = {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "pattern": "^[0-9]{4}\\.[0-9]{2}$"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                    "description": {"type": "string"},
                    "alternatives": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                                "confidence": {"type": "number"},
                                "description": {"type": "string"}
                            },
                            "required": ["code", "confidence", "description"]
                        }
                    }
                },
                "required": ["code", "confidence", "description", "alternatives"]
            }
            
            # Call LLM with structured output
            logger.debug("Calling LLM for HS code prediction")
            response = self.llm_client.generate_structured(
                prompt=prompt,
                schema=response_schema,
                system_prompt=system_prompt
            )
            
            # Parse response into HSCodePrediction
            alternatives = [
                HSCodeAlternative(
                    code=alt['code'],
                    confidence=alt['confidence'],
                    description=alt['description']
                )
                for alt in response.get('alternatives', [])
            ]
            
            prediction = HSCodePrediction(
                code=response['code'],
                confidence=response['confidence'],
                description=response['description'],
                alternatives=alternatives
            )
            
            return prediction
        
        except Exception as e:
            logger.error(f"LLM prediction failed: {e}", exc_info=True)
            
            # Fallback: Try to extract HS code from similar products
            if similar_products:
                return self._fallback_prediction_from_similar(similar_products)
            
            # Last resort: Return unknown
            return HSCodePrediction(
                code="0000.00",
                confidence=0.0,
                description="Unable to predict HS code",
                alternatives=[]
            )
    
    def _build_similar_products_context(self, similar_products: List[Document]) -> str:
        """
        Build context string from similar products with known HS codes.
        
        Args:
            similar_products: List of similar product documents
            
        Returns:
            Formatted context string
        """
        if not similar_products:
            return "No similar products found in database."
        
        context_parts = ["Similar products with known HS codes:"]
        
        for i, doc in enumerate(similar_products, 1):
            # Extract HS code from metadata
            hs_code = doc.metadata.get('hs_code', 'Unknown')
            product_name = doc.metadata.get('product_name', 'Unknown product')
            relevance = doc.relevance_score or 0.0
            
            # Extract key information from document content
            content_preview = doc.content[:200] if len(doc.content) > 200 else doc.content
            
            context_parts.append(
                f"\n{i}. Product: {product_name}\n"
                f"   HS Code: {hs_code}\n"
                f"   Relevance: {relevance:.2f}\n"
                f"   Details: {content_preview}"
            )
        
        return "\n".join(context_parts)
    
    def _build_prediction_prompt(
        self,
        product_features: ProductFeatures,
        similar_products_context: str,
        destination_country: Optional[str]
    ) -> str:
        """
        Build prompt for LLM HS code prediction.
        
        Args:
            product_features: Combined product features
            similar_products_context: Context from similar products
            destination_country: Destination country
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "Please predict the HS code for the following product:\n",
            f"Product Name: {product_features.product_name}"
        ]
        
        if product_features.ingredients:
            prompt_parts.append(f"Ingredients: {product_features.ingredients}")
        
        if product_features.bom:
            prompt_parts.append(f"Bill of Materials: {product_features.bom}")
        
        if product_features.image_text:
            prompt_parts.append(f"Text from Product Image: {product_features.image_text}")
        
        if product_features.image_labels:
            prompt_parts.append(f"Labels Detected in Image: {', '.join(product_features.image_labels)}")
        
        if destination_country:
            prompt_parts.append(f"\nDestination Country: {destination_country}")
        
        prompt_parts.append(f"\n{similar_products_context}")
        
        prompt_parts.append(
            "\nBased on the product information and similar products above, "
            "predict the most appropriate HS code with confidence percentage. "
            "If confidence is below 70%, provide up to 3 alternative HS codes."
        )
        
        return "\n".join(prompt_parts)
    
    def _fallback_prediction_from_similar(self, similar_products: List[Document]) -> HSCodePrediction:
        """
        Fallback prediction using the most similar product's HS code.
        
        Args:
            similar_products: List of similar products
            
        Returns:
            HSCodePrediction based on most similar product
        """
        if not similar_products:
            return HSCodePrediction(
                code="0000.00",
                confidence=0.0,
                description="No similar products found",
                alternatives=[]
            )
        
        # Use the most similar product (first in list)
        most_similar = similar_products[0]
        hs_code = most_similar.metadata.get('hs_code', '0000.00')
        product_name = most_similar.metadata.get('product_name', 'Unknown')
        relevance = most_similar.relevance_score or 0.0
        
        # Convert relevance score to confidence (scale 0-1 to 0-100)
        confidence = min(relevance * 100, 60.0)  # Cap at 60% for fallback
        
        # Build alternatives from other similar products
        alternatives = []
        for doc in similar_products[1:4]:  # Up to 3 alternatives
            alt_code = doc.metadata.get('hs_code')
            if alt_code and alt_code != hs_code:
                alt_relevance = doc.relevance_score or 0.0
                alt_confidence = min(alt_relevance * 100, 50.0)
                alt_name = doc.metadata.get('product_name', 'Similar product')
                
                alternatives.append(HSCodeAlternative(
                    code=alt_code,
                    confidence=alt_confidence,
                    description=f"Based on similar product: {alt_name}"
                ))
        
        logger.warning(
            f"Using fallback prediction from similar product: {product_name} "
            f"(HS code: {hs_code}, confidence: {confidence}%)"
        )
        
        return HSCodePrediction(
            code=hs_code,
            confidence=confidence,
            description=f"Based on similar product: {product_name}",
            alternatives=alternatives
        )


# Convenience function for quick HS code prediction
def predict_hs_code(
    product_name: str,
    image: Optional[bytes] = None,
    bom: Optional[str] = None,
    ingredients: Optional[str] = None,
    destination_country: Optional[str] = None
) -> HSCodePrediction:
    """
    Convenience function to predict HS code.
    
    Args:
        product_name: Name of the product
        image: Product image bytes (optional)
        bom: Bill of Materials (optional)
        ingredients: Product ingredients (optional)
        destination_country: Destination country (optional)
        
    Returns:
        HSCodePrediction with code, confidence, and alternatives
    """
    predictor = HSCodePredictor()
    return predictor.predict_hs_code(
        product_name=product_name,
        image=image,
        bom=bom,
        ingredients=ingredients,
        destination_country=destination_country
    )
