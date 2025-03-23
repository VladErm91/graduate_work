from services.collaborative_filter import CollaborativeFilter
from services.content_filter import ContentFilter
from repositories.movie_repository import MovieRepository
from sqlalchemy.ext.asyncio import AsyncSession
import random


class HybridRecommender:
    def __init__(self):
        self.collaborative = CollaborativeFilter()
        self.content = ContentFilter()

    async def get_hybrid_recommendations(self, user_id: str, db: AsyncSession):
        collab_recs = await self.collaborative.recommend(user_id, db)
        content_recs = []

        if collab_recs:
            for movie_id in collab_recs[:3]:
                content_recs += self.content.recommend(
                    movie_id, await MovieRepository.get_all_movies(db)
                )

        final_recs = list(set(collab_recs + content_recs))[:10]
        random.shuffle(final_recs)
        return final_recs
