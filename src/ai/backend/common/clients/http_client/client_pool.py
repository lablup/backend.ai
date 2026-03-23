from __future__ import annotations

import abc
import asyncio
import inspect
import logging
import time
import warnings
from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Any, Protocol

import aiohttp
from aiotools import cancel_and_wait

from ai.backend.common.sync import SyncWorkerThread
from ai.backend.common.types import Sentinel
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ClientSessionFactory(Protocol):
    def __call__(self, key: ClientKey, /) -> aiohttp.ClientSession: ...


def tcp_client_session_factory(
    key: ClientKey,
    /,
    ssl: bool = True,
    limit: int = 100,
    limit_per_host: int = 0,
    timeout: aiohttp.ClientTimeout | None = None,
    **kwargs: Any,
) -> aiohttp.ClientSession:
    """
    The default TCP-based ClientSession factory.
    It creates ClientSession instances with base_url set from the endpoint of
    client keys, so all HTTP requests must use relative URL paths.

    All custom keyword arguments are passed to the ClientSession constructor,
    while ssl, limit, limit_per_host are passed to the TCPConnector constructor.
    """
    connector = aiohttp.TCPConnector(
        ssl=ssl,
        limit=limit,
        limit_per_host=limit_per_host,
    )
    return aiohttp.ClientSession(
        connector=connector,
        base_url=key.endpoint,
        timeout=timeout,
        **kwargs,
    )


@dataclass(slots=True)
class _Client:
    session: aiohttp.ClientSession
    last_used: float


@dataclass(frozen=True, slots=True)
class ClientKey:
    endpoint: str
    """The URL or unique identifier of the target server."""

    domain: str
    """An arbitrary string reprenting the usage scope."""

    access_key: str | None = None
    """An optional identifier to associate with the API request context."""


class BaseClientPool(metaclass=abc.ABCMeta):
    """Base class for client session pools with shared session management."""

    _clients: MutableMapping[ClientKey, _Client]
    _client_session_factory: ClientSessionFactory

    def __init__(
        self,
        factory: ClientSessionFactory,
        *,
        _stacklevel: int = 1,
    ) -> None:
        frame = inspect.stack()[_stacklevel]
        self._creator_info = f"{frame.filename}:{frame.lineno}:{frame.function}()"
        self._client_session_factory = factory
        self._clients = {}

    def __del__(self) -> None:
        if self._clients:
            warnings.warn(
                f"{self!r} is garbage-collected but still has active client sessions.",
                ResourceWarning,
            )

    def load_client_session(self, key: ClientKey) -> aiohttp.ClientSession:
        session = self._clients.get(key, None)
        now = time.perf_counter()
        if session is not None:
            session.last_used = now
            return session.session
        client_session = self._client_session_factory(key)
        self._clients[key] = _Client(session=client_session, last_used=now)
        return client_session

    async def _close_sessions(self) -> None:
        for client in self._clients.values():
            await client.session.close()
        self._clients.clear()


class ClientPool(BaseClientPool):
    """Async client pool with a background cleanup task for idle sessions."""

    _cleanup_task: asyncio.Task[None]

    def __init__(
        self,
        factory: ClientSessionFactory,
        cleanup_interval_seconds: float = 600,
    ) -> None:
        super().__init__(factory, _stacklevel=2)
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop(cleanup_interval_seconds),
            name=f"_cleanup_task from {self!r}",
        )

    async def close(self) -> None:
        if not (self._cleanup_task.cancelled() or self._cleanup_task.done()):
            await cancel_and_wait(self._cleanup_task)
        await self._close_sessions()

    def __repr__(self) -> str:
        return (
            f"<http_client.ClientPool object at {hex(id(self))} created from {self._creator_info}>"
        )

    async def _cleanup_loop(self, cleanup_interval_seconds: float) -> None:
        while True:
            await asyncio.sleep(cleanup_interval_seconds)
            now = time.perf_counter()
            for key, client in list(self._clients.items()):
                if now - client.last_used > cleanup_interval_seconds:
                    del self._clients[key]
                    try:
                        await client.session.close()
                    except Exception as e:
                        log.exception("Error closing client session: {}", e)


AsyncClientPool = ClientPool


class SyncClientPool(BaseClientPool):
    """
    Synchronous client pool with inline eviction of idle sessions.

    Unlike :class:`ClientPool` (which uses a background ``asyncio.Task``
    for periodic cleanup), this pool evicts stale sessions lazily during
    :meth:`load_client_session` calls.  This avoids the need for a
    continuously-running event loop and the associated thread-safety
    complexity of cross-thread ``asyncio.run_coroutine_threadsafe``.

    A dedicated :class:`SyncWorkerThread` is used only for closing
    ``aiohttp.ClientSession`` objects (which require an event loop).
    """

    _worker_thread: SyncWorkerThread
    _cleanup_interval: float

    def __init__(
        self,
        factory: ClientSessionFactory,
        cleanup_interval_seconds: float = 600,
    ) -> None:
        super().__init__(factory, _stacklevel=2)
        self._cleanup_interval = cleanup_interval_seconds
        self._worker_thread = SyncWorkerThread(daemon=True)
        self._worker_thread.start()

    def load_client_session(self, key: ClientKey) -> aiohttp.ClientSession:
        self._evict_stale_sessions()
        return super().load_client_session(key)

    def _evict_stale_sessions(self) -> None:
        """Remove and close sessions that have been idle longer than the cleanup interval."""
        now = time.perf_counter()
        stale_keys = [
            key
            for key, client in self._clients.items()
            if now - client.last_used > self._cleanup_interval
        ]
        for key in stale_keys:
            client = self._clients.pop(key, None)
            if client is not None:
                try:
                    self._worker_thread.execute(client.session.close())
                except Exception as e:
                    log.exception("Error closing stale client session: {}", e)

    def close(self) -> None:
        """Synchronously close all sessions and stop the worker thread."""
        if self._worker_thread.is_alive():
            self._worker_thread.execute(self._close_sessions())
            self._worker_thread.work_queue.put(Sentinel.TOKEN)
            self._worker_thread.join()

    def __repr__(self) -> str:
        return (
            f"<http_client.SyncClientPool object at {hex(id(self))}"
            f" created from {self._creator_info}>"
        )
