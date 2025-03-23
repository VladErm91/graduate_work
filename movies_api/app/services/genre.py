import json
from functools import lru_cache
from typing import List, Optional, Tuple

from db.elastic import get_search_engine
from db.interfaces import AsyncCache, AsyncSearchEngine
from db.redis import get_cache_service
from elasticsearch import NotFoundError
from fastapi import Depends, HTTPException
from models.genre import Genre
from services.base_service import BaseService


class GenreService(BaseService):
    """Сервис для получения информации о жанре/жанрах из ES."""

    async def get_by_uuid(self, genre_id: str) -> Optional[Genre]:

        params_to_key = {
            "uuid": genre_id,
        }
        cache_key = self.cache.generate_cache_key(
            index="genres", params_to_key=params_to_key
        )

        cached_genre = await self.cache.get(key=cache_key)
        if cached_genre:
            return Genre(**json.loads(cached_genre))

        try:
            doc = await self.search_engine.get(index="genres", id=genre_id)
        except NotFoundError:
            return None
        genre = Genre(**doc["_source"])
        await self.cache.set(
            cache_key, genre.model_dump_json(), ex=300
        )  # Кеш на 5 минут
        return genre

    async def search(
        self,
        query: str,
        order: str,
        page_number: int,
        page_size: int,
    ) -> Tuple[List[Genre], int]:
        params_to_key = {
            "query": query,
            "order": order,
            "page_number": str(page_number),
            "page_size": str(page_size),
        }

        cache_key = self.cache.generate_cache_key(
            index="genres", params_to_key=params_to_key
        )

        cached_genres = await self.cache.get(key=cache_key)
        if cached_genres:
            data = json.loads(cached_genres)
            return [Genre.model_validate_json(genre) for genre in data["items"]], data[
                "total"
            ]

        body = {}
        if query:
            body["query"] = {
                "bool": {
                    "should": [
                        {"prefix": {"name": query.lower()}},
                        {"wildcard": {"name": f"{query.lower()}*"}},
                    ]
                }
            }
        else:
            body["query"] = {"match_all": {}}

        if order:
            body["sort"] = [{"name.raw": {"order": order}}]

        body["from"] = (page_number - 1) * page_size
        body["size"] = page_size

        result = await self.search_engine.search(index="genres", body=body)
        genres = [Genre(**hit["_source"]) for hit in result["hits"]["hits"]]
        total = result["hits"]["total"]["value"]

        if (page_number - 1) * page_size >= total:
            raise HTTPException(status_code=404, detail="Page not found")

        await self.cache.set(
            cache_key,
            json.dumps(
                {"items": [genre.model_dump_json() for genre in genres], "total": total}
            ),
            ex=300,
        )  # Кеш на 5 минут
        return genres, total


@lru_cache()
def get_genre_service(
    cache: AsyncCache = Depends(get_cache_service),
    elastic: AsyncSearchEngine = Depends(get_search_engine),
) -> GenreService:
    return GenreService(cache=cache, search_engine=elastic)
