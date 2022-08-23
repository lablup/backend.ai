from __future__ import annotations

import abc
import asyncio
import fcntl
import logging
from io import IOBase
from pathlib import Path
from typing import Any, Optional

from etcetra.client import EtcdCommunicator, EtcdConnectionManager
from redis.asyncio import Redis
from redis.asyncio.lock import Lock as AsyncRedisLock
from redis.asyncio.sentinel import SentinelConnectionPool
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_delay,
    stop_never,
    wait_exponential,
    wait_random,
)

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.redis_helper import _default_conn_opts
from ai.backend.common.types import RedisConnectionInfo

from .logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))


class AbstractDistributedLock(metaclass=abc.ABCMeta):
    def __init__(self, *, lifetime: Optional[float] = None) -> None:
        assert lifetime is None or lifetime >= 0.0
        self._lifetime = lifetime

    @abc.abstractmethod
    async def __aenter__(self) -> Any:
        raise NotImplementedError

    @abc.abstractmethod
    async def __aexit__(self, *exc_info) -> Optional[bool]:
        raise NotImplementedError


class FileLock(AbstractDistributedLock):

    default_timeout: float = 3  # not allow infinite timeout for safety

    _file: IOBase | None
    _locked: bool = False

    def __init__(
        self,
        path: Path,
        *,
        timeout: Optional[float] = None,
        lifetime: Optional[float] = None,
        remove_when_unlock: bool = False,
        debug: bool = False,
    ) -> None:
        super().__init__(lifetime=lifetime)
        self._file = None
        self._path = path
        self._timeout = timeout if timeout is not None else self.default_timeout
        self._debug = debug
        self._remove_when_unlock = remove_when_unlock
        self._watchdog_task: Optional[asyncio.Task[Any]] = None

    @property
    def locked(self) -> bool:
        return self._locked

    def __del__(self) -> None:
        if self._file is not None:
            self._debug = False
            self.release()
            log.debug("file lock implicitly released: {}", self._path)

    async def acquire(self) -> None:
        assert self._file is None
        assert not self._locked
        if not self._path.exists():
            self._path.touch()
        self._file = open(self._path, "rb")
        stop_func = stop_never if self._timeout <= 0 else stop_after_delay(self._timeout)
        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(BlockingIOError),
                wait=wait_exponential(multiplier=0.02, min=0.02, max=1.0) + wait_random(0, 0.05),
                stop=stop_func,
            ):
                with attempt:
                    fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._locked = True
                    if self._lifetime is not None:
                        self._watchdog_task = asyncio.create_task(
                            self._watchdog_timer(ttl=self._lifetime),
                        )
                    if self._debug:
                        log.debug("file lock acquired: {}", self._path)
        except RetryError:
            raise asyncio.TimeoutError(f"failed to lock file: {self._path}")

    def release(self) -> None:
        assert self._file is not None
        if task := self._watchdog_task:
            if not task.done():
                task.cancel()
        if self._locked:
            fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
            self._locked = False
            if self._debug:
                log.debug("file lock explicitly released: {}", self._path)
        self._file.close()
        if self._locked and self._remove_when_unlock:
            self._path.unlink()
        self._file = None

    async def __aenter__(self) -> FileLock:
        await self.acquire()
        return self

    async def __aexit__(self, *exc_info) -> bool | None:
        self.release()
        return None

    async def _watchdog_timer(self, ttl: float):
        await asyncio.sleep(ttl)
        if self._locked:
            assert self._file is not None
            fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
            self._locked = False
            if self._debug:
                log.debug(f"file lock implicitly released by watchdog: {self._path}")

    @property
    def is_locked(self) -> bool:
        return self._locked


class EtcdLock(AbstractDistributedLock):

    _con_mgr: Optional[EtcdConnectionManager]
    _debug: bool

    lock_name: str
    etcd: AsyncEtcd
    timeout: float

    default_timeout: float = 9600  # not allow infinite timeout for safety

    def __init__(
        self,
        lock_name: str,
        etcd: AsyncEtcd,
        *,
        timeout: Optional[float] = None,
        lifetime: Optional[float] = None,
        debug: bool = False,
    ) -> None:
        super().__init__(lifetime=lifetime)
        self.lock_name = lock_name
        self.etcd = etcd
        self._timeout = timeout if timeout is not None else self.default_timeout
        self._debug = debug

    async def __aenter__(self) -> EtcdCommunicator:
        self._con_mgr = self.etcd.etcd.with_lock(
            self.lock_name,
            timeout=self._timeout,
            ttl=int(self._lifetime) if self._lifetime is not None else None,
        )
        assert (
            self._con_mgr is not None
        )  # FIXME: not required if with_lock() has an explicit return type.
        communicator = await self._con_mgr.__aenter__()
        if self._debug:
            log.debug("etcd lock acquired")
        return communicator

    async def __aexit__(self, *exc_info) -> Optional[bool]:
        assert self._con_mgr is not None
        await self._con_mgr.__aexit__(*exc_info)
        if self._debug:
            log.debug("etcd lock released")
        self._con_mgr = None
        return None


class RedisLock(AbstractDistributedLock):

    debug: bool
    _redis: Redis
    _timeout: Optional[float]
    _lock: Optional[AsyncRedisLock]

    default_timeout = 9600

    def __init__(
        self,
        lock_name: str,
        redis: RedisConnectionInfo,
        *,
        timeout: Optional[float] = None,
        lifetime: Optional[float] = None,
        socket_connect_timeout: float = 0.3,
        debug: bool = False,
    ):
        super().__init__(lifetime=lifetime)
        self.lock_name = lock_name
        if isinstance(redis.client, Redis):
            self._redis = redis.client
        else:
            assert redis.service_name is not None
            _conn_opts = {
                **_default_conn_opts,
                "socket_connect_timeout": socket_connect_timeout,
            }
            self._redis = redis.client.master_for(
                redis.service_name,
                redis_class=Redis,
                connection_pool_class=SentinelConnectionPool,
                **_conn_opts,
            )
        self._timeout = timeout if timeout is not None else self.default_timeout
        self._debug = debug

    async def __aenter__(self) -> None:
        self._lock = AsyncRedisLock(
            self._redis,
            self.lock_name,
            blocking_timeout=self._timeout,
            timeout=self._lifetime,
            thread_local=False,
        )
        await self._lock.acquire()
        if self._debug:
            log.debug("RedisLock.__aenter__(): lock acquired")

    async def __aexit__(self, *exc_info) -> Optional[bool]:
        assert self._lock is not None
        await self._lock.release()
        if self._debug:
            log.debug("RedisLock.__aexit__(): lock released")

        return None
