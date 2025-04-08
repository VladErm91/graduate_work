import json
import logging
import random
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from redis.asyncio import Redis
from typing_extensions import Annotated

from core.config import db, settings
from core.jwt import JWTBearer, security_jwt
from core.redis import get_redis
from ml.recommendation_model import recommendation_model
from schemas.schemas import RecommendationResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["recommend"])


@router.get(
    "/genres_top/{user_id}",
    summary="Get top movies by user's favorite genres",
    description="Returns a list of top-rated movies that match the user's favorite genres.",
)
async def get_base_recommendations_for_user(
    request: Request,
    user: Annotated[dict, Depends(security_jwt)],  # Данные пользователя из JWT
    limit: int = Query(settings.RECOMMENDATIONS_LIMITS, description="Number of movies to return", ge=1, le=50),
):
    """
    Получает топ фильмов по любимым жанрам пользователя из MongoDB и делает запрос в эндпоинт movie_api.
    """

    token = JWTBearer.get_token_from_request(request)  # Извлекаем токен из запроса

    if not token:
        raise HTTPException(status_code=403, detail="Authorization token is missing")

    user_id = user["id"]

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
            num_genres = min(3, len(favorite_genres))
            genre_limit = limit // num_genres

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

        movie_ids = [movie["uuid"] for movie in all_movies]
        
        return {"recommendations": movie_ids}


@router.get("/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(
    user: Annotated[dict, Depends(security_jwt)],
    user_id: str,
    model: str = Query(None, description="models like als or lightfm"),
    redis: Redis = Depends(get_redis),
):
    """
    Возвращает рекомендации для пользователя.
    """

    # user_id = user["id"]
    model_type = (
        model if model in ["als", "lightfm"] else random.choice(["als", "lightfm"])
    )
    cache_key = f"recommendations:{user_id}:{model_type}"

    cached = await redis.get(cache_key)
    if cached:
        logger.info(f"Cache hit for user {user_id} with {model_type}: {cached}")
        return json.loads(cached)

    result = await recommendation_model.get_recommendations(
        user_id, db, model_type=model_type
    )
    await redis.setex(cache_key, settings.REDIS_CACHE_EXPIRE, json.dumps(result))

    # Сохранение рекомендаций для анализа
    await db["recommendation_logs"].insert_one(
        {
            "user_id": user_id,
            "model_type": model_type,
            "recommendations": result["recommendations"],
            "session_id": result["session_id"],
            "timestamp": datetime.now(timezone.utc),
        }
    )

    logger.info(f"Cached {model_type} recommendations for user {user_id}: {result}")
    return result


@router.post("/feedback/{session_id}")
async def submit_feedback(
    user: Annotated[dict, Depends(security_jwt)],
    session_id: str,
    movie_id: str,
    liked: bool,
):
    """
    Отправляет обратную связь о просмотренном фильме.
    """
    await db["feedback"].insert_one(
        {
            "session_id": session_id,
            "movie_id": {"_id": movie_id},
            "liked": liked,
            "timestamp": datetime.now(timezone.utc),
        }
    )
    logger.info(
        f"Feedback submitted for session {session_id}, movie {movie_id}, liked: {liked}"
    )
    return {"status": "success"}
