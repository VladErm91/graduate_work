import json
from typing import Any, Dict

import httpx
from core.config import db, settings
from core.jwt import JWTBearer, security_jwt
from core.utils import get_user_data
from db.redis import get_redis
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from redis.asyncio import Redis
from typing_extensions import Annotated

router = APIRouter(tags=["recommend"])


@router.get(
    "/genres_top",
    summary="Get top movies by user's favorite genres",
    description="Returns a list of top-rated movies that match the user's favorite genres.",
)
async def get_base_recommendations_for_user(
    request: Request,
    user: Annotated[dict, Depends(security_jwt)],  # Данные пользователя из JWT
    limit: int = Query(12, description="Number of movies to return", ge=1, le=50),
):
    """
    Получает топ фильмов по любимым жанрам пользователя из MongoDB и делает запрос в эндпоинт movie_api.
    """

    token = JWTBearer.get_token_from_request(request)  # Извлекаем токен из запроса

    if not token:
        raise HTTPException(status_code=403, detail="Authorization token is missing")

    user_id = str(user["id"])

    # Получаем любимые жанры пользователя из MongoDB
    user_genres = await db.favourite_genres.find_one(
        {"user_id": user_id}, {"_id": 0, "genres": 1}
    )
    favorite_genres = user_genres.get("genres") if user_genres else []

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Request-Id": "recommendation-request",
    }

    async with httpx.AsyncClient() as client:
        all_movies = []

        # Если у пользователя есть любимые жанры, выполняем запрос для каждого жанра
        if favorite_genres:
            # Ограничиваем количество жанров до 3
            num_genres = min(3, len(favorite_genres))

            # Вычисляем лимит фильмов для каждого жанра (лимит фильмов делится на количество жанров)
            genre_limit = limit // num_genres

            # Если лимит не делится на количество жанров без остатка, добавляем остаток фильмов к одному из жанров
            remaining_limit = limit % num_genres
            if remaining_limit > 0:
                genre_limit += 1

            # Для каждого жанра выполняем запрос
            for genre in favorite_genres[:num_genres]:
                params = {
                    "genre": genre,
                    "sort": "-imdb_rating",
                    "page_size": genre_limit,
                    "page_number": 1,
                }

                response = await client.get(
                    settings.url_movies_search, params=params, headers=headers
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code, detail="Error fetching movies"
                    )

                movies = response.json()
                all_movies.extend(movies)

            # Обрезаем количество фильмов до нужного лимита
            # all_movies = all_movies[:limit]

        else:
            # Если жанров нет, выполняем запрос без учета жанров, с обычным лимитом
            params = {
                "sort": "-imdb_rating",
                "page_size": limit,
                "page_number": 1,
            }

            response = await client.get(
                settings.url_movies_search, params=params, headers=headers
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, detail="Error fetching movies"
                )

            all_movies = response.json()

        return {"movies": all_movies}


@router.post(
    "/analyze_user",
    summary="Send user data for ML analysis and get result",
    description="Fetches user interactions (likes, reviews, bookmarks, views, genres) from multiple MongoDB collections and sends them to the ML service for analysis. The result is fetched from Redis.",
)
async def get_ml_recommendations_for_user(
    user: Dict[str, Any] = Depends(security_jwt),  # Данные пользователя из JWT
    redis: Redis = Depends(get_redis),
):
    """
    Загружает данные пользователя из MongoDB (несколько коллекций), отправляет в ML-сервис и получает результат из Redis.
    """
    user_id = str(user["id"])

    # Загружаем данные пользователя из MongoDB
    user_data = await get_user_data(db, user_id)

    # Преобразуем Pydantic-модель в словарь
    user_data_dict = user_data.model_dump()
    user_data_dict["user_id"] = user_id

    # Отправка данных в ML-сервис
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.ML_SERVICE, json=user_data_dict)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Error sending data to ML service"
        )

    # Проверяем, есть ли готовый анализ в Redis
    recommends = await redis.get(f"user_analysis:{user_id}")

    return json.loads(recommends)
