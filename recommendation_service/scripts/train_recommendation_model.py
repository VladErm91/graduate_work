import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal
from models.watch_history import WatchHistory
from models.movie import Movie


async def load_data():
    async with AsyncSessionLocal() as db:
        query = """
        SELECT user_id, movie_id FROM watch_history
        """
        result = await db.execute(query)
        data = result.fetchall()

        return pd.DataFrame(data, columns=["user_id", "movie_id"])


def train_model(data):
    user_movie_matrix = data.pivot_table(
        index="user_id", columns="movie_id", aggfunc=len, fill_value=0
    )

    # Вычисляем схожесть пользователей
    user_similarity = cosine_similarity(user_movie_matrix)
    similarity_df = pd.DataFrame(
        user_similarity, index=user_movie_matrix.index, columns=user_movie_matrix.index
    )

    # Сохраняем модель
    with open("models/user_similarity.pkl", "wb") as f:
        pickle.dump(similarity_df, f)


async def main():
    data = await load_data()
    if not data.empty:
        train_model(data)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
