"""Database configuration and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def get_async_engine(database_url: str, echo: bool = False) -> AsyncEngine:
    """Create async database engine.

    Args:
        database_url: Database connection URL (postgresql+asyncpg:// or sqlite+aiosqlite://)
        echo: Whether to log all SQL statements

    Returns:
        AsyncEngine instance
    """
    return create_async_engine(database_url, echo=echo)


def get_async_session(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create async session factory.

    Args:
        engine: AsyncEngine instance

    Returns:
        async_sessionmaker for creating sessions
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions.

    Args:
        session_factory: Session factory created by get_async_session

    Yields:
        AsyncSession instance
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
