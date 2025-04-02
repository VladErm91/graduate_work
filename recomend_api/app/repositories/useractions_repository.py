
from core.config import db
from models.models import Likes, Reviews, Bookmarks, WatchedMovies, UserDataRequest
from pydantic import ValidationError

def convert_mongo_doc(doc, model, exclude_fields=None):
    """Функция конвертации документа MongoDB в Pydantic-модель"""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])  # Преобразуем ObjectId в строку
    
    # Исключаем ненужные поля
    if exclude_fields:
        doc = {key: value for key, value in doc.items() if key not in exclude_fields}
    
    try:
        return model(**doc)
    except ValidationError as e:
        print(f"Ошибка валидации {model.__name__}: {e}")  # Логируем ошибку
        return None

async def get_user_data(user_id:str):
    # Загружаем данные из MongoDB если только по текущему пользователю
    # likes = await db.likes.find({"user_id": user_id}).to_list(None)
    # reviews = await db.reviews.find({"user_id": user_id}).to_list(None)
    # bookmarks = await db.bookmarks.find({"user_id": user_id}).to_list(None)
    # watched_movies = await db.watched_movies.find({"user_id": user_id}).to_list(None)
    # genres = await db.favourite_genres.find({"user_id": user_id}).to_list(None)

    likes = await db.likes.find({"user_id": user_id}).sort("created_at", -1).limit(100).to_list(None) 

    reviews = await db.reviews.find().sort("created_at", -1).limit(100).to_list(None) 
    bookmarks = await db.bookmarks.find().to_list(None)
    watched_movies = await db.watched_movies.find().sort("created_at", -1).limit(100).to_list(None) 
    genres = await db.favourite_genres.find().to_list(None)

    # Преобразуем в Pydantic-модели
    likes_list = [convert_mongo_doc(item, Likes) for item in likes]
    reviews_list = [converted for item in reviews
    if (converted := convert_mongo_doc(item, Reviews, 
        exclude_fields={"publication_date", "additional_data"}))
    ]
    reviews_list = [convert_mongo_doc(item, Reviews) for item in reviews]
    bookmarks_list = [convert_mongo_doc(item, Bookmarks) for item in bookmarks]
    watched_movies_list = [convert_mongo_doc(item, WatchedMovies) for item in watched_movies]
    genres_list = [item["genre_name"] for item in genres]

    # Возвращаем результат
    return UserDataRequest(
        likes=likes_list,
        reviews=reviews_list,
        bookmarks=bookmarks_list,
        watched_movies=watched_movies_list,
        genres=genres_list,
    )
