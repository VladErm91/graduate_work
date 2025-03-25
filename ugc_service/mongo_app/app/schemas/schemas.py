from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from bson import ObjectId
from models.models import PyObjectId
from pydantic import BaseModel, Field


class MovieBase(BaseModel):
    title: str
    description: str


class MovieCreate(MovieBase):
    pass


class Movie(MovieBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}


class LikeBase(BaseModel):
    user_id: UUID
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
    user_id: UUID
    movie_id: str


class WatchedMovieCreate(BaseModel):
    pass



class WatchedMovie(WatchedMovieBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}



class ReviewBase(BaseModel):
    user_id: UUID
    movie_id: PyObjectId
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
    user_id: UUID
    movie_id: PyObjectId


class BookmarkCreate(BookmarkBase):
    pass


class Bookmark(BookmarkBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}
