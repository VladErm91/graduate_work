import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from main import app
from core.config import db
from core.jwt import security_jwt

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


@pytest.mark.asyncio
@patch.object(db, 'favourite_genres')
async def test_add_favorite_genres_first_time(mock_collection, valid_token_header):
    """
    Тест для ситуации, когда пользователь впервые добавляет любимые жанры.
    """
    # Смоделировать, что записи для пользователя изначально нет
    # Первый вызов find_one -> None, второй вызов -> документ с добавленными жанрами.
    mock_collection.find_one = AsyncMock(side_effect=[
        None,
        {"user_id": "hashed_user_id", "genres": ["Action", "Drama"]}
    ])

    # Мокаем успешный вызов insert_one
    mock_collection.insert_one = AsyncMock(return_value=None)

    payload = ['Action', 'Drama']

    response = client.post("/api/recommend/v1/favorites/genres", json=payload, headers=valid_token_header)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["genres"] == ["Action", "Drama"]

    # Проверяем, что insert_one был вызван один раз
    mock_collection.insert_one.assert_awaited_once()


@pytest.mark.asyncio
@patch.object(db, 'favourite_genres')
async def test_add_favorite_genres_with_existing_1_genre(mock_collection, valid_token_header):
    """
    Тест, когда у пользователя уже есть 1 жанр, и он добавляет ещё 2.
    Всего становится 3.
    """
    existing = {
        "user_id": "hashed_user_id",
        "genres": ["Family"]
    }
    updated = {
        "user_id": "hashed_user_id",
        "genres": ["Family", "Action", "Drama"]
    }
    mock_collection.find_one = AsyncMock(side_effect=[existing, updated])
    mock_collection.update_one = AsyncMock(return_value=None)

    payload = ["Action", 'Drama']

    response = client.post("/api/recommend/v1/favorites/genres", json=payload, headers=valid_token_header)
    assert response.status_code == status.HTTP_200_OK, response.text

    result_genres = response.json()["genres"]
    assert "Family" in result_genres
    assert "Action" in result_genres
    assert "Drama" in result_genres
    assert len(result_genres) == 3

    mock_collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
@patch.object(db, 'favourite_genres')
async def test_add_favorite_genres_with_existing_2_genres_only_1_free_slot(mock_collection, valid_token_header):
    """
    Тест, когда у пользователя уже есть 2 жанра.
    Он пытается добавить сразу 2 новых, но слотов осталось только 1.
    Значит, добавится только 1 новый жанр, а второй проигнорируется.
    """
    existing = {
        "user_id": "hashed_user_id",
        "genres": ["Fantasy", "Music"]
    }
    updated = {
        "user_id": "hashed_user_id",
        "genres": ["Fantasy", "Music", "Romance"]
    }

    mock_collection.find_one = AsyncMock(side_effect=[existing, updated])
    mock_collection.update_one = AsyncMock(return_value=None)

    payload = ["Romance", "Comedy"]

    response = client.post('/api/recommend/v1/favorites/genres', json=payload, headers=valid_token_header)
    assert response.status_code == status.HTTP_200_OK

    updated_genres = response.json()["genres"]
    assert len(updated_genres) == 3
    assert "Fantasy" in updated_genres
    assert "Music" in updated_genres
    assert "Romance" in updated_genres
    assert "Comedy" not in updated_genres

    mock_collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
@patch.object(db, 'favourite_genres')
async def test_add_favorite_genres_already_3_genres(mock_collection, valid_token_header):
    """
    Тест, когда у пользователя уже есть 3 жанра.
    Добавлять больше нельзя.
    """
    existing = {
        "user_id": "hashed_user_id",
        "genres": ["Action", "Fantasy", "Drama"]
    }
    mock_collection.find_one = AsyncMock(return_value=existing)

    payload = ["Music"]

    response = client.post("/api/recommend/v1/favorites/genres", json=payload, headers=valid_token_header)

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    assert response.json()["detail"] == "You can only have up to 3 favorite genres."


@pytest.mark.asyncio
@patch.object(db, 'favourite_genres')
async def test_add_favorite_genres_with_existing_but_duplicate(mock_collection, valid_token_header):
    """
    Тест, когда у пользователя есть 2 жанра, и он пытается добавить дубликат (один из них совпадает).
    В результате должен сохраниться оригинальный жанр, а новый (не дубль) добавиться.
    """
    existing = {
        "user_id": "hashed_user_id",
        "genres": ["Action", "Fantasy"]
    }
    updated = {
        "user_id": "hashed_user_id",
        "genres": ["Action", "Fantasy", "Music"]
    }

    mock_collection.find_one = AsyncMock(side_effect=[existing, updated])
    mock_collection.update_one = AsyncMock(return_value=None)

    payload = ["Action", "Music"]

    response = client.post("/api/recommend/v1/favorites/genres", json=payload, headers=valid_token_header)
    assert response.status_code == status.HTTP_200_OK, response.text

    updated_genres = response.json()["genres"]

    assert len(updated_genres) == 3
    assert "Action" in updated_genres
    assert "Fantasy" in updated_genres
    assert "Music" in updated_genres

    mock_collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
@patch.object(db, 'favourite_genres')
async def test_add_favorite_genres_more_than_3_in_one_request(mock_collection, valid_token_header):
    """
    Тест, когда пользователь пытается добавить более 3 жанров сразу (а у него нет жанров).
    Допустим, он передал 4 жанра. Всё равно останется лимит в 3.
    """
    updated_document = {"user_id": "hashed_user_id", "genres": ["Action", "Fantasy", "Music"]}
    mock_collection.find_one = AsyncMock(side_effect=[None, updated_document])
    mock_collection.insert_one = AsyncMock(return_value=None)

    payload = ["Action", "Fantasy", "Music", "Drama"]

    response = client.post("/api/recommend/v1/favorites/genres", json=payload, headers=valid_token_header)
    assert response.status_code == status.HTTP_200_OK, response.text

    updated_genres = response.json()["genres"]
    assert len(updated_genres) == 3
    for genre in ["Action", "Fantasy", "Music"]:
        assert genre in updated_genres

    mock_collection.insert_one.assert_awaited_once()
