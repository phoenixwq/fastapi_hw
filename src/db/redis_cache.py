from typing import NoReturn, Optional, Union

from src.core import config
from src.db import AbstractCache

__all__ = ("CacheRedis", "CacheToken")


class CacheRedis(AbstractCache):
    def get(self, key: str) -> Optional[dict]:
        return self.cache.get(name=key)

    def set(
            self,
            key: str,
            value: Union[bytes, str],
            expire: int = config.CACHE_EXPIRE_IN_SECONDS,
    ):
        self.cache.set(name=key, value=value, ex=expire)

    def close(self) -> NoReturn:
        self.cache.close()


class CacheToken(CacheRedis):

    def get(self, key: str) -> Optional[list]:
        list_len = self.cache.llen(key)
        return self.cache.lrange(key, 0, list_len)

    def close(self) -> NoReturn:
        self.cache.close()

    def add(self, key, *values):
        self.cache.lpush(key, *values)

    def clean(self, key):
        list_len = self.cache.llen(key)
        for i in range(list_len):
            self.cache.lpop(key)
