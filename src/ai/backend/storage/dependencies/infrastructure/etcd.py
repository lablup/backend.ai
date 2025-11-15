from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import DependencyProvider, HealthCheckerRegistration
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.health_checker import HealthCheckKey
from ai.backend.common.health_checker.checkers.etcd import EtcdHealthChecker
from ai.backend.common.health_checker.types import ETCD, ComponentId
from ai.backend.storage.config.loaders import make_etcd
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig


class EtcdProvider(DependencyProvider[StorageProxyUnifiedConfig, AsyncEtcd]):
    """Provider for etcd client connection."""

    @property
    def stage_name(self) -> str:
        return "etcd"

    @asynccontextmanager
    async def provide(self, setup_input: StorageProxyUnifiedConfig) -> AsyncIterator[AsyncEtcd]:
        """Create and provide an etcd client."""
        etcd = make_etcd(setup_input)
        try:
            yield etcd
        finally:
            await etcd.close()

    def gen_health_checkers(self, resource: AsyncEtcd) -> list[HealthCheckerRegistration]:
        """
        Return health checker for etcd.

        Args:
            resource: The initialized etcd client

        Returns:
            List containing health checker registration for etcd
        """
        return [
            HealthCheckerRegistration(
                key=HealthCheckKey(service_group=ETCD, component_id=ComponentId("config")),
                checker=EtcdHealthChecker(etcd=resource),
            )
        ]
