from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from repositories.history_repository import HistoryRepository
from core.database import get_db
from core.redis import get_redis
from core.kafka_utils import get_producer

router = APIRouter()


@router.post("/{user_id}/{movie_id}")
async def add_to_history(
    user_id: str,
    movie_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    await HistoryRepository.save_user_history(user_id, movie_id, db)
    await redis.delete(f"recommendations:{user_id}")
    producer = get_producer()
    producer.send("user_history", {"user_id": user_id, "movie_id": movie_id})
    return {"message": "Added to history, recommendations will be updated soon"}
