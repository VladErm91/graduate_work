from pydantic import BaseModel
from typing import List

class RecommendationResponse(BaseModel):
    source: str
    recommendations: List[str]
    session_id: str