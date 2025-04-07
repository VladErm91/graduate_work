from contextvars import ContextVar

from core.config import db

ctx_request_id: ContextVar[str] = ContextVar("request_id")


# async def is_new_user(user_id: str) -> bool:
#     """Проверяет, что у пользователя нет ни лайков, ни закладок, ни отзывов, ни просмотров."""

#     collections = ["likes", "bookmarks", "reviews", "watched_movies"]

#     for collection in collections:
#         if await db[collection].find_one({"user_id": user_id}):
#             return False  # Если хотя бы одна запись найдена, значит данные есть

#     return True  # Все коллекции проверены и данные отсутствуют
