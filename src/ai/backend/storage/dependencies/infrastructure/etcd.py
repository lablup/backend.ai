from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.etcd import AsyncEtcd
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
