import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal
from models.user import User
from models.movie import Movie
from models.watch_history import WatchHistory

USERNAMES = ["alice", "bob", "charlie", "dave", "eve"]
MOVIES = [
    {"title": "Inception", "genre": "Sci-Fi"},
    {"title": "Interstellar", "genre": "Sci-Fi"},
    {"title": "The Dark Knight", "genre": "Action"},
    {"title": "The Matrix", "genre": "Sci-Fi"},
    {"title": "Pulp Fiction", "genre": "Crime"},
]


async def generate_data():
    async with AsyncSessionLocal() as db:
        users = [User(username=name, email=f"{name}@example.com") for name in USERNAMES]
        db.add_all(users)

        movies = [
            Movie(title=m["title"], genre=m["genre"], release_date=datetime.utcnow())
            for m in MOVIES
        ]
        db.add_all(movies)

        await db.commit()

        # Связка пользователей с фильмами (случайные просмотры)
        for user in users:
            watched_movies = random.sample(movies, k=random.randint(1, 3))
            history = [
                WatchHistory(
                    user_id=user.id,
                    movie_id=movie.id,
                    watched_at=datetime.utcnow()
                    - timedelta(days=random.randint(1, 30)),
                )
                for movie in watched_movies
            ]
            db.add_all(history)

        await db.commit()


if __name__ == "__main__":
    asyncio.run(generate_data())
