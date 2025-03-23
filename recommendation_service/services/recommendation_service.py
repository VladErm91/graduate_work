import pickle
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from core.redis import get_redis
from repositories.recommendation_repository import RecommendationRepository


class RecommendationService:
    @staticmethod
    async def get_recommendations(user_id: str, db: AsyncSession):
        redis = await get_redis()
        cached_data = await redis.get(f"user_recommendations:{user_id}")

        if cached_data:
            return pickle.loads(cached_data)

        try:
            with open("models/user_similarity.pkl", "rb") as f:
                similarity_df = pickle.load(f)
        except FileNotFoundError:
            return await RecommendationRepository.get_popular_movies(db)

        if user_id not in similarity_df.index:
            return await RecommendationRepository.get_popular_movies(db)

        similar_users = (
            similarity_df.loc[user_id].sort_values(ascending=False).index[1:6]
        )
        recommended_movies = await RecommendationRepository.get_movies_from_users(
            similar_users, db
        )

        # Кешируем на 1 час
        await redis.set(
            f"user_recommendations:{user_id}", pickle.dumps(recommended_movies), ex=3600
        )

        return recommended_movies
