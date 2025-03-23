from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.watch_history import WatchHistory
from models.movie import Movie


class RecommendationRepository:
    @staticmethod
    async def get_watched_movies(user_id: str, db: AsyncSession):
        query = select(WatchHistory.movie_id).where(WatchHistory.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_popular_movies(db: AsyncSession):
        query = select(Movie).limit(5)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_similar_movies(watched_movies, db: AsyncSession):
        query = select(Movie).where(Movie.id.notin_(watched_movies)).limit(5)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_movies_from_users(user_ids, db: AsyncSession):
        query = select(Movie).join(WatchHistory).where(WatchHistory.user_id.in_(user_ids)).limit(5)
        result = await db.execute(query)
        return result.scalars().all()
