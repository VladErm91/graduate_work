from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Определяем Pydantic-модели
class Likes(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None) 
    user_id: str
    movie_id: str
    rating: float


class Reviews(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None) 
    user_id: str
    movie_id: str
    content: str
    # publication_date: datetime
    # additional_data: Optional[dict] = None
    likes: Optional[int] = 0
    dislikes: Optional[int] = 0


class Bookmarks(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None) 
    user_id: str
    movie_id: str


class WatchedMovies(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None) 
    user_id: str
    movie_id: str
    watched_at: datetime
    complete: bool


# Pydantic-схема для запроса данных пользователя
class UserDataRequest(BaseModel):
    likes: List[Likes] = []
    reviews: List[Reviews] = []
    bookmarks: List[Bookmarks] = []
    watched_movies: List[WatchedMovies] = []
    genres: List[str] = []
