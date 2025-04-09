# recommendation_service/core/redis.py

from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis

from core.config import settings

async_redis = None
sync_redis = None


async def get_redis() -> AsyncRedis:
    global async_redis
    if async_redis is None:
        async_redis = await AsyncRedis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return async_redis


def get_sync_redis() -> SyncRedis:
    global sync_redis
    if sync_redis is None or sync_redis.connection_pool.connection is None:
        sync_redis = SyncRedis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return sync_redis
