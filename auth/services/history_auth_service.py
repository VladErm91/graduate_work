import logging
from uuid import UUID

from async_fastapi_jwt_auth import AuthJWT
from fastapi import APIRouter, HTTPException
from models.history_auth import AuthenticationHistory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter()

logger = logging.getLogger(__name__)


class AuthHistoryService:
    @staticmethod
    async def get_auth_history(user_id: UUID, Authorize: AuthJWT, db: AsyncSession):
        try:
            Authorize.jwt_required()
        except Exception as e:
            logger.exception(f"Error getting id: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        query = select(AuthenticationHistory).filter(
            AuthenticationHistory.user_id == user_id,
        )
        result = await db.execute(query)

        history_user = result.scalars().all()
        return history_user
