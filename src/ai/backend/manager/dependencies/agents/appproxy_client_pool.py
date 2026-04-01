from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool


class AppProxyClientPoolDependency(
    NonMonitorableDependencyProvider[None, AppProxyClientPool],
):
    """Provides AppProxyClientPool lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "appproxy-client-pool"

    @asynccontextmanager
    async def provide(self, setup_input: None) -> AsyncIterator[AppProxyClientPool]:
        """Initialize and provide an app proxy client pool.

        Args:
            setup_input: Not used (no dependencies required)

        Yields:
            Initialized AppProxyClientPool
        """
        pool = AppProxyClientPool()
        try:
            yield pool
        finally:
            await pool.close()
