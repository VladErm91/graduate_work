# recommendation_service/repositories/user_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class UserRepository:
    @staticmethod
    async def get_user_algorithm(user_id: str, db: AsyncSession) -> str:
        from models.user_preferences import UserPreferences
        stmt = select(UserPreferences.algorithm).where(UserPreferences.user_id == user_id)
        result = await db.execute(stmt)
        algorithm = result.scalar()
        if algorithm is None:
            # Создаём запись с дефолтным алгоритмом
            pref = UserPreferences(user_id=user_id, algorithm="A")
            db.add(pref)
            await db.commit()
            return "A"
        return algorithm
