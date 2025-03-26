# recommendation_service/repositories/history_repository.py
from core.redis import get_redis  # Используем get_redis вместо redis_client


class HistoryRepository:
    @staticmethod
    async def save_user_history(user_id: str, movie_id: str):
        redis = await get_redis()
        cache_key = f"user_history:{user_id}"
        await redis.lpush(cache_key, movie_id)
        await redis.ltrim(cache_key, 0, 9)  # Храним только 10 записей
        await redis.expire(cache_key, 86400)  # Кешируем на 24 часа

    @staticmethod
    async def get_user_history(user_id: str):
        redis = await get_redis()
        cache_key = f"user_history:{user_id}"
        return await redis.lrange(cache_key, 0, -1)
