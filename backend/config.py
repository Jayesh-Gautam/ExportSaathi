"""
Configuration settings for ExportSathi backend
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "ExportSathi"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    
    # AWS Bedrock
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    BEDROCK_TEMPERATURE: float = 0.7
    BEDROCK_MAX_TOKENS: int = 4096
    
    # AWS Textract
    TEXTRACT_ENABLED: bool = True
    
    # AWS Comprehend
    COMPREHEND_ENABLED: bool = True
    
    # AWS S3
    S3_KNOWLEDGE_BASE_BUCKET: str = "exportsathi-knowledge-base"
    S3_PRODUCT_IMAGES_BUCKET: str = "exportsathi-product-images"
    S3_GENERATED_DOCS_BUCKET: str = "exportsathi-generated-docs"
    
    # AWS RDS PostgreSQL
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/exportsathi"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Groq API (Alternative LLM)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "mixtral-8x7b-32768"
    USE_GROQ: bool = False
    
    # Vector Store
    VECTOR_STORE_TYPE: str = "faiss"  # faiss or chromadb
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    EMBEDDING_DIMENSION: int = 768
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Rate Limiting
    RATE_LIMIT_PER_HOUR: int = 100
    
    # File Upload
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/jpg"]
    
    # Redis (Optional for caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
