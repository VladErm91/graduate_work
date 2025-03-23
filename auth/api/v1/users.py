import logging
from uuid import UUID

from api.v1.role import is_admin
from core.auth import get_current_user
from db.db import get_session
from fastapi import APIRouter, Depends, Header, HTTPException, status
from models.user import User
from repositories.password_repository import update_password
from repositories.user_repository import (
    delete_user,
    get_user_action_history,
    get_user_by_id,
    get_user_by_login,
    get_user_roles,
)
from schemas.auth import ChangePassword
from schemas.user import UserCreate, UserOut, UserProfile, UserUpdate
from services.token_service import decode_token, verify_old_password
from services.user_activity_service import log_user_action
from services.user_service import build_user_profile, register_user, update_user_profile
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


# Регистрация пользователя
@router.post("/register", response_model=UserOut)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_session),
):
    # Проверка, существует ли уже пользователь с таким логином
    existing_user = await get_user_by_login(db, user.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already registered",
        )

    new_user = await register_user(db, user)
    logger.info(f"User {new_user.login} registered successfully.")
    return new_user


# Получение профиля пользователя
@router.get("/me", response_model=UserProfile)
async def get_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Получение ролей пользователя
    roles = await get_user_roles(current_user)

    # Получаем историю действий
    activity = await get_user_action_history(session, current_user.id)

    # Собираем профиль
    user_profile = await build_user_profile(current_user, roles, activity)
    return user_profile


# Обновление профиля пользователя
@router.put("/me", response_model=UserOut)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    # Обновление имени и фамилии пользователя
    updated_user = await update_user_profile(db, current_user, update_data)
    await log_user_action(db, current_user.id, "update_profile")
    logging.info(f"User {current_user.login} updated their profile.")

    return updated_user


@router.put("/change-password", response_model=dict)
async def change_password(
    request_data: ChangePassword,
    authorization: str = Header(),
    db: AsyncSession = Depends(get_session),
):

    user_id = await decode_token(authorization)  # Проверка токена
    current_user = await get_user_by_id(db, user_id)  # Получение пользователя
    verify_old_password(
        request_data,
        current_user,
    )  # Проверка старого пароля# Декодируем JWT токен
    await update_password(
        current_user,
        request_data.new_password,
        db,
    )  # Изменение пароля
    await log_user_action(
        db,
        current_user.id,
        "change_password",
    )  # Запись действия в историю

    return {"msg": "Password changed successfully"}


@router.delete("/users/{user_id}")
async def delete(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
    _: bool = Depends(is_admin),
):

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"{user} not found")
    await delete_user(db, user)
    return {"message": f"{user} deleted successfully."}

@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(is_admin),
):
    # Получение ролей пользователя
    user = await get_user_by_id(db, user_id)
    roles = await get_user_roles(user)

    # Получаем историю действий
    activity = await get_user_action_history(session, user.id)

    # Собираем профиль
    user_profile = await build_user_profile(user, roles, activity)
    return user_profile