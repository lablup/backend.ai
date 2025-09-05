import enum
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import PurePosixPath
from typing import Any, Optional
from uuid import UUID, uuid4

import yarl

from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    DeploymentStrategy,
    LivenessStatus,
    ModelDeploymentStatus,
    ReadinessStatus,
)
from ai.backend.common.types import (
    AutoScalingMetricSource,
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
    SessionId,
    VFolderMount,
)
from ai.backend.manager.data.deployment.scale import AutoScalingRule
from ai.backend.manager.data.image.types import ImageIdentifier


class EndpointLifecycle(enum.Enum):
    PENDING = "pending"
    CREATED = "created"  # Deprecated, use READY instead
    SCALING = "scaling"
    READY = "ready"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"

    @classmethod
    @lru_cache(maxsize=1)
    def active_states(cls) -> set["EndpointLifecycle"]:
        return {cls.PENDING, cls.CREATED, cls.SCALING, cls.READY}

    @classmethod
    @lru_cache(maxsize=1)
    def need_scaling_states(cls) -> set["EndpointLifecycle"]:
        return {cls.CREATED, cls.READY}

    @classmethod
    @lru_cache(maxsize=1)
    def inactive_states(cls) -> set["EndpointLifecycle"]:
        return {cls.DESTROYING, cls.DESTROYED}


class RouteStatus(enum.Enum):
    PROVISIONING = "provisioning"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    FAILED_TO_START = "failed_to_start"

    @classmethod
    @lru_cache(maxsize=1)
    def active_route_statuses(cls) -> set["RouteStatus"]:
        return {RouteStatus.PROVISIONING, RouteStatus.HEALTHY, RouteStatus.UNHEALTHY}

    @classmethod
    @lru_cache(maxsize=1)
    def inactive_route_statuses(cls) -> set["RouteStatus"]:
        return {RouteStatus.TERMINATING, RouteStatus.TERMINATED, RouteStatus.FAILED_TO_START}

    def is_active(self) -> bool:
        return self in self.active_route_statuses()

    def is_inactive(self) -> bool:
        return self in self.inactive_route_statuses()

    def termination_priority(self) -> int:
        priority_map = {
            RouteStatus.UNHEALTHY: 1,
            RouteStatus.PROVISIONING: 2,
            RouteStatus.HEALTHY: 3,
        }
        return priority_map.get(self, 0)


@dataclass
class DeploymentMetadata:
    name: str
    domain: str
    project: UUID
    resource_group: str
    created_user: UUID
    session_owner: UUID
    created_at: Optional[datetime]
    tag: Optional[str] = None


@dataclass
class DeploymentState:
    lifecycle: EndpointLifecycle
    retry_count: int


@dataclass
class MountSpec:
    mounts: list[UUID]
    mount_map: Mapping[UUID, str]
    mount_options: Mapping[UUID, dict[str, Any]]


@dataclass
class MountInfo:
    vfolder_id: UUID
    kernel_path: PurePosixPath


@dataclass
class MountMetadata:
    model_vfolder_id: UUID
    model_definition_path: Optional[str] = None
    model_mount_destination: str = "/models"
    extra_mounts: list[VFolderMount] = field(default_factory=list)

    def to_mount_spec(self) -> MountSpec:
        mounts = [
            self.model_vfolder_id,
            *[m.vfid.folder_id for m in self.extra_mounts],
        ]
        mount_map = {
            self.model_vfolder_id: self.model_mount_destination,
            **{m.vfid.folder_id: m.kernel_path.as_posix() for m in self.extra_mounts},
        }
        mount_options = {m.vfid.folder_id: {"permission": m.mount_perm} for m in self.extra_mounts}
        return MountSpec(mounts=mounts, mount_map=mount_map, mount_options=mount_options)


@dataclass
class ReplicaSpec:
    replica_count: int
    desired_replica_count: Optional[int] = None

    @property
    def target_replica_count(self) -> int:
        if self.desired_replica_count is not None:
            return self.desired_replica_count
        return self.replica_count


@dataclass
class ResourceSpec:
    cluster_mode: ClusterMode
    cluster_size: int
    resource_slots: Mapping[str, Any]
    resource_opts: Optional[Mapping[str, Any]] = None


@dataclass
class ExecutionSpec:
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None
    environ: Optional[dict[str, str]] = None
    runtime_variant: RuntimeVariant = RuntimeVariant.CUSTOM
    callback_url: Optional[yarl.URL] = None
    inference_runtime_config: Optional[Mapping[str, Any]] = None


@dataclass
class ModelRevisionSpec:
    image_identifier: ImageIdentifier
    resource_spec: ResourceSpec
    mounts: MountMetadata
    execution: ExecutionSpec


@dataclass
class DeploymentNetworkSpec:
    open_to_public: bool
    access_token_ids: Optional[list[UUID]] = None
    url: Optional[str] = None
    preferred_domain_name: Optional[str] = None


@dataclass
class DeploymentInfo:
    id: UUID
    metadata: DeploymentMetadata
    state: DeploymentState
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revisions: list[ModelRevisionSpec]

    def target_revision(self) -> Optional[ModelRevisionSpec]:
        if self.model_revisions:
            return self.model_revisions[0]
        return None


@dataclass
class DeploymentSessionSpec:
    id: UUID
    metadata: DeploymentMetadata


