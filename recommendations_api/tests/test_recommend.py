import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from core.jwt import security_jwt
from core.config import db
import json
from api.v1.recommend import get_redis
from datetime import datetime

client = TestClient(app)


@pytest.fixture(scope="module")
def valid_token_header():
    return {"Authorization": "Bearer some_valid_jwt_token", "X-Request-Id": "test-request-id"}


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


# ============================================================================
# 1. Тест: Отсутствует токен авторизации
# ============================================================================
@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value=None)
async def test_missing_authorization_token(jwt_get_token):
    """
    Если токен отсутствует, эндпоинт должен вернуть 403 с соответствующим сообщением.
    """
    response = client.get("/api/recommend/v1/recommendations/genres_top", headers={"X-Request-Id": "test-request-id"})
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Authorization token is missing"


# # ============================================================================
# # 2. Тест: Отсутствуют любимые жанры (ветка else)
# # ============================================================================
@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value="some_valid_jwt_token")
@patch.object(db, "favourite_genres")
@patch("httpx.AsyncClient.get")
async def test_no_favorite_genres(get_mock, favourite_genres_mock, jwt_get_token, valid_token_header):
    """
    Если в БД нет любимых жанров, делается один запрос к movie API без параметра genre.
    Возвращается список id фильмов.
    """
    favourite_genres_mock.find_one = AsyncMock(return_value=None)

    simulated_movies = [
        {"id": "movie1"},
        {"id": "movie2"},
        {"id": "movie3"}
    ]
    response_mock = AsyncMock()
    response_mock.status_code = 200
    response_mock.json = lambda: simulated_movies
    get_mock.return_value = response_mock

    response = client.get("/api/recommend/v1/recommendations/genres_top", headers=valid_token_header)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    expected_ids = [movie["id"] for movie in simulated_movies]
    assert data["movies"] == expected_ids
    get_mock.assert_called_once()


# # ============================================================================
# # 3. Тест: Пользователь имеет один любимый жанр
# # ============================================================================
@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value="some_valid_jwt_token")
@patch.object(db, "favourite_genres")
@patch("httpx.AsyncClient.get")
async def test_one_favorite_genre(get_mock, favourite_genres_mock, jwt_get_token, valid_token_header):
    """
    Если у пользователя один любимый жанр, делается один запрос с параметром genre.
    Количество возвращаемых фильмов соответствует limit.
    """
    favourite_genres_mock.find_one = AsyncMock(return_value={"genres": ["Action"]})

    simulated_movies = [
        {"id": "action_movie1"},
        {"id": "action_movie2"},
        {"id": "action_movie3"},
        {"id": "action_movie4"},
        {"id": "action_movie5"},
        {"id": "action_movie6"}
    ]
    response_mock = AsyncMock()
    response_mock.status_code = 200
    response_mock.json = lambda: simulated_movies
    get_mock.return_value = response_mock

    response = client.get("/api/recommend/v1/recommendations/genres_top", headers=valid_token_header)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    expected_ids = [movie["id"] for movie in simulated_movies]
    assert data["movies"] == expected_ids
    get_mock.assert_called_once()


# # ============================================================================
# # 4. Тест: Пользователь имеет два любимых жанра
# # ============================================================================
@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value="some_valid_jwt_token")
@patch.object(db, "favourite_genres")
@patch("httpx.AsyncClient.get")
async def test_two_favorite_genres(get_mock, favourite_genres_mock, jwt_get_token, valid_token_header):
    """
    При наличии 2 жанров и limit=6:
      - num_genres = 2, genre_limit = 6 // 2 = 3, remainder = 0.
      - Должно быть сделано 2 запроса, по 3 фильма для каждого жанра.
    """
    # Мокаем возвращаемое значение из БД — два любимых жанра.
    favourite_genres_mock.find_one = AsyncMock(return_value={"genres": ["Action", "Comedy"]})

    simulated_movies_action = [
        {"id": "movieA1"}, {"id": "movieA2"}, {"id": "movieA3"}
    ]
    simulated_movies_comedy = [
        {"id": "movieC1"}, {"id": "movieC2"}, {"id": "movieC3"}
    ]

    response_mock1 = AsyncMock()
    response_mock1.status_code = 200
    response_mock1.json = lambda: simulated_movies_action

    response_mock2 = AsyncMock()
    response_mock2.status_code = 200
    response_mock2.json = lambda: simulated_movies_comedy

    get_mock.side_effect = [response_mock1, response_mock2]

    response = client.get("/api/recommend/v1/recommendations/genres_top", headers=valid_token_header)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    expected_ids = [movie["id"] for movie in (simulated_movies_action + simulated_movies_comedy)]
    assert data["movies"] == expected_ids
    assert get_mock.call_count == 2


