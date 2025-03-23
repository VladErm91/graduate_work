import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

BASE_URL = "http://127.0.0.1/api/auth/v1/roles"
BASE_URL_AUTH = "http://127.0.0.1/api/auth/v1/login/"


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def admin_token():
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        response = await client.post(
            "",
            data={"username": "admin", "password": "12345678"},
        )
        access_token = response.json().get("access_token")
    return f"Bearer {access_token}"


@pytest_asyncio.fixture(scope="module")
async def user_token_and_id():
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        response = await client.post(
            "",
            data={"username": "testuser", "password": "testpassword"},
        )
        access_token = response.json().get("access_token")
        user_id = response.json().get("user_id")
    return f"Bearer {access_token}", user_id


async def clean(role_id):
    async with AsyncClient(base_url=BASE_URL_AUTH) as client:
        login = await client.post(
            "",
            data={"username": "admin", "password": "12345678"},
        )
        access_token = login.json().get("access_token")
        response = await client.delete(
            f"/roles/{role_id}",
            headers={"Authorization": access_token},
        )
    return response


@pytest.mark.asyncio
async def test_create_role_as_admin(admin_token):
    unique_role_name = f"manager_{uuid.uuid4()}"
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/",
            json={"name": unique_role_name, "description": "Manager role"},
            headers={"Authorization": admin_token},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == unique_role_name
    assert data["description"] == "Manager role"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_role_as_non_admin(user_token_and_id):
    user_token, _ = user_token_and_id
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/",
            json={"name": "developer", "description": "Developer role"},
            headers={"Authorization": user_token},
        )
    assert (
        response.status_code == 403
    ), f"Unexpected status code: {response.status_code}"
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_create_existing_role(admin_token):
    async with AsyncClient(base_url=BASE_URL) as client:
        unique_role_name = f"manager_{uuid.uuid4()}"
        response1 = await client.post(
            "/",
            json={"name": unique_role_name, "description": "Tester role"},
            headers={"Authorization": admin_token},
        )
        assert response1.status_code == 200

        # Пытаемся создать ту же роль снова
        response2 = await client.post(
            "/",
            json={"name": unique_role_name, "description": "Another tester role"},
            headers={"Authorization": admin_token},
        )
        assert (
            response2.status_code == 400
        ), f"Unexpected status code: {response2.status_code}"
        assert response2.json()["detail"] == "Role already exists"
        created_role = response1.json()
        role_id = created_role["id"]
    await clean(role_id)


@pytest.mark.asyncio
async def test_get_roles_as_admin(admin_token):
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/", headers={"Authorization": admin_token})
    assert (
        response.status_code == 200
    ), f"Ожидался статус 200, получен {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Ожидался список ролей"


@pytest.mark.asyncio
async def test_get_roles_as_non_admin(user_token_and_id):
    user_token, _ = user_token_and_id
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/", headers={"Authorization": user_token})
    assert (
        response.status_code == 403
    ), f"Ожидался статус 403, получен {response.status_code}"
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_get_role_as_admin(admin_token):
    unique_role_name = f"tester_{uuid.uuid4()}"
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post(
            "/",
            json={"name": unique_role_name, "description": "Tester role"},
            headers={"Authorization": admin_token},
        )
    assert (
        create_response.status_code == 200
    ), f"Ожидался статус 200, получен {create_response.status_code}"
    created_role = create_response.json()
    role_id = created_role["id"]

    async with AsyncClient(base_url=BASE_URL) as client:
        get_response = await client.get(
            f"/{role_id}",
            headers={"Authorization": admin_token},
        )
    assert (
        get_response.status_code == 200
    ), f"Ожидался статус 200, получен {get_response.status_code}"
    role_data = get_response.json()
    assert role_data["name"] == unique_role_name
    assert role_data["description"] == "Tester role"
    assert role_data["id"] == role_id
    await clean(role_id)


@pytest.mark.asyncio
async def test_get_role_as_non_admin(user_token_and_id):

    _, user_id = user_token_and_id
    # Предполагается, что роль с определенным ID существует
    role_id = (
        uuid.uuid4()
    )  # Генерируем случайный UUID, который, вероятно, не существует
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            f"/{role_id}",
            headers={"Authorization": user_token_and_id[0]},
        )
    assert (
        response.status_code == 403
    ), f"Ожидался статус 403, получен {response.status_code}"
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_get_nonexistent_role(admin_token):
    non_existent_role_id = uuid.uuid4()
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            f"/{non_existent_role_id}",
            headers={"Authorization": admin_token},
        )
    assert (
        response.status_code == 404
    ), f"Ожидался статус 404, получен {response.status_code}"
    assert response.json()["detail"] == "Role not found"


