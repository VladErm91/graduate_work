# recommendation_service/ml/tasks.py

from rq import Queue
from core.redis import get_redis, get_sync_redis
from core.mongo import get_mongo_db
from ml.recommendation_model import recommendation_model
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_queue() -> Queue:
    redis = get_sync_redis()
    return Queue(connection=redis)


async def update_recommendations(user_id: str):
    db = await get_mongo_db()  # Просто получаем объект базы
    result = await recommendation_model.get_recommendations(user_id, db)
    cache_data = {
        "source": result["source"],
        "recommendations": result["recommendations"],
    }
    redis = await get_redis()
    await redis.setex(f"recommendations:{user_id}", 3600, json.dumps(cache_data))
    logger.info(f"Cached recommendations for user {user_id} via RQ: {cache_data}")


async def update_all_recommendations():
    db = await get_mongo_db()  # Просто получаем объект базы
    users = await db["watched_movies"].distinct("user_id")
    queue = await get_queue()
    for user_id in map(str, users):
        queue.enqueue(update_recommendations, user_id)
        logger.info(f"Enqueued update_recommendations for user {user_id}")


async def train_model():
    db = await get_mongo_db()  # Просто получаем объект базы
    await recommendation_model.train(db)
