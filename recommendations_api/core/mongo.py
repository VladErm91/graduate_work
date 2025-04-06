# recommendation_service/core/mongo.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.config import settings


async def get_mongo_db() -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(settings.MONGO_URL)
    return client[settings.DATABASE_NAME]
