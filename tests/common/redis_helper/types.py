from __future__ import annotations

import contextlib
from abc import ABCMeta, abstractmethod
from typing import AsyncIterator, Sequence, Tuple

import attr


@attr.define
class RedisClusterInfo:
    node_addrs: Sequence[Tuple[str, int]]
    nodes: Sequence[AbstractRedisNode]
    sentinel_addrs: Sequence[Tuple[str, int]]
    sentinels: Sequence[AbstractRedisNode]


class AbstractRedisSentinelCluster(metaclass=ABCMeta):
    def __init__(
        self,
        test_ns: str,
        test_case_ns: str,
        password: str,
        service_name: str,
        *,
        verbose: bool = False,
    ) -> None:
        self.test_ns = test_ns
        self.test_case_ns = test_case_ns
        self.password = password
        self.service_name = service_name
        self.verbose = verbose

    @contextlib.asynccontextmanager
    @abstractmethod
    async def make_cluster(self) -> AsyncIterator[RedisClusterInfo]:
        raise NotImplementedError
        yield self


class AbstractRedisNode(metaclass=ABCMeta):
    @property
    @abstractmethod
    def addr(self) -> Tuple[str, int]:
        raise NotImplementedError

    @abstractmethod
    async def pause(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def unpause(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self, force_kill: bool = False) -> None:
        raise NotImplementedError

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError
