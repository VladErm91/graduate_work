# recommendation_service/core/redis.py

from redis.asyncio import Redis
from core.config import settings

redis = None


async def get_redis():
    global redis
    if redis is None:
        redis = await Redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return redis
