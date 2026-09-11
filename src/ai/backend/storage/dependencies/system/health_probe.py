from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.health_checker import (
    CID_REDIS_ARTIFACT,
    CID_REDIS_BGTASK,
    EtcdHealthChecker,
    HealthProbe,
    HealthProbeOptions,
    ValkeyHealthChecker,
)
from ai.backend.storage.dependencies.infrastructure.redis import StorageProxyValkeyClients


@dataclass
class HealthProbeInput:
    """Input required for health probe setup."""

    etcd: AsyncEtcd
    valkey: StorageProxyValkeyClients


class HealthProbeProvider(NonMonitorableDependencyProvider[HealthProbeInput, HealthProbe]):
    """Provides HealthProbe with health checker registration and lifecycle management."""

    @property
    @override
    def stage_name(self) -> str:
        return "health-probe"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: HealthProbeInput) -> AsyncIterator[HealthProbe]:
        probe = HealthProbe(options=HealthProbeOptions(check_interval=60))
        await probe.register_liveness(EtcdHealthChecker(etcd=setup_input.etcd))
        await probe.register_liveness(
            ValkeyHealthChecker(
                clients={
                    CID_REDIS_BGTASK: setup_input.valkey.bgtask,
                    CID_REDIS_ARTIFACT: setup_input.valkey.artifact,
                }
            )
        )
        await probe.start()
        try:
            yield probe
        finally:
            await probe.stop()
