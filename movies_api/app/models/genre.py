from enum import Enum
from typing import List

from pydantic import BaseModel


class Genre(BaseModel):
    """Схема данных по жанрам."""

    uuid: str
    name: str


class GenrePaginationResponse(BaseModel):
    """Схема данных по жанрам с пагинацией."""

    items: List[Genre]
    total: int
    page_number: int
    page_size: int


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"
