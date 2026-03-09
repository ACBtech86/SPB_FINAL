from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from spb_shared.database import Base  # Import shared Base

# Import all models to register them with Base
from spb_shared import models  # noqa: F401

# Main database (spbsite.db) - operational tables
engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Catalog database (spb_catalog) - unified SPB message catalog
catalog_engine = create_async_engine(settings.catalog_database_url, echo=False)
catalog_async_session = async_sessionmaker(catalog_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Get main database session (operational tables)."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_catalog_db():
    """Get catalog database session (form catalog tables)."""
    async with catalog_async_session() as session:
        try:
            yield session
        finally:
            await session.close()
