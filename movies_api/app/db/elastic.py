from typing import Optional

from elasticsearch import AsyncElasticsearch

es: Optional[AsyncElasticsearch] = None


async def get_search_engine() -> AsyncElasticsearch | None:
    return es
