# recommendation_service/services/model_storage.py

import pickle
from core.minio_client import minio_client, MINIO_BUCKET
from io import BytesIO

MODEL_PATH = "movie_recommender.pkl"


def save_model_to_minio(model, model_name=MODEL_PATH):
    """Сохраняет обученную модель в MinIO."""
    buffer = BytesIO()
    pickle.dump(model, buffer)
    buffer.seek(0)

    minio_client.put_object(
        MINIO_BUCKET,
        model_name,
        buffer,
        length=buffer.getbuffer().nbytes,
        content_type="application/octet-stream",
    )


def load_model_from_minio(model_name=MODEL_PATH):
    """Загружает обученную модель из MinIO."""
    try:
        response = minio_client.get_object(MINIO_BUCKET, model_name)
        return pickle.load(response)
    except Exception as e:
        print(f"Ошибка загрузки модели: {e}")
        return None
