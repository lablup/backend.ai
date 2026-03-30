from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.clients.http_client import ClientPool, tcp_client_session_factory
from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig


class PrometheusClientDependency(
    NonMonitorableDependencyProvider[ManagerUnifiedConfig, PrometheusClient],
):
    """Provides PrometheusClient with managed ClientPool lifecycle."""

    @property
    def stage_name(self) -> str:
        return "prometheus-client"

    @asynccontextmanager
    async def provide(self, setup_input: ManagerUnifiedConfig) -> AsyncIterator[PrometheusClient]:
        client_pool = ClientPool(tcp_client_session_factory)
        client = PrometheusClient(
            endpoint=f"http://{setup_input.metric.address.to_legacy()}/api/v1/",
            client_pool=client_pool,
        )
        try:
            yield client
        finally:
            await client_pool.close()
