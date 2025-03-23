import asyncio

import aiohttp
import pytest
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from functional.settings import test_settings


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name="es_client", scope="session")
async def es_client():
    es_client = AsyncElasticsearch(hosts=test_settings.es_dsl, verify_certs=False)
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture(name="es_write_data")
def es_write_data(es_client):
    async def inner(data: list[dict], es_index, es_index_mapping):
        if await es_client.indices.exists(index=es_index):
            await es_client.indices.delete(index=es_index)
        await es_client.indices.create(index=es_index, **es_index_mapping)
        updated, errors = await async_bulk(client=es_client, actions=data)

        if errors:
            raise Exception("Ошибка записи данных в Elasticsearch")

    return inner


@pytest_asyncio.fixture()
async def session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture()
def make_get_request(session):
    async def inner(url, query_data={}):
        response = await session.get(url, params=query_data)
        return response

    return inner
