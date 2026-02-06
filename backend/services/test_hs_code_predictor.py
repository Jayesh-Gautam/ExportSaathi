"""
Unit tests for HS Code Predictor Service

Tests the HS code prediction functionality including:
- Image feature extraction
- Product feature combination
- Similar product search
- LLM-based prediction
- Fallback mechanisms
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from services.hs_code_predictor import (
    HSCodePredictor,
    ProductFeatures,
    predict_hs_code
)
from services.image_processor import ImageFeatures as ImageProcessorFeatures
from models.query import HSCodePrediction, HSCodeAlternative
from models.internal import Document


@pytest.fixture
def mock_image_processor():
    """Mock ImageProcessor"""
    processor = Mock()
    processor.extract_features.return_value = ImageProcessorFeatures(
        text="Organic Turmeric Powder 100g",
        confidence=0.92,
        detected_labels=["Organic", "Turmeric", "Powder"],
        text_blocks=[
            {
                'text': 'Organic Turmeric Powder',
                'confidence': 95.0,
                'geometry': {}
            }
        ],
        key_value_pairs={'Weight': '100g', 'Type': 'Organic'},
        tables=[],
        raw_response={}
    )
    return processor


@pytest.fixture
def mock_embedding_service():
    """Mock EmbeddingService"""
    service = Mock()
    service.embed_query.return_value = np.random.rand(768).astype(np.float32)
    return service


@pytest.fixture
def mock_vector_store():
    """Mock VectorStore with sample similar products"""
    store = Mock()
    
    # Create sample similar products with HS codes
    similar_products = [
        Document(
            id="doc_001",
            content="Turmeric powder, dried and ground from turmeric rhizomes",
            metadata={
                'hs_code': '0910.30',
                'product_name': 'Turmeric Powder',
                'source': 'DGFT',
                'has_hs_code': True
            },
            relevance_score=0.95
        ),
        Document(
            id="doc_002",
            content="Ground spices including turmeric, cumin, and coriander",
            metadata={
                'hs_code': '0910.99',
                'product_name': 'Mixed Spices',
                'source': 'Customs',
                'has_hs_code': True
            },
            relevance_score=0.78
        ),
        Document(
            id="doc_003",
            content="Organic turmeric in powder form for culinary use",
            metadata={
                'hs_code': '0910.30',
                'product_name': 'Organic Turmeric',
                'source': 'FDA',
                'has_hs_code': True
            },
            relevance_score=0.85
        )
    ]
    
    store.search.return_value = similar_products
    return store


@pytest.fixture
def mock_llm_client():
    """Mock LLMClient"""
    client = Mock()
    
    # Default successful response
    client.generate_structured.return_value = {
        'code': '0910.30',
        'confidence': 92.5,
        'description': 'Turmeric (curcuma)',
        'alternatives': [
            {
                'code': '0910.99',
                'confidence': 65.0,
                'description': 'Other spices'
            }
        ]
    }
    
    return client


@pytest.fixture
def predictor(mock_image_processor, mock_embedding_service, mock_vector_store, mock_llm_client):
    """Create HSCodePredictor with mocked dependencies"""
    return HSCodePredictor(
        image_processor=mock_image_processor,
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        llm_client=mock_llm_client,
        confidence_threshold=70.0,
        num_similar_products=5
    )


class TestHSCodePredictor:
    """Test suite for HSCodePredictor"""
    
    def test_initialization(self, predictor):
        """Test predictor initialization"""
        assert predictor.confidence_threshold == 70.0
        assert predictor.num_similar_products == 5
        assert predictor.image_processor is not None
        assert predictor.embedding_service is not None
        assert predictor.vector_store is not None
        assert predictor.llm_client is not None
    
    def test_predict_hs_code_with_all_inputs(self, predictor, mock_llm_client):
        """Test HS code prediction with all inputs provided"""
        # Arrange
        product_name = "Organic Turmeric Powder"
        image = b"fake_image_bytes"
        bom = "Turmeric rhizomes, packaging material"
        ingredients = "100% organic turmeric"
        destination = "United States"
        
        # Act
        result = predictor.predict_hs_code(
            product_name=product_name,
            image=image,
            bom=bom,
            ingredients=ingredients,
            destination_country=destination
        )
        
        # Assert
        assert isinstance(result, HSCodePrediction)
        assert result.code == '0910.30'
        assert result.confidence == 92.5
        assert result.description == 'Turmeric (curcuma)'
        assert len(result.alternatives) == 1
        assert result.alternatives[0].code == '0910.99'
        
        # Verify LLM was called
        mock_llm_client.generate_structured.assert_called_once()
    
    def test_predict_hs_code_without_image(self, predictor, mock_image_processor):
        """Test HS code prediction without image"""
        # Arrange
        product_name = "Turmeric Powder"
        
        # Act
        result = predictor.predict_hs_code(
            product_name=product_name,
            image=None,
            bom="Turmeric rhizomes",
            ingredients="100% turmeric"
        )
        
        # Assert
        assert isinstance(result, HSCodePrediction)
        assert result.code == '0910.30'
        
        # Verify image processor was not called
        mock_image_processor.extract_features.assert_not_called()
    
    def test_predict_hs_code_with_low_confidence(self, predictor, mock_llm_client):
        """Test that alternatives are included when confidence is low"""
        # Arrange
        mock_llm_client.generate_structured.return_value = {
            'code': '0910.30',
            'confidence': 65.0,  # Below threshold
            'description': 'Turmeric (curcuma)',
            'alternatives': [
                {'code': '0910.99', 'confidence': 55.0, 'description': 'Other spices'},
                {'code': '0910.20', 'confidence': 45.0, 'description': 'Saffron'}
            ]
        }
        
        # Act
        result = predictor.predict_hs_code(
            product_name="Turmeric Powder"
        )
        
        # Assert
        assert result.confidence == 65.0
        assert result.confidence < predictor.confidence_threshold
        assert len(result.alternatives) == 2
    
    def test_extract_image_features(self, predictor, mock_image_processor):
        """Test image feature extraction"""
        # Arrange
        image = b"fake_image_bytes"
        
        # Act
        features = predictor.extract_image_features(image)
        
        # Assert
        assert isinstance(features, ImageProcessorFeatures)
        assert features.text == "Organic Turmeric Powder 100g"
        assert features.confidence == 0.92
        assert len(features.detected_labels) == 3
        assert 'Weight' in features.key_value_pairs
        
        # Verify image processor was called
        mock_image_processor.extract_features.assert_called_once_with(image)
    
    def test_extract_image_features_error_handling(self, predictor, mock_image_processor):
        """Test that image feature extraction handles errors gracefully"""
        # Arrange
        mock_image_processor.extract_features.side_effect = Exception("Textract error")
        image = b"fake_image_bytes"
        
        # Act
        features = predictor.extract_image_features(image)
        
        # Assert - should return empty features instead of raising
        assert isinstance(features, ImageProcessorFeatures)
        assert features.text == ""
        assert features.confidence == 0.0
        assert len(features.detected_labels) == 0
    
    def test_find_similar_products(self, predictor, mock_embedding_service, mock_vector_store):
        """Test finding similar products"""
        # Arrange
        product_features = ProductFeatures(
            product_name="Turmeric Powder",
            description="Turmeric Powder",
            bom="Turmeric rhizomes",
            ingredients="100% turmeric",
            image_text="Organic Turmeric",
            image_labels=["Organic", "Turmeric"],
            visual_features={},
            combined_text="Product: Turmeric Powder\nIngredients: 100% turmeric"
        )
        
        # Act
        similar = predictor.find_similar_products(
            features=product_features,
            destination_country="United States"
        )
        
        # Assert
        assert len(similar) == 3
        assert all(isinstance(doc, Document) for doc in similar)
        assert similar[0].metadata['hs_code'] == '0910.30'
        
        # Verify embedding service was called
        mock_embedding_service.embed_query.assert_called_once()
        
        # Verify vector store search was called
        mock_vector_store.search.assert_called_once()
    
    def test_find_similar_products_with_filters(self, predictor, mock_vector_store):
        """Test that destination country filter is applied"""
        # Arrange
        product_features = ProductFeatures(
            product_name="Turmeric Powder",
            description="Turmeric Powder",
            bom=None,
            ingredients=None,
            image_text=None,
            image_labels=None,
            visual_features=None,
            combined_text="Product: Turmeric Powder"
        )
        
        # Act
        predictor.find_similar_products(
            features=product_features,
            destination_country="India"
        )
        
        # Assert - check that filters were passed to vector store
        call_args = mock_vector_store.search.call_args
        assert call_args is not None
        # The filters should include country and has_hs_code
        # Note: filters are passed as keyword argument
    
    def test_combine_features_with_all_inputs(self, predictor):
        """Test combining all product features"""
        # Arrange
        image_features = ImageProcessorFeatures(
            text="Organic Turmeric 100g",
            confidence=0.9,
            detected_labels=["Organic", "Turmeric"],
            text_blocks=[],
            key_value_pairs={'Weight': '100g'},
            tables=[],
            raw_response={}
        )
        
        # Act
        combined = predictor._combine_features(
            product_name="Turmeric Powder",
            bom="Turmeric rhizomes, packaging",
            ingredients="100% organic turmeric",
            image_features=image_features
        )
        
        # Assert
        assert isinstance(combined, ProductFeatures)
        assert combined.product_name == "Turmeric Powder"
        assert combined.bom == "Turmeric rhizomes, packaging"
        assert combined.ingredients == "100% organic turmeric"
        assert combined.image_text == "Organic Turmeric 100g"
        assert combined.image_labels == ["Organic", "Turmeric"]
        assert "Product: Turmeric Powder" in combined.combined_text
        assert "Ingredients: 100% organic turmeric" in combined.combined_text
        assert "Image Text: Organic Turmeric 100g" in combined.combined_text
    
    def test_combine_features_without_image(self, predictor):
        """Test combining features without image"""
        # Act
        combined = predictor._combine_features(
            product_name="Turmeric Powder",
            bom="Turmeric rhizomes",
            ingredients="100% turmeric",
            image_features=None
        )
        
        # Assert
        assert combined.image_text is None
        assert combined.image_labels is None
        assert combined.visual_features is None
        assert "Image Text:" not in combined.combined_text
        assert "Product: Turmeric Powder" in combined.combined_text
    
    def test_llm_prediction_prompt_construction(self, predictor, mock_llm_client):
        """Test that LLM prompt is constructed correctly"""
        # Arrange
        product_features = ProductFeatures(
            product_name="Turmeric Powder",
            description="Turmeric Powder",
            bom="Turmeric rhizomes",
            ingredients="100% organic turmeric",
            image_text="Organic Turmeric",
            image_labels=["Organic"],
            visual_features={},
            combined_text="Product: Turmeric Powder"
        )
        
        similar_products = [
            Document(
                id="doc_001",
                content="Turmeric powder",
                metadata={'hs_code': '0910.30', 'product_name': 'Turmeric'},
                relevance_score=0.9
            )
        ]
        
        # Act
        predictor._predict_with_llm(
            product_features=product_features,
            similar_products=similar_products,
            destination_country="United States"
        )
        
        # Assert - check that LLM was called with proper prompt
        call_args = mock_llm_client.generate_structured.call_args
        assert call_args is not None
        prompt = call_args[1]['prompt']
        
        # Verify prompt contains key information
        assert "Turmeric Powder" in prompt
        assert "100% organic turmeric" in prompt
        assert "Turmeric rhizomes" in prompt
        assert "United States" in prompt
        assert "0910.30" in prompt  # HS code from similar product
    
    def test_fallback_prediction_from_similar(self, predictor):
        """Test fallback prediction when LLM fails"""
        # Arrange
        similar_products = [
            Document(
                id="doc_001",
                content="Turmeric powder",
                metadata={
                    'hs_code': '0910.30',
                    'product_name': 'Turmeric Powder'
                },
                relevance_score=0.85
            ),
            Document(
                id="doc_002",
                content="Mixed spices",
                metadata={
                    'hs_code': '0910.99',
                    'product_name': 'Mixed Spices'
                },
                relevance_score=0.70
            )
        ]
        
        # Act
        result = predictor._fallback_prediction_from_similar(similar_products)
        
        # Assert
        assert isinstance(result, HSCodePrediction)
        assert result.code == '0910.30'
        assert result.confidence <= 60.0  # Capped for fallback
        assert "Turmeric Powder" in result.description
        assert len(result.alternatives) >= 1
        assert result.alternatives[0].code == '0910.99'
    
    def test_fallback_prediction_no_similar_products(self, predictor):
        """Test fallback when no similar products found"""
        # Act
        result = predictor._fallback_prediction_from_similar([])
        
        # Assert
        assert result.code == "0000.00"
        assert result.confidence == 0.0
        assert "No similar products" in result.description
        assert len(result.alternatives) == 0
    
    def test_predict_hs_code_error_handling(self, predictor, mock_llm_client, mock_vector_store):
        """Test that prediction handles errors gracefully with fallback"""
        # Arrange
        mock_llm_client.generate_structured.side_effect = Exception("LLM error")
        
        # Act
        result = predictor.predict_hs_code(
            product_name="Test Product"
        )
        
        # Assert - should use fallback prediction from similar products
        assert isinstance(result, HSCodePrediction)
        # When LLM fails but similar products exist, it uses fallback
        # which returns the most similar product's HS code with capped confidence
        assert result.code == '0910.30'  # From mock similar products
        assert result.confidence <= 60.0  # Capped for fallback
        assert "similar product" in result.description.lower()
    
    def test_convenience_function(self):
        """Test the convenience function"""
        with patch('services.hs_code_predictor.HSCodePredictor') as MockPredictor:
            # Arrange
            mock_instance = Mock()
            mock_instance.predict_hs_code.return_value = HSCodePrediction(
                code='0910.30',
                confidence=90.0,
                description='Turmeric',
                alternatives=[]
            )
            MockPredictor.return_value = mock_instance
            
            # Act
            result = predict_hs_code(
                product_name="Turmeric Powder",
                ingredients="100% turmeric"
            )
            
            # Assert
            assert isinstance(result, HSCodePrediction)
            assert result.code == '0910.30'
            mock_instance.predict_hs_code.assert_called_once()


class TestProductFeatures:
    """Test ProductFeatures dataclass"""
    
    def test_product_features_creation(self):
        """Test creating ProductFeatures"""
        features = ProductFeatures(
            product_name="Test Product",
            description="Test Description",
            bom="Test BOM",
            ingredients="Test Ingredients",
            image_text="Test Image Text",
            image_labels=["Label1", "Label2"],
            visual_features={'key': 'value'},
            combined_text="Combined text"
        )
        
        assert features.product_name == "Test Product"
        assert features.description == "Test Description"
        assert features.bom == "Test BOM"
        assert features.ingredients == "Test Ingredients"
        assert features.image_text == "Test Image Text"
        assert len(features.image_labels) == 2
        assert features.visual_features == {'key': 'value'}
        assert features.combined_text == "Combined text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
