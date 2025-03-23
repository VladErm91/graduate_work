import logging
from urllib.parse import urlencode

from core.auth import get_user_from_token, oauth2_scheme
from core.config import settings
from core.jwt import create_access_token, verify_token
from db.db import get_session
from db.redis import get_redis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from repositories.token_repository import TokenRepository
from schemas.auth import Token
from services.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    # Аутентификация пользователя
    user = await AuthService.authenticate_user(
        db, form_data.username, form_data.password, request
    )

    user_roles = [role.name for role in user.roles]

    user_data = {
        "id": str(user.id),
        "login": user.login,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "roles": user_roles,
    }
    # Генерация токенов
    access_token, refresh_token = await AuthService.create_tokens(user_data)

    # Сохранение токенов в Redis
    await TokenRepository.store_tokens(
        redis,
        str(user.id),
        access_token,
        refresh_token,
        settings.access_token_expire_minutes * 60,
        settings.refresh_token_expire_days * 86400,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": str(user.id),
    }


# Обновление токена
@router.post("/refresh-token")
async def refresh_token(
    token: str,
    redis: Redis = Depends(get_redis),
):
    payload = verify_token(token, refresh=True)  # Проверка refresh-токена
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("id")

    # Создаем новый access-токен
    new_access_token = create_access_token({"id": str(user_id)})

    # Обновляем токен в Redis
    await redis.set(
        f"access_token:{user_id}",
        new_access_token,
        ex=settings.access_token_expire_minutes * 60,
    )

    return {"access_token": new_access_token}


# Выход из системы (логаут)
@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis),
):
    user_id = await get_user_from_token(token)

    # Удаление токенов из Redis
    await TokenRepository.delete_tokens(redis, user_id)

    return {"msg": "Successfully logged out"}


# Логаут со всех устройств
@router.post("/logout-all")
async def logout_all(
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis),
):
    user_id = await get_user_from_token(token)

    # Удаление всех токенов пользователя из Redis
    await TokenRepository.delete_tokens(redis, user_id)

    return {"msg": "Successfully logged out from all devices"}


@router.get("/social/login")
async def social_login(provider: str):
    if provider not in settings.providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider",
        )

    provider_conf = settings.providers[provider]
    params = {
        "client_id": provider_conf.client_id,
        "redirect_uri": provider_conf.redirect_uri,
        "response_type": "code",
        "scope": provider_conf.scope,
        "state": "random_state_string",
    }

    auth_url = f"{provider_conf.auth_url}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/social/callback")
async def social_callback(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    if provider not in settings.providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider",
        )

    code = request.query_params.get("code")

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided",
        )

    user = await AuthService.authenticate(db, provider, code)
    user_roles = [role.name for role in user.roles]

    user_data = {
        "id": str(user.id),
        "login": user.login,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "roles": user_roles,
    }
    access_token, refresh_token = await AuthService.create_tokens(user_data)

    await TokenRepository.store_tokens(
        redis,
        str(user.id),
        access_token,
        refresh_token,
        settings.access_token_expire_minutes * 60,
        settings.refresh_token_expire_days * 86400,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": str(user.id),
    }
