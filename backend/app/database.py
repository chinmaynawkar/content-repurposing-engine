"""Async database connection and session management."""

# Async version of SQLAlchemy engine creation for PostgreSQL (using asyncpg driver)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
# Base class for declarative ORM table models (used for defining ORM models)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings

# Supabase URL is postgresql://... ; asyncpg needs postgresql+asyncpg://...
url = settings.DATABASE_URL
if url.startswith("postgresql://"):
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

# echo=True logs every SQL statement; use DEBUG or SQL_ECHO for troubleshooting
engine = create_async_engine(url, poolclass=NullPool, echo=False)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
