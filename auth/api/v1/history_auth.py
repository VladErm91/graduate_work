import logging
from uuid import UUID

from async_fastapi_jwt_auth import AuthJWT
from db.db import get_session
from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, paginate
from schemas.history_auth import HistoryAuthDBModel
from services.history_auth_service import AuthHistoryService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    "/{user_id}",
    response_model=Page[HistoryAuthDBModel],
    status_code=status.HTTP_200_OK,
    summary="Получение истории аутентификаций пользователя",
)
async def get_auth_history(
    user_id: UUID,
    Authorize: AuthJWT = Depends(),
    db: AsyncSession = Depends(get_session),
) -> Page[HistoryAuthDBModel]:

    history_user = await AuthHistoryService.get_auth_history(user_id, Authorize, db)
    return paginate(history_user)
