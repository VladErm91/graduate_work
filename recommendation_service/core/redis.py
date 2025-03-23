import aioredis
from core.config import settings

redis = None


async def get_redis():
    global redis
    if redis is None:
        redis = await aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return redis