@pytest.mark.asyncio
async def test_update_role_as_admin(admin_token):
    # Сначала создаем роль для обновления
    unique_role_name = f"developer_{uuid.uuid4()}"
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post(
            "/",
            json={"name": unique_role_name, "description": "Developer role"},
            headers={"Authorization": admin_token},
        )
    assert create_response.status_code == 200
    created_role = create_response.json()
    role_id = created_role["id"]

    # Обновляем роль
    updated_name = f"s_developer_{uuid.uuid4()}"
    updated_description = "Senior Developer role"
    async with AsyncClient(base_url=BASE_URL) as client:
        update_response = await client.put(
            f"/{role_id}",
            json={"name": updated_name, "description": updated_description},
            headers={"Authorization": admin_token},
        )
    assert (
        update_response.status_code == 200
    ), f"Ожидался статус 200, получен {update_response.status_code}"
    updated_role = update_response.json()
    assert updated_role["name"] == updated_name
    assert updated_role["description"] == updated_description
    assert updated_role["id"] == role_id
    await clean(role_id)


@pytest.mark.asyncio
async def test_update_role_as_non_admin(user_token_and_id):
    _, user_id = user_token_and_id
    # Предполагается, что роль с определенным ID существует
    role_id = (
        uuid.uuid4()
    )  # Генерируем случайный UUID, который, вероятно, не существует
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.put(
            f"/{role_id}",
            json={"name": "new_name", "description": "New description"},
            headers={"Authorization": user_token_and_id[0]},
        )
    assert (
        response.status_code == 403
    ), f"Ожидался статус 403, получен {response.status_code}"
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_update_nonexistent_role(admin_token):
    non_existent_role_id = uuid.uuid4()
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.put(
            f"/{non_existent_role_id}",
            json={"name": "ghost_role", "description": "This role does not exist"},
            headers={"Authorization": admin_token},
        )
    assert (
        response.status_code == 404
    ), f"Ожидался статус 404, получен {response.status_code}"
    assert response.json()["detail"] == "Role not found"


@pytest.mark.asyncio
async def test_delete_role_as_admin(admin_token):
    # Сначала создаем роль для удаления
    unique_role_name = f"tester_{uuid.uuid4()}"
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post(
            "/",
            json={"name": unique_role_name, "description": "Tester role"},
            headers={"Authorization": admin_token},
        )
    assert create_response.status_code == 200
    created_role = create_response.json()
    role_id = created_role["id"]

    # Удаляем роль
    async with AsyncClient(base_url=BASE_URL) as client:
        delete_response = await client.delete(
            f"/{role_id}",
            headers={"Authorization": admin_token},
        )
    assert delete_response.status_code in [
        200,
        204,
    ], f"Ожидался статус 200 или 204, получен {delete_response.status_code}"
    assert delete_response.json()["message"] == "Role deleted successfully"

    # Проверяем, что роль действительно удалена
    async with AsyncClient(base_url=BASE_URL) as client:
        get_response = await client.get(
            f"/{role_id}",
            headers={"Authorization": admin_token},
        )
    assert get_response.status_code == 404, "Ожидался статус 404 после удаления роли"


@pytest.mark.asyncio
async def test_delete_role_as_non_admin(user_token_and_id):
    _, user_id = user_token_and_id
    # Предполагается, что роль с определенным ID существует
    role_id = (
        uuid.uuid4()
    )  # Генерируем случайный UUID, который, вероятно, не существует
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.delete(
            f"/{role_id}",
            headers={"Authorization": user_token_and_id[0]},
        )
    assert (
        response.status_code == 403
    ), f"Ожидался статус 403, получен {response.status_code}"
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_delete_nonexistent_role(admin_token):
    non_existent_role_id = uuid.uuid4()
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.delete(
            f"/{non_existent_role_id}",
            headers={"Authorization": admin_token},
        )
    assert (
        response.status_code == 404
    ), f"Ожидался статус 404, получен {response.status_code}"
    assert response.json()["detail"] == "Role not found"


