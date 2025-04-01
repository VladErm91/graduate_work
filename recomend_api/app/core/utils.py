from contextvars import ContextVar

from core.config import db
from models.models import UserAnalysisRequest

ctx_request_id: ContextVar[str] = ContextVar("request_id")


def convert_objectid(data):
    if isinstance(data, list):
        for item in data:
            item["_id"] = str(item["_id"])
    else:
        data["_id"] = str(data["_id"])
    return data


async def user_has_no_action_data(user_id: str) -> bool:
    """Проверяет, что у пользователя нет ни лайков, ни закладок, ни отзывов, ни просмотров."""

    collections = ["likes", "bookmarks", "reviews", "movie_timestamps"]

    for collection in collections:
        if await db[collection].find_one({"user_id": user_id}):
            return False  # Если хотя бы одна запись найдена, значит данные есть

    return True  # Все коллекции проверены и данные отсутствуют


async def get_user_data(user_id: str) -> UserAnalysisRequest:
    """Загружает данные пользователя из нескольких коллекций MongoDB и собирает в объект."""

    # Загружаем данные из каждой коллекции (предполагаем, что user_id - это поле в каждой из них)
    likes = await db.likes.find({"user_id": user_id}).to_list(None)
    reviews = await db.reviews.find({"user_id": user_id}).to_list(None)
    bookmarks = await db.bookmarks.find({"user_id": user_id}).to_list(None)
    movie_timestamps = await db.views.find({"user_id": user_id}).to_list(None)
    genres = await db.genres.find({"user_id": user_id}).to_list(None)

    # Извлекаем только значения (например, id фильмов или названия жанров)
    likes_list = [item["movie_id"] for item in likes]
    reviews_list = [item["review"] for item in reviews]
    bookmarks_list = [item["movie_id"] for item in bookmarks]
    movie_timestamps_list = [item["movie_id"] for item in views]
    genres_list = [item["genre"] for item in genres]

    # Возвращаем данные в виде Pydantic-модели
    return UserAnalysisRequest(
        likes=likes_list,
        reviews=reviews_list,
        bookmarks=bookmarks_list,
        movie_timestamps=movie_timestamps_list,
        genres=genres_list,
    )
