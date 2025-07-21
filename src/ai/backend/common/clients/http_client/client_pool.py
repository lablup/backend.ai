import asyncio
import logging
import time
from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Optional

import aiohttp

from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ClientConfig:
    ssl: bool = True
    limit: int = 100
    limit_per_host: int = 0


@dataclass
class _Client:
    session: aiohttp.ClientSession
    last_used: float


@dataclass(frozen=True)
class ClientKey:
    endpoint: str
    domain: str
    access_key: Optional[str] = None


class ClientPool:
    _config: ClientConfig
    _clients: MutableMapping[ClientKey, _Client]
    _cleanup_task: asyncio.Task

    def __init__(self, config: ClientConfig, cleanup_interval_seconds: int = 600) -> None:
        self._config = config
        self._clients = {}
        self._cleanup_task = asyncio.create_task(self._cleanup_loop(cleanup_interval_seconds))

    async def close(self) -> None:
        self._cleanup_task.cancel()
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

    def _make_client_session(self) -> aiohttp.ClientSession:
        connector = aiohttp.TCPConnector(
            ssl=self._config.ssl,
            limit=self._config.limit,
            limit_per_host=self._config.limit_per_host,
        )
        return aiohttp.ClientSession(connector=connector)

    def load_client_session(self, key: ClientKey) -> aiohttp.ClientSession:
        session = self._clients.get(key, None)
        now = time.perf_counter()
        if session is not None:
            session.last_used = now
            return session.session
        client_session = self._make_client_session()
        self._clients[key] = _Client(session=client_session, last_used=now)
        return client_session
