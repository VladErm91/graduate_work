from random import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User


class UserRepository:
    @staticmethod
    async def get_user_by_id(user_id: str, db: AsyncSession):
        result = await db.execute(select(User).filter(User.user_id == user_id))
        return result.scalar()

    @staticmethod
    async def get_user_algorithm(user_id: str, db: AsyncSession):
        query = "SELECT algorithm FROM user_algorithms WHERE user_id = :user_id"
        result = await db.execute(query, {"user_id": user_id})
        algorithm = result.scalar()

        if not algorithm:
            weights = await db.execute(
                "SELECT algorithm, weight FROM algorithm_weights"
            )
            weights = dict(weights.fetchall())  # {"A": 0.7, "B": 0.3}

            algorithm = random.choices(
                list(weights.keys()), weights=list(weights.values())
            )[0]
            await db.execute(
                "INSERT INTO user_algorithms (user_id, algorithm) VALUES (:user_id, :algorithm)",
                {"user_id": user_id, "algorithm": algorithm},
            )
            await db.commit()

        return algorithm
