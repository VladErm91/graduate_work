import logging
from datetime import datetime
from functools import lru_cache
from http import HTTPStatus
from pprint import pformat
from typing import Optional

from core.config import settings
from db.elastic import get_search_engine
from db.interfaces import AsyncCache, AsyncSearchEngine
from db.redis import get_cache_service
from elasticsearch import NotFoundError
from fastapi import Depends, HTTPException
from models.film import Film, FilmDetailed
from models.genre import Genre
from pydantic import TypeAdapter
from services.base_service import BaseService

FILM_ADAPTER = TypeAdapter(list[Film])


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class FilmService(BaseService):
    """Сервис для получения детальной информации по фильму из ES."""

    # 1.1. получение фильма по id
    # get_by_uuid возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_uuid(self, film_uuid: str) -> Optional[FilmDetailed]:
        """Получить детальную информацию о фильме по его id.

        Parameters:
            film_uuid: uuid фильма

        Returns:
            детальная информация о фильме
        """
        # Получаем данные из кеша
        film = await self._get_film_from_cache(film_uuid)
        if not film:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            film = await self._get_film_from_elastic(film_uuid)
            if not film:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм в кеш
            await self._put_film_to_cache(film)

        return film

    # 2.1. получение фильма из ES по id
    async def _get_film_from_elastic(self, film_id: str) -> Optional[FilmDetailed]:
        try:
            doc = await self.search_engine.get(index="movies", id=film_id)
        except NotFoundError:
            return None
        source = doc["_source"]
        logger.debug(pformat(doc["_source"]))
        genres = source.get("genre", [])
        genre_objs = [Genre(**genre) for genre in genres]
        film_data = {
            "uuid": source.get("uuid"),
            "title": source.get("title"),
            "description": source.get("description"),
            "imdb_rating": source.get("imdb_rating"),
            "genre": genre_objs,
            "directors": source.get("directors", []),
            "actors": source.get("actors", []),
            "writers": source.get("writers", []),
            "file": source.get("file", []),
        }
        return FilmDetailed(**film_data)

    # 3.1. получение фильма из кэша по id
    async def _get_film_from_cache(self, film_uuid: str) -> Optional[FilmDetailed]:
        params_to_key = {
            "uuid": film_uuid,
        }
        cache_key = self.cache.generate_cache_key("movies", params_to_key)

        film_data = await self.cache.get(cache_key)
        if not film_data:
            return None

        logging.info("Взято из кэша по ключу: {0}".format(cache_key))
        # pydantic предоставляет удобное API для создания объекта моделей из json
        return FilmDetailed.model_validate_json(film_data)  # возвращаем

    # десериализованный объект Film

    # 4.1. сохранение фильма в кэш по id:
    async def _put_film_to_cache(self, film: Film):
        # подготовка к генерации ключа
        params_to_key = {
            "uuid": film.uuid,
        }
        cache_key = self.cache.generate_cache_key("movies", params_to_key)

        await self.cache.set(
            cache_key,
            film.model_dump_json(),
            settings.cache_time_life,
        )


