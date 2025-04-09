import random
import uuid
from datetime import datetime, timedelta, timezone

import pymongo
from faker import Faker

# Настройки подключения к MongoDB
MONGO_URL = "mongodb://localhost:27017"
DATABASE_NAME = "cinema"

# Подключение к MongoDB
client = pymongo.MongoClient(MONGO_URL)
db = client[DATABASE_NAME]

# Инициализация Faker
fake = Faker()
GENRES = [
    "Action",
    "Adventure",
    "Fantasy",
    "Sci-Fi",
    "Drama",
    "Music",
    "Romance",
    "Thriller",
    "Mystery",
    "Comedy",
    "Animation",
    "Family",
    "Biography",
    "Musical",
    "Crime",
    "Short",
    "Western",
    "Documentary",
    "History",
    "War",
    "Game-Show",
    "Reality-TV",
    "Horror",
    "Sport",
    "Talk-Show",
    "News",
]

# Количество записей для генерации
NUM_USERS = 100
NUM_MOVIES = 200
NUM_LIKES = 500  # Увеличили для лучшей плотности данных
NUM_REVIEWS = 200
NUM_BOOKMARKS = 300
NUM_WATCHEDFILMS = 1000
NUM_RECOMMENDATIONS = 50  # Логи рекомендаций
NUM_FEEDBACK = 80  # Обратная связь
BATCH_SIZE = 100  # Размер пакета для вставки в MongoDB


# Очистка базы (опционально)
db.movies.drop()
db.users.drop()
db.likes.drop()
db.reviews.drop()
db.bookmarks.drop()
db.watched_movies.drop()
db.recommendation_logs.drop()
db.feedback.drop()
db.favourite_genres.drop()  # Для /genres_top

# Генерация фильмов
movies = []
for _ in range(NUM_MOVIES):
    movie = {
        "_id": str(uuid.uuid4()),  # Генерация UUID для _id
        "genres": list(random.sample(GENRES, k=random.randint(1, 3))),
        "rating": round(random.uniform(1, 10), 1),
        "creation_date": datetime.now(timezone.utc)
        - timedelta(days=random.randint(0, 60)),  # Случайная дата за последние 2 месяца
    }
    movies.append(movie)
    if len(movies) >= BATCH_SIZE:
        db.movies.insert_many(movies)
        movies = []
if movies:
    db.movies.insert_many(movies)

# Генерация пользователей
users = []
for _ in range(NUM_USERS):
    user = {
        "_id": str(uuid.uuid4()),  # Генерация UUID для _id
        "username": fake.user_name(),
    }
    users.append(user)
    if len(users) >= BATCH_SIZE:
        db.users.insert_many(users)
        users = []
if users:
    db.users.insert_many(users)

# Извлекаем ID один раз
user_ids = list(db.users.find().distinct("_id"))
movie_ids = list(db.movies.find().distinct("_id"))


# Генерация любимых жанров пользователей (для /genres_top)
favourite_genres = []
for user_id in user_ids:
    genres_entry = {
        "user_id": user_id,
        "genres": random.sample(GENRES, k=random.randint(1, 3)),  # 1-3 любимых жанров
        "timestamp": datetime.now(timezone.utc)
        - timedelta(days=random.randint(0, 180)),
    }
    favourite_genres.append(genres_entry)
    if len(favourite_genres) >= BATCH_SIZE:
        db.favourite_genres.insert_many(favourite_genres)
        favourite_genres = []
if favourite_genres:
    db.favourite_genres.insert_many(favourite_genres)
# Генерация лайков
likes = []
for _ in range(NUM_LIKES):
    like = {
        "user_id": random.choice(user_ids),
        "movie_id": random.choice(movie_ids),
        "rating": random.randint(0, 10),
        "timestamp": datetime.now(timezone.utc)
        - timedelta(days=random.randint(0, 180)),
    }
    likes.append(like)
    if len(likes) >= BATCH_SIZE:
        db.likes.insert_many(likes)
        likes = []
