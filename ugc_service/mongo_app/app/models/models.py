from datetime import datetime
from typing import Optional, List

from bson import ObjectId
from pydantic import BaseModel, Field


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


class Movie(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    title: str
    description: Optional[str] = None
    rating: float
    genres: List[str]

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {ObjectId: str}


class WatchedMovie(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: PyObjectId
    movie_id: PyObjectId
    watched_at: datetime
    complete: bool


    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {ObjectId: str}


class Like(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: PyObjectId
    movie_id: PyObjectId
    rating: Optional[int] = 1  # Оценка от 0 до 10

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {ObjectId: str}


class Review(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: PyObjectId
    movie_id: PyObjectId
    content: str
    publication_date: datetime
    additional_data: Optional[dict] = None
    likes: Optional[int] = 0
    dislikes: Optional[int] = 0

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {ObjectId: str}


class Bookmark(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: PyObjectId
    movie_id: PyObjectId

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {ObjectId: str}
