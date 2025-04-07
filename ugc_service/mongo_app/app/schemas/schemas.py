from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID

from bson import ObjectId
from models.models import PyObjectId
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: Optional[UUID] = Field(alias="_id", default=None)

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}
        populate_by_name = True


class MovieBase(BaseModel):
    rating: float
    genres: List[str] = None
    creation_date: datetime


class MovieCreate(MovieBase):
    pass


class Movie(MovieBase):
    id: Optional[UUID] = Field(alias="_id", default=None)

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}


class LikeBase(BaseModel):
    user_id: str
    movie_id: str
    rating: Annotated[
        int, Field(strict=True, gt=0, le=10)
    ]  # Ограничиваем значение от 0 до 10


class LikeCreate(BaseModel):
    movie_id: str
    rating: Annotated[
        int, Field(strict=True, gt=0, le=10)
    ]  # Ограничиваем значение от 0 до 10


class Like(LikeBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}


class WatchedMovieBase(BaseModel):
    user_id: str
    movie_id: str
    watched_at: datetime
    complete: bool


class WatchedMovieCreate(WatchedMovieBase):
    pass


class WatchedMovie(WatchedMovieBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}


class ReviewBase(BaseModel):
    user_id: str
    movie_id: str
    content: str
    publication_date: datetime
    additional_data: Optional[dict] = None
    likes: Optional[int] = 0
    dislikes: Optional[int] = 0


class ReviewCreate(ReviewBase):
    pass


class Review(ReviewBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}


class BookmarkBase(BaseModel):
    user_id: str
    movie_id: str


class BookmarkCreate(BookmarkBase):
    pass


class Bookmark(BookmarkBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}
