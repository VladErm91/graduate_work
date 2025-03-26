# recommendation_service/scripts/generate_test_data.py
import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from core.database import SessionLocal  # Исправлено с AsyncSessionLocal на SessionLocal
from models.user import User
from models.movie import Movie
from models.watch_history import WatchHistory

USERNAMES = ["alice", "bob", "charlie", "dave", "eve"]
MOVIES = [
    {"title": "Inception", "genres": "Sci-Fi"},
    {"title": "Interstellar", "genres": "Sci-Fi"},
    {"title": "The Dark Knight", "genres": "Action"},
    {"title": "The Matrix", "genres": "Sci-Fi"},
    {"title": "Pulp Fiction", "genres": "Crime"},
]


async def generate_data():
    async with SessionLocal() as db:  # Исправлено здесь
        # Генерация пользователей
        users = [
            User(user_id=str(uuid.uuid4()), username=name, age=random.randint(18, 60))
            for name in USERNAMES
        ]
        db.add_all(users)

        # Генерация фильмов
        movies = [
            Movie(
                movie_id=str(uuid.uuid4()),
                title=m["title"],
                genres=m["genres"],
                directors="Unknown",
                rating=round(random.uniform(1.0, 5.0), 1),
            )
            for m in MOVIES
        ]
        db.add_all(movies)

        await db.commit()

        # Связка пользователей с фильмами
        for user in users:
            watched_movies = random.sample(movies, k=random.randint(1, 3))
            history = [
                WatchHistory(
                    id=str(uuid.uuid4()),
                    user_id=user.user_id,
                    movie_id=movie.movie_id,
                    watched_at=datetime.now(timezone.utc)
                    - timedelta(days=random.randint(1, 30)),
                    completed=False
                )
                for movie in watched_movies
            ]
            db.add_all(history)

        await db.commit()
        print("Test data generated successfully!")
        print("Generated users:", [user.user_id for user in users])


if __name__ == "__main__":
    asyncio.run(generate_data())
