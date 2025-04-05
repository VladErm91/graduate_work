from logging import getLogger
from typing import List

from core.config import db
from core.jwt import security_jwt
from core.utils import convert_objectid, hash_to_str
from fastapi import APIRouter, Depends
from schemas.schemas import Movie, MovieCreate, WatchedMovie, WatchedMovieCreate
from typing_extensions import Annotated

logger = getLogger().getChild("movies-router")

router = APIRouter()


@router.post("/", response_model=Movie)
async def create_movie(
    user: Annotated[dict, Depends(security_jwt)], 
    movie: MovieCreate
):
    """
    Create a new movie.

    Args:
        movie: MovieCreate - The movie object containing the title and description.

    Returns:
        The created Movie object from the database.
    """
    movie_dict = movie.model_dump()
    logger.info(f"movie_dict: {movie_dict}")
    result = await db.movies.insert_one(movie_dict)
    created_movie = convert_objectid(
        await db.movies.find_one({"_id": result.inserted_id})
    )
    return created_movie


@router.get("/", response_model=List[Movie])
async def get_movies():
    """
    Get all movies from db
    Returns:
        A list of Movies objects from the database that match the given user_id. dev_endpoint - для проверки генератора
    """
    movies = convert_objectid(await db.movies.find().to_list(1000))
    return movies


@router.post("/movie_timestamp/", response_model=WatchedMovie)
async def create_movie_timestamp(
    user: Annotated[dict, Depends(security_jwt)],
    movie_timestamp: WatchedMovieCreate,
):
    """
    Create a mark for watched movie.

    Args:
        movie_timestamp: WatchedMovieCreate - The object containing the movie_id.

    Returns:
        The created Movie object from the database.
    """
    watched_movies_dict = movie_timestamp.model_dump()
    watched_movies_dict["user_id"] = hash_to_str(user["id"])
    logger.info(f"watched_movies_dict: {watched_movies_dict}")
    result = await db.watched_movies.insert_one(watched_movies_dict)
    created_watched_movies = convert_objectid(
        await db.watched_movies.find_one({"_id": result.inserted_id})
    )
    return created_watched_movies


@router.get("/users/{user_id}/movie_timestamps/", response_model=List[WatchedMovie])
async def get_watched_movies(
    user: Annotated[dict, Depends(security_jwt)],
):
    """
    Get all watched_movies for a given user as list.

    Args:
        user_id: str - The id of the user.
        user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        A list of WatchedMovies objects from the database that match the given user_id.
    """
    watchedMovies = convert_objectid(
        await db.watched_movies.find({"user_id": hash_to_str(user["id"])}).to_list(100)
    )
    return watchedMovies
