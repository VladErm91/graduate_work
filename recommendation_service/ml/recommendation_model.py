# recommendation_service/recommendation_model.py

import implicit
import numpy as np
from scipy.sparse import csr_matrix
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from minio import Minio
from core.config import settings
import pickle
import io
from bson import ObjectId

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

    async def train(self, db: AsyncIOMotorDatabase):
        logger.info("Starting model training...")
        watched_movies = await db["watched_movies"].find().to_list(None)
        likes = await db["likes"].find().to_list(None)

        if not watched_movies and not likes:
            logger.warning("No interaction data available for training.")
            return

        interactions = []
        for wm in watched_movies:
            user_id = str(wm["user_id"])
            movie_id = str(wm["movie_id"])
            weight = 1.0 if wm["complete"] else 0.5
            interactions.append((user_id, movie_id, weight))

        for like in likes:
            user_id = str(like["user_id"])
            movie_id = str(like["movie_id"])
            weight = like["rating"] / 10.0
            interactions.append((user_id, movie_id, weight))

        self.user_ids = sorted(set(user_id for user_id, _, _ in interactions))
        self.movie_ids = sorted(set(movie_id for _, movie_id, _ in interactions))
        self.user_to_idx = {user_id: idx for idx, user_id in enumerate(self.user_ids)}
        self.movie_to_idx = {
            movie_id: idx for idx, movie_id in enumerate(self.movie_ids)
        }
        self.idx_to_movie = {
            idx: movie_id for movie_id, idx in self.movie_to_idx.items()
        }

        rows = [self.user_to_idx[user_id] for user_id, _, _ in interactions]
        cols = [self.movie_to_idx[movie_id] for _, movie_id, _ in interactions]
        data = [weight for _, _, weight in interactions]
        self.user_item_matrix = csr_matrix(
            (data, (rows, cols)), shape=(len(self.user_ids), len(self.movie_ids))
        )

        self.model.fit(self.user_item_matrix)
        self.save_model()
        logger.info("Model training completed.")

    async def get_user_row(self, user_id: str, db: AsyncIOMotorDatabase) -> csr_matrix:
        # Получаем просмотры пользователя из MongoDB
        watched = (
            await db["watched_movies"]
            .find({"user_id": ObjectId(user_id)})
            .to_list(None)
        )
        likes = await db["likes"].find({"user_id": ObjectId(user_id)}).to_list(None)

        # Формируем словарь с весами взаимодействий
        movie_weights = {str(like["movie_id"]): like["rating"] / 10.0 for like in likes}
        for wm in watched:
            movie_id = str(wm["movie_id"])
            if movie_id not in movie_weights:
                movie_weights[movie_id] = 1.0 if wm["complete"] else 0.5

        # Создаём разреженную строку для пользователя
        cols = [
            self.movie_to_idx[movie_id]
            for movie_id in movie_weights
            if movie_id in self.movie_to_idx
        ]
        data = [
            movie_weights[movie_id]
            for movie_id in movie_weights
            if movie_id in self.movie_to_idx
        ]
        rows = np.zeros(len(cols))
        return csr_matrix((data, (rows, cols)), shape=(1, len(self.movie_ids)))

    async def get_recommendations(
        self, user_id: str, db: AsyncIOMotorDatabase, n: int = 3
    ) -> dict:
        # Если модель не обучена или нет данных
        if self.user_item_matrix is None or not self.user_ids:
            popular = (
                await db["movies"]
                .aggregate([{"$sort": {"rating": -1}}, {"$limit": n}])
                .to_list(n)
            )
            recommendations = (
                [str(movie["_id"]) for movie in popular] if popular else []
            )
            logger.info(
                f"Returning popular movies for user {user_id} (no model): {recommendations}"
            )
            return {"source": "popular", "recommendations": recommendations}

        # Получаем строку взаимодействий пользователя
        user_row = await self.get_user_row(user_id, db)

        # Если пользователь новый
        if user_id not in self.user_to_idx:
            popular = (
                await db["movies"]
                .aggregate([{"$sort": {"rating": -1}}, {"$limit": n}])
                .to_list(n)
            )
            recommendations = (
                [str(movie["_id"]) for movie in popular] if popular else []
            )
            logger.info(
                f"Returning popular movies for new user {user_id}: {recommendations}"
            )
            return {"source": "popular", "recommendations": recommendations}

        # Генерация рекомендаций через ALS
        user_idx = self.user_to_idx[user_id]
        watched = set(
            str(wm["movie_id"])
            for wm in await db["watched_movies"]
            .find({"user_id": ObjectId(user_id)})
            .to_list(None)
        )
        recommended_ids, _ = self.model.recommend(
            user_idx, user_row, N=n + len(watched)
        )
        recommendations = [
            self.idx_to_movie[idx]
            for idx in recommended_ids
            if idx in self.idx_to_movie and self.idx_to_movie[idx] not in watched
        ][:n]
        if not recommendations:
            popular = (
                await db["movies"]
                .aggregate([{"$sort": {"rating": -1}}, {"$limit": n}])
                .to_list(n)
            )
            recommendations = (
                [str(movie["_id"]) for movie in popular] if popular else []
            )
        logger.info(
            f"Generated recommendations for user {user_id} using ALS: {recommendations}"
        )
        return {"source": "als", "recommendations": recommendations}


recommendation_model = RecommendationModel()