@dataclass
class ScaleOutDecision:
    deployment_info: DeploymentInfo
    new_replica_count: int


@dataclass
class DefinitionFiles:
    service_definition: Optional[dict[str, Any]]
    model_definition: dict[str, Any]


@dataclass
class RouteInfo:
    """Route information for deployment."""

    route_id: UUID
    endpoint_id: UUID
    session_id: Optional[SessionId]
    status: RouteStatus
    traffic_ratio: float
    created_at: datetime
    error_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentInfoWithRoutes:
    """DeploymentInfo with its routes."""

    deployment_info: DeploymentInfo
    routes: list[RouteInfo] = field(default_factory=list)


@dataclass
class DeploymentInfoWithAutoScalingRules:
    """DeploymentInfo with its autoscaling rules."""

    deployment_info: DeploymentInfo
    rules: list[AutoScalingRule] = field(default_factory=list)


@dataclass
class ModelDeploymentAutoScalingRuleData:
    id: UUID
    model_deployment_id: UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    min_threshold: Optional[Decimal]
    max_threshold: Optional[Decimal]
    step_size: int
    time_window: int
    min_replicas: Optional[int]
    max_replicas: Optional[int]
    created_at: datetime
    last_triggered_at: datetime


@dataclass
class ModelDeploymentAccessTokenData:
    id: UUID
    token: str
    valid_until: datetime
    created_at: datetime


@dataclass
class ModelReplicaData:
    id: UUID
    revision_id: UUID
    session_id: UUID
    readiness_status: ReadinessStatus
    liveness_status: LivenessStatus
    activeness_status: ActivenessStatus
    weight: int
    detail: dict[str, Any]
    created_at: datetime
    live_stat: dict[str, Any]


@dataclass
class ClusterConfigData:
    mode: ClusterMode
    size: int


@dataclass
class ResourceConfigData:
    resource_group_name: str
    resource_slot: ResourceSlot
    resource_opts: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class ModelRuntimeConfigData:
    runtime_variant: RuntimeVariant
    inference_runtime_config: Optional[Mapping[str, Any]] = None
    environ: Optional[dict[str, Any]] = None


@dataclass
class ModelMountConfigData:
    vfolder_id: UUID
    mount_destination: str
    definition_path: str


@dataclass
class ExtraVFolderMountData:
    vfolder_id: UUID
    mount_destination: str


@dataclass
class ModelRevisionData:
    id: UUID
    name: str
    cluster_config: ClusterConfigData
    resource_config: ResourceConfigData
    model_runtime_config: ModelRuntimeConfigData
    model_mount_config: ModelMountConfigData
    created_at: datetime
    image_id: UUID
    extra_vfolder_mounts: list[ExtraVFolderMountData] = field(default_factory=list)


@dataclass
class ModelDeploymentMetadataInfo:
    name: str
    status: ModelDeploymentStatus
    tags: list[str]
    project_id: UUID
    domain_name: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ReplicaStateData:
    desired_replica_count: int
    replica_ids: list[UUID]


@dataclass
class ModelDeploymentData:
    id: UUID
    metadata: ModelDeploymentMetadataInfo
    network_access: DeploymentNetworkSpec
    revision: Optional[ModelRevisionData]
    revision_history_ids: list[UUID]
    scaling_rule_ids: list[UUID]
    replica_state: ReplicaStateData
    default_deployment_strategy: DeploymentStrategy
    created_user_id: UUID
    access_token_ids: Optional[UUID] = None


mock_revision_data_1 = ModelRevisionData(
    id=uuid4(),
    name="test-revision",
    cluster_config=ClusterConfigData(
        mode=ClusterMode.SINGLE_NODE,
        size=1,
    ),
    resource_config=ResourceConfigData(
        resource_group_name="default",
        resource_slot=ResourceSlot.from_json({"cpu": 1, "memory": 1024}),
    ),
    model_mount_config=ModelMountConfigData(
        vfolder_id=uuid4(),
        mount_destination="/model",
        definition_path="model-definition.yaml",
    ),
    model_runtime_config=ModelRuntimeConfigData(
        runtime_variant=RuntimeVariant.VLLM,
        inference_runtime_config={"tp_size": 2, "max_length": 1024},
    ),
    extra_vfolder_mounts=[
        ExtraVFolderMountData(
            vfolder_id=uuid4(),
            mount_destination="/var",
        ),
        ExtraVFolderMountData(
            vfolder_id=uuid4(),
            mount_destination="/example",
        ),
    ],
    image_id=uuid4(),
    created_at=datetime.now(),
)

mock_revision_data_2 = ModelRevisionData(
    id=uuid4(),
    name="test-revision-2",
    cluster_config=ClusterConfigData(
        mode=ClusterMode.MULTI_NODE,
        size=1,
    ),
    resource_config=ResourceConfigData(
        resource_group_name="default",
        resource_slot=ResourceSlot.from_json({"cpu": 1, "memory": 1024}),
    ),
    model_mount_config=ModelMountConfigData(
        vfolder_id=uuid4(),
        mount_destination="/model",
        definition_path="model-definition.yaml",
    ),
    model_runtime_config=ModelRuntimeConfigData(
        runtime_variant=RuntimeVariant.NIM,
        inference_runtime_config={"tp_size": 2, "max_length": 1024},
    ),
    image_id=uuid4(),
    created_at=datetime.now(),
)
