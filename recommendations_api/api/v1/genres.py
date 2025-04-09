from typing import List

from core.config import db
from core.enum import Genre
from core.jwt import security_jwt
from fastapi import APIRouter, Depends, HTTPException, status
from typing_extensions import Annotated

router = APIRouter(tags=["genres"])


@router.post(
    "/genres/{user_id}",
    summary="Add user's favorite genres",
    description="Add a list of genres to the user's favorite genres list.",
    status_code=status.HTTP_200_OK,
)
async def add_favorite_user_genres(
    genres: List[Genre],
    user: Annotated[dict, Depends(security_jwt)],  # Данные пользователя из JWT
):
    """
    Добавляет список любимых жанров пользователя в MongoDB.

    Args:
        genres: List[Genre] - Список жанров
        user: dict - Информация о пользователе (из токена).

    Returns:
        Обновлённый список любимых жанров.
    """

    # Получаем ID пользователя
    user_id = user["id"]

    # Получаем текущие любимые жанры пользователя
    user_genres = await db.favourite_genres.find_one({"user_id": user_id})

    # Если у пользователя уже есть 3 жанра, разрешаем добавить только один новый
    if user_genres and len(user_genres.get("genres", [])) >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only have up to 3 favorite genres.",
        )

    # Убираем дубликаты из переданных жанров
    genre_values = {genre.value for genre in genres}

    # Если у пользователя уже есть жанры, проверяем сколько можно добавить
    if user_genres:
        existing_genres = set(user_genres.get("genres", []))
        new_genres = genre_values - existing_genres  # Оставляем только новые жанры

        # Проверяем, сколько жанров можно добавить
        remaining_space = 3 - len(existing_genres)
        if remaining_space > 0:
            genres_to_add = list(new_genres)[
                :remaining_space
            ]  # Оставляем только столько, сколько помещается
            if genres_to_add:
                await db.favourite_genres.update_one(
                    {"user_id": user_id},
                    {"$addToSet": {"genres": {"$each": genres_to_add}}},
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot add more than 3 genres in total.",
            )
    else:
        # Если жанров нет, создаем новый документ
        await db.favourite_genres.insert_one(
            {"user_id": user_id, "genres": list(genre_values)}
        )

    # Получаем обновленный список жанров
    updated_user_genres = await db.favourite_genres.find_one(
        {"user_id": user_id}, {"_id": 0}
    )

    return updated_user_genres or {"genres": []}
