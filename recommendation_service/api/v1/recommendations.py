from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.redis import get_redis
from redis.asyncio import Redis as AsyncRedis
from recommendation_model import recommendation_model
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{user_id}")
async def get_recommendations(
    user_id: str, db: AsyncSession = Depends(get_db), redis: AsyncRedis = Depends(get_redis)
):
    cache_key = f"recommendations:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        logger.info(f"Cache hit for user {user_id}: {cached}")
        return json.loads(cached)

    # Если кэша нет, генерируем рекомендации
    result = await recommendation_model.get_recommendations(user_id, db)
    logger.info(f"Cache miss for user {user_id}, generated: {result}")

    # Сохраняем в кэш
    try:
        await redis.setex(f"recommendations:{user_id}", 3600, json.dumps(result))
        logger.info(f"Cached recommendations for user {user_id}: {result}")
    except Exception as e:
        logger.error(f"Failed to cache recommendations for user {user_id}: {e}")
    return result
