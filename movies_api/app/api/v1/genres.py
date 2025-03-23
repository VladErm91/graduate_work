from http import HTTPStatus
from typing import Optional

from core.jwt import security_jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from models.genre import Genre, GenrePaginationResponse, SortOrder
from services.genre import GenreService, get_genre_service
from typing_extensions import Annotated

router = APIRouter()


@router.get("/{genre_id}", response_model=Genre, summary="Запрос жанра по id")
async def genre_details(
    user: Annotated[dict, Depends(security_jwt)],
    genre_id: str,
    genre_service: GenreService = Depends(get_genre_service),
) -> Genre:
    genre = await genre_service.get_by_uuid(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Genre not found")
    return genre


@router.get(
    "", response_model=GenrePaginationResponse, summary="Поиск жанра по наименованию"
)
async def search_genres(
    query: str = Query("", description="Get Genre by genre name"),
    order: Optional[SortOrder] = None,
    page_size: int = Query(default=10, description="Number of items per page", lt=100),
    page_number: int = Query(default=1, description="Page number"),
    genre_service: GenreService = Depends(get_genre_service),
) -> GenrePaginationResponse:
    genres, total = await genre_service.search(
        query=query, order=order, page_number=page_number, page_size=page_size
    )

    max_pages = (total + page_size - 1) // page_size
    if page_number > max_pages:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Page not found")

    return GenrePaginationResponse(
        items=genres, total=total, page_number=page_number, page_size=page_size
    )
