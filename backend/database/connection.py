"""
Database connection and session management for ExportSathi.
Provides connection pooling and session utilities for SQLAlchemy.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Database connection manager with connection pooling."""
    
    def __init__(self):
        """Initialize database connection with pooling."""
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Create SQLAlchemy engine with connection pooling."""
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                settings.DATABASE_URL,
                poolclass=QueuePool,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=settings.DEBUG,  # Log SQL queries in debug mode
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Add connection event listeners
            self._setup_event_listeners()
            
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    def _setup_event_listeners(self):
        """Setup event listeners for connection management."""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Event listener for new connections."""
            logger.debug("New database connection established")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Event listener for connection checkout from pool."""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Event listener for connection checkin to pool."""
            logger.debug("Connection checked in to pool")
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            Session: SQLAlchemy session instance
        """
        if self.SessionLocal is None:
            raise RuntimeError("Database connection not initialized")
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope for database operations.
        
        Usage:
            with db.session_scope() as session:
                session.add(user)
                # Automatically commits on success, rolls back on error
        
        Yields:
            Session: SQLAlchemy session instance
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database connection and dispose of connection pool."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# Global database connection instance
db_connection = DatabaseConnection()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.
    
    Usage in FastAPI endpoint:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    
    Yields:
        Session: SQLAlchemy session instance
    """
    session = db_connection.get_session()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models if they don't exist.
    """
    from backend.database.models import Base
    
    try:
        Base.metadata.create_all(bind=db_connection.engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise


def drop_db():
    """
    Drop all database tables.
    WARNING: This will delete all data! Use only in development/testing.
    """
    from backend.database.models import Base
    
    try:
        Base.metadata.drop_all(bind=db_connection.engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with db_connection.session_scope() as session:
            session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
