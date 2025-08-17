from __future__ import annotations

import asyncio
import inspect
import logging
import time
from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Optional, Protocol

import aiohttp

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
    timeout: Optional[aiohttp.ClientTimeout] = None,
    **kwargs,
) -> aiohttp.ClientSession:
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

    access_key: Optional[str] = None
    """An optional identifier to associate with the API request context."""


class ClientPool:
    _clients: MutableMapping[ClientKey, _Client]
    _cleanup_task: asyncio.Task[None]

    def __init__(self, factory: ClientSessionFactory, cleanup_interval_seconds: int = 600) -> None:
        self._client_session_factory = factory
        self._clients = {}

        frame = inspect.stack()[1]
        caller_info = f"{frame.filename}:{frame.lineno} in {frame.function}"
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop(cleanup_interval_seconds),
            name=f"_cleanup_task from http_client.ClientPool created at {caller_info}",
        )

    async def close(self) -> None:
        if not (self._cleanup_task.cancelled() or self._cleanup_task.done()):
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                # FIXME: use safer cancel-and-wait approach
                pass
        for client in self._clients.values():
            await client.session.close()
        self._clients.clear()

    async def _cleanup_loop(self, cleanup_interval_seconds: int) -> None:
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

    def load_client_session(self, key: ClientKey) -> aiohttp.ClientSession:
        session = self._clients.get(key, None)
        now = time.perf_counter()
        if session is not None:
            session.last_used = now
            return session.session
        client_session = self._client_session_factory(key)
        self._clients[key] = _Client(session=client_session, last_used=now)
        return client_session
