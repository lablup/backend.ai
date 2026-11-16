from __future__ import annotations

import functools
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

import aiohttp

from ai.backend.common.clients.http_client.client_pool import (
    ClientPool,
    tcp_client_session_factory,
)
from ai.backend.common.dependencies import NonMonitorableDependencyProvider


class WorkerClientPoolProvider(NonMonitorableDependencyProvider[aiohttp.ClientTimeout, ClientPool]):
    """HTTP sessions to the api-delivery workers, one per worker address."""

    @property
    @override
    def stage_name(self) -> str:
        return "worker-client-pool"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: aiohttp.ClientTimeout) -> AsyncIterator[ClientPool]:
        worker_client_pool = ClientPool(
            functools.partial(tcp_client_session_factory, timeout=setup_input),
        )
        try:
            yield worker_client_pool
        finally:
            await worker_client_pool.close()
