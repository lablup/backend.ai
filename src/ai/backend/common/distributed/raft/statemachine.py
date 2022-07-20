import abc
from typing import Optional

import redis
from redis.asyncio import Redis

from ...types import aobject


class AbstractStateMachine(abc.ABC):
    @abc.abstractmethod
    async def apply(self, command: str) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        raise NotImplementedError()


class RedisStateMachine(aobject, AbstractStateMachine):
    def __init__(self, *args, **kwargs) -> None:
        self._redis = Redis.from_url("redis://127.0.0.1:8111")

    async def apply(self, command: str) -> None:
        try:
            await self._redis.execute_command(command)
        except redis.exceptions.ResponseError:
            pass

    async def get(self, key: str) -> Optional[bytes]:
        return await self._redis.get(key)

    """
    async def get(self, key: str) -> Optional[Union[bytes, float, int, str]]:
        if value := await self._redis.get(key):
            for dtype in (int, float, str):
                try:
                    return dtype(value)
                except ValueError:
                    pass
        return value
    """
