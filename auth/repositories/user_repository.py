from uuid import UUID

from models.user import User, UserActionHistory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def get_user_by_login(db: AsyncSession, login: str) -> User:
    result = await db.execute(select(User).where(User.login == login))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, new_user: User) -> User:
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def delete_user(db: AsyncSession, user: User):
    await db.delete(user)
    await db.commit()


async def get_user_roles(current_user: User) -> list[str]:
    return [role.name for role in current_user.roles]


async def get_user_action_history(session: AsyncSession, user_id: UUID) -> list[dict]:
    result = await session.execute(
        select(UserActionHistory)
        .where(UserActionHistory.user_id == user_id)
        .order_by(UserActionHistory.timestamp.desc()),
    )
    activity_logs = result.scalars().all()
    return [
        {"action": log.action, "timestamp": log.timestamp.isoformat()}
        for log in activity_logs
    ]
