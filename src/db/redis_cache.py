from typing import NoReturn, Optional, Union

from src.core import config
from src.db import AbstractCache

__all__ = ("CacheRedis",)


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
