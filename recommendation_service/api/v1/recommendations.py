# recommendation_service/api/v1/recommendations.py

from fastapi import APIRouter, Depends
from core.mongo import get_mongo_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from ml.recommendation_model import recommendation_model
from core.redis import get_redis
from redis.asyncio import Redis
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{user_id}")
async def get_recommendations(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    redis: Redis = Depends(get_redis),
):
    cached = await redis.get(f"recommendations:{user_id}")
    if cached:
        logger.info(f"Cache hit for user {user_id}: {cached}")
        return json.loads(cached)

    result = await recommendation_model.get_recommendations(user_id, db)
    await redis.setex(f"recommendations:{user_id}", 3600, json.dumps(result))
    logger.info(f"Cached recommendations for user {user_id}: {result}")
    return result
