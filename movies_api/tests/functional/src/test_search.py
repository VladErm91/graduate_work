from http import HTTPStatus

import pytest
from functional.settings import api_url
from functional.settings import es_index as es
from functional.settings import test_settings
from functional.testdata import films_testdata as films
from functional.testdata import person_testdata as person

#  Название теста должно начинаться со слова `test_`
#  Любой тест с асинхронными вызовами нужно оборачивать декоратором `pytest.mark.asyncio`, который следит за запуском и работой цикла событий.


@pytest.mark.asyncio
async def test_load_testing_data(es_write_data):
    await es_write_data(
        data=[
            {
                "_index": es.es_index_films,
                "_id": films.search_film_0["uuid"],
                "_source": films.search_film_0,
            },
            {
                "_index": es.es_index_films,
                "_id": films.search_film_1["uuid"],
                "_source": films.search_film_1,
            },
            {
                "_index": es.es_index_films,
                "_id": films.search_film_2["uuid"],
                "_source": films.search_film_2,
            },
            {
                "_index": es.es_index_films,
                "_id": films.search_film_3["uuid"],
                "_source": films.search_film_3,
            },
            {
                "_index": es.es_index_films,
                "_id": films.search_film_4["uuid"],
                "_source": films.search_film_4,
            },
        ],
        es_index=es.es_index_films,
        es_index_mapping=es.es_movies_mapping,
    )
    await es_write_data(
        data=[
            {
                "_index": es.es_index_persons,
                "_id": person.search_person_0["uuid"],
                "_source": person.search_person_0,
            },
            {
                "_index": es.es_index_persons,
                "_id": person.search_person_1["uuid"],
                "_source": person.search_person_1,
            },
            {
                "_index": es.es_index_persons,
                "_id": person.search_person_2["uuid"],
                "_source": person.search_person_2,
            },
            {
                "_index": es.es_index_persons,
                "_id": person.search_person_3["uuid"],
                "_source": person.search_person_3,
            },
        ],
        es_index=es.es_index_persons,
        es_index_mapping=es.es_persons_mapping,
    )


@pytest.mark.parametrize(
    "endpoint, query_data, expected_answer",
    [
        # Эндпоинты фильмов
        (
            "films/",
            {"query": "Star", "page_size": 1},
            {"status": HTTPStatus.OK, "length": 1},
        ),
        (
            "films/",
            {"query": "Mashed potato", "page_size": 1},
            {"status": HTTPStatus.OK, "length": 1},
        ),
        # Эндпоинты персоналий
        (
            "persons/",
            {"query": "John", "page_size": 1},
            {"status": HTTPStatus.OK, "length": 1},
        ),
    ],
)
@pytest.mark.asyncio
async def test_search(
    make_get_request, query_data: dict, expected_answer: dict, endpoint
):

    postfix = endpoint + "search"

    url = test_settings.service_url + api_url.api_v1_prefix + postfix

    response = await make_get_request(url=url, query_data=query_data)
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]


@pytest.mark.parametrize(
    "endpoint, query_data, expected_answer",
    [
        # Эндпоинты фильмов
        ("films/", {"query": "Unknown"}, {"status": HTTPStatus.OK, "length": 0}),
        # Эндпоинты персоналий
        ("persons/", {"query": ""}, {"status": HTTPStatus.NOT_FOUND, "length": 1}),
        (
            "persons/",
            {"query": "Unknown"},
            {"status": HTTPStatus.NOT_FOUND, "length": 1},
        ),
    ],
)
@pytest.mark.asyncio
async def test_failed_search(
    make_get_request, query_data: dict, expected_answer: dict, endpoint
):

    postfix = endpoint + "search"

    url = test_settings.service_url + api_url.api_v1_prefix + postfix

    response = await make_get_request(url=url, query_data=query_data)
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]


@pytest.mark.parametrize(
    "endpoint, query_data, expected_answer",
    [
        (
            "films/",
            {"query": "Mashed potato", "page_size": "4a"},
            {"status": HTTPStatus.UNPROCESSABLE_ENTITY},
        ),
        (
            "persons/",
            {"query": "John", "page_size": "5f"},
            {"status": HTTPStatus.UNPROCESSABLE_ENTITY},
        ),
    ],
)
@pytest.mark.asyncio
async def test_search_invalid_params(
    make_get_request, query_data: dict, expected_answer: dict, endpoint
):
    postfix = endpoint + "search"

    url = test_settings.service_url + api_url.api_v1_prefix + postfix

    response = await make_get_request(url=url, query_data=query_data)
    status = response.status
    assert status == expected_answer["status"]


