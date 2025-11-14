from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.etcd import AsyncEtcd
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
