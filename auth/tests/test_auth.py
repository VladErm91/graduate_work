import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient

BASE_URL_AUTH = "http://127.0.0.1/api/auth/v1/login"
BASE_URL_USERS = "http://127.0.0.1/api/auth/v1/users/"


user_data = {
    "login": "testuser",
    "email": "test@example.com",
    "password": "testpassword",
    "first_name": "Test",
    "last_name": "User",
}


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def get_user_id():
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        response = await client.post(
            "/",
            data={"username": "testuser", "password": "testpassword"},
        )
        user_id = response.json().get("user_id")
    return user_id


@pytest_asyncio.fixture(scope="module")
async def get_user_token():
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        response = await client.post(
            "/",
            data={"username": "testuser", "password": "testpassword"},
        )
        token = response.json().get("access_token")
    return token


@pytest_asyncio.fixture(scope="module")
async def get_user_refresh_token():
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        response = await client.post(
            "/",
            data={"username": "testuser", "password": "testpassword"},
        )
        token = response.json().get("refresh_token")
    return token


@pytest.mark.asyncio
async def test_register_user():
    async with AsyncClient(base_url=BASE_URL_USERS) as client:
        response = await client.post("/register", json=user_data)
    assert response.status_code == 200
    assert response.json()["login"] == user_data["login"]


# @pytest.mark.asyncio
# async def test_register_user2():
#     async with AsyncClient(base_url=BASE_URL_USERS) as client:
#         response = await client.post("/register", json=user_data2)
#     assert response.status_code == 200
#     assert response.json()["login"] == user_data2["login"]


@pytest.mark.asyncio
async def test_login_user():
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        response = await client.post(
            "/",
            data={"username": "testuser", "password": "testpassword"},
        )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_user_failed():
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        response = await client.post(
            "/",
            data={"username": "testuser", "password": "testpassword1"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(get_user_refresh_token):
    user_token = get_user_refresh_token
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        response = await client.post(f"/refresh-token?token={user_token}")
    print(response.request.url)
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_get_user(get_user_token):
    user_token = get_user_token
    async with AsyncClient(base_url=BASE_URL_USERS) as client:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = await client.get("/me", headers=headers)

    assert response.status_code == 200
    # assert response.json()["login"] == "testuser"


@pytest.mark.asyncio
async def test_change_username(get_user_token):
    user_token = get_user_token
    async with AsyncClient(base_url=BASE_URL_USERS) as client:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = await client.put(
            "/me",
            headers=headers,
            json={"first_name": "Test", "last_name": "Hoffer"},
        )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Test"


@pytest.mark.asyncio
async def test_user_auth_history(get_user_id):
    user_id = get_user_id
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        response = await client.get(f"/history_auth/{user_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_change_password(get_user_refresh_token):
    refresh_token = get_user_refresh_token
    # проверяем смену пароля
    async with AsyncClient(base_url=BASE_URL_USERS) as client:
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = await client.put(
            "/change-password",
            headers=headers,
            json={"old_password": "testpassword", "new_password": "testpassword2"},
        )
    assert response.status_code == 200
    # проверяем смену пароля на старый чтобы не нарушать работу тестов
    async with AsyncClient(base_url=BASE_URL_USERS) as client:
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = await client.put(
            "/change-password",
            headers=headers,
            json={"old_password": "testpassword2", "new_password": "testpassword"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_logout_user(get_user_refresh_token):
    refresh_token = get_user_refresh_token
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = await client.post("/logout", headers=headers)
    assert response.status_code == 200
    assert response.json()["msg"] == "Successfully logged out"
