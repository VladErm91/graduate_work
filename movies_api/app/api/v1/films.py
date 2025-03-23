import datetime
from http import HTTPStatus
from typing import List, Optional

from core.jwt import security_jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from models.film import Film, FilmDetailed
from services.film import (
    FilmService,
    MultipleFilmsService,
    get_film_service,
    get_multiple_films_service,
)
from typing_extensions import Annotated

# Define the cutoff date for unauthorized users
THREE_YEARS_AGO = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
    days=3 * 365
)

# Объект router, в котором регистрируем обработчики
router = APIRouter()


@router.get(
    "/",
    summary="Популярные фильмы",
    description="Популярное кино в своем жанре с сортировкой результата, указать количество и номер страницы",
)
async def get_popular_films(
    user: Annotated[dict, Depends(security_jwt)],
    similar: Optional[str] = Query(
        None, description="Get films of same genre as similar"
    ),
    genre: Optional[str] = Query(None, description="Get films of given genres"),
    sort: str = Query("-imdb_rating", description="Sort by field"),
    page_size: int = Query(10, description="Number of items per page", ge=1),
    page_number: int = Query(1, description="Page number", ge=1),
    film_service: MultipleFilmsService = Depends(get_multiple_films_service),
):
    valid_sort_fields = ("imdb_rating", "-imdb_rating")
    if sort not in valid_sort_fields:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Invalid value for "sort" parameter',
        )

    desc = sort.startswith("-")

    # Adjust query filters based on authorization
    release_date_cutoff = None if user else THREE_YEARS_AGO
    return await film_service.get_multiple_films(
        similar=similar,
        genre=genre,
        desc_order=desc,
        page_size=page_size,
        page_number=page_number,
        release_date_cutoff=release_date_cutoff,
    )


# 3. Поиск по фильмам (2.1. из т.з.)
# GET /api/v1/films/search?query=star&page_number=1&page_size=50


@router.get(
    "/search",
    response_model=List[Film],
    summary="Поиск фильма по наименованию",
    description="Запрос должен содержать наименование фильма, количество фильмов на странице и номер страницы",
)
async def fulltext_search_filmworks(
    user: Annotated[dict, Depends(security_jwt)],
    query: str = Query("Star", description="Film title or part of film title"),
    page_size: int = Query(50, description="Number of items per page", ge=1),
    page_number: int = Query(1, description="Page number", ge=1),
    pop_film_service: MultipleFilmsService = Depends(get_multiple_films_service),
) -> List[Film]:

    return await pop_film_service.search_films(
        query,
        page_number,
        page_size,
    )


# 4. Полная информация по фильму (т.з. 3.1.)


# Внедряем FilmService с помощью Depends(get_film_service)
@router.get(
    "/{film_uuid}",
    response_model=FilmDetailed,
    summary="Запрос фильма по id",
    description="Полная информация о фильме: id, наименование, рейтинг, жанр, описание, режиссер, актёры, авторы",
)
async def film_details(
    user: Annotated[dict, Depends(security_jwt)],
    film_uuid: str,
    film_service: FilmService = Depends(get_film_service),
) -> FilmDetailed:
    film = await film_service.get_by_uuid(film_uuid)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Film not found")
    return film
