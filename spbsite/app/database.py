from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from spb_shared.database import Base  # Import shared Base

# Import all models to register them with Base
from spb_shared import models  # noqa: F401

# Single database (banuxSPB) - all tables (operational + catalog)
engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Get database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
