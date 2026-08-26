from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
from ai.backend.manager.secret.pool import KeyProviderPool


@dataclass
class RepositoryArgs:
    db: ExtendedAsyncSAEngine
    ops_provider: DBOpsProvider
    v2_ops_provider: V2DBOpsProvider
    rbac_v2_ops_provider: V2RBACOpsProvider
    container_registry_ops_provider: ContainerRegistryOpsProvider
    reconcile_ops_provider: ReconcileOpsProvider
    artifact_registry_ops_provider: ArtifactRegistryOpsProvider
    replica_group_ops_provider: ReplicaGroupOpsProvider
    retention_ops_provider: RetentionOpsProvider
    secret_ops_provider: SecretOpsProvider
    storage_manager: StorageSessionManager
    config_provider: ManagerConfigProvider
    key_provider_pool: KeyProviderPool
    valkey_stat_client: ValkeyStatClient
    valkey_schedule_client: ValkeyScheduleClient
    valkey_image_client: ValkeyImageClient
    valkey_live_client: ValkeyLiveClient
    prometheus_client: PrometheusClient
