import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from api.v1.recommend import get_redis
from core.config import db
from core.jwt import security_jwt
from main import app

client = TestClient(app)

BASE_URL_AUTH = "http://localhost:8084/api/recommend/v1/recommendations"


@pytest.fixture(scope="module")
def valid_token_header():
    return {
        "Authorization": "Bearer some_valid_jwt_token",
        "X-Request-Id": "test-request-id",
    }


@pytest.fixture(scope="module")
def invalid_token_header():
    return {"Authorization": "Bearer invalid_token", "X-Request-Id": "test-request-id"}


@pytest.fixture(autouse=True)
def override_jwt_dependency():
    def fake_security_jwt():
        return {"id": "hashed_user_id", "username": "test_user"}

    app.dependency_overrides[security_jwt] = fake_security_jwt
    yield
    app.dependency_overrides.pop(security_jwt, None)


@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value=None)
async def test_missing_authorization_token(jwt_get_token):
    user_id = "user123"
    response = client.get(
        BASE_URL_AUTH + f"/genres_top/{user_id}",
        headers={"X-Request-Id": "test-request-id"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Authorization token is missing"


@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value="some_valid_jwt_token")
@patch.object(db, "favourite_genres")
@patch("httpx.AsyncClient.get")
async def test_error_fetching_movies_favorite_genres(
    get_mock, favourite_genres_mock, jwt_get_token, valid_token_header
):
    user_id = "user123"
    favourite_genres_mock.find_one = AsyncMock(
        return_value={"genres": ["Action", "Comedy"]}
    )

    error_response_mock = AsyncMock()
    error_response_mock.status_code = 500
    error_response_mock.json.return_value = {}
    get_mock.side_effect = [error_response_mock]

    response = client.get(
        BASE_URL_AUTH + f"/genres_top/{user_id}",
        headers=valid_token_header,
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "Error fetching movies"


@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value="some_valid_jwt_token")
@patch.object(db, "favourite_genres")
@patch("httpx.AsyncClient.get")
async def test_error_fetching_movies_no_favorite(
    get_mock, favourite_genres_mock, jwt_get_token, valid_token_header
):
    user_id = "user123"
    favourite_genres_mock.find_one = AsyncMock(return_value=None)

    error_response_mock = AsyncMock()
    error_response_mock.status_code = 404
    error_response_mock.json.return_value = {}
    get_mock.return_value = error_response_mock

    response = client.get(
        BASE_URL_AUTH + f"/genres_top/{user_id}",
        headers=valid_token_header,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Error fetching movies"


###########################################
# get_recommendations
###########################################


# ==================================================================
# 1. Cache hit
# ==================================================================
@pytest.mark.asyncio
@patch("api.v1.recommend.get_recommendations")
@patch("core.jwt.security_jwt")
async def test_get_recommendations_cache_hit(
    mock_security, mock_get_recommendations, valid_token_header
):
    """
    Если данные уже закэшированы в Redis, эндпоинт должен вернуть их сразу
    без вызова модели.
    """
    user_id = "user123"
    result = {
        "recommendations": ["movie1", "movie2"],
        "session_id": "sess123",
        "source": "cache",
    }
    cache_key = f"/recommendations:{user_id}:als"

    # Асинхронный мок Redis
    fake_redis = AsyncMock()
    fake_redis.get = AsyncMock(return_value=json.dumps(result))
    fake_redis.setex = AsyncMock()

    app.dependency_overrides[get_redis] = lambda: fake_redis

    mock_security.return_value = {"id": "hashed_user_id", "username": "test_user"}
    mock_get_recommendations.return_value = None

    # Выполняем запрос
    response = client.get(
        BASE_URL_AUTH + f"/{user_id}?model=als",
        headers=valid_token_header,
    )

    # Проверяем статус и ответ
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == result


# # ==================================================================
# # 2. Cache miss
# # ==================================================================
@patch("api.v1.recommend.db")
@patch("api.v1.recommend.recommendation_model.get_recommendations")
@patch("core.jwt.security_jwt")
@pytest.mark.asyncio
async def test_get_recommendations_cache_miss(
    mock_security, mock_get_recommendations, mock_db, valid_token_header
):
    """
    Если кеш отсутствует, функция recommendation_model.get_recommendations вызывается,
    затем результат кэшируется в Redis и логируется в MongoDB.
    """
    user_id = "hashed_user_id"
    result = {
        "recommendations": ["movie3", "movie4"],
        "session_id": "sess456",
        "source": "model",
    }
    cache_key = f"recommendations:{user_id}:lightfm"

    fake_redis = AsyncMock()
    fake_redis.get = AsyncMock(return_value=None)
    fake_redis.setex = AsyncMock()

    app.dependency_overrides[get_redis] = lambda: fake_redis

    mock_get_recommendations.return_value = result

    mock_security.return_value = {"id": "hashed_user_id", "username": "test_user"}

    fake_logs = AsyncMock()
    fake_logs.insert_one = AsyncMock()
    mock_db.__getitem__.return_value = fake_logs

    response = client.get(
        BASE_URL_AUTH + f"/{user_id}?model=lightfm",
        headers=valid_token_header,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == result

    fake_redis.get.assert_awaited_with(cache_key)
    mock_get_recommendations.assert_awaited_with(user_id, mock_db, model_type="lightfm")
    fake_redis.setex.assert_awaited()
    fake_logs.insert_one.assert_awaited_once()

    app.dependency_overrides.pop(get_redis, None)


# # ==================================================================
# # 3. Неверный параметр model → используется random.choice
# # ==================================================================
@patch("api.v1.recommend.random.choice", return_value="als")
@patch("api.v1.recommend.db")
@patch("api.v1.recommend.recommendation_model.get_recommendations")
@patch("core.jwt.security_jwt")
@pytest.mark.asyncio
async def test_get_recommendations_invalid_model(
    mock_security,
    mock_get_recommendations,
    mock_db,
    mock_random_choice,
    valid_token_header,
):
    """
    Если передан недопустимый параметр model (например, "invalid"),
    то выбирается случайное значение. Поскольку random.choice замокано и возвращает "als",
    в итоге используется модель "als".
    """
    user_id = "hashed_user_id"
    result = {"recommendations": ["movieX"], "session_id": "sess789", "source": "model"}
    cache_key = f"recommendations:{user_id}:als"

    fake_redis = AsyncMock()
    fake_redis.get = AsyncMock(return_value=None)
    fake_redis.setex = AsyncMock()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    mock_get_recommendations.return_value = result

    mock_security.return_value = {"id": "hashed_user_id", "username": "test_user"}

    fake_logs = AsyncMock()
    fake_logs.insert_one = AsyncMock()
    mock_db.__getitem__.return_value = fake_logs

    response = client.get(
        BASE_URL_AUTH + f"/{user_id}?model=invalid",
        headers=valid_token_header,
    )
    assert response.status_code == status.HTTP_200_OK

    fake_redis.get.assert_awaited_with(cache_key)
    mock_get_recommendations.assert_awaited_with(user_id, mock_db, model_type="als")
    assert response.json() == result

    fake_redis.setex.assert_awaited()
    fake_logs.insert_one.assert_awaited_once()

    app.dependency_overrides.pop(get_redis, None)


# # ==================================================================
# # 4. Отсутствует параметр model → используется random.choice
# # ==================================================================
@patch("api.v1.recommend.random.choice", return_value="lightfm")
@patch("api.v1.recommend.db")
@patch("api.v1.recommend.recommendation_model.get_recommendations")
@patch("core.jwt.security_jwt")
@pytest.mark.asyncio
async def test_get_recommendations_no_model_param(
    mock_security,
    mock_get_recommendations,
    mock_db,
    mock_random_choice,
    valid_token_header,
):
    """
    Если параметр model не передан, то выбирается случайная модель.
    Здесь random.choice замокан и возвращает "lightfm".
    """
    user_id = "hashed_user_id"
    result = {
        "recommendations": ["movieY", "movieZ"],
        "session_id": "sess999",
        "source": "model",
    }
    cache_key = f"recommendations:{user_id}:lightfm"

    fake_redis = AsyncMock()
    fake_redis.get = AsyncMock(return_value=None)
    fake_redis.setex = AsyncMock()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    mock_get_recommendations.return_value = result
    mock_security.return_value = {"id": "hashed_user_id", "username": "test_user"}
    fake_logs = AsyncMock()
    fake_logs.insert_one = AsyncMock()
    mock_db.__getitem__.return_value = fake_logs

    response = client.get(
        BASE_URL_AUTH + f"/{user_id}",
        headers=valid_token_header,
    )
    assert response.status_code == status.HTTP_200_OK

    fake_redis.get.assert_awaited_with(cache_key)
    mock_get_recommendations.assert_awaited_with(user_id, mock_db, model_type="lightfm")
    assert response.json() == result

    app.dependency_overrides.pop(get_redis, None)


###########################################
# submit_feedback
###########################################


# --------------------------------------------
# 1. Успешная отправка обратной связи
# --------------------------------------------
@patch("api.v1.recommend.db")
@patch("core.jwt.security_jwt")
@pytest.mark.asyncio
async def test_submit_feedback_success(mock_security, mock_db, valid_token_header):
    """
    При наличии валидного токена и всех обязательных параметров обратной связи,
    feedback сохраняется в базе и возвращается {"status": "success"}.
    """
    session_id = "sess_001"
    movie_id = "movie_123"
    liked = True

    mock_security.return_value = {"id": "hashed_user_id", "username": "test_user"}

    fake_feedback_collection = AsyncMock()
    fake_feedback_collection.insert_one = AsyncMock()
    mock_db.__getitem__.return_value = fake_feedback_collection

    response = client.post(
        BASE_URL_AUTH
        + f"/feedback/{session_id}?movie_id={movie_id}&liked={str(liked).lower()}",
        headers=valid_token_header,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "success"}

    fake_feedback_collection.insert_one.assert_awaited_once()

    args, kwargs = fake_feedback_collection.insert_one.await_args
    inserted_data = args[0]

    assert inserted_data["session_id"] == session_id
    assert inserted_data["movie_id"] == movie_id
    assert inserted_data["liked"] is liked
    assert "timestamp" in inserted_data
    assert isinstance(inserted_data["timestamp"], datetime)


# # --------------------------------------------
# # 2. Невалидные (отсутствующие) параметры запроса
# # --------------------------------------------
@patch("core.jwt.security_jwt")
@pytest.mark.asyncio
async def test_submit_feedback_missing_parameters(mock_security, valid_token_header):
    session_id = "sess_002"
    mock_security.return_value = {"id": "hashed_user_id", "username": "test_user"}

    response = client.post(
        BASE_URL_AUTH + f"/feedback/{session_id}",
        headers=valid_token_header,
    )
    assert response.status_code == 422
