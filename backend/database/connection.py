"""
PostgreSQL Connection Manager for Yacco Health
Enterprise-grade async database connection with connection pooling
"""

import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql+asyncpg://yacco:yacco_secure_2024@localhost:5432/yacco_health'
)

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=os.environ.get('SQL_ECHO', 'false').lower() == 'true',
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_async_session() -> AsyncSession:
    """Get async database session - use as dependency"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db():
    """Context manager for database session"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - create tables"""
    from .models import Base
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")


async def check_db_connection():
    """Check database connectivity"""
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
