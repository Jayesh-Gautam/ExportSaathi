"""
Database initialization script for ExportSathi.
Creates all tables and sets up the database schema.
"""
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.connection import db_connection, init_db, check_db_connection
from backend.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database."""
    logger.info("Starting database initialization...")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not configured'}")
    
    # Check database connection
    logger.info("Checking database connection...")
    if not check_db_connection():
        logger.error("Failed to connect to database. Please check your DATABASE_URL configuration.")
        sys.exit(1)
    
    logger.info("Database connection successful!")
    
    # Initialize tables
    logger.info("Creating database tables...")
    try:
        init_db()
        logger.info("✓ Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        sys.exit(1)
    
    logger.info("Database initialization complete!")
    logger.info("\nNext steps:")
    logger.info("1. Run 'alembic upgrade head' to apply migrations")
    logger.info("2. Start the FastAPI server with 'uvicorn backend.main:app --reload'")


if __name__ == "__main__":
    main()
