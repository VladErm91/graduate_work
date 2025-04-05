from logging import getLogger
from typing import List

from bson import ObjectId
from core.config import db
from core.jwt import security_jwt
from core.utils import convert_objectid, hash_to_str
from fastapi import APIRouter, Depends, HTTPException
from schemas.schemas import Review, ReviewCreate
from typing_extensions import Annotated

logger = getLogger().getChild("reviews-router")

router = APIRouter()


@router.post("/", response_model=Review)
async def create_review(
    user: Annotated[dict, Depends(security_jwt)],
    review: ReviewCreate,
):
    """
    Create a new review.

    Args:
        review: ReviewCreate - The review object containing the title, content, movie_id and rating.
        current_user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        The created Review object from the database.
    """
    review_dict = review.model_dump()
    review_dict["user_id"] = hash_to_str(user["id"])
    logger.info(f"review_dict: {review_dict}")
    result = await db.reviews.insert_one(review_dict)
    created_review = convert_objectid(
        await db.reviews.find_one({"_id": result.inserted_id})
    )
    return created_review


@router.post("/{review_id}/like/", response_model=Review)
async def like_review(
    user: Annotated[dict, Depends(security_jwt)],
    review_id: str,
):
    """
    Like a review.

    Args:
        review_id: str - The id of the review to be liked.
        current_user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        The updated Review object from the database.

    Raises:
        HTTPException: 404 if the review is not found.
    """
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    await db.reviews.update_one({"_id": ObjectId(review_id)}, {"$inc": {"likes": 1}})
    updated_review = convert_objectid(
        await db.reviews.find_one({"_id": ObjectId(review_id)})
    )
    return updated_review


@router.post("/{review_id}/dislike/", response_model=Review)
async def dislike_review(
    user: Annotated[dict, Depends(security_jwt)],
    review_id: str,
):
    """
    Dislike a review.

    Args:
        review_id: str - The id of the review to be disliked.
        current_user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        The updated Review object from the database.

    Raises:
        HTTPException: 404 if the review is not found.
    """
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    await db.reviews.update_one({"_id": ObjectId(review_id)}, {"$inc": {"dislikes": 1}})
    updated_review = convert_objectid(
        await db.reviews.find_one({"_id": ObjectId(review_id)})
    )
    return updated_review


@router.get("/movies/{movie_id}/reviews/", response_model=List[Review])
async def get_reviews(
    user: Annotated[dict, Depends(security_jwt)],
    movie_id: str,
):
    """
    Get the list of reviews of a movie.

    Args:
        movie_id: str - The id of the movie.
        sort_by: str - The field to sort the reviews by. Defaults to "publication_date".
        current_user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        List[Review]
    """

    reviews = convert_objectid(
        await db.reviews.find({"movie_id": movie_id}).to_list(length=None)
    )
    if len(reviews) == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    return reviews


@router.delete(
    "/{review_id}/",
)
async def delete_review(
    user: Annotated[dict, Depends(security_jwt)],
    review_id: str,
):
    """
    Delete a review.

    Args:
        review_id: str - The id of the review to be deleted.
        current_user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        The deleted Review object from the database.

    Raises:
        HTTPException: 404 if the review is not found.
    """
    review = await db.reviews.find_one(
        {"_id": ObjectId(review_id), "user_id": hash_to_str(user["id"])}
    )
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    await db.reviews.delete_one({"_id": ObjectId(review_id)})
    return f"Review {review_id} successfully removed"
