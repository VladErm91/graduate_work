from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository
from repositories.algorithms import AlgorithmA, AlgorithmB
from db.database import get_db

router = APIRouter()


@router.get("/{user_id}")
async def get_recommendations(user_id: str, db: AsyncSession = Depends(get_db)):
    algorithm = await UserRepository.get_user_algorithm(user_id, db)

    if algorithm == "A":
        recommendations = await AlgorithmA.get_recommendations(user_id, db)
    else:
        recommendations = await AlgorithmB.get_recommendations(user_id, db)

    return {"algorithm": algorithm, "recommendations": recommendations}
