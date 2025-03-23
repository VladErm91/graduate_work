import pandas as pd
import pickle
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.movie_repository import MovieRepository


class CollaborativeFilter:
    def __init__(self):
        try:
            with open("models/movie_collab.pkl", "rb") as f:
                self.model = pickle.load(f)
        except FileNotFoundError:
            self.model = None

    async def recommend(self, user_id: str, db: AsyncSession):
        if self.model is None:
            return []

        movies = await MovieRepository.get_all_movies(db)
        movie_df = pd.DataFrame([movie.__dict__ for movie in movies])

        if user_id not in self.model.index:
            return []

        recs = self.model.loc[user_id].sort_values(ascending=False).index.tolist()[:5]
        return recs
