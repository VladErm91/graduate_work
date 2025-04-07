from typing import List

from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    source: str
    recommendations: List[str]
    session_id: str
