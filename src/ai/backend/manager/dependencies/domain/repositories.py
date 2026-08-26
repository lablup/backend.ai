from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.ops.v2.artifact_registry.provider import (
    ArtifactRegistryOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.container_registry.provider import (
    ContainerRegistryOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.rbac.provider import V2RBACOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.ops.v2.replica_group.provider import ReplicaGroupOpsProvider
from ai.backend.manager.repositories.ops.v2.retention.provider import RetentionOpsProvider
from ai.backend.manager.repositories.ops.v2.secret.provider import SecretOpsProvider
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.secret.pool import KeyProviderPool

from .base import DomainDependency

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
    from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
    from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
        ValkeyScheduleClient,
    )
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.manager.clients.prometheus.client import PrometheusClient
    from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class RepositoriesInput:
    """Input required for repositories setup."""

    db: ExtendedAsyncSAEngine
    storage_manager: StorageSessionManager
    config_provider: ManagerConfigProvider
    key_provider_pool: KeyProviderPool
    valkey_stat: ValkeyStatClient
    valkey_live: ValkeyLiveClient
    valkey_schedule: ValkeyScheduleClient
    valkey_image: ValkeyImageClient
    prometheus_client: PrometheusClient


class RepositoriesDependency(DomainDependency[RepositoriesInput, Repositories]):
    """Provides Repositories lifecycle management.

    Repositories is a composite dataclass that holds all repository instances
    used across the manager. It requires database, storage, config, and
    valkey client dependencies.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "repositories"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: RepositoriesInput) -> AsyncIterator[Repositories]:
        """Initialize and provide Repositories.

        Args:
            setup_input: Input containing db, storage_manager, config_provider,
                         and valkey client references.

        Yields:
            Initialized Repositories instance.
        """
        repositories = Repositories.create(
            args=RepositoryArgs(
                db=setup_input.db,
                ops_provider=DBOpsProvider(setup_input.db),
                v2_ops_provider=V2DBOpsProvider(setup_input.db),
                rbac_v2_ops_provider=V2RBACOpsProvider(setup_input.db),
                container_registry_ops_provider=ContainerRegistryOpsProvider(setup_input.db),
                reconcile_ops_provider=ReconcileOpsProvider(setup_input.db),
                artifact_registry_ops_provider=ArtifactRegistryOpsProvider(setup_input.db),
                replica_group_ops_provider=ReplicaGroupOpsProvider(setup_input.db),
                retention_ops_provider=RetentionOpsProvider(setup_input.db),
                secret_ops_provider=SecretOpsProvider(setup_input.db),
                storage_manager=setup_input.storage_manager,
                config_provider=setup_input.config_provider,
                key_provider_pool=setup_input.key_provider_pool,
                valkey_stat_client=setup_input.valkey_stat,
                valkey_live_client=setup_input.valkey_live,
                valkey_schedule_client=setup_input.valkey_schedule,
                valkey_image_client=setup_input.valkey_image,
                prometheus_client=setup_input.prometheus_client,
            )
        )
        yield repositories