@pytest.mark.asyncio
async def test_assign_role_to_user_as_admin(admin_token, user_token_and_id):
    user_token, user_id = user_token_and_id
    # Сначала создаем роль для назначения
    unique_role_name = f"role_{uuid.uuid4()}"
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post(
            "/",
            json={"name": unique_role_name, "description": "Role to assign"},
            headers={"Authorization": admin_token},
        )
    assert create_response.status_code == 200
    created_role = create_response.json()
    role_id = created_role["id"]

    # Назначаем роль пользователю
    async with AsyncClient(base_url=BASE_URL) as client:
        assign_response = await client.post(
            f"/users/{user_id}/roles/{role_id}",
            headers={"Authorization": admin_token},
        )
    assert (
        assign_response.status_code == 200
    ), f"Ожидался статус 200, получен {assign_response.status_code}"
    assert assign_response.json()["message"] == "Role assigned to user successfully"

    # Попытка назначить ту же роль снова должна вернуть 400
    async with AsyncClient(base_url=BASE_URL) as client:
        assign_response_duplicate = await client.post(
            f"/users/{user_id}/roles/{role_id}",
            headers={"Authorization": admin_token},
        )
    assert (
        assign_response_duplicate.status_code == 400
    ), f"Ожидался статус 400, получен {assign_response_duplicate.status_code}"
    assert assign_response_duplicate.json()["detail"] == "Role already assigned to user"
    await clean(role_id)


@pytest.mark.asyncio
async def test_assign_role_to_user_as_non_admin(user_token_and_id):
    user_token, user_id = user_token_and_id
    # Создаем роль для назначения
    unique_role_name = f"non_admin_assign_{uuid.uuid4()}"
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post(
            "/",
            json={
                "name": unique_role_name,
                "description": "Role for non-admin assignment",
            },
            headers={"Authorization": user_token},
        )
    # Предполагается, что создание роли требует прав администратора
    assert (
        create_response.status_code == 403
    ), "Ожидался статус 403 при создании роли не администратором"


@pytest.mark.asyncio
async def test_assign_nonexistent_role_to_user(admin_token, user_token_and_id):
    user_token, user_id = user_token_and_id
    non_existent_role_id = uuid.uuid4()
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            f"/users/{user_id}/roles/{non_existent_role_id}",
            headers={"Authorization": admin_token},
        )
    assert (
        response.status_code == 404
    ), f"Ожидался статус 404, получен {response.status_code}"
    assert response.json()["detail"] == "Role not found"


@pytest.mark.asyncio
async def test_assign_role_to_nonexistent_user(admin_token):
    non_existent_user_id = uuid.uuid4()
    # Сначала создаем роль для назначения
    unique_role_name = f"role_{uuid.uuid4()}"
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post(
            "/",
            json={"name": unique_role_name, "description": "non-existent user"},
            headers={"Authorization": admin_token},
        )
    assert create_response.status_code == 200
    created_role = create_response.json()
    role_id = created_role["id"]

    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            f"/users/{non_existent_user_id}/roles/{role_id}",
            headers={"Authorization": admin_token},
        )
    assert (
        response.status_code == 404
    ), f"Ожидался статус 404, получен {response.status_code}"
    assert response.json()["detail"] == "User not found"
    await clean(role_id)


@pytest.mark.asyncio
async def test_revoke_role_from_user_as_admin(admin_token, user_token_and_id):
    user_token, user_id = user_token_and_id
    # Сначала создаем роль и назначаем ее пользователю
    unique_role_name = f"role_{uuid.uuid4()}"
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post(
            "/",
            json={"name": unique_role_name, "description": "Role to revoke"},
            headers={"Authorization": admin_token},
        )
    assert create_response.status_code == 200
    created_role = create_response.json()
    role_id = created_role["id"]

    # Назначаем роль пользователю
    async with AsyncClient(base_url=BASE_URL) as client:
        assign_response = await client.post(
            f"/users/{user_id}/roles/{role_id}",
            headers={"Authorization": admin_token},
        )
    assert assign_response.status_code == 200

    # Отзываем роль у пользователя
    async with AsyncClient(base_url=BASE_URL) as client:
        revoke_response = await client.delete(
            f"/users/{user_id}/roles/{role_id}",
            headers={"Authorization": admin_token},
        )
    assert (
        revoke_response.status_code == 200
    ), f"Ожидался статус 200, получен {revoke_response.status_code}"
    assert revoke_response.json()["message"] == "Role revoked from user successfully"

    # Попытка отозвать ту же роль снова должна вернуть 400
    async with AsyncClient(base_url=BASE_URL) as client:
        revoke_response_duplicate = await client.delete(
            f"/users/{user_id}/roles/{role_id}",
            headers={"Authorization": admin_token},
        )
    assert (
        revoke_response_duplicate.status_code == 400
    ), f"Ожидался статус 400, получен {revoke_response_duplicate.status_code}"
    assert revoke_response_duplicate.json()["detail"] == "Role not assigned to user"
    await clean(role_id)


