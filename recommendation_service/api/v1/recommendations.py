from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services.hybrid_recommender import HybridRecommender

router = APIRouter()
recommender = HybridRecommender()


@router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str, db: AsyncSession = Depends(get_db)):
    return await recommender.get_hybrid_recommendations(user_id, db)
