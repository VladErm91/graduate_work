import logging

from core.config import MIN_PASSWORD_LENGTH
from fastapi import HTTPException, status
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Определяем контекст для хеширования паролей с использованием bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Функция для хеширования пароля
def get_password_hash(password: str) -> str:
    # Проверяем длину пароля
    if len(password) < MIN_PASSWORD_LENGTH:
        logger.warning(f"Attempted to hash a password that is too short: {password}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.",
        )
    hashed_password = pwd_context.hash(password)
    logger.info("Password successfully hashed.")
    return hashed_password


# Функция для проверки пароля
def verify_password(plain_password: str, hashed_password: str) -> bool:
    is_valid = pwd_context.verify(plain_password, hashed_password)
    if is_valid:
        logger.info("Password verification succeeded.")
    else:
        logger.warning("Password verification failed.")
    return is_valid
