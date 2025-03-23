from core.config import settings
from db.db import get_session
from db.redis import get_redis
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from models.user import User
from sqlalchemy.future import select
from sqlalchemy.orm import Session, selectinload
from starlette.status import HTTP_401_UNAUTHORIZED

# Определяем URL для OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/v1/login")


# Функция для декодирования JWT токена и получения текущего пользователя
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session),
    redis=Depends(get_redis),
) -> User:
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Декодируем токен с использованием секретного ключа и алгоритма
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        # print("here:", payload)
        user_id: str = payload.get("id")
        # print("here:", user_id)

        if user_id is None:
            raise credentials_exception

        # Проверяем, что токен не был заблокирован (если реализовано разлогинивание через Redis)
        redis_key = f"jwt_blacklist:{user_id}"
        token_blacklisted = await redis.exists(redis_key)
        if token_blacklisted:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Token is invalid or expired",
            )

    except JWTError:
        raise credentials_exception

    stmt = select(User).options(selectinload(User.roles)).filter(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_user_from_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id: str = payload.get("sub")
        return user_id
    except JWTError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")
