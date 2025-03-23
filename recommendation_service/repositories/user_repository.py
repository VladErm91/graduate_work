from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User


class UserRepository:
    @staticmethod
    async def get_user_by_id(user_id: str, db: AsyncSession):
        result = await db.execute(select(User).filter(User.user_id == user_id))
        return result.scalar()