@pytest.mark.parametrize(
    "endpoint, query_data, expected_answer",
    [
        (
            "films/",
            {"query": "Star", "page_size": 1},
            {
                "status": HTTPStatus.OK,
                "items": [
                    {
                        "uuid": "68e9a139-976d-4a83-ad1b-e374376814c9",
                        "title": "The Star",
                        "imdb_rating": 6.6,
                    },
                ],
            },
        ),
        (
            "persons/",
            {"query": "John Farrell", "page_size": 1},
            {
                "status": HTTPStatus.OK,
                "items": [
                    {
                        "uuid": "d8fc6948-6762-4a05-a87b-8c5eee203472",
                        "full_name": "John Farrell",
                        "films": [
                            {
                                "uuid": "68e9a139-976d-4a83-ad1b-e374376814c9",
                                "roles": ["actors"],
                            }
                        ],
                    },
                ],
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_search_contents(
    make_get_request, query_data: dict, expected_answer: dict, endpoint
):
    postfix = endpoint + "search"
    url = test_settings.service_url + api_url.api_v1_prefix + postfix

    response = await make_get_request(url=url, query_data=query_data)
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert body == expected_answer["items"]


@pytest.mark.parametrize(
    "endpoint, query_data, expected_answer",
    [
        (
            "films/",
            {"query": "Test", "page_size": 1},
            {"status": HTTPStatus.OK, "length": 1},
        )
    ],
)
@pytest.mark.asyncio
async def test_search_film_pagination(
    make_get_request, query_data: dict, expected_answer: dict, endpoint, es_write_data
):

    postfix = endpoint + "search"

    url = test_settings.service_url + api_url.api_v1_prefix + postfix

    response = await make_get_request(url=url, query_data=query_data)
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]
    assert body[0]["uuid"] == films.search_film_3["uuid"]
    response = await make_get_request(
        url=url, query_data={"query": "Test", "page_size": 1, "page_number": 2}
    )
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]
    assert body[0]["uuid"] == films.search_film_4["uuid"]


@pytest.mark.parametrize(
    "endpoint, query_data, expected_answer",
    [
        (
            "persons/",
            {"query": "Ivan", "page_size": 1},
            {"status": HTTPStatus.OK, "length": 1},
        )
    ],
)
@pytest.mark.asyncio
async def test_search_person_pagination(
    make_get_request, query_data: dict, expected_answer: dict, endpoint, es_write_data
):
    postfix = endpoint + "search"

    url = test_settings.service_url + api_url.api_v1_prefix + postfix

    response = await make_get_request(url=url, query_data=query_data)
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]
    assert body[0]["uuid"] == person.search_person_2["uuid"]
    response = await make_get_request(
        url=url, query_data={"query": "Ivan", "page_size": 1, "page_number": 2}
    )
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]
    assert body[0]["uuid"] == person.search_person_3["uuid"]


@pytest.mark.parametrize(
    "endpoint, query_data, expected_answer",
    [
        # Эндпоинты фильмов
        (
            "films/",
            {"query": "Smashed potato", "page_size": 1},
            {"status": HTTPStatus.OK, "length": 1},
        ),
    ],
)
@pytest.mark.asyncio
async def test_search_films_redis_caching(
    make_get_request, query_data: dict, expected_answer: dict, endpoint, es_write_data
):

    postfix = endpoint + "search"

    url = test_settings.service_url + api_url.api_v1_prefix + postfix

    response = await make_get_request(url=url, query_data=query_data)
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]

    await es_write_data(
        data=[],
        es_index=es.es_index_films,
        es_index_mapping=es.es_movies_mapping,
    )

    response = await make_get_request(url=url, query_data=query_data)
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]


@pytest.mark.parametrize(
    "endpoint, query_data, expected_answer",
    [
        # Эндпоинты фильмов
        ("persons/", {"query": "Pierce"}, {"status": HTTPStatus.OK, "length": 1}),
    ],
)
@pytest.mark.asyncio
async def test_search_person_redis_caching(
    make_get_request, query_data: dict, expected_answer: dict, endpoint, es_write_data
):

    postfix = endpoint + "search"

    url = test_settings.service_url + api_url.api_v1_prefix + postfix

    response = await make_get_request(url=url, query_data=query_data)
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]

    await es_write_data(
        data=[],
        es_index=es.es_index_films,
        es_index_mapping=es.es_movies_mapping,
    )

    response = await make_get_request(url=url, query_data=query_data)
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]
