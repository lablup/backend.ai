from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.defs import REDIS_BGTASK_DB, REDIS_STATISTICS_DB, RedisRole
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig


@dataclass
class RedisProviderInput:
    """Input for Redis provider."""

    local_config: StorageProxyUnifiedConfig
    etcd: AsyncEtcd


@dataclass
class StorageProxyValkeyClients:
    """Valkey clients for storage proxy."""

    bgtask: ValkeyBgtaskClient
    artifact: ValkeyArtifactDownloadTrackingClient


class RedisProvider(DependencyProvider[RedisProviderInput, StorageProxyValkeyClients]):
    """Provider for Redis configuration and Valkey clients."""

    @property
    def stage_name(self) -> str:
        return "redis"

    @asynccontextmanager
    async def provide(
        self, setup_input: RedisProviderInput
    ) -> AsyncIterator[StorageProxyValkeyClients]:
        """Load and provide Redis configuration and Valkey clients."""
        # Load Redis config from etcd
        raw_redis_config = await setup_input.etcd.get_prefix("config/redis")
        redis_config = RedisConfig.model_validate(raw_redis_config)

        redis_profile_target = redis_config.to_redis_profile_target()

        # Create ValkeyBgtaskClient
        bgtask_client = await ValkeyBgtaskClient.create(
            redis_profile_target.profile_target(RedisRole.BGTASK).to_valkey_target(),
            human_readable_name="storage_bgtask",
            db_id=REDIS_BGTASK_DB,
        )

        # Create ValkeyArtifactDownloadTrackingClient
        artifact_client = await ValkeyArtifactDownloadTrackingClient.create(
            valkey_target=redis_profile_target.profile_target(
                RedisRole.STATISTICS
            ).to_valkey_target(),
            db_id=REDIS_STATISTICS_DB,
            human_readable_name="storage_artifact",
        )

        try:
            yield StorageProxyValkeyClients(
                bgtask=bgtask_client,
                artifact=artifact_client,
            )
        finally:
            await bgtask_client.close()
            await artifact_client.close()
