from logging import getLogger
from typing import List

from bson import ObjectId
from core.config import db
from core.jwt import security_jwt
from core.utils import convert_objectid
from fastapi import APIRouter, Depends, HTTPException
from schemas.schemas import Like, LikeCreate
from typing_extensions import Annotated

logger = getLogger().getChild("likes-router")

router = APIRouter()


@router.post("/", response_model=Like)
async def create_like(
    like: LikeCreate,
    user: Annotated[dict, Depends(security_jwt)],
):
    """
    Create a new like for a movie.

    Args:
        like: LikeCreate - The like object containing the movie_id and rating.
        current_user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        The created Like object from the database.
    """
    like_dict = like.model_dump()
    like_dict["user_id"] = str(user["id"])
    logger.info(f"like_dict: {like_dict}")
    result = await db.likes.insert_one(like_dict)
    created_like = convert_objectid(
        await db.likes.find_one({"_id": result.inserted_id})
    )
    return created_like


@router.get("/movies/{movie_id}/likes/", response_model=List[Like])
async def get_likes(
    user: Annotated[dict, Depends(security_jwt)],
    movie_id: str,
):
    """
    Get all likes for a given movie.

    Args:
        movie_id: str - The id of the movie.
        current_user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        A list of Like objects from the database that match the given movie_id.
    """
    likes = await db.likes.find({"movie_id": movie_id}).to_list(1000)
    return likes


@router.get("/movies/{movie_id}/average_rating/", response_model=float)
async def get_average_rating(
    user: Annotated[dict, Depends(security_jwt)],
    movie_id: str,
):
    """
    Get the average rating for a given movie.

    Args:
        movie_id: str - The id of the movie.
        current_user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        The average rating of the movie.
    """
    likes = await db.likes.find({"movie_id": ObjectId(movie_id)}).to_list(1000)
    if not likes:
        return 0.0
    total_rating = sum(like.rating for like in likes)
    average_rating = total_rating / len(likes)
    return average_rating


@router.delete("/{like_id}/")
async def delete_like(
    like_id: str,
    user: Annotated[dict, Depends(security_jwt)],
):
    """
    Delete a like.

    Args:
        like_id: str - The id of the like to be deleted.
        current_user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        The deleted Like object from the database.

    Raises:
        HTTPException: 404 if the like is not found.
    """
    like = await db.likes.find_one({"_id": ObjectId(like_id), "user_id": user["id"]})
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    await db.likes.delete_one({"_id": ObjectId(like_id)})
    return f"Like {like_id} successfully removed"
