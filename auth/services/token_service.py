import logging
from uuid import UUID

from core.config import settings
from core.security import verify_password
from fastapi import HTTPException, status
from jose import JWTError, jwt
from models.user import User
from schemas.auth import ChangePassword

logger = logging.getLogger(__name__)


async def decode_token(authorization: str):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization.split(" ")[1]
    # logger.info(f"authorization token: {authorization}")

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id: str = payload.get("id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return UUID(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def verify_old_password(request_data: ChangePassword, current_user: User) -> None:
    if not verify_password(request_data.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
