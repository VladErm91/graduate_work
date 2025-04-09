from typing import List

from pydantic import BaseModel, Field


class FavoriteGenres(BaseModel):
    user_id: str = Field(..., alias="_id")
    genres: List[str]


class RecommendationResponse(BaseModel):
    source: str
    recommendations: List[str]
    session_id: str
