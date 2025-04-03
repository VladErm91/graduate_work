# recommendation_service/tasks.py
from rq import Queue
from core.redis import get_redis, get_sync_redis
from core.mongo import get_mongo_db
from ml.recommendation_model import recommendation_model
import json
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_queue() -> Queue:
    redis = get_sync_redis()
    return Queue(connection=redis)


async def update_recommendations_async(user_id: str, model_type: str = "als"):
    db = await get_mongo_db()
    result = await recommendation_model.get_recommendations(
        user_id, db, model_type=model_type
    )
    cache_data = {
        "source": result["source"],
        "recommendations": result["recommendations"],
    }
    redis = await get_redis()
    cache_key = f"recommendations:{user_id}:{model_type}"
    await redis.setex(cache_key, 3600, json.dumps(cache_data))
    logger.info(
        f"Cached {model_type} recommendations for user {user_id} via RQ: {cache_data}"
    )


def update_recommendations(user_id: str, model_type: str = "als"):
    asyncio.run(update_recommendations_async(user_id, model_type))


async def update_all_recommendations_async():
    db = await get_mongo_db()
    users = await db["watched_movies"].distinct("user_id")
    queue = get_queue()
    for user_id in map(str, users):
        queue.enqueue(update_recommendations, user_id, "als")
        queue.enqueue(update_recommendations, user_id, "lightfm")
        logger.info(
            f"Enqueued update_recommendations for user {user_id} with ALS and LightFM"
        )


def update_all_recommendations():
    asyncio.run(update_all_recommendations_async())


async def train_model_async():
    db = await get_mongo_db()
    await recommendation_model.train(db)


def train_model():
    asyncio.run(train_model_async())


async def schedule_training():
    queue = get_queue()
    queue.enqueue(train_model)
    logger.info("Scheduled model training")
