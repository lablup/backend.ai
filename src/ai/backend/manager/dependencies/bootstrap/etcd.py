from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import HealthCheckerRegistration
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.health_checker import HealthCheckKey
from ai.backend.common.health_checker.checkers.etcd import EtcdHealthChecker
from ai.backend.common.health_checker.types import ETCD, ComponentId
from ai.backend.manager.config.bootstrap import BootstrapConfig

from .base import BootstrapDependency


class EtcdDependency(BootstrapDependency[AsyncEtcd]):
    """Provides etcd client lifecycle management for bootstrap stage."""

    @property
    def stage_name(self) -> str:
        return "etcd"

    @asynccontextmanager
    async def provide(self, setup_input: BootstrapConfig) -> AsyncIterator[AsyncEtcd]:
        """Initialize and provide an etcd client.

        Args:
            setup_input: Bootstrap configuration containing etcd settings

        Yields:
            Initialized AsyncEtcd client
        """
        etcd = AsyncEtcd.initialize(setup_input.etcd.to_dataclass())
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
