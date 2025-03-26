# recommendation_service/workers/train_model.py

import pandas as pd
from clickhouse_driver import Client
from services.model_storage import save_model_to_minio
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

CLICKHOUSE_HOST = "clickhouse"
CLICKHOUSE_DB = "default"

client = Client(host=CLICKHOUSE_HOST)


def fetch_data():
    """Получает данные о просмотрах и лайках из ClickHouse."""
    query = """
    SELECT user_id, movie_id, rating
    FROM user_movie_interactions
    """
    data = client.execute(query)
    df = pd.DataFrame(data, columns=["user_id", "movie_id", "rating"])
    return df


def train_model():
    """Обучает рекомендательную модель на основе коллаборативной фильтрации."""
    df = fetch_data()

    if df.empty:
        print("Нет данных для обучения модели")
        return

    user_movie_matrix = df.pivot_table(
        index="user_id", columns="movie_id", values="rating", fill_value=0
    )
    similarity_matrix = cosine_similarity(user_movie_matrix)

    similarity_df = pd.DataFrame(
        similarity_matrix,
        index=user_movie_matrix.index,
        columns=user_movie_matrix.index,
    )

    save_model_to_minio(similarity_df)
    print("Модель успешно обновлена")


if __name__ == "__main__":
    train_model()
