from http import HTTPStatus

import pytest
from functional.settings import api_url, es_index, test_settings


@pytest.mark.asyncio
async def test_get_genre_by_id(make_get_request, es_write_data):
    """Тест для получения конкретного жанра по ID."""

    test_genre = {
        "uuid": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Horror",
    }

    await es_write_data(
        data=[
            {
                "_index": es_index.es_index_genres,
                "_id": test_genre["uuid"],
                "_source": test_genre,
            }
        ],
        es_index=es_index.es_index_genres,
        es_index_mapping=es_index.es_genres_mapping,
    )
    print(f"{test_settings.service_url}{api_url.genres_url}{test_genre['uuid']}")

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}{test_genre['uuid']}"
    )

    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert response_json["uuid"] == test_genre["uuid"]
    assert response_json["name"] == test_genre["name"]


@pytest.mark.asyncio
async def test_get_genre_not_found(make_get_request):
    """Тест для получения жанра по несуществующему ID."""
    invalid_id = "not-a-valid-uuid"

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}{invalid_id}"
    )

    assert response.status == HTTPStatus.NOT_FOUND
    response_json = await response.json()
    assert response_json["detail"] == "Genre not found"


@pytest.mark.asyncio
async def test_search_genres(make_get_request, es_write_data):
    """Тест для поиска жанров по имени."""

    test_genres = [
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174001",
            "name": "Horror",
        },
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174002",
            "name": "Comedy",
        },
    ]

    await es_write_data(
        data=[
            {"_index": es_index.es_index_genres, "_id": genre["uuid"], "_source": genre}
            for genre in test_genres
        ],
        es_index=es_index.es_index_genres,
        es_index_mapping=es_index.es_genres_mapping,
    )

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}",
        query_data={"query": "Hor"},
    )

    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert len(response_json["items"]) == 1
    assert response_json["items"][0]["uuid"] == test_genres[0]["uuid"]
    assert response_json["items"][0]["name"] == test_genres[0]["name"]


@pytest.mark.asyncio
async def test_search_genres_no_results(make_get_request, es_write_data):
    """Тест для поиска жанров с пустым результатом."""

    test_genres = [
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174001",
            "name": "Horror",
        },
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174002",
            "name": "Comedy",
        },
    ]

    await es_write_data(
        data=[
            {"_index": es_index.es_index_genres, "_id": genre["uuid"], "_source": genre}
            for genre in test_genres
        ],
        es_index=es_index.es_index_genres,
        es_index_mapping=es_index.es_genres_mapping,
    )

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}",
        query_data={"query": "Sci-Fi"},
    )
    text = await response.text()
    print(text)

    assert response.status == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_search_genres_sort_order(make_get_request, es_write_data):
    """Тест для проверки сортировки и порядка вывода."""

    test_genres = [
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174001",
            "name": "Horror",
        },
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174002",
            "name": "Comedy",
        },
    ]

    await es_write_data(
        data=[
            {"_index": es_index.es_index_genres, "_id": genre["uuid"], "_source": genre}
            for genre in test_genres
        ],
        es_index=es_index.es_index_genres,
        es_index_mapping=es_index.es_genres_mapping,
    )

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}",
        query_data={"order": "asc", "page_number": 1, "page_size": 10},
    )
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert len(response_json["items"]) == 2
    assert response_json["items"][0]["name"] == "Comedy"
    assert response_json["items"][1]["name"] == "Horror"

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}",
        query_data={"order": "desc", "page_number": 1, "page_size": 10},
    )
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert len(response_json["items"]) == 2
    assert response_json["items"][0]["name"] == "Horror"
    assert response_json["items"][1]["name"] == "Comedy"


@pytest.mark.asyncio
async def test_search_genres_pagination(make_get_request, es_write_data):
    """Тест для проверки пагинации."""

    test_genres = [{"uuid": f"uuid-{i}", "name": f"Genre-{i}"} for i in range(20)]

    await es_write_data(
        data=[
            {"_index": es_index.es_index_genres, "_id": genre["uuid"], "_source": genre}
            for genre in test_genres
        ],
        es_index=es_index.es_index_genres,
        es_index_mapping=es_index.es_genres_mapping,
    )

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}",
        query_data={"page_number": 1, "page_size": 5},
    )
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert len(response_json["items"]) == 5
    assert response_json["items"][0]["name"] == "Genre-0"
    assert response_json["page_number"] == 1
    assert response_json["page_size"] == 5

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}",
        query_data={"page_number": 2, "page_size": 5},
    )
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert len(response_json["items"]) == 5
    assert response_json["items"][0]["name"] == "Genre-5"
    assert response_json["page_number"] == 2
    assert response_json["page_size"] == 5

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}",
        query_data={"page_number": 10, "page_size": 5},
    )
    assert response.status == HTTPStatus.NOT_FOUND
    response_json = await response.json()
    assert response_json["detail"] == "Page not found"


@pytest.mark.asyncio
async def test_search_genres_invalid_order(make_get_request):
    """Тест для проверки невалидного значения параметра order."""

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}",
        query_data={"order": "invalid"},
    )
    assert (
        response.status == HTTPStatus.UNPROCESSABLE_ENTITY
    )  # Ожидаем ошибку валидации

    response_json = await response.json()
    assert "Input should be 'asc' or 'desc'" in response_json["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_search_genres_invalid_page_size(make_get_request):
    """Тест для проверки невалидного значения параметра page_size."""

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}",
        query_data={"page_size": 101},
    )
    assert (
        response.status == HTTPStatus.UNPROCESSABLE_ENTITY
    )  # Ожидаем ошибку валидации

    response_json = await response.json()
    assert "Input should be less than 100" in response_json["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_genre_details_caching(make_get_request, es_write_data):
    """Тест проверки кеширования данных в Redis при повторном запросе."""

    test_genre = {
        "uuid": "123e4567-e89b-12d3-a456-426614174001",
        "name": "Comedy",
    }

    await es_write_data(
        data=[
            {
                "_index": es_index.es_index_genres,
                "_id": test_genre["uuid"],
                "_source": test_genre,
            }
        ],
        es_index=es_index.es_index_genres,
        es_index_mapping=es_index.es_genres_mapping,
    )

    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}{test_genre['uuid']}"
    )
    assert (
        response.status == HTTPStatus.OK
    ), f"Unexpected status code: {response.status}"
    response_json = await response.json()
    assert response_json is not None, f"Response JSON is None: {response}"
    assert (
        response_json["uuid"] == test_genre["uuid"]
    ), "Returned genre UUID does not match expected value"
    assert (
        response_json["name"] == test_genre["name"]
    ), "Returned genre name does not match expected value"

    # Удаляем данные из Elasticsearch, чтобы убедиться, что при следующем запросе данные будут взяты из кеша
    await es_write_data(
        data=[],
        es_index=es_index.es_index_genres,
        es_index_mapping=es_index.es_genres_mapping,
    )

    # Повторный запрос к API (данные должны вернуться из кеша Redis)
    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.genres_url}{test_genre['uuid']}"
    )
    assert (
        response.status == HTTPStatus.OK
    ), f"Unexpected status code: {response.status}"
    response_json = await response.json()
    assert response_json is not None, f"Response JSON is None: {response}"
    assert (
        response_json["uuid"] == test_genre["uuid"]
    ), "Returned genre UUID does not match expected value"
    assert (
        response_json["name"] == test_genre["name"]
    ), "Returned genre name does not match expected value"
