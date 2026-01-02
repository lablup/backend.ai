from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import aiohttp

from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.web.config.unified import WebServerUnifiedConfig


@dataclass
class HiveRouterClientInfo:
    """Hive Router client information."""

    client_pool: ClientPool
    endpoints: list[str]


class HiveRouterClientProvider(
    NonMonitorableDependencyProvider[WebServerUnifiedConfig, HiveRouterClientInfo]
):
    """
    Provider for Hive Router (Apollo Router) client pool.
    """

    @property
    def stage_name(self) -> str:
        return "hive-router-client"

    @asynccontextmanager
    async def provide(
        self, setup_input: WebServerUnifiedConfig
    ) -> AsyncIterator[HiveRouterClientInfo]:
        """
        Provide Hive Router client information with HTTP client pool.

        Note: This provider is only called when apollo_router is enabled.
        """
        client_pool = ClientPool(
            lambda key: aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    ssl=True,  # GraphQL router typically uses HTTPS
                ),
                base_url=key.endpoint,
                auto_decompress=False,
            )
        )

        try:
            yield HiveRouterClientInfo(
                client_pool=client_pool,
                endpoints=setup_input.apollo_router.endpoints,
            )
        finally:
            await client_pool.close()
