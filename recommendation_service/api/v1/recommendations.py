# recommendation_service/api/v1/recommendations.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository
from repositories.algorithms import AlgorithmA, AlgorithmB
from core.database import get_db
from core.redis import get_redis
from redis.asyncio import Redis
import json

router = APIRouter()


@router.get("/{user_id}")
async def get_recommendations(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    # Проверяем кэш
    cache_key = f"recommendations:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Если кэша нет, получаем рекомендации
    algorithm = await UserRepository.get_user_algorithm(user_id, db)

    if algorithm == "A":
        recommendations = await AlgorithmA.get_recommendations(user_id, db)
    else:
        recommendations = await AlgorithmB.get_recommendations(user_id, db)

    result = {"algorithm": algorithm, "recommendations": recommendations}
    await redis.setex(cache_key, 3600, json.dumps(result))
    return result
