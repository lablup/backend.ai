from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.health_checker import ServiceHealthChecker
from ai.backend.common.health_checker.checkers.etcd import EtcdHealthChecker
from ai.backend.storage.config.loaders import make_etcd
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig


class EtcdProvider(DependencyProvider[StorageProxyUnifiedConfig, AsyncEtcd]):
    """Provider for etcd client connection."""

    @property
    @override
    def stage_name(self) -> str:
        return "etcd"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: StorageProxyUnifiedConfig) -> AsyncIterator[AsyncEtcd]:
        """Create and provide an etcd client."""
        async with make_etcd(setup_input) as etcd:
            yield etcd

    @override
    def gen_liveness_checker(self, resource: AsyncEtcd) -> ServiceHealthChecker:
        """Liveness — stuck etcd connection observed; restart is the recovery path."""
        return EtcdHealthChecker(etcd=resource)
