from logging import getLogger

from core.config import db
from core.jwt import security_jwt
from core.utils import convert_objectid,uuid_to_objectid
from fastapi import APIRouter, Depends
from schemas.schemas import User, UserCreate
from typing_extensions import Annotated

logger = getLogger().getChild("users-router")

router = APIRouter()


@router.post("/", response_model=User)
async def create_user(
    user: Annotated[dict, Depends(security_jwt)], 
    user_data: UserCreate
):
    user_id = user["id"]  # UUID-строка из токена
    mongo_user_id = uuid_to_objectid(user_id)

    result = await db.users.insert_one({
        "_id": mongo_user_id,
        "username": user_data.username
    })
    created_user = convert_objectid(
        await db.users.find_one({"_id": result.inserted_id})
    )
    return created_user