# # ============================================================================
# # 5. Тест: Пользователь имеет больше 3 любимых жанров
# # ============================================================================
@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value="some_valid_jwt_token")
@patch.object(db, "favourite_genres")
@patch("httpx.AsyncClient.get")
async def test_more_than_three_favorite_genres(get_mock, favourite_genres_mock, jwt_get_token, valid_token_header):
    """
    Если у пользователя более 3 жанров, используется только первые 3.
    """
    favourite_genres_mock.find_one = AsyncMock(
        return_value={"genres": ["Action", "Comedy", "Drama", "Horror"]}
    )

    simulated_movies_1 = [{"id": "movie1"}, {"id": "movie2"}]
    simulated_movies_2 = [{"id": "movie3"}, {"id": "movie4"}]
    simulated_movies_3 = [{"id": "movie5"}]

    response_mock1 = AsyncMock()
    response_mock1.status_code = 200
    response_mock1.json = lambda: simulated_movies_1

    response_mock2 = AsyncMock()
    response_mock2.status_code = 200
    response_mock2.json = lambda: simulated_movies_2

    response_mock3 = AsyncMock()
    response_mock3.status_code = 200
    response_mock3.json = lambda: simulated_movies_3

    get_mock.side_effect = [response_mock1, response_mock2, response_mock3]

    response = client.get("/api/recommend/v1/recommendations/genres_top", headers=valid_token_header)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    expected_ids = [movie["id"] for movie in (simulated_movies_1 + simulated_movies_2 + simulated_movies_3)]
    assert data["movies"] == expected_ids
    assert get_mock.call_count == 3


# # ============================================================================
# # 6. Тест: Ошибка запроса к API (ветка favorite_genres)
# # ============================================================================
@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value="some_valid_jwt_token")
@patch.object(db, "favourite_genres")
@patch("httpx.AsyncClient.get")
async def test_error_fetching_movies_favorite_genres(get_mock, favourite_genres_mock, jwt_get_token, valid_token_header):
    """
    Если один из запросов по любимым жанрам возвращает статус != 200,
    генерируется HTTPException с сообщением "Error fetching movies".
    """
    favourite_genres_mock.find_one = AsyncMock(return_value={"genres": ["Action", "Comedy"]})

    error_response_mock = AsyncMock()
    error_response_mock.status_code = 500
    error_response_mock.json.return_value = {}
    get_mock.side_effect = [error_response_mock]

    response = client.get("/api/recommend/v1/recommendations/genres_top", headers=valid_token_header)
    assert response.status_code == 500
    assert response.json()["detail"] == "Error fetching movies"



# # ============================================================================
# # 7. Тест: Ошибка запроса к API (ветка else, когда нет любимых жанров)
# # ============================================================================
@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value="some_valid_jwt_token")
@patch.object(db, "favourite_genres")
@patch("httpx.AsyncClient.get")
async def test_error_fetching_movies_no_favorite(get_mock, favourite_genres_mock, jwt_get_token, valid_token_header):
    """
    Если пользователь не имеет любимых жанров, а запрос к movie API завершается ошибкой,
    генерируется HTTPException.
    """
    favourite_genres_mock.find_one = AsyncMock(return_value=None)

    error_response_mock = AsyncMock()
    error_response_mock.status_code = 404
    error_response_mock.json.return_value = {}
    get_mock.return_value = error_response_mock

    response = client.get("/api/recommend/v1/recommendations/genres_top", headers=valid_token_header)
    assert response.status_code == 404
    assert response.json()["detail"] == "Error fetching movies"