@pytest.mark.asyncio
async def test_revoke_role_from_user_as_non_admin(user_token_and_id):
    user_token, user_id = user_token_and_id
    # Предполагается, что роль с определенным ID существует
    role_id = (
        uuid.uuid4()
    )  # Генерируем случайный UUID, который, вероятно, не существует
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.delete(
            f"/users/{user_id}/roles/{role_id}",
            headers={"Authorization": user_token},
        )
    assert (
        response.status_code == 403
    ), f"Ожидался статус 403, получен {response.status_code}"
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_revoke_role_from_nonexistent_user(admin_token):
    non_existent_user_id = uuid.uuid4()
    # Сначала создаем роль
    unique_role_name = f"role_{uuid.uuid4()}"
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post(
            "/",
            json={
                "name": unique_role_name,
                "description": "Role for revoking from non-existent user",
            },
            headers={"Authorization": admin_token},
        )
    assert create_response.status_code == 200
    created_role = create_response.json()
    role_id = created_role["id"]

    # Пытаемся отозвать роль у несуществующего пользователя
    async with AsyncClient(base_url=BASE_URL) as client:
        revoke_response = await client.delete(
            f"/users/{non_existent_user_id}/roles/{role_id}",
            headers={"Authorization": admin_token},
        )
    assert (
        revoke_response.status_code == 404
    ), f"Ожидался статус 404, получен {revoke_response.status_code}"
    assert revoke_response.json()["detail"] == "User not found"
    await clean(role_id)


@pytest.mark.asyncio
async def test_check_user_permission_as_admin(admin_token, user_token_and_id):
    user_token, user_id = user_token_and_id
    # Сначала создаем две роли
    role_names = [f"role_{uuid.uuid4()}" for _ in range(2)]
    role_ids = []
    async with AsyncClient(base_url=BASE_URL) as client:
        for name in role_names:
            response = await client.post(
                "/",
                json={"name": name, "description": f"{name} description"},
                headers={"Authorization": admin_token},
            )
            assert response.status_code == 200
            role = response.json()
            role_ids.append(role["id"])

    # Назначаем первой роли пользователю
    async with AsyncClient(base_url=BASE_URL) as client:
        assign_response = await client.post(
            f"/users/{user_id}/roles/{role_ids[0]}",
            headers={"Authorization": admin_token},
        )
    assert assign_response.status_code == 200

    # Проверяем наличие разрешений
    required_roles = f"{role_names[0]}, non_existing_role"
    async with AsyncClient(base_url=BASE_URL) as client:
        check_response = await client.get(
            f"/users/{user_id}/has-permission",
            params={"required_roles": required_roles},
            headers={"Authorization": admin_token},
        )
    assert (
        check_response.status_code == 200
    ), f"Ожидался статус 200, получен {check_response.status_code}"
    has_permission = check_response.json().get("has_permission")
    assert (
        has_permission is True
    ), "Ожидалось, что пользователь имеет одно из требуемых разрешений"

    # Проверяем отсутствие разрешений
    required_roles = "another_non_existing_role"
    async with AsyncClient(base_url=BASE_URL) as client:
        check_response = await client.get(
            f"/users/{user_id}/has-permission",
            params={"required_roles": required_roles},
            headers={"Authorization": admin_token},
        )
    assert check_response.status_code == 200
    has_permission = check_response.json().get("has_permission")
    assert (
        has_permission is False
    ), "Ожидалось, что пользователь не имеет требуемых разрешений"
    await clean(role_ids[0])
    await clean(role_ids[1])


@pytest.mark.asyncio
async def test_check_user_permission_as_non_admin(user_token_and_id):
    user_token, user_id = user_token_and_id
    required_roles = "any_role"
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            f"/users/{user_id}/has-permission",
            params={"required_roles": required_roles},
            headers={"Authorization": user_token},
        )
    assert (
        response.status_code == 403
    ), f"Ожидался статус 403, получен {response.status_code}"
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_check_permission_for_nonexistent_user(admin_token):
    non_existent_user_id = uuid.uuid4()
    required_roles = "any_role"
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            f"/users/{non_existent_user_id}/has-permission",
            params={"required_roles": required_roles},
            headers={"Authorization": admin_token},
        )
    assert (
        response.status_code == 404
    ), f"Ожидался статус 404, получен {response.status_code}"
    assert response.json()["detail"] == "User not found"
