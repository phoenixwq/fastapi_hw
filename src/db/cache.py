from abc import ABC, abstractmethod
from typing import Optional, Union

__all__ = (
    "AbstractCache",
    "get_cache",
    "get_access_cash",
    "get_refresh_cash",
)

from src.core import config


class AbstractCache(ABC):
    def __init__(self, cache_instance):
        self.cache = cache_instance

    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def set(
            self,
            key: str,
            value: Union[bytes, str],
            expire: int = config.CACHE_EXPIRE_IN_SECONDS,
    ):
        pass

    @abstractmethod
    def close(self):
        pass


cache: Optional[AbstractCache] = None
blocked_access_tokens: Optional[AbstractCache] = None
active_refresh_tokens: Optional[AbstractCache] = None


def get_access_cash() -> AbstractCache:
    return blocked_access_tokens


def get_refresh_cash() -> AbstractCache:
    return active_refresh_tokens


# Функция понадобится при внедрении зависимостей
def get_cache() -> AbstractCache:
    return cache
