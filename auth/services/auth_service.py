import secrets
from datetime import datetime

import httpx
from core.config import settings
from core.device_type import get_device_type
from core.jwt import create_access_token, create_refresh_token
from core.security import get_password_hash, verify_password
from fastapi import HTTPException, Request, status
from models.history_auth import AuthenticationHistory
from models.user import User
from models.social_account import SocialAccount
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError


class AuthService:
    @staticmethod
    async def authenticate_user(
        db: AsyncSession, login: str, password: str, request: Request
    ):
        # Поиск пользователя по логину
        result = await db.execute(select(User).filter(User.login == login))
        user = result.scalars().first()

        # Проверка пользователя и пароля
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect login",
            )

        user_device_type = get_device_type(str(request.headers.get("User-Agent")))
        if not verify_password(password, user.password):
            await AuthService.log_auth_event(
                db, user.id, success=False, user_device_type=user_device_type
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
            )

        # Логируем успешную аутентификацию
        await AuthService.log_auth_event(
            db, user.id, success=True, user_device_type=user_device_type
        )
        return user

    @staticmethod
    async def create_tokens(user_data: dict):
        user_id = user_data["id"]
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token({"id": user_id})
        return access_token, refresh_token

    @staticmethod
    async def log_auth_event(
        session: AsyncSession, user_id: str, success: bool, user_device_type: str
    ):
        event = AuthenticationHistory(
            user_id=user_id,
            success=success,
            created_at=datetime.now(),
            user_device_type=user_device_type,
        )
        session.add(event)
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to log auth event",
            )

    @staticmethod
    async def authenticate(db: AsyncSession, provider: str, code: str) -> User:
        if provider not in settings.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported provider",
            )

        provider_conf = settings.providers[provider]
        token_params = {
            "client_id": provider_conf.client_id,
            "client_secret": provider_conf.client_secret,
            "redirect_uri": provider_conf.redirect_uri,
            "code": code,
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.get(
                provider_conf.token_url, params=token_params
            )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to obtain {provider} access token",
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        social_user_id = token_data.get("user_id") or token_data.get("sub")
        email = token_data.get("email")

        if not access_token or not social_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token response",
            )

        user_info_params = {
            "access_token": access_token,
            "v": provider_conf.api_version,
        }

        if provider == "vk":
            user_info_params.update(
                {
                    "user_ids": social_user_id,
                    "fields": "email,first_name,last_name",
                }
            )
            user_info_url = provider_conf.user_info_url
        elif provider == "google":
            user_info_url = provider_conf.user_info_url
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User info retrieval not implemented for this provider",
            )

        user_info_response = await client.get(user_info_url, params=user_info_params)

        if user_info_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to obtain {provider} user info",
            )

        user_info = user_info_response.json()

        if provider == "vk":
            if "response" not in user_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid VK user info response",
                )
            vk_user_data = user_info["response"][0]
            first_name = vk_user_data.get("first_name", "")
            last_name = vk_user_data.get("last_name", "")
            email = token_data.get("email")
        elif provider == "google":
            user_info = user_info_response.json()
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")
            email = user_info.get("email")

        stmt = (
            select(User)
            .join(SocialAccount)
            .filter(
                (SocialAccount.social_id == str(social_user_id))
                & (SocialAccount.social_name == provider)
            )
        )
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            if email:
                stmt = select(User).filter(User.email == email)
                result = await db.execute(stmt)
                user = result.scalars().first()

            if not user:
                if email:
                    login = email
                else:
                    login = f"{provider}_user_{social_user_id}"

                existing_user = await db.execute(
                    select(User).filter(User.login == login)
                )
                existing_user = existing_user.scalars().first()
                if existing_user:
                    login = f"{login}_{secrets.token_hex(4)}"

                random_password = secrets.token_urlsafe(16)
                hashed_password = get_password_hash(random_password)

                user = User(
                    login=login,
                    password=hashed_password,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    created_at=datetime.now(),
                )
                db.add(user)
                try:
                    await db.commit()
                    await db.refresh(user)
                except IntegrityError:
                    await db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create user",
                    )

            social_account = SocialAccount(
                user_id=user.id,
                social_id=str(social_user_id),
                social_name=provider,
            )
            db.add(social_account)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to link social account",
                )

        await AuthService.log_auth_event(db, user.id, success=True)

        return user
