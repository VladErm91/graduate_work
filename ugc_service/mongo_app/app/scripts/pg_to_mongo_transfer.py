import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Настройки подключения
POSTGRES_DSN = "postgresql+asyncpg://app:123qwe@db:5432/movies_database"
MONGO_DSN = "mongodb://mongodb:27017"
MONGO_DB = "cinema"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Подключение к PostgreSQL
engine = create_async_engine(POSTGRES_DSN, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Подключение к MongoDB
mongo_client = AsyncIOMotorClient(MONGO_DSN)
mongo_db = mongo_client[MONGO_DB]
movies_collection = mongo_db["movies"]  # Коллекция в MongoDB


async def migrate_movies():
    try:
        async with AsyncSessionLocal() as session:
            # Получаем все фильмы из PostgreSQL
            # sql_query = text("SELECT id, title, description, imdb_rating, genre FROM film_work")

            sql_query = text(
                """
                SELECT f.id, f.title, f.description, f.rating, g.name AS genre
                FROM content.film_work f
                JOIN content.genre_film_work gf ON gf.film_work_id = f.id
                JOIN content.genre g ON g.id = gf.genre_id;
            """
            )

            result = await session.execute(sql_query)

            movies_to_add = [
                {
                    "movie_id": str(row[0]),
                    "title": row[1],
                    "description": row[2],
                    "rating": row[3],
                    "genres": row[4],
                }
                for row in result
            ]

            logging.info(f"Из PostgreSQL получено {len(movies_to_add)} фильмов.")

            existing_movie_ids = await movies_collection.distinct(
                "movie_id"
            )  # правильный вызов distinct
            existing_movie_ids = list(set(existing_movie_ids))
            new_movies = [
                movie
                for movie in movies_to_add
                if movie["movie_id"] not in existing_movie_ids
            ]

            if not new_movies:
                logging.info("Все фильмы уже есть в MongoDB. Ничего не добавляем.")
                return

            # Добавляем новые фильмы в MongoDB
            await movies_collection.insert_many(new_movies)
            logging.info(f"Добавлено {len(new_movies)} новых фильмов в MongoDB.")

    except Exception as e:
        logging.error(f"Ошибка при миграции данных: {e}")


if __name__ == "__main__":
    asyncio.run(migrate_movies())
