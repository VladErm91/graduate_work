from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from repositories.analytics_repository import AnalyticsRepository

router = APIRouter()


@router.post("/")
async def track_interaction(
    user_id: str,
    algorithm: str,
    recommended: list[str],
    clicked: list[str],
    watched: list[str],
    completed: list[str],
    db: AsyncSession = Depends(get_db),
):
    """Логируем метрики рекомендаций"""
    await AnalyticsRepository.log_interaction(
        user_id, algorithm, recommended, clicked, watched, completed, db
    )
    return {"message": "Metrics logged"}
