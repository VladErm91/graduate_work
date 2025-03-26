# recommendation_service/services/сontent_filter.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle


class ContentFilter:
    def __init__(self):
        try:
            with open("models/movie_content.pkl", "rb") as f:
                self.movie_features = pickle.load(f)
        except FileNotFoundError:
            self.movie_features = None

    def fit(self, movie_data: pd.DataFrame):
        tfidf = TfidfVectorizer(stop_words="english")
        tfidf_matrix = tfidf.fit_transform(
            movie_data["genres"] + " " + movie_data["directors"]
        )
        self.movie_features = cosine_similarity(tfidf_matrix)

        with open("models/movie_content.pkl", "wb") as f:
            pickle.dump(self.movie_features, f)

    def recommend(self, movie_id, movie_data):
        if self.movie_features is None:
            return []

        idx = movie_data.index[movie_data["movie_id"] == movie_id].tolist()
        if not idx:
            return []

        idx = idx[0]
        scores = list(enumerate(self.movie_features[idx]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        recommended_idx = [i[0] for i in scores[1:6]]
        return movie_data.iloc[recommended_idx]["movie_id"].tolist()
