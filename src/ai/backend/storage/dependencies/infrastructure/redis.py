from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.clients.valkey_client.valkey_tus.client import ValkeyTusClient
from ai.backend.common.clients.valkey_client.valkey_volume_stats import ValkeyVolumeStatsClient
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.defs import (
    REDIS_BGTASK_DB,
    REDIS_STATISTICS_DB,
    REDIS_TUS_DB,
    RedisRole,
)
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import (
    CID_REDIS_ARTIFACT,
    CID_REDIS_BGTASK,
    ServiceHealthChecker,
)
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker


@dataclass
class RedisProviderInput:
    """Input for the Valkey client provider."""

    redis_config: RedisConfig
    pidx: int


@dataclass
class StorageProxyValkeyClients:
    """Valkey clients for storage proxy."""

    bgtask: ValkeyBgtaskClient
    artifact: ValkeyArtifactDownloadTrackingClient
    tus: ValkeyTusClient
    volume_stats: ValkeyVolumeStatsClient


class RedisProvider(DependencyProvider[RedisProviderInput, StorageProxyValkeyClients]):
    """Provider for the Valkey clients of the storage proxy."""

    @property
    @override
    def stage_name(self) -> str:
        return "redis"

    @asynccontextmanager
    @override
    async def provide(
        self, setup_input: RedisProviderInput
    ) -> AsyncIterator[StorageProxyValkeyClients]:
        pidx = setup_input.pidx
        redis_profile_target = setup_input.redis_config.to_redis_profile_target()

        bgtask_client = await ValkeyBgtaskClient.create(
            redis_profile_target.profile_target(RedisRole.BGTASK).to_valkey_target(),
            human_readable_name=f"storage-proxy-bgtask-{pidx}",
            db_id=REDIS_BGTASK_DB,
        )

        artifact_client = await ValkeyArtifactDownloadTrackingClient.create(
            valkey_target=redis_profile_target.profile_target(
                RedisRole.STATISTICS
            ).to_valkey_target(),
            db_id=REDIS_STATISTICS_DB,
            human_readable_name=f"storage-proxy-artifact-download-tracker-{pidx}",
        )

        tus_client = await ValkeyTusClient.create(
            valkey_target=redis_profile_target.profile_target(RedisRole.TUS).to_valkey_target(),
            db_id=REDIS_TUS_DB,
            human_readable_name=f"storage-proxy-tus-{pidx}",
        )

        volume_stats_client = await ValkeyVolumeStatsClient.create(
            valkey_target=redis_profile_target.profile_target(
                RedisRole.STATISTICS
            ).to_valkey_target(),
            db_id=REDIS_STATISTICS_DB,
            human_readable_name=f"storage-proxy-volume-stats-{pidx}",
        )

        try:
            yield StorageProxyValkeyClients(
                bgtask=bgtask_client,
                artifact=artifact_client,
                tus=tus_client,
                volume_stats=volume_stats_client,
            )
        finally:
            await bgtask_client.close()
            await artifact_client.close()
            await tus_client.close()
            await volume_stats_client.close()

    @override
    def gen_liveness_checker(self, resource: StorageProxyValkeyClients) -> ServiceHealthChecker:
        """Liveness — Valkey connection-stuck observed; restart recovers."""
        return ValkeyHealthChecker(
            clients={
                CID_REDIS_BGTASK: resource.bgtask,
                CID_REDIS_ARTIFACT: resource.artifact,
            }
        )
