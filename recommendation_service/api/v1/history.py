# recommendation_service/api/v1/history.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from repositories.history_repository import HistoryRepository

router = APIRouter()


@router.get("/{user_id}")
async def get_user_history(user_id: str, db: AsyncSession = Depends(get_db)):
    """Получить историю просмотров пользователя"""
    history = await HistoryRepository.get_user_history(user_id)
    return {"user_id": user_id, "history": history}


@router.post("/{user_id}/{movie_id}")
async def add_to_history(
    user_id: str, movie_id: str, db: AsyncSession = Depends(get_db)
):
    """Добавить фильм в историю просмотров"""
    await HistoryRepository.save_user_history(user_id, movie_id)
    return {"message": f"Movie {movie_id} added to history for user {user_id}"}
