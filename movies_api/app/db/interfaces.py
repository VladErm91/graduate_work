from abc import ABC, abstractmethod
from typing import Optional


class AsyncSearchEngine(ABC):
    @abstractmethod
    async def get(self, key: str, **kwargs):
        pass

    @abstractmethod
    async def set(self, key: str, value: str, expire: int, **kwargs):
        pass


class AsyncCache(ABC):
    @abstractmethod
    async def get(self, **kwargs) -> Optional[str]:
        pass

    @abstractmethod
    async def set(self, **kwargs) -> None:
        pass

    @abstractmethod
    async def generate_cache_key(self, **kwargs):
        pass

    @abstractmethod
    async def close(self):
        raise NotImplementedError
