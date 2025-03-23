import logging
from typing import Any

from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# взял за основу файл из FileAPI возможно его нужно будет дорабатывать
Base = declarative_base()

# Database URL from  settings
engine = create_async_engine(settings.get_url(), future=True, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Function to create all tables
async def create_database() -> None:
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("Database tables created successfully.")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")


# Function to drop all tables
async def purge_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Create a new async session
async def get_session() -> AsyncSession | Any:
    """Получение сессии для работы с базой данных."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
