# recommendation_service/scripts/generate_test_data.py
import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
from core.database import SessionLocal, Base, engine
from models.user import User
from models.movie import Movie
from models.watch_history import WatchHistory

# Расширенные списки для генерации
USERNAMES = [
    "alice",
    "bob",
    "charlie",
    "dave",
    "eve",
    "frank",
    "grace",
    "hank",
    "ivy",
    "jack",
    "kate",
    "leo",
    "mia",
    "nina",
    "oscar",
    "paul",
    "quinn",
    "rose",
    "sam",
    "tina",
]
MOVIES = [
    {
        "title": "Inception",
        "genres": "Sci-Fi, Thriller",
        "directors": "Christopher Nolan",
        "rating": 4.8,
    },
    {
        "title": "Interstellar",
        "genres": "Sci-Fi, Drama",
        "directors": "Christopher Nolan",
        "rating": 4.7,
    },
    {
        "title": "The Dark Knight",
        "genres": "Action, Crime",
        "directors": "Christopher Nolan",
        "rating": 4.9,
    },
    {
        "title": "The Matrix",
        "genres": "Sci-Fi, Action",
        "directors": "Wachowski Sisters",
        "rating": 4.6,
    },
    {
        "title": "Pulp Fiction",
        "genres": "Crime, Drama",
        "directors": "Quentin Tarantino",
        "rating": 4.7,
    },
    {
        "title": "Forrest Gump",
        "genres": "Drama, Romance",
        "directors": "Robert Zemeckis",
        "rating": 4.5,
    },
    {
        "title": "The Shawshank Redemption",
        "genres": "Drama",
        "directors": "Frank Darabont",
        "rating": 4.9,
    },
    {
        "title": "Titanic",
        "genres": "Romance, Drama",
        "directors": "James Cameron",
        "rating": 4.3,
    },
    {
        "title": "Avatar",
        "genres": "Sci-Fi, Adventure",
        "directors": "James Cameron",
        "rating": 4.4,
    },
    {
        "title": "Jurassic Park",
        "genres": "Adventure, Sci-Fi",
        "directors": "Steven Spielberg",
        "rating": 4.2,
    },
]


async def init_tables():
    """Создаём таблицы в базе данных перед генерацией данных."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, checkfirst=True)
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized.")


async def generate_data():
    async with SessionLocal() as db:
        # Генерируем пользователей
        users = [
            User(user_id=str(uuid.uuid4()), username=name, age=random.randint(18, 60))
            for name in USERNAMES
        ]
        db.add_all(users)
        await db.commit()
        print(f"Generated {len(users)} users.")

        # Генерируем фильмы
        movies = [
            Movie(
                movie_id=str(uuid.uuid4()),
                title=m["title"],
                # description=m["description"],
                genres=m["genres"],
                directors=m["directors"],
                rating=m["rating"],
            )
            for m in MOVIES
        ]
        db.add_all(movies)
        await db.commit()
        print(f"Generated {len(movies)} movies.")

        # Генерируем историю просмотров
        history_entries = []
        for user in users:
            # Каждый пользователь смотрел от 2 до 7 фильмов
            watched_movies = random.sample(movies, k=random.randint(2, 7))
            for movie in watched_movies:
                history_entries.append(
                    WatchHistory(
                        id=str(uuid.uuid4()),
                        user_id=user.user_id,
                        movie_id=movie.movie_id,
                        watched_at=(
                            datetime.now(timezone.utc)
                            - timedelta(days=random.randint(1, 30))
                        ),
                        watch_time=timedelta(minutes=random.randint(5, 120)),
                        completed=random.choice([True, False]),
                    )
                )
        db.add_all(history_entries)
        await db.commit()
        print(f"Generated {len(history_entries)} watch history entries.")

        # Выводим примеры для проверки
        print("Sample users:", [user.user_id for user in users[:3]])
        print("Sample movies:", [movie.movie_id for movie in movies[:3]])


async def main():
    await init_tables()
    await generate_data()


if __name__ == "__main__":
    asyncio.run(main())
