from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import aiohttp

from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.web.config.unified import WebServerUnifiedConfig


@dataclass
class ManagerClientInfo:
    """Manager API client information."""

    client_pool: ClientPool
    endpoints: list[str]


class ManagerClientProvider(
    NonMonitorableDependencyProvider[WebServerUnifiedConfig, ManagerClientInfo]
):
    """
    Provider for Manager API client pool.
    """

    @property
    def stage_name(self) -> str:
        return "manager-client"

    @asynccontextmanager
    async def provide(
        self, setup_input: WebServerUnifiedConfig
    ) -> AsyncIterator[ManagerClientInfo]:
        """
        Provide Manager API client information with HTTP client pool.
        """
        client_pool = ClientPool(
            lambda key: aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    ssl=setup_input.api.ssl_verify,
                    limit=setup_input.api.connection_limit,
                ),
                base_url=key.endpoint,
                auto_decompress=False,
            )
        )

        try:
            yield ManagerClientInfo(
                client_pool=client_pool,
                endpoints=setup_input.api.endpoint,
            )
        finally:
            await client_pool.close()
