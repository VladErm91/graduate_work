import http
import time
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from core.config import settings


def decode_token(token: str) -> Optional[dict]:
    try:
        decoded_token = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return decoded_token if decoded_token["exp"] >= time.time() else None
    except Exception:
        return None


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(
                status_code=http.HTTPStatus.FORBIDDEN,
                detail="Invalid authorization code.",
            )
        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=http.HTTPStatus.UNAUTHORIZED,
                detail="Only Bearer token might be accepted",
            )
        decoded_token = self.parse_token(credentials.credentials)
        if not decoded_token:
            raise HTTPException(
                status_code=http.HTTPStatus.FORBIDDEN,
                detail="Invalid or expired token.",
            )
        return decoded_token

    @staticmethod
    def parse_token(jwt_token: str) -> Optional[dict]:
        return decode_token(jwt_token)

    @staticmethod
    def get_token_from_request(request: Request) -> Optional[str]:
        """
        Функция для получения токена из заголовка Authorization.

        Если токен найден в заголовке Authorization, возвращает его строку.
        """
        authorization: str = request.headers.get("Authorization")
        if authorization:
            parts = authorization.split()
            if parts[0].lower() == "bearer" and len(parts) == 2:
                return parts[1]
        return None


security_jwt = JWTBearer()
