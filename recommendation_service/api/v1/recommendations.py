from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository
from core.database import get_db
from core.redis import get_redis
from redis.asyncio import Redis
from recommendation_service.ml.recommendation_model import recommendation_model
import json

router = APIRouter()


@router.get("/{user_id}")
async def get_recommendations(
    user_id: str, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
):
    cache_key = f"recommendations:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    await recommendation_model.train(db)
    recommendations = await recommendation_model.get_recommendations(user_id, db)
    algorithm = await UserRepository.get_user_algorithm(user_id, db)
    result = {"algorithm": algorithm, "recommendations": recommendations}
    await redis.setex(cache_key, 3600, json.dumps(result))
    return result
