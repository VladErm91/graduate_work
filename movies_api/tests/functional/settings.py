from typing import Any

from functional.testdata import es_mapping
from pydantic import Field
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    service_url: str = Field("http://127.0.0.1:8000", alias="SERVICE_URL")
    # Elastic settings
    es_dsl: str = Field("http://127.0.0.1:9200", alias="ELASTIC_DSL")
    es_id_field: str = Field("id")
    # Redis settings
    redis_host: str = Field("redis", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")


test_settings = TestSettings()


class ES_INDEX(BaseSettings):
    # Indexes_settings
    es_index_films: str = "movies"
    es_index_genres: str = "genres"
    es_index_persons: str = "persons"
    # Mapping_settings
    es_movies_mapping: dict[str, Any] = Field(es_mapping.MOVIES_MAPPING)
    es_genres_mapping: dict[str, Any] = Field(es_mapping.GENRES_MAPPING)
    es_persons_mapping: dict[str, Any] = Field(es_mapping.PERSONS_MAPPING)


es_index = ES_INDEX()


class API_URLS(BaseSettings):
    # Url settings
    films_postfix: str = "films/"
    genres_postfix: str = "genres/"
    persons_postfix: str = "persons/"

    api_v1_prefix: str = "/api/v1/"

    films_url: str = api_v1_prefix + films_postfix
    genres_url: str = api_v1_prefix + genres_postfix
    persons_url: str = api_v1_prefix + persons_postfix


api_url = API_URLS()
