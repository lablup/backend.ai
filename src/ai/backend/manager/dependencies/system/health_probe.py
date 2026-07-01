from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.health_checker import (
    CID_REDIS_ARTIFACT,
    CID_REDIS_BGTASK,
    CID_REDIS_CONTAINER_LOG,
    CID_REDIS_IMAGE,
    CID_REDIS_LIVE,
    CID_REDIS_SCHEDULE,
    CID_REDIS_STAT,
    CID_REDIS_STREAM,
    EtcdHealthChecker,
    HealthProbe,
    HealthProbeOptions,
    PrometheusHealthChecker,
    ValkeyHealthChecker,
)
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.health.database import DatabaseHealthChecker
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class HealthProbeInput:
    """Input required for health probe setup."""

    db: ExtendedAsyncSAEngine
    etcd: AsyncEtcd
    valkey: ValkeyClients


class HealthProbeDependency(DependencyProvider[HealthProbeInput, HealthProbe]):
    """Provides HealthProbe with health checker registration and lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "health-probe"

    @asynccontextmanager
    async def provide(self, setup_input: HealthProbeInput) -> AsyncIterator[HealthProbe]:
        probe = HealthProbe(options=HealthProbeOptions(check_interval=60))

        # Readiness-only: failure should drain traffic, but no restart is warranted.
        await probe.register_readiness(DatabaseHealthChecker(db=setup_input.db))

        # Informational: surfaced in detail /health but does not gate either
        # probe. Prometheus is an observability dependency — its outage
        # should neither restart the manager nor cut user traffic.
        await probe.register_informational(PrometheusHealthChecker())

        # Liveness-registered: also surfaced in readiness — connection-stuck
        # issues observed where restart is the actual recovery path.
        await probe.register_liveness(EtcdHealthChecker(etcd=setup_input.etcd))
        await probe.register_liveness(
            ValkeyHealthChecker(
                clients={
                    CID_REDIS_ARTIFACT: setup_input.valkey.artifact,
                    CID_REDIS_CONTAINER_LOG: setup_input.valkey.container_log,
                    CID_REDIS_LIVE: setup_input.valkey.live,
                    CID_REDIS_STAT: setup_input.valkey.stat,
                    CID_REDIS_IMAGE: setup_input.valkey.image,
                    CID_REDIS_STREAM: setup_input.valkey.stream,
                    CID_REDIS_SCHEDULE: setup_input.valkey.schedule,
                    CID_REDIS_BGTASK: setup_input.valkey.bgtask,
                }
            )
        )

        await probe.start()
        try:
            yield probe
        finally:
            await probe.stop()
