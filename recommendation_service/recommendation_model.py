# recommendation_service/recommendation_model.py
import implicit
import numpy as np
from scipy.sparse import csr_matrix
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.watch_history import WatchHistory
from minio import Minio
from core.config import settings
import pickle
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_KEY = "recommendation_model.pkl"


class RecommendationModel:
    def __init__(self):
        self.model = implicit.als.AlternatingLeastSquares(factors=20, iterations=10)
        self.user_ids = []
        self.movie_ids = []
        self.user_to_idx = {}
        self.movie_to_idx = {}
        self.idx_to_movie = {}
        self.user_item_matrix = None
        self.minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        self.ensure_bucket()
        self.load_model()

    def ensure_bucket(self):
        if not self.minio_client.bucket_exists(settings.MINIO_BUCKET):
            self.minio_client.make_bucket(settings.MINIO_BUCKET)
            logger.info(f"Created MinIO bucket: {settings.MINIO_BUCKET}")

    def save_model(self):
        data = {
            "model": self.model,
            "user_ids": self.user_ids,
            "movie_ids": self.movie_ids,
            "user_to_idx": self.user_to_idx,
            "movie_to_idx": self.movie_to_idx,
            "idx_to_movie": self.idx_to_movie,
            "user_item_matrix": self.user_item_matrix,
        }
        buffer = io.BytesIO()
        pickle.dump(data, buffer)
        buffer.seek(0)
        self.minio_client.put_object(
            settings.MINIO_BUCKET, MODEL_KEY, buffer, length=buffer.getbuffer().nbytes
        )
        logger.info(f"Model saved to MinIO: {MODEL_KEY}")

    def load_model(self):
        try:
            obj = self.minio_client.get_object(settings.MINIO_BUCKET, MODEL_KEY)
            data = pickle.load(obj)
            self.model = data["model"]
            self.user_ids = data["user_ids"]
            self.movie_ids = data["movie_ids"]
            self.user_to_idx = data["user_to_idx"]
            self.movie_to_idx = data["movie_to_idx"]
            self.idx_to_movie = data["idx_to_movie"]
            self.user_item_matrix = data.get("user_item_matrix")
            logger.info(f"Model loaded from MinIO: {MODEL_KEY}")
        except Exception as e:
            logger.info(
                f"No model found in MinIO or error loading: {e}, starting fresh."
            )

    async def train(self, db: AsyncSession):
        logger.info("Starting model training...")
        stmt = select(WatchHistory.user_id, WatchHistory.movie_id)
        result = await db.execute(stmt)
        interactions = result.all()

        if not interactions:
            logger.warning("No interaction data available for training.")
            return

        self.user_ids = sorted(set(user_id for user_id, _ in interactions))
        self.movie_ids = sorted(set(movie_id for _, movie_id in interactions))
        self.user_to_idx = {user_id: idx for idx, user_id in enumerate(self.user_ids)}
        self.movie_to_idx = {
            movie_id: idx for idx, movie_id in enumerate(self.movie_ids)
        }
        self.idx_to_movie = {
            idx: movie_id for movie_id, idx in self.movie_to_idx.items()
        }

        rows = [self.user_to_idx[user_id] for user_id, _ in interactions]
        cols = [self.movie_to_idx[movie_id] for _, movie_id in interactions]
        data = np.ones(len(interactions))
        self.user_item_matrix = csr_matrix(
            (data, (rows, cols)), shape=(len(self.user_ids), len(self.movie_ids))
        )

        self.model.fit(self.user_item_matrix)
        self.save_model()
        logger.info("Model training completed.")

    async def get_user_row(self, user_id: str, db: AsyncSession) -> csr_matrix:
        """Получаем строку взаимодействий для конкретного пользователя."""
        stmt = select(WatchHistory.movie_id).where(WatchHistory.user_id == user_id)
        result = await db.execute(stmt)
        watched_movies = result.scalars().all()

        if not watched_movies:
            # Если у пользователя нет просмотров, возвращаем пустую строку
            return csr_matrix((1, len(self.movie_ids)), dtype=np.float32)

        cols = [
            self.movie_to_idx[movie_id]
            for movie_id in watched_movies
            if movie_id in self.movie_to_idx
        ]
        data = np.ones(len(cols))
        rows = np.zeros(len(cols))  # Одна строка (индекс 0)
        return csr_matrix((data, (rows, cols)), shape=(1, len(self.movie_ids)))

    async def get_recommendations(
        self, user_id: str, db: AsyncSession, n: int = 3
    ) -> dict:
        # Если модель не обучена, возвращаем популярные фильмы
        if self.user_item_matrix is None or not self.user_ids:
            stmt = (
                select(WatchHistory.movie_id)
                .group_by(WatchHistory.movie_id)
                .order_by(func.count().desc())
                .limit(n)
            )
            popular = (await db.execute(stmt)).scalars().all()
            recommendations = list(popular) if popular else ["movie1", "movie2", "movie3"]
            logger.info(f"Returning popular movies for user {user_id} (no model or data): {recommendations}")
            return {"source": "popular", "recommendations": recommendations}

        # Получаем строку взаимодействий пользователя
        user_row = await self.get_user_row(user_id, db)

        # Если пользователь новый, возвращаем популярные фильмы
        if user_id not in self.user_to_idx:
            stmt = (
                select(WatchHistory.movie_id)
                .group_by(WatchHistory.movie_id)
                .order_by(func.count().desc())
                .limit(n)
            )
            popular = (await db.execute(stmt)).scalars().all()
            recommendations = list(popular) if popular else ["movie1", "movie2", "movie3"]
            logger.info(f"Returning popular movies for new user {user_id}: {recommendations}")
            return {"source": "popular", "recommendations": recommendations}

        user_idx = self.user_to_idx[user_id]
        stmt = select(WatchHistory.movie_id).where(WatchHistory.user_id == user_id)
        watched = set((await db.execute(stmt)).scalars().all())

        # Передаём строку пользователя вместо полной матрицы
        recommended_ids, _ = self.model.recommend(
            user_idx, user_row, N=n + len(watched)
        )
        recommendations = [
            self.idx_to_movie[idx]
            for idx in recommended_ids
            if idx in self.idx_to_movie and self.idx_to_movie[idx] not in watched
        ][:n]
        recommendations = recommendations if recommendations else ["movie1", "movie2", "movie3"]
        logger.info(f"Generated recommendations for user {user_id} using ALS model: {recommendations}")
        return {"source": "als", "recommendations": recommendations}


recommendation_model = RecommendationModel()
