from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        from pydantic_core import core_schema

        return core_schema.str_schema()


class MovieBase(BaseModel):
    id: Optional[PyObjectId]
    title: str
    description: Optional[str] = None
    genres: list[str]
    rating: Optional[float] = None

    class Config:
        from_attributes = True  # Позволяет работать с ORM
        json_encoders = {ObjectId: str}  # Кодируем ObjectId в строку


class UserAnalysisRequest(BaseModel):
    likes: List[str] = []
    reviews: List[str] = []
    bookmarks: List[str] = []
    movie_timestamps: List[str] = []
    genres: List[str] = []
