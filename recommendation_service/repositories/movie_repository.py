# recommendation_service/repositories/movie_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.movie import Movie
from schemas.schemas import Movie

class MovieRepository:
    @staticmethod
    async def get_movies_for_users(user_ids: list[int], db: AsyncSession):
        """Получает фильмы, которые смотрели похожие пользователи."""
        query = select(Movie).where(Movie.user_id.in_(user_ids))
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_similar_movies(user_id: str, db: AsyncSession):
        """Получает фильмы, похожие на те, что смотрел пользователь."""
        query = """
        SELECT m.* FROM movies m
        JOIN user_movie_interactions um ON m.id = um.movie_id
        WHERE um.user_id = :user_id
        ORDER BY m.genre, m.director DESC
        LIMIT 10
        """
        result = await db.execute(query, {"user_id": user_id})
        return result.scalars().all()