class MultipleFilmsService(BaseService):
    """Сервис для получения информации о нескольких фильмов из elastic."""

    async def get_by_uuid(self, uuid: str):
        response = await self.search_engine.get(index="movies", id=uuid)
        if not response["found"]:
            return None
        return response["_source"]

    # 1.2. получение страницы списка фильмов отсортированных по популярности
    async def get_multiple_films(
        self,
        desc_order: bool,
        page_size: int,
        page_number: int,
        genre: Optional[str] = None,
        similar: Optional[str] = None,
        release_date_cutoff: Optional[datetime] = None,
    ) -> Optional[list[Film]]:
        """Получение нескольких фильмов"""
        # ключ для кэша задается в формате ключ::значение::ключ::значение и т.д.
        params_to_key = {
            "desc": str(int(desc_order)),
            "page_size": str(page_size),
            "page_number": str(page_number),
            "genre": genre,
            "similar": similar,
        }
        # создаём ключ для кэша
        cache_key = self.cache.generate_cache_key("movies", params_to_key)

        # запрашиваем инфо в кэше по ключу
        films_page = await self._get_multiple_films_from_cache(cache_key)
        if not films_page:
            # если в кэше нет значения по этому ключу, делаем запрос в ES
            films_page = await self._get_multiple_films_from_elastic(
                desc_order=desc_order,
                page_size=page_size,
                page_number=page_number,
                genre=genre,
                similar=similar,
                release_date_cutoff=release_date_cutoff,
            )
            # Кэшируем результат (пустой результат тоже)
            await self._put_multiple_films_to_cache(
                cache_key=cache_key,
                films=films_page,
            )

            if not films_page:
                return None

        return films_page

    async def search_films(
        self,
        query: str,
        page_number: int,
        page_size: int,
    ) -> list[Film]:
        """Полнотекстовый поиск фильмов."""
        # ключ для кэша задается в формате ключ::значение::ключ::значение и т.д.
        params_to_key = {
            "query": query,
            "page_size": str(page_size),
            "page_number": str(page_number),
        }

        # создаём ключ для кэша
        cache_key = self.cache.generate_cache_key("movies", params_to_key)

        # запрашиваем инфо в кэше
        films_page = await self._get_multiple_films_from_cache(cache_key)
        if not films_page:
            films_page = await self._fulltext_search_films_in_elastic(
                query=query,
                page_number=page_number,
                page_size=page_size,
            )

        # Сохраняем поиск по фильму в кеш (даже если поиск не дал результата)
        await self._put_multiple_films_to_cache(cache_key, films_page)

        return films_page

    async def _get_multiple_films_from_elastic(
        self,
        similar: Optional[str] = None,
        genre: Optional[str] = None,
        desc_order: bool = True,
        page_size: int = 50,
        page_number: int = 1,
        release_date_cutoff: Optional[datetime] = None,
    ):
        query = {
            "size": page_size,
            "from": (page_number - 1) * page_size,
            "sort": [{"imdb_rating": {"order": "desc" if desc_order else "asc"}}],
            "query": {"bool": {"must": [], "filter": []}},
        }

        # Фильтр по дате релиза для неавторизованных пользователей
        if release_date_cutoff:
            query["query"]["bool"]["filter"].append(
                {
                    "range": {
                        "creation_date": {
                            "lte": release_date_cutoff.strftime("%Y-%m-%d")
                        }
                    }
                }
            )

        if similar:
            logging.info("similar: %s", similar)

            similar_film = await self.get_by_uuid(similar)
            logging.info("similar film retrieved: %s", similar_film)
            if similar_film and similar_film.get("genre"):
                first_genre_uuid = similar_film["genre"][0]["uuid"]
                logging.info("first_genre_uuid: %s", first_genre_uuid)
                query["query"]["bool"]["filter"].append(
                    {
                        "nested": {
                            "path": "genre",
                            "query": {"term": {"genre.uuid": first_genre_uuid}},
                        }
                    }
                )
                logging.info("query: %s", query)
            else:
                logging.warning("No genre found for film with id: %s", similar)

        if genre:
            query["query"]["bool"]["filter"].append(
                {"nested": {"path": "genre", "query": {"term": {"genre.uuid": genre}}}}
            )
            logging.info("genre: %s", genre)
        logging.info(f"Query to Elasticsearch: {pformat(query)}")
        try:
            similar_response = await self.search_engine.search(
                index="movies", body=query
            )
            logging.debug(f"Response from Elasticsearch: {pformat(similar_response)}")
        except Exception as e:
            logging.error(f"Error while querying Elasticsearch: {str(e)}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
            )

        if not similar_response["hits"]["hits"]:
            return []

        films_page = [
            Film(**hit["_source"]) for hit in similar_response["hits"]["hits"]
        ]
        return films_page

    # 2.3 Полнотекстовый поиск по фильмам:
    async def _fulltext_search_films_in_elastic(
        self,
        query: str,
        page_number: int,
        page_size: int,
    ):
        search_results = await self.search_engine.search(
            index="movies",
            body={
                "query": {"match": {"title": query}},
                "from": (page_number - 1) * page_size,
                "size": page_size,
            },
        )
        logging.debug(search_results)
        return [Film(**hit["_source"]) for hit in search_results["hits"]["hits"]]

    # 3.2. получение страницы списка фильмов отсортированных по популярности из кэша
    async def _get_multiple_films_from_cache(self, cache_key: str):
        films_data = await self.cache.get(cache_key)
        if not films_data:
            logging.info("Не найдено в кэш")
            return None

        logging.info("Взято из кэша по ключу: {0}".format(cache_key))
        return FILM_ADAPTER.validate_json(films_data)

    # 4.2. сохранение страницы фильмов (отсортированных по популярности) в кэш:
    async def _put_multiple_films_to_cache(self, cache_key: str, films):
        await self.cache.set(
            cache_key,
            FILM_ADAPTER.dump_json(films),
            settings.cache_time_life,
        )


@lru_cache()
def get_film_service(
    cache: AsyncCache = Depends(get_cache_service),
    elastic: AsyncSearchEngine = Depends(get_search_engine),
) -> FilmService:
    print(f"Cache: {cache}, Elastic: {elastic}")
    return FilmService(cache=cache, search_engine=elastic)


@lru_cache()
def get_multiple_films_service(
    cache: AsyncCache = Depends(get_cache_service),
    elastic: AsyncSearchEngine = Depends(get_search_engine),
) -> MultipleFilmsService:
    print(f"Cache: {cache}, Elastic: {elastic}")
    return MultipleFilmsService(cache=cache, search_engine=elastic)
