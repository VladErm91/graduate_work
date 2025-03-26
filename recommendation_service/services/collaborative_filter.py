# recommendation_service/services/collaborative_filter.py

import random
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.movie_repository import MovieRepository
from services.model_storage import load_model_from_minio


class RecommendationSystem:
    def __init__(self):
        self.cf_model = load_model_from_minio("collaborative_model.pkl")
        self.cb_model = load_model_from_minio("content_model.pkl")

    async def recommend(self, user_id: str, db: AsyncSession):
        """Определяет, какой алгоритм использовать (A/B-тестирование)"""
        group = self.assign_user_to_group(user_id)

        if group == "A":
            return await self.collaborative_filtering(user_id, db)
        else:
            return await self.content_based_filtering(user_id, db)

    def assign_user_to_group(self, user_id: str) -> str:
        """Назначает пользователя в группу A или B (50/50)"""
        return "A" if hash(user_id) % 2 == 0 else "B"

    async def collaborative_filtering(self, user_id: str, db: AsyncSession):
        """Коллаборативная фильтрация"""
        if self.cf_model is None or user_id not in self.cf_model.index:
            return []
        recommended_users = (
            self.cf_model.loc[user_id].sort_values(ascending=False).index.tolist()
        )
        return await MovieRepository.get_movies_for_users(recommended_users, db)

    async def content_based_filtering(self, user_id: str, db: AsyncSession):
        """Контентная рекомендация (по жанрам, актерам и т. д.)"""
        return await MovieRepository.get_similar_movies(user_id, db)
