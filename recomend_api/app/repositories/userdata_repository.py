from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
mongo_db = mongo_client[settings.DATABASE_NAME]
users_collection = mongo_db["users"]  # Коллекция в MongoDB

# Асинхронная функция для чтения всех пользователей
async def read_all_users_from_mongo():
    users_cursor = users_collection.find()

    users = []
    async for user in users_cursor:
        users.append(user)
    
    return users