from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.movie import Movie


class MovieRepository:
    @staticmethod
    async def get_all_movies(db: AsyncSession):
        result = await db.execute(select(Movie))
        return result.scalars().all()
