from core.config import db

from contextvars import ContextVar
import hashlib
from uuid import UUID
from bson import ObjectId

ctx_request_id: ContextVar[str] = ContextVar("request_id")

def hash_uid(uuid_str: str) -> str:
    """
    Хеширует UUID и обрезает до 12 байт 
    """
    uuid_bytes = UUID(uuid_str).bytes
    hashed = hashlib.sha1(uuid_bytes).digest()[:12]
    return str(ObjectId(hashed))

async def is_new_user(user_id: str) -> bool:
    """Проверяет, что у пользователя нет ни лайков, ни закладок, ни отзывов, ни просмотров."""

    collections = ["likes", "bookmarks", "reviews", "watched_movies"]

    for collection in collections:
        if await db[collection].find_one({"user_id": user_id}):
            return False  # Если хотя бы одна запись найдена, значит данные есть

    return True  # Все коллекции проверены и данные отсутствуют