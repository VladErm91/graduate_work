import random

import pymongo
from faker import Faker

# Настройки подключения к MongoDB
MONGO_URL = "mongodb://mongodb:27017"
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
NUM_LIKES = 100
NUM_REVIEWS = 100
NUM_BOOKMARKS = 100
NUM_WATCHEDFILMS = 100

# Размер пачки для вставки
BATCH_SIZE = 100

# Генерация фильмов
movies = []
for _ in range(NUM_MOVIES):
    movie = {
        "genres": random.choice(GENRES),
        "rating": round(random.uniform(1, 10), 1),
        "publication_date": fake.date_time(),
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
        "username": fake.user_name(),
        "email": fake.email(),
        "hashed_password": fake.password(),
    }
    users.append(user)
    if len(users) >= BATCH_SIZE:
        db.users.insert_many(users)
        users = []
if users:
    db.users.insert_many(users)

# Генерация лайков
likes = []
for _ in range(NUM_LIKES):
    like = {
        "user_id": random.choice(db.users.find().distinct("_id")),
        "movie_id": random.choice(db.movies.find().distinct("_id")),
        "rating": random.randint(0, 10),
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
        "user_id": random.choice(db.users.find().distinct("_id")),
        "movie_id": random.choice(db.movies.find().distinct("_id")),
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
        "user_id": random.choice(db.users.find().distinct("_id")),
        "movie_id": random.choice(db.movies.find().distinct("_id")),
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
        "user_id": random.choice(db.users.find().distinct("_id")),
        "movie_id": random.choice(db.movies.find().distinct("_id")),
        "watched_at": fake.date_time_this_decade(),
        "complete": random.choice([True, False]),
    }
    watched_films.append(watched_film)
    if len(watched_films) >= BATCH_SIZE:
        db.watched_movies.insert_many(watched_films)
        watched_films = []
if watched_films:
    db.watched_movies.insert_many(watched_films)
