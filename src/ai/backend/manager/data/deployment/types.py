import enum
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any, Optional
from uuid import UUID

import yarl

from ai.backend.common.types import ClusterMode, RuntimeVariant, SessionId, VFolderMount
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


@dataclass
class ModelRevisionSpec:
    image_identifier: ImageIdentifier
    resource_spec: ResourceSpec
    mounts: MountMetadata
    execution: ExecutionSpec


@dataclass
class DeploymentNetworkSpec:
    open_to_public: bool
    url: Optional[str] = None


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