# # ============================================================================
# # 8. Тест: Пользователь задал нестандартный лимит (например, limit=7) и два жанра
# # ============================================================================
@pytest.mark.asyncio
@patch("core.jwt.JWTBearer.get_token_from_request", return_value="some_valid_jwt_token")
@patch.object(db, "favourite_genres")
@patch("httpx.AsyncClient.get")
async def test_custom_limit_param_with_favorite_genres(get_mock, favourite_genres_mock, jwt_get_token, valid_token_header):
    """
    При наличии 2 жанров и limit=7:
      - num_genres = 2, genre_limit = 7 // 2 = 3, remainder = 1, и затем genre_limit увеличивается до 4.
      - Каждому жанру передается page_size = 4.
    """
    favourite_genres_mock.find_one = AsyncMock(return_value={"genres": ["Action", "Comedy"]})

    simulated_movies_action = [
        {"id": "movieA1"}, {"id": "movieA2"}, {"id": "movieA3"}, {"id": "movieA4"}
    ]
    simulated_movies_comedy = [
        {"id": "movieC1"}, {"id": "movieC2"}, {"id": "movieC3"}, {"id": "movieC4"}
    ]

    response_mock1 = AsyncMock()
    response_mock1.status_code = 200
    response_mock1.json = lambda: simulated_movies_action

    response_mock2 = AsyncMock()
    response_mock2.status_code = 200
    response_mock2.json = lambda: simulated_movies_comedy

    get_mock.side_effect = [response_mock1, response_mock2]

    response = client.get("/api/recommend/v1/recommendations/genres_top?limit=7", headers=valid_token_header)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    expected_ids = [movie["id"] for movie in simulated_movies_action + simulated_movies_comedy]
    assert data["movies"] == expected_ids
    assert get_mock.call_count == 2


###########################################
# get_recommendations
###########################################

# ==================================================================
# 1. Cache hit
# ==================================================================
@patch("api.v1.recommend.get_recommendations")
@patch("core.jwt.security_jwt")
@pytest.mark.asyncio
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
        "source": "cache"
    }
    cache_key = f"recommendations:{user_id}:als"

    fake_redis = AsyncMock()
    fake_redis.get = AsyncMock(return_value=json.dumps(result))
    fake_redis.setex = AsyncMock()

    app.dependency_overrides[get_redis] = lambda: fake_redis

    mock_security.return_value = {"id": "hashed_user_id", "username": "test_user"}
    mock_get_recommendations.return_value = None

    response = client.get(
        f"/api/recommend/v1/recommendations/{user_id}?model=als",
        headers=valid_token_header
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == result

    fake_redis.get.assert_awaited_with(cache_key)
    mock_get_recommendations.assert_not_called()

    app.dependency_overrides.pop(get_redis, None)


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
    user_id = "user456"
    result = {
        "recommendations": ["movie3", "movie4"],
        "session_id": "sess456",
        "source": "model"
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
        f"/api/recommend/v1/recommendations/{user_id}?model=lightfm",
        headers=valid_token_header
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
    valid_token_header
):
    """
    Если передан недопустимый параметр model (например, "invalid"),
    то выбирается случайное значение. Поскольку random.choice замокано и возвращает "als",
    в итоге используется модель "als".
    """
    user_id = "user789"
    result = {
        "recommendations": ["movieX"],
        "session_id": "sess789",
        "source": "model"
    }
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
        f"/api/recommend/v1/recommendations/{user_id}?model=invalid",
        headers=valid_token_header
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
    valid_token_header
):
    """
    Если параметр model не передан, то выбирается случайная модель.
    Здесь random.choice замокан и возвращает "lightfm".
    """
    user_id = "user999"
    result = {
        "recommendations": ["movieY", "movieZ"],
        "session_id": "sess999",
        "source": "model"
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
        f"/api/recommend/v1/recommendations/{user_id}",
        headers=valid_token_header
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
        f"/api/recommend/v1/recommendations/feedback/{session_id}?movie_id={movie_id}&liked={str(liked).lower()}",
        headers=valid_token_header,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "success"}

    fake_feedback_collection.insert_one.assert_awaited_once()

    args, kwargs = fake_feedback_collection.insert_one.await_args
    inserted_data = args[0]

    assert inserted_data["session_id"] == session_id
    assert inserted_data["movie_id"] == {"_id": movie_id}
    assert inserted_data["liked"] is liked
    assert "timestamp" in inserted_data
    assert isinstance(inserted_data["timestamp"], datetime)


# # --------------------------------------------
# # 2. Невалидные (отсутствующие) параметры запроса
# # --------------------------------------------
@patch("core.jwt.security_jwt")
@pytest.mark.asyncio
async def test_submit_feedback_missing_parameters(mock_security, valid_token_header):
    """
    Если не переданы обязательные query-параметры (movie_id и liked),
    FastAPI возвращает ошибку валидации (422).
    """
    session_id = "sess_002"
    mock_security.return_value = {"id": "hashed_user_id", "username": "test_user"}

    response = client.post(f"/api/recommend/v1/recommendations/feedback/{session_id}", headers=valid_token_header)
    assert response.status_code == 422
