from __future__ import annotations

import abc
import asyncio
import fcntl
import logging
from io import IOBase
from pathlib import Path
from typing import Any, Optional

from etcd_client import Client as EtcdClient
from etcd_client import Communicator as EtcdCommunicator
from etcd_client import EtcdLockOption
from etcetra.client import EtcdCommunicator as EtcetraCommunicator
from etcetra.client import EtcdConnectionManager as EtcetraConnectionManager
from redis.asyncio import Redis
from redis.asyncio.lock import Lock as AsyncRedisLock
from redis.exceptions import LockError, LockNotOwnedError
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
from ai.backend.common.etcd_etcetra import AsyncEtcd as EtcetraAsyncEtcd
from ai.backend.common.types import RedisConnectionInfo

from .logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


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
        self._file = open(self._path, "wb")
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
        if self._remove_when_unlock:
            try:
                self._path.unlink()
            except FileNotFoundError:
                pass
        self._file = None

    async def __aenter__(self) -> FileLock:
        await self.acquire()
        return self

    async def __aexit__(self, *exc_info) -> Optional[bool]:
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
    _etcd_client: Optional[EtcdClient]
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
        self._etcd_client = None

    async def __aenter__(self) -> EtcdCommunicator:
        self._etcd_client = self.etcd.etcd.with_lock(
            EtcdLockOption(
                lock_name=self.lock_name.encode("utf-8"),
                timeout=self._timeout,
                ttl=int(self._lifetime) if self._lifetime is not None else None,
            ),
        )

        etcd_communicator = await self._etcd_client.__aenter__()

        if self._debug:
            log.debug("etcd lock acquired")

        return etcd_communicator

    async def __aexit__(self, *exc_info) -> Optional[bool]:
        assert self._etcd_client is not None
        await self._etcd_client.__aexit__(*exc_info)

        if self._debug:
            log.debug("etcd lock released")

        self._etcd_client = None
        return None


class RedisLock(AbstractDistributedLock):
    debug: bool
    _redis: Redis
    _timeout: Optional[float]
    _lock: Optional[AsyncRedisLock]

    default_timeout = 9600
    default_lock_acquire_pause = 1.0

    def __init__(
        self,
        lock_name: str,
        redis: RedisConnectionInfo,
        *,
        timeout: Optional[float] = None,
        lifetime: Optional[float] = None,
        debug: bool = False,
        lock_acquire_pause: Optional[float] = None,
    ):
        super().__init__(lifetime=lifetime)
        self.lock_name = lock_name
        self._redis = redis.client
        self._timeout = timeout if timeout is not None else self.default_timeout
        self._debug = debug
        self._lock_acquire_pause = lock_acquire_pause or self.default_lock_acquire_pause

    async def __aenter__(self) -> None:
        self._lock = AsyncRedisLock(
            self._redis,
            self.lock_name,
            blocking_timeout=self._timeout,
            timeout=self._lifetime,
            thread_local=False,
            sleep=self._lock_acquire_pause,
        )
        try:
            await self._lock.__aenter__()
        except LockError as e:
            raise asyncio.TimeoutError(str(e))
        if self._debug:
            log.debug("RedisLock.__aenter__(): lock acquired")

    async def __aexit__(self, *exc_info) -> Optional[bool]:
        assert self._lock is not None
        try:
            val = await self._lock.__aexit__(*exc_info)  # type: ignore[func-returns-value]
        except LockNotOwnedError:
            log.exception("Lock no longer owned. Skip.")
            return True
        except LockError:
            log.exception("Already unlocked. Skip.")
            return True
        if self._debug:
            log.debug("RedisLock.__aexit__(): lock released")

        return val


class EtcetraLock(AbstractDistributedLock):
    _con_mgr: Optional[EtcetraConnectionManager]
    _debug: bool

    lock_name: str
    etcd: EtcetraAsyncEtcd
    timeout: float

    default_timeout: float = 9600  # not allow infinite timeout for safety

    def __init__(
        self,
        lock_name: str,
        etcd: EtcetraAsyncEtcd,
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

    async def __aenter__(self) -> EtcetraCommunicator:
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
