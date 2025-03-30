from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.watch_history import WatchHistory
from models.movie import Movie


class AlgorithmA:
    @staticmethod
    async def get_recommendations(user_id: str, db: AsyncSession) -> list[str]:
        stmt = select(WatchHistory.movie_id).where(WatchHistory.user_id == user_id)
        user_watched = set((await db.execute(stmt)).scalars().all())
        if not user_watched:
            stmt = select(Movie.movie_id).limit(3)
            return (await db.execute(stmt)).scalars().all()
        stmt = select(Movie.genres).where(Movie.movie_id.in_(user_watched))
        watched_genres = set((await db.execute(stmt)).scalars().all())
        stmt = (
            select(Movie.movie_id)
            .where(Movie.genres.in_(watched_genres))
            .where(Movie.movie_id.not_in(user_watched))
            .limit(3)
        )
        recommendations = (await db.execute(stmt)).scalars().all()
        return recommendations if recommendations else ["movie1", "movie2", "movie3"]


class AlgorithmB:
    @staticmethod
    async def get_recommendations(user_id: str, db: AsyncSession) -> list[str]:
        stmt = select(WatchHistory.movie_id).where(WatchHistory.user_id == user_id)
        watched_ids = (await db.execute(stmt)).scalars().all()
        stmt = (
            select(Movie.movie_id)
            .where(Movie.rating >= 3.5)
            .where(Movie.movie_id.not_in(watched_ids))
            .order_by(Movie.rating.desc())
            .limit(3)
        )
        recommendations = (await db.execute(stmt)).scalars().all()
        return recommendations if recommendations else ["movie4", "movie5", "movie6"]
