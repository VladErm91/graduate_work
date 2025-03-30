from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
import random


class UserRepository:
    @staticmethod
    async def get_user_algorithm(user_id: str, db: AsyncSession) -> str:
        stmt = select(User).where(User.user_id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            user = User(user_id=user_id, username=f"user_{user_id[:8]}", age=25)
            db.add(user)
            await db.commit()
            return "A" if random.choice([True, False]) else "B"
        return "A" if user.age < 30 else "B"
