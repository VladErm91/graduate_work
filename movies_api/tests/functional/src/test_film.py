import time
from http import HTTPStatus

import pytest
from functional.settings import api_url, es_index, test_settings
from functional.testdata.films_testdata import film_data


@pytest.mark.parametrize("test_film", [film_data["test_film"]])
@pytest.mark.asyncio
async def test_get_film_by_id(make_get_request, es_write_data, test_film):
    """Тест для получения конкретного фильма по ID."""

    # Подготовка данных для Elasticsearch
    await es_write_data(
        data=[
            {
                "_index": es_index.es_index_films,
                "_id": test_film["uuid"],
                "_source": test_film,
            }
        ],
        es_index=es_index.es_index_films,
        es_index_mapping=es_index.es_movies_mapping,
    )

    # Запрос фильма по ID
    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.films_url}{test_film['uuid']}",
        query_data={},
    )

    # Проверка успешного статуса и корректности возвращаемых данных
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert response_json["uuid"] == test_film["uuid"]
    assert response_json["title"] == test_film["title"]


@pytest.mark.parametrize(
    "invalid_id", ["not-a-valid-uuid", "12345678", "invalid-uuid-format"]
)
@pytest.mark.asyncio
async def test_get_film_by_invalid_id(make_get_request, invalid_id):
    """Тест на запрос фильма по некорректному ID."""
    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.films_url}{invalid_id}", query_data={}
    )

    # Проверка, что API возвращает ошибку 404
    assert response.status == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    "test_films, expected_uuids",
    [
        (
            film_data["test_films"],
            [
                "123e4567-e89b-12d3-a456-426614174002",
                "123e4567-e89b-12d3-a456-426614174001",
            ],
        )
    ],
)
@pytest.mark.asyncio
async def test_get_default_films(
    make_get_request, es_write_data, test_films, expected_uuids
):
    """Тест получения фильмов с дефолтными параметрами при пустом запросе."""

    # Запись данных в Elasticsearch
    await es_write_data(
        data=[
            {"_index": es_index.es_index_films, "_id": film["uuid"], "_source": film}
            for film in test_films
        ],
        es_index=es_index.es_index_films,
        es_index_mapping=es_index.es_movies_mapping,
    )

    # Пустой запрос (должен вернуть фильмы по дефолтным параметрам)
    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.films_url}", query_data={}
    )
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert response_json is not None, f"Response JSON is None: {response}"
    assert len(response_json) == len(test_films)  # Ожидается, что вернутся все фильмы

    # Проверка порядка сортировки по умолчанию (desc)
    for i, film_uuid in enumerate(expected_uuids):
        assert response_json[i]["uuid"] == film_uuid


@pytest.mark.parametrize(
    "page_size, page_number, expected_uuid",
    [
        (1, 1, "123e4567-e89b-12d3-a456-426614174002"),
        (1, 2, "123e4567-e89b-12d3-a456-426614174001"),
    ],
)
@pytest.mark.asyncio
async def test_get_films_with_pagination_and_sorting(
    make_get_request, es_write_data, page_size, page_number, expected_uuid
):
    """Тест получения фильмов с параметрами сортировки и пагинации."""

    test_films = film_data["test_films"]

    # Запись данных в Elasticsearch
    await es_write_data(
        data=[
            {"_index": es_index.es_index_films, "_id": film["uuid"], "_source": film}
            for film in test_films
        ],
        es_index=es_index.es_index_films,
        es_index_mapping=es_index.es_movies_mapping,
    )

    # Запрос с пагинацией и сортировкой
    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.films_url}",
        query_data={"page_size": page_size, "page_number": page_number},
    )
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert response_json is not None, f"Response JSON is None: {response}"
    assert len(response_json) == 1
    assert response_json[0]["uuid"] == expected_uuid  # Проверка UUID фильма


@pytest.mark.asyncio
async def test_redis_caching(make_get_request, es_write_data):
    """Тест проверки кеширования данных в Redis при повторном запросе."""

    # Данные для тестового фильма
    test_film = film_data["test_film"]

    # Подготовка данных для Elasticsearch
    await es_write_data(
        data=[
            {
                "_index": es_index.es_index_films,
                "_id": test_film["uuid"],
                "_source": test_film,
            }
        ],
        es_index=es_index.es_index_films,
        es_index_mapping=es_index.es_movies_mapping,
    )

    # Первый запрос фильма по ID (данные должны быть загружены из Elasticsearch)
    start_time = time.monotonic()
    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.films_url}{test_film['uuid']}",
        query_data={},
    )
    first_duration = time.monotonic() - start_time

    # Проверка успешного статуса и корректности возвращаемых данных
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert response_json["uuid"] == test_film["uuid"]
    assert response_json["title"] == test_film["title"]

    # Второй запрос того же фильма (данные должны быть загружены из кеша Redis)
    start_time = time.monotonic()
    response = await make_get_request(
        url=f"{test_settings.service_url}{api_url.films_url}{test_film['uuid']}",
        query_data={},
    )
    second_duration = time.monotonic() - start_time

    # Проверка успешного статуса и корректности возвращаемых данных
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert response_json["uuid"] == test_film["uuid"]
    assert response_json["title"] == test_film["title"]

    # Проверка, что второй запрос выполняется быстрее за счет использования кеша
    assert second_duration < first_duration, (
        "Кеширование данных не работает: "
        "второй запрос выполняется дольше или так же долго, как первый."
    )