if likes:
    db.likes.insert_many(likes)

# Генерация рецензий
reviews = []
for _ in range(NUM_REVIEWS):
    review = {
        "user_id": random.choice(user_ids),
        "movie_id": random.choice(movie_ids),
        "content": fake.text(),
        "publication_date": fake.date_time_this_decade(),
        "additional_data": {"key": fake.word()},
        "likes": random.randint(0, 100),
        "dislikes": random.randint(0, 100),
    }
    reviews.append(review)
    if len(reviews) >= BATCH_SIZE:
        db.reviews.insert_many(reviews)
        reviews = []
if reviews:
    db.reviews.insert_many(reviews)

# Генерация закладок
bookmarks = []
for _ in range(NUM_BOOKMARKS):
    bookmark = {
        "user_id": random.choice(user_ids),
        "movie_id": random.choice(movie_ids),
    }
    bookmarks.append(bookmark)
    if len(bookmarks) >= BATCH_SIZE:
        db.bookmarks.insert_many(bookmarks)
        bookmarks = []
if bookmarks:
    db.bookmarks.insert_many(bookmarks)

# Генерация просмотров
watched_films = []
for _ in range(NUM_WATCHEDFILMS):
    watched_film = {
        "user_id": random.choice(user_ids),
        "movie_id": random.choice(movie_ids),
        "watched_at": fake.date_time_this_decade(),
        "complete": random.choice([True, False]),  # Исправлено
    }
    watched_films.append(watched_film)
    if len(watched_films) >= BATCH_SIZE:
        db.watched_movies.insert_many(watched_films)
        watched_films = []
if watched_films:
    db.watched_movies.insert_many(watched_films)

# Генерация логов рекомендаций
recommendation_logs = []
for _ in range(NUM_RECOMMENDATIONS):
    user_id = random.choice(user_ids)
    session_id = str(uuid.uuid4())
    model_type = random.choice(["als", "lightfm"])
    num_recommendations = random.randint(3, 5)  # Топ-3 или чуть больше для разнообразия
    recommendations = random.sample(
        movie_ids, k=min(num_recommendations, len(movie_ids))
    )

    log_entry = {
        "user_id": user_id,
        "session_id": session_id,
        "source": model_type,
        "model_type": model_type,  # Для совместимости с evaluate_metrics.py
        "recommendations": recommendations,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7)),
    }
    recommendation_logs.append(log_entry)
    if len(recommendation_logs) >= BATCH_SIZE:
        db.recommendation_logs.insert_many(recommendation_logs)
        recommendation_logs = []
if recommendation_logs:
    db.recommendation_logs.insert_many(recommendation_logs)

# Генерация обратной связи
feedback = []
session_ids = list(db.recommendation_logs.find().distinct("session_id"))

for _ in range(NUM_FEEDBACK):
    session_id = random.choice(session_ids)
    rec_log = db.recommendation_logs.find_one({"session_id": session_id})
    if not rec_log:
        continue

    movie_id = random.choice(rec_log["recommendations"])
    liked = random.choice([True, False])  # Случайный выбор liked

    feedback_entry = {
        "user_id": rec_log["user_id"],
        "session_id": session_id,
        "movie_id": movie_id,
        "liked": liked,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7)),
    }
    feedback.append(feedback_entry)
    if len(feedback) >= BATCH_SIZE:
        db.feedback.insert_many(feedback)
        feedback = []
if feedback:
    db.feedback.insert_many(feedback)

print("Data generation completed!")
print(
    f"Generated: {NUM_USERS} users, {NUM_MOVIES} movies, {NUM_LIKES} likes, "
    f"{NUM_REVIEWS} reviews, {NUM_BOOKMARKS} bookmarks, {NUM_WATCHEDFILMS} watched, "
    f"{NUM_RECOMMENDATIONS} recommendation logs, {NUM_FEEDBACK} feedback entries"
)
