from typing import Optional

from core.config import settings
from redis.asyncio import Redis

# Переменная для хранения экземпляра Redis
redis: Optional[Redis] = None


# Функция для получения экземпляра Redis
async def get_redis() -> Redis:
    if redis is None:
        raise RuntimeError("Redis is not initialized")
    return redis


# Функция для инициализации подключения к Redis
async def init_redis():
    global redis
    redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=0,
        decode_responses=True,
    )
    try:
        # Пробуем сделать пинг для проверки подключения
        await redis.ping()
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Redis: {e}")


# Функция для закрытия подключения к Redis
async def close_redis():
    global redis
    if redis:
        await redis.close()
