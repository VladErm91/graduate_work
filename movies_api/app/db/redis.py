from typing import Optional

from core.config import settings
from db.interfaces import AsyncCache
from redis.asyncio import Redis


class RedisCache(AsyncCache):
    def __init__(self, redis_instance: Redis):
        self.redis_instance = redis_instance

    async def get(self, key: str) -> Optional[str]:
        value = await self.redis_instance.get(key)
        return value.decode("utf-8") if value else None

    async def set(self, key: str, value: str, ex: int) -> None:
        await self.redis_instance.set(key, value, ex=ex)

    async def close(self):
        raise NotImplementedError

    def generate_cache_key(self, index: str, params_to_key: dict) -> str:
        """Генерация ключа для кеширования"""
        if not params_to_key:
            raise TypeError("Missing parameters to generate cache-key")

        sorted_keys = sorted(params_to_key.keys())
        volumes = [
            "{0}::{1}".format(key, str(params_to_key[key])) for key in sorted_keys
        ]
        cache_key = "{0}::{1}".format(index, "::".join(volumes))
        return cache_key


def get_cache_service() -> AsyncCache:
    redis_instance = Redis(host=settings.redis_host, port=settings.redis_port)
    return RedisCache(redis_instance)
