from logging import getLogger
from typing import List

from bson import ObjectId
from core.config import db
from core.jwt import security_jwt
from core.utils import convert_objectid, hash_to_str
from fastapi import APIRouter, Depends, HTTPException
from schemas.schemas import Bookmark, BookmarkCreate
from typing_extensions import Annotated

logger = getLogger().getChild("bookmarks-router")

router = APIRouter()


@router.post("/", response_model=Bookmark)
async def create_bookmark(
    user: Annotated[dict, Depends(security_jwt)],
    bookmark: BookmarkCreate,
):
    """
    Create a new bookmark.

    Args:
        bookmark: BookmarkCreate - The bookmark object containing the title and description.

    Returns:
        The created Bookmark object from the database.
    """

    bookmark_dict = bookmark.model_dump()
    bookmark_dict["user_id"] = hash_to_str(user["id"])
    logger.info(f"bookmark_dict: {bookmark_dict}")
    result = await db.bookmarks.insert_one(bookmark_dict)
    created_bookmark = convert_objectid(
        await db.bookmarks.find_one({"_id": result.inserted_id})
    )
    return created_bookmark


@router.get("/users/{user_id}/bookmarks/", response_model=List[Bookmark])
async def get_bookmarks(
    user: Annotated[dict, Depends(security_jwt)],
    user_id: str,
):
    """
    Get all bookmarks for a given user.

    Args:
        user_id: str - The id of the user.
        user: User - The current user making the request, automatically injected by FastAPI.

    Returns:
        A list of Bookmark objects from the database that match the given user_id.
    """
    bookmarks = convert_objectid(
        await db.bookmarks.find({"user_id": hash_to_str(user_id)}).to_list(1000)
    )
    return bookmarks


@router.delete("/{bookmark_id}/")
async def delete_bookmark(
    user: Annotated[dict, Depends(security_jwt)], bookmark_id: str
):
    """
    Delete a bookmark.

    Args:
        bookmark_id: str

    Returns:
        Bookmark

    Raises:
        HTTPException: 404 if the bookmark is not found
    """
    bookmark = await db.bookmarks.find_one(
        {"_id": ObjectId(bookmark_id), "user_id": hash_to_str(user["id"])}
    )
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    await db.bookmarks.delete_one({"_id": ObjectId(bookmark_id)})
    return f"Like {bookmark_id} successfully removed"
