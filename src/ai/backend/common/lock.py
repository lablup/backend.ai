from __future__ import annotations

import abc
import asyncio
import fcntl
import logging
from io import IOBase
from pathlib import Path
from typing import Any, Optional

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_delay,
    stop_never,
    wait_exponential,
    wait_random,
)

from etcetra.client import EtcdConnectionManager, EtcdCommunicator

from ai.backend.common.etcd import AsyncEtcd

from .logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))


class AbstractDistributedLock(metaclass=abc.ABCMeta):

    def __init__(self, *, lifetime: Optional[float] = None) -> None:
        self._lifetime = lifetime

    @abc.abstractmethod
    async def __aenter__(self) -> Any:
        raise NotImplementedError

    @abc.abstractmethod
    async def __aexit__(self, *exc_info) -> Optional[bool]:
        raise NotImplementedError


class FileLock(AbstractDistributedLock):

    default_timeout: float = 3  # not allow infinite timeout for safety

    _fp: IOBase | None
    _locked: bool = False

    def __init__(
        self,
        path: Path,
        *,
        timeout: Optional[float] = None,
        lifetime: Optional[float] = None,
        debug: bool = False,
    ) -> None:
        super().__init__(lifetime=lifetime)
        self._fp = None
        self._path = path
        self._timeout = timeout if timeout is not None else self.default_timeout
        self._debug = debug

    @property
    def locked(self) -> bool:
        return self._locked

    def __del__(self) -> None:
        if self._fp is not None:
            self._debug = False
            self.release()
            log.debug("file lock implicitly released: {}", self._path)

    async def acquire(self) -> None:
        assert self._fp is None
        assert not self._locked
        self._path.touch(exist_ok=True)
        self._fp = open(self._path, "rb")
        stop_func = stop_never if self._timeout <= 0 else stop_after_delay(self._timeout)
        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(BlockingIOError),
                wait=wait_exponential(multiplier=0.02, min=0.02, max=1.0) + wait_random(0, 0.05),
                stop=stop_func,
            ):
                with attempt:
                    fcntl.flock(self._fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._locked = True
                    if self._debug:
                        log.debug("file lock acquired: {}", self._path)
        except RetryError:
            raise asyncio.TimeoutError(f"failed to lock file: {self._path}")

    def release(self) -> None:
        assert self._fp is not None
        if self._locked:
            fcntl.flock(self._fp, fcntl.LOCK_UN)
            self._locked = False
            if self._debug:
                log.debug("file lock explicitly released: {}", self._path)
        self._fp.close()
        self._fp = None

    async def __aenter__(self) -> None:
        await self.acquire()

    async def __aexit__(self, *exc_info) -> bool | None:
        self.release()
        return None


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
        assert self._con_mgr is not None  # FIXME: not required if with_lock() has an explicit return type.
        communicator = await self._con_mgr.__aenter__()
        if self._debug:
            log.debug('etcd lock acquired')
        return communicator

    async def __aexit__(self, *exc_info) -> Optional[bool]:
        assert self._con_mgr is not None
        await self._con_mgr.__aexit__(*exc_info)
        if self._debug:
            log.debug('etcd lock released')
        self._con_mgr = None
        return None
