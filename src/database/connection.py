"""
Database connection and session management.
"""
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from ..config import DATABASE_URL
from .models import Base
from .models_tapesearch import Base as TapeSearchBase

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""

    def __init__(self, database_url: str = None):
        """
        Initialize database connection.

        Args:
            database_url: PostgreSQL connection string. If None, uses config default.
        """
        self.database_url = database_url or DATABASE_URL
        self.engine = None
        self.SessionLocal = None

    def connect(self):
        """Create database engine and session factory."""
        try:
            self.engine = create_engine(self.database_url, echo=False)
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            logger.info("Database connection established")
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def create_tables(self):
        """Create all tables defined in models."""
        try:
            Base.metadata.create_all(bind=self.engine)
            TapeSearchBase.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy Session instance
        """
        if not self.SessionLocal:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.SessionLocal()

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope for database operations.

        Usage:
            with db.session_scope() as session:
                session.query(Model).all()
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# Global database instance
db = Database()


def init_db(database_url: str = None):
    """
    Initialize the database connection and create tables.

    Args:
        database_url: PostgreSQL connection string. If None, uses config default.
    """
    db.__init__(database_url)
    db.connect()
    db.create_tables()


def get_db_session() -> Session:
    """
    Get a database session.

    Returns:
        SQLAlchemy Session instance
    """
    return db.get_session()
