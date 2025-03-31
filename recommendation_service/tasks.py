# recommendation_service/tasks.py
from rq import Queue
from core.redis import get_redis, get_sync_redis
from repositories.user_repository import UserRepository
from core.database import SessionLocal
from models.user import User
from sqlalchemy import select
from recommendation_model import recommendation_model
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_queue() -> Queue:
    redis = get_sync_redis()  # Используем синхронный Redis для RQ
    return Queue(connection=redis)


async def update_recommendations(user_id: str):
    async with SessionLocal() as db:
        result = await recommendation_model.get_recommendations(user_id, db)
        algorithm = await UserRepository.get_user_algorithm(user_id, db)
        cache_data = {
            "algorithm": algorithm,
            "source": result["source"],
            "recommendations": result["recommendations"]
        }
        redis = await get_redis()
        try:
            await redis.setex(f"recommendations:{user_id}", 3600, json.dumps(cache_data))
            logger.info(f"Cached recommendations for user {user_id} via RQ: {cache_data}")
        except Exception as e:
            logger.error(f"Failed to cache recommendations for user {user_id} via RQ: {e}")


async def update_all_recommendations():
    async with SessionLocal() as db:
        stmt = select(User.user_id)
        user_ids = (await db.execute(stmt)).scalars().all()
        queue = await get_queue()
        for user_id in user_ids:
            queue.enqueue(update_recommendations, user_id)
            logger.info(f"Enqueued update_recommendations for user {user_id}")


async def train_model():
    async with SessionLocal() as db:
        await recommendation_model.train(db)
