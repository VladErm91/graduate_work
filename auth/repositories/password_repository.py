import logging

from core.security import get_password_hash
from fastapi import HTTPException, status
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def update_password(
    current_user: User,
    new_password: str,
    db: AsyncSession,
) -> None:
    hashed_password = get_password_hash(new_password)
    current_user.password = hashed_password

    try:
        await db.commit()
        logger.info(f"Password changed for user: {current_user.login}")
    except Exception as e:
        logger.error(f"Error changing password for user {current_user.login}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password",
        )
