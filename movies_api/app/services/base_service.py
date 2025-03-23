from abc import ABC

from db.interfaces import AsyncCache, AsyncSearchEngine


class BaseService(ABC):
    def __init__(self, search_engine: AsyncSearchEngine, cache: AsyncCache):
        self.search_engine = search_engine
        self.cache = cache
