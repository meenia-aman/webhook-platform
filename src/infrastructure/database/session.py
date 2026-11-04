from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings

# ======================================================
# Create an async engine for the database connection
# ======================================================

engine: AsyncEngine = create_async_engine(
    url=settings.DATABASE_URL,  # Database URL
    echo=settings.DB_ECHO,  # Echo SQL statements to the console
    pool_size=settings.DB_POOL_SIZE,  # Max number of connections to keep open in the pool
    max_overflow=settings.DB_MAX_OVERFLOW,  # Number of connections to keep open beyond the pool size
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # Ping the database to check if the connection is still alive
    pool_timeout=settings.DB_POOL_TIMEOUT,  # How long to wait for a connection from the pool
    future=True,  # Use the asyncio-compatible future API
)

# ======================================================
# Create an async session factory for the database session
# ======================================================

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# ======================================================
# Dependency for getting a database session
# ======================================================


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
