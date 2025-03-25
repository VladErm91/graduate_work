from db.redis import redis_client


class HistoryRepository:
    @staticmethod
    async def save_user_history(user_id: str, movie_id: str):
        cache_key = f"user_history:{user_id}"
        await redis_client.lpush(cache_key, movie_id)
        await redis_client.ltrim(cache_key, 0, 9)  # Храним только 10 записей
        await redis_client.expire(cache_key, 86400)  # Кешируем на 24 часа

    @staticmethod
    async def get_user_history(user_id: str):
        cache_key = f"user_history:{user_id}"
        return await redis_client.lrange(cache_key, 0, -1)
