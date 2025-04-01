# recommendation_service/core/mongo.py

from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

mongo_client = None


async def get_mongo_client() -> AsyncIOMotorClient:
    global mongo_client
    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
    return mongo_client


async def get_mongo_db():
    client = await get_mongo_client()
    return client[settings.MONGO_DB_NAME]
