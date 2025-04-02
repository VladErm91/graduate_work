import asyncio
from sqlalchemy.sql import text
from db.db import async_session

# SQL-запрос для получения данных о фильмах
SQL_QUERY = text(
    """
    SELECT f.id, f.title, f.description, f.rating, g.name AS genre
    FROM content.film_work f
    JOIN content.genre_film_work gf ON gf.film_work_id = f.id
    JOIN content.genre g ON g.id = gf.genre_id;
    """
)

# Асинхронная функция для получения данных о фильмах
async def get_movies():
    async with async_session() as session:
        result = await session.execute(SQL_QUERY)
        rows = result.fetchall()

        # Группировка жанров по id фильма
        movies = {}
        for row in rows:
            movie_id, title, description, rating, genre = row
            if movie_id not in movies:
                movies[movie_id] = {
                    "movie_id": movie_id,
                    "title": title,
                    "description": description,
                    "rating": rating,
                    "genres": [],
                }
            movies[movie_id]["genres"].append(genre)

        return list(movies.values())