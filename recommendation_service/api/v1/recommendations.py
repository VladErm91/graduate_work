# recommendation_service/api/v1/recommendations.py
from fastapi import APIRouter, Depends
from core.mongo import get_mongo_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from ml.recommendation_model import recommendation_model
from core.redis import get_redis
from redis.asyncio import Redis
import json
import logging
from bson import ObjectId
import random
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{user_id}")
async def get_recommendations(
    user_id: str,
    model: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    redis: Redis = Depends(get_redis),
):
    model_type = (
        model if model in ["als", "lightfm"] else random.choice(["als", "lightfm"])
    )
    cache_key = f"recommendations:{user_id}:{model_type}"

    cached = await redis.get(cache_key)
    if cached:
        logger.info(f"Cache hit for user {user_id} with {model_type}: {cached}")
        return json.loads(cached)

    result = await recommendation_model.get_recommendations(
        user_id, db, model_type=model_type
    )
    await redis.setex(cache_key, 3600, json.dumps(result))

    # Сохранение рекомендаций для анализа
    await db["recommendation_logs"].insert_one(
        {
            "user_id": ObjectId(user_id),
            "model_type": model_type,
            "recommendations": result["recommendations"],
            "session_id": result["session_id"],
            "timestamp": datetime.utcnow(),
        }
    )

    logger.info(f"Cached {model_type} recommendations for user {user_id}: {result}")
    return result


@router.post("/feedback/{session_id}")
async def submit_feedback(
    session_id: str,
    movie_id: str,
    liked: bool,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    await db["feedback"].insert_one(
        {
            "session_id": session_id,
            "movie_id": ObjectId(movie_id),
            "liked": liked,
            "timestamp": datetime.utcnow(),
        }
    )
    logger.info(
        f"Feedback submitted for session {session_id}, movie {movie_id}, liked: {liked}"
    )
    return {"status": "success"}
