from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.health_checker import ServiceHealthChecker
from ai.backend.common.health_checker.checkers.etcd import EtcdHealthChecker
from ai.backend.manager.config.bootstrap import BootstrapConfig

from .base import BootstrapDependency


class EtcdDependency(BootstrapDependency[AsyncEtcd]):
    """Provides etcd client lifecycle management for bootstrap stage."""

    @property
    @override
    def stage_name(self) -> str:
        return "etcd"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: BootstrapConfig) -> AsyncIterator[AsyncEtcd]:
        """Initialize and provide an etcd client.

        Args:
            setup_input: Bootstrap configuration containing etcd settings

        Yields:
            Initialized AsyncEtcd client
        """
        async with AsyncEtcd.create_from_config(setup_input.etcd.to_dataclass()) as etcd:
            yield etcd

    @override
    def gen_liveness_checker(self, resource: AsyncEtcd) -> ServiceHealthChecker:
        """Liveness — stuck etcd connection observed; restart is the recovery path."""
        return EtcdHealthChecker(etcd=resource)
