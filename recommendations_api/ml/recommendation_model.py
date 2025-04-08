import io
import logging
import pickle
import random
import uuid
from datetime import datetime, timedelta
from time import time

import implicit
import numpy as np
from lightfm import LightFM
from minio import Minio
from motor.motor_asyncio import AsyncIOMotorDatabase
from prometheus_client import Counter, Gauge, Histogram
from scipy.sparse import coo_matrix, csr_matrix
from sklearn.preprocessing import MultiLabelBinarizer

from core.config import settings
from core.metrics import (
    MATRIX_SIZE,  # Импортируем существующие метрики
    TRAIN_COUNT,
    TRAIN_DURATION,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALS_MODEL_KEY = "als_model.pkl"
LIGHTFM_MODEL_KEY = "lightfm_model.pkl"

# Новые метрики для рекомендаций


RECOMMENDATION_DURATION = Histogram(
    "recommendation_duration_seconds",
    "Time taken to generate recommendations",
    ["model_type"],
)
POPULAR_RECOMMENDATIONS = Counter(
    "popular_recommendations_total",
    "Total number of times popular recommendations were returned",
    ["reason"],
)
MODEL_STATUS = Gauge(
    "model_loaded_status",
    "Status of model loading (1 = loaded, 0 = not loaded)",
    ["model_type"],
)


class RecommendationModel:
    def __init__(self):
        self.als_model = implicit.als.AlternatingLeastSquares(factors=20, iterations=10)
        self.lightfm_model = LightFM(no_components=20, learning_rate=0.05, loss="warp")
        self.user_ids = []
        self.movie_ids = []
        self.user_to_idx = {}
        self.movie_to_idx = {}
        self.idx_to_movie = {}
        self.als_user_item_matrix = None
        self.lightfm_user_item_matrix = None
        self.item_features = None
        self.minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        self.ensure_bucket()
        # Сохраняем статус загрузки моделей
        self.als_loaded = self.load_model(ALS_MODEL_KEY, "als")
        self.lightfm_loaded = self.load_model(LIGHTFM_MODEL_KEY, "lightfm")

        # Устанавливаем начальные значения статуса моделей
        MODEL_STATUS.labels(model_type="als").set(1 if self.als_loaded else 0)
        MODEL_STATUS.labels(model_type="lightfm").set(1 if self.lightfm_loaded else 0)

    def ensure_bucket(self):
        if not self.minio_client.bucket_exists(settings.MINIO_BUCKET):
            self.minio_client.make_bucket(settings.MINIO_BUCKET)
            logger.info(f"Created MinIO bucket: {settings.MINIO_BUCKET}")

    def save_models(self):
        als_data = {
            "model": self.als_model,
            "user_ids": self.user_ids,
            "movie_ids": self.movie_ids,
            "user_to_idx": self.user_to_idx,
            "movie_to_idx": self.movie_to_idx,
            "idx_to_movie": self.idx_to_movie,
            "user_item_matrix": self.als_user_item_matrix,
        }
        buffer = io.BytesIO()
        pickle.dump(als_data, buffer)
        buffer.seek(0)
        self.minio_client.put_object(
            settings.MINIO_BUCKET,
            ALS_MODEL_KEY,
            buffer,
            length=buffer.getbuffer().nbytes,
        )
        logger.info(f"ALS model saved to MinIO: {ALS_MODEL_KEY}")
        MODEL_STATUS.labels(model_type="als").set(1)  # Модель загружена

        lightfm_data = {
            "model": self.lightfm_model,
            "user_ids": self.user_ids,
            "movie_ids": self.movie_ids,
            "user_to_idx": self.user_to_idx,
            "movie_to_idx": self.movie_to_idx,
            "idx_to_movie": self.idx_to_movie,
            "user_item_matrix": self.lightfm_user_item_matrix,
            "item_features": self.item_features,
        }
        buffer = io.BytesIO()
        pickle.dump(lightfm_data, buffer)
        buffer.seek(0)
        self.minio_client.put_object(
            settings.MINIO_BUCKET,
            LIGHTFM_MODEL_KEY,
            buffer,
            length=buffer.getbuffer().nbytes,
        )
        logger.info(f"LightFM model saved to MinIO: {LIGHTFM_MODEL_KEY}")
        MODEL_STATUS.labels(model_type="lightfm").set(1)  # Модель загружена

    def load_model(self, key: str, model_type: str) -> bool:
        try:
            obj = self.minio_client.get_object(settings.MINIO_BUCKET, key)
            data = pickle.load(obj)
            if model_type == "als":
                self.als_model = data["model"]
                self.user_ids = data["user_ids"]
                self.movie_ids = data["movie_ids"]
                self.user_to_idx = data["user_to_idx"]
                self.movie_to_idx = data["movie_to_idx"]
                self.idx_to_movie = data["idx_to_movie"]
                self.als_user_item_matrix = data.get("user_item_matrix")
                logger.info(f"ALS model loaded from MinIO: {key}")
            elif model_type == "lightfm":
                self.lightfm_model = data["model"]
                self.user_ids = data["user_ids"]
                self.movie_ids = data["movie_ids"]
                self.user_to_idx = data["user_to_idx"]
                self.movie_to_idx = data["movie_to_idx"]
                self.idx_to_movie = data["idx_to_movie"]
                self.lightfm_user_item_matrix = data.get("user_item_matrix")
                self.item_features = data.get("item_features")
                logger.info(f"LightFM model loaded from MinIO: {key}")
            return True
        except Exception as e:
            logger.info(
                f"No {model_type.upper()} model found in MinIO or error loading: {e}"
            )
            return False

    async def partial_train(self, db: AsyncIOMotorDatabase, last_timestamp=None):
        """Инкрементальное дообучение моделей на основе новых взаимодействий"""

        logger.info("Starting partial model training...")
        start_time = time()

        # Получаем новые взаимодействия с момента последнего обучения
        query = {"timestamp": {"$gt": last_timestamp}} if last_timestamp else {}
        watched_movies = await db["watched_movies"].find(query).to_list(None)
        likes = await db["likes"].find(query).to_list(None)
        bookmarks = await db["bookmarks"].find(query).to_list(None)

        if not (watched_movies or likes or bookmarks):
            logger.info("No new interactions found for partial training.")
            return

        # Новые взаимодействия
        new_interactions = (
            [
                (
                    str(wm["user_id"]),
                    str(wm["movie_id"]),
                    1.0 if wm["complete"] else 0.5,
                )
                for wm in watched_movies
            ]
            + [
                (str(like["user_id"]), str(like["movie_id"]), like["rating"] / 10.0)
                for like in likes
            ]
            + [(str(bm["user_id"]), str(bm["movie_id"]), 0.3) for bm in bookmarks]
        )

        # Обновляем списки пользователей и фильмов
        new_users = set(
            user_id
            for user_id, _, _ in new_interactions
            if user_id not in self.user_to_idx
        )
        new_movies = set(
            movie_id
            for _, movie_id, _ in new_interactions
            if movie_id not in self.movie_to_idx
        )

        if new_users:
            self.user_ids.extend(new_users)
            self.user_to_idx.update(
                {
                    uid: idx
                    for idx, uid in enumerate(self.user_ids, len(self.user_to_idx))
                }
            )
        if new_movies:
            self.movie_ids.extend(new_movies)
            self.movie_to_idx.update(
                {
                    mid: idx
                    for idx, mid in enumerate(self.movie_ids, len(self.movie_to_idx))
                }
            )
            self.idx_to_movie.update(
                {idx: mid for mid, idx in self.movie_to_idx.items()}
            )

        # Обновляем матрицы
        rows = [self.user_to_idx[uid] for uid, _, _ in new_interactions]
        cols = [self.movie_to_idx[mid] for _, mid, _ in new_interactions]
        data = [weight for _, _, weight in new_interactions]

        new_als_matrix = csr_matrix(
            (data, (rows, cols)), shape=(len(self.user_ids), len(self.movie_ids))
        )
        new_lightfm_matrix = coo_matrix(
            (data, (rows, cols)), shape=(len(self.user_ids), len(self.movie_ids))
        )

        if self.als_user_item_matrix is not None:
            self.als_user_item_matrix = self.als_user_item_matrix + new_als_matrix
        else:
            self.als_user_item_matrix = new_als_matrix

        if self.lightfm_user_item_matrix is not None:
            self.lightfm_user_item_matrix = (
                self.lightfm_user_item_matrix + new_lightfm_matrix
            )
        else:
            self.lightfm_user_item_matrix = new_lightfm_matrix

        # Обновляем метрики размера матрицы
        MATRIX_SIZE.labels(model="als").set(self.als_user_item_matrix.nnz)
        MATRIX_SIZE.labels(model="lightfm").set(self.lightfm_user_item_matrix.nnz)

        # Полное обучение ALS (нет fit_partial)
        self.als_model.fit(self.als_user_item_matrix)

        # Инкрементальное обучение LightFM
        self.lightfm_model.fit_partial(
            self.lightfm_user_item_matrix, item_features=self.item_features, epochs=5
        )

        self.save_models()
        duration = time() - start_time
        TRAIN_DURATION.labels(type="partial").observe(duration)
        TRAIN_COUNT.labels(type="partial").inc()
        logger.info("Partial model training completed for ALS and LightFM.")

    async def train(self, db: AsyncIOMotorDatabase):
        logger.info("Starting model training...")
        start_time = time()

        watched_movies = await db["watched_movies"].find().to_list(None)
        likes = await db["likes"].find().to_list(None)
        bookmarks = await db["bookmarks"].find().to_list(None)

        if not watched_movies and not likes and not bookmarks:
            logger.warning("No interaction data available for training.")
            return

        interactions = (
            [
                (
                    str(wm["user_id"]),
                    str(wm["movie_id"]),
                    1.0 if wm["complete"] else 0.5,
                )
                for wm in watched_movies
            ]
            + [
                (str(like["user_id"]), str(like["movie_id"]), like["rating"] / 10.0)
                for like in likes
            ]
            + [(str(bm["user_id"]), str(bm["movie_id"]), 0.3) for bm in bookmarks]
        )

        self.user_ids = sorted(set(user_id for user_id, _, _ in interactions))
        self.movie_ids = sorted(set(movie_id for _, movie_id, _ in interactions))
        self.user_to_idx = {uid: idx for idx, uid in enumerate(self.user_ids)}
        self.movie_to_idx = {mid: idx for idx, mid in enumerate(self.movie_ids)}
        self.idx_to_movie = {idx: mid for mid, idx in self.movie_to_idx.items()}

        rows = [self.user_to_idx[uid] for uid, _, _ in interactions]
        cols = [self.movie_to_idx[mid] for _, mid, _ in interactions]
        data = [weight for _, _, weight in interactions]
        self.als_user_item_matrix = csr_matrix(
            (data, (rows, cols)), shape=(len(self.user_ids), len(self.movie_ids))
        )
        self.lightfm_user_item_matrix = coo_matrix(
            (data, (rows, cols)), shape=(len(self.user_ids), len(self.movie_ids))
        )

        # Обновляем метрики размера матрицы
        MATRIX_SIZE.labels(model="als").set(self.als_user_item_matrix.nnz)
        MATRIX_SIZE.labels(model="lightfm").set(self.lightfm_user_item_matrix.nnz)

        # Подготовка item_features в формате CSR
        movies = await db["movies"].find().to_list(None)
        genres = [
            movie["genres"] if isinstance(movie["genres"], list) else [movie["genres"]]
            for movie in movies
        ]
        mlb = MultiLabelBinarizer(sparse_output=True)  # Возвращаем разреженную матрицу
        sparse_features = mlb.fit_transform(genres)
        self.item_features = sparse_features.tocsr()  # Преобразуем в CSR

        # Проверка соответствия размеров
        if self.item_features.shape[0] != len(self.movie_ids):
            logger.warning(
                "Mismatch between item_features and movie_ids. Adjusting item_features..."
            )
            # Если нужно, можно дополнить или обрезать item_features до нужного размера
            self.item_features = self.item_features[: len(self.movie_ids), :]

        self.als_model.fit(self.als_user_item_matrix)
        self.lightfm_model.fit(
            self.lightfm_user_item_matrix, item_features=self.item_features, epochs=10
        )
        self.save_models()
        duration = time() - start_time
        TRAIN_DURATION.labels(type="full").observe(duration)
        TRAIN_COUNT.labels(type="full").inc()
        logger.info("Model training completed for ALS and LightFM.")

    async def get_user_row(
        self, user_id: str, db: AsyncIOMotorDatabase, model_type: str = "als"
    ) -> csr_matrix:
        watched = await db["watched_movies"].find({"user_id": user_id}).to_list(None)
        likes = await db["likes"].find({"user_id": user_id}).to_list(None)
        bookmarks = await db["bookmarks"].find({"user_id": user_id}).to_list(None)

        movie_weights = {}
        for wm in watched:
            movie_id = str(wm["movie_id"])
            movie_weights[movie_id] = 1.0 if wm["complete"] else 0.5
        for like in likes:
            movie_id = str(like["movie_id"])
            movie_weights[movie_id] = like["rating"] / 10.0
        for bm in bookmarks:
            movie_id = str(bm["movie_id"])
            if movie_id not in movie_weights:
                movie_weights[movie_id] = 0.3

        cols = [
            self.movie_to_idx[mid] for mid in movie_weights if mid in self.movie_to_idx
        ]
        data = [movie_weights[mid] for mid in movie_weights if mid in self.movie_to_idx]
        rows = np.zeros(len(cols))
        matrix = csr_matrix if model_type == "als" else coo_matrix
        return matrix((data, (rows, cols)), shape=(1, len(self.movie_ids)))

    async def get_recommendations(
        self,
        user_id: str,
        db: AsyncIOMotorDatabase,
        n: int = settings.RECOMMENDATIONS_LIMITS,
        model_type: str = "als",
    ) -> dict:

        start_time = time()

        watched = await db["watched_movies"].find({"user_id": user_id}).to_list(None)
        watched = set(str(w["movie_id"]) for w in watched)

        if model_type == "als":
            user_item_matrix = self.als_user_item_matrix
            model = self.als_model
        else:
            user_item_matrix = self.lightfm_user_item_matrix
            model = self.lightfm_model

        if user_item_matrix is None or not self.user_ids:

            popular = (
                await db["movies"]
                .aggregate([{"$sort": {"rating": -1}}, {"$limit": n}])
                .to_list(n)
            )

            recommendations = (
                [str(movie["_id"]) for movie in popular] if popular else []
            )

            session_id = str(uuid.uuid4())

            logger.info(
                f"Returning popular movies for user {user_id} (no {model_type} model): {recommendations}, session {session_id}"
            )
            duration = time() - start_time
            RECOMMENDATION_DURATION.labels(model_type="popular").observe(duration)
            POPULAR_RECOMMENDATIONS.labels(reason="no_model").inc()

            return {
                "source": "popular",
                "recommendations": recommendations,
                "session_id": session_id,
            }

        if user_id not in self.user_to_idx:

            popular = (
                await db["movies"]
                .aggregate([{"$sort": {"rating": -1}}, {"$limit": n}])
                .to_list(n)
            )

            recommendations = (
                [str(movie["_id"]) for movie in popular] if popular else []
            )

            session_id = str(uuid.uuid4())

            logger.info(
                f"Returning popular movies for new user {user_id} ({model_type}): {recommendations}, session {session_id}"
            )

            duration = time() - start_time
            RECOMMENDATION_DURATION.labels(model_type="popular").observe(duration)
            POPULAR_RECOMMENDATIONS.labels(reason="new_user").inc()
            return {
                "source": "popular",
                "recommendations": recommendations,
                "session_id": session_id,
            }

        user_idx = self.user_to_idx[user_id]
        user_row = await self.get_user_row(user_id, db, model_type)

        if model_type == "als":
            recommended_ids, _ = model.recommend(user_idx, user_row, N=n + len(watched))
            recommendations = [
                self.idx_to_movie[idx]
                for idx in recommended_ids
                if idx in self.idx_to_movie and self.idx_to_movie[idx] not in watched
            ][:n]
        else:
            scores = model.predict(
                user_idx,
                np.arange(len(self.movie_ids)),
                item_features=self.item_features,
            )

            top_items = np.argsort(-scores)[: n + len(watched)]
            recommendations = [
                self.idx_to_movie[idx]
                for idx in top_items
                if self.idx_to_movie[idx] not in watched
            ][:n]

        # Подмешивание новых непросмотренных фильмов (добавленных за последний месяц)
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        all_movies = (
            await db["movies"]
            .find({"creation_date": {"$gte": one_month_ago}})
            .to_list(None)
        )
        new_unwatched_movies = [
            str(movie["_id"])
            for movie in all_movies
            if str(movie["_id"]) not in self.movie_to_idx  # Нет взаимодействий
            and str(movie["_id"]) not in watched  # Не просмотрен пользователем
        ]

        # Определяем количество новых фильмов для добавления (минимум 1, максимум треть от n)
        n_unwatched = min(1, max(1, n // 3))
        if new_unwatched_movies and len(recommendations) >= n_unwatched:
            recommendations = recommendations[
                :-n_unwatched
            ]  # Убираем последние элементы
            selected_new_movies = random.sample(
                new_unwatched_movies, min(n_unwatched, len(new_unwatched_movies))
            )
            recommendations.extend(selected_new_movies)
            logger.info(
                f"Added {len(selected_new_movies)} new unwatched movies to recommendations for user {user_id}"
            )

        session_id = str(uuid.uuid4())
        duration = time() - start_time
        RECOMMENDATION_DURATION.labels(model_type=model_type).observe(duration)

        logger.info(
            f"Generated {model_type} recommendations for user {user_id}: {recommendations}, session {session_id}"
        )

        return {
            "source": model_type,
            "recommendations": recommendations,
            "session_id": session_id,
        }


recommendation_model = RecommendationModel()
