"""Async database connection and session management."""

import ssl

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

# Supabase (and most cloud Postgres) expect SSL. Without it you can get
# ConnectionResetError: [Errno 54] Connection reset by peer on the second
# or later connection. Use direct connection (port 5432), not pooler (6543).
# See: https://supabase.com/docs/guides/database/connecting-to-postgres
_ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE  # equivalent to sslmode=require

engine = create_async_engine(
    url,
    poolclass=NullPool,
    echo=False,
    connect_args={"ssl": _ssl_context},
)

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
