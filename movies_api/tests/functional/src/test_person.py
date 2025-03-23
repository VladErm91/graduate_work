from http import HTTPStatus

import pytest
from functional.settings import api_url
from functional.settings import es_index as es
from functional.settings import test_settings
from functional.testdata import films_testdata as films
from functional.testdata import person_testdata as persons


@pytest.mark.parametrize(
    "endpoint, query_data, expected_answer",
    [
        (
            "persons/",
            {"query": "d8fc6948-6762-4a05-a87b-8c5eee203472"},
            {
                "status": HTTPStatus.OK,
                "length": 1,
                "expected_result": [
                    {
                        "uuid": "68e9a139-976d-4a83-ad1b-e374376814c9",
                        "title": "The Star",
                        "imdb_rating": 6.6,
                    }
                ],
            },
        ),
        (
            "persons/",
            {"query": "bad"},
            {
                "status": HTTPStatus.NOT_FOUND,
                "length": 1,
                "expected_result": {"detail": "Films not found"},
            },
        ),
        (
            "persons/",
            {"query": ""},
            {
                "status": HTTPStatus.NOT_FOUND,
                "length": 1,
                "expected_result": {"detail": "Not Found"},
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_film_details_by_person__films_present__return_details(
    make_get_request, query_data: dict, expected_answer: dict, endpoint, es_write_data
):
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
        ],
        es_index=es.es_index_films,
        es_index_mapping=es.es_movies_mapping,
    )
    await es_write_data(
        data=[
            {
                "_index": es.es_index_persons,
                "_id": persons.search_person_0["uuid"],
                "_source": persons.search_person_0,
            },
        ],
        es_index=es.es_index_persons,
        es_index_mapping=es.es_persons_mapping,
    )
    postfix = endpoint + query_data["query"] + "/film/"

    url = test_settings.service_url + api_url.api_v1_prefix + postfix

    response = await make_get_request(url=url, query_data={})
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]
    assert body == expected_answer["expected_result"]


@pytest.mark.parametrize(
    "endpoint, query_data, expected_answer",
    [
        (
            "persons/",
            {"query": "d8fc6948-6762-4a05-a87b-8c5eee203472"},
            {
                "status": HTTPStatus.OK,
                "length": 3,
                "expected_result": {
                    "uuid": "d8fc6948-6762-4a05-a87b-8c5eee203472",
                    "full_name": "John Farrell",
                    "films": [
                        {
                            "uuid": "68e9a139-976d-4a83-ad1b-e374376814c9",
                            "roles": ["actors"],
                        }
                    ],
                },
            },
        ),
        (
            "persons/",
            {"query": "bad"},
            {
                "status": HTTPStatus.NOT_FOUND,
                "length": 1,
                "expected_result": {"detail": "Person not found"},
            },
        ),
        (
            "persons/",
            {"query": ""},
            {
                "status": HTTPStatus.NOT_FOUND,
                "length": 1,
                "expected_result": {"detail": "Not Found"},
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_person_by_id__person_present__return_person(
    make_get_request, query_data: dict, expected_answer: dict, endpoint, es_write_data
):
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
        ],
        es_index=es.es_index_films,
        es_index_mapping=es.es_movies_mapping,
    )
    await es_write_data(
        data=[
            {
                "_index": es.es_index_persons,
                "_id": persons.search_person_0["uuid"],
                "_source": persons.search_person_0,
            },
        ],
        es_index=es.es_index_persons,
        es_index_mapping=es.es_persons_mapping,
    )
    postfix = endpoint + query_data["query"]

    url = test_settings.service_url + api_url.api_v1_prefix + postfix

    response = await make_get_request(url=url, query_data={})
    body = await response.json()
    status = response.status
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]
    assert body == expected_answer["expected_result"]
