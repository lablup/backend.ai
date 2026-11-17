from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Self

import yarl
from pydantic import HttpUrl

from ai.backend.common.config import ModelDefinition
from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.types import FieldData
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.session.types import MountOption as MountOptionDTO
from ai.backend.common.types import (
    AccessKey,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    MountInfoEntry,
    MountPermission,
    MountTypes,
    QuotaScopeID,
    ResourceSlot,
    SessionId,
    VFolderMount,
)
from ai.backend.manager.data.image.types import ImageData

if TYPE_CHECKING:
    from ai.backend.manager.data.deployment.types import (
        DeploymentInfo,
        ModelRevisionData,
        RouteHealthStatus,
        RouteStatus,
    )

__all__ = [
    "EndpointAccessValidationData",
    "EndpointAutoScalingRuleData",
    "EndpointData",
    "EndpointLifecycle",
    "EndpointTokenData",
    "RoutingData",
    "ScalingState",
    "ServiceSearchItem",
    "ServiceSearchResult",
]


@dataclass
class EndpointAccessValidationData:
    """Minimal endpoint data required for access validation."""

    session_owner_id: uuid.UUID | None
    session_owner_role: UserRole | None
    domain: str


@dataclass
class EndpointData:
    """Legacy model-serving endpoint projection — DO NOT USE in new code.

    Backs the legacy ``/services`` (model-serving) responses, which flatten
    the active revision's fields (image, model, resources, mounts, …) onto
    the endpoint and carry no separate revision object. New deployment code
    uses ``ModelDeploymentData`` (v2) / ``LegacyDeploymentData`` (REST v1).
    """

    id: uuid.UUID
    name: str
    image: ImageData | None
    domain: str
    project: uuid.UUID
    resource_group: str
    resource_slots: ResourceSlot
    url: str | None
    model: uuid.UUID
    model_definition_path: str | None
    model_mount_destination: str | None
    created_user_id: uuid.UUID
    created_user_email: str | None
    session_owner_id: uuid.UUID
    session_owner_email: str
    tag: str | None
    startup_command: str | None
    bootstrap_script: str | None
    callback_url: yarl.URL | None
    environ: Mapping[str, Any] | None
    resource_opts: Mapping[str, Any] | None
    replicas: int
    cluster_mode: ClusterMode
    cluster_size: int
    open_to_public: bool
    created_at: datetime | None
    destroyed_at: datetime | None
    retries: int
    lifecycle_stage: EndpointLifecycle
    # Projected from whichever revision is currently active —
    # ``current_revision`` preferred, falling back to
    # ``deploying_revision``. ``None`` when the endpoint has neither
    # (e.g. a freshly-created PENDING endpoint before any revision is
    # attached); legacy response surfaces render this as the historical
    # "custom" fallback.
    runtime_variant_id: RuntimeVariantID | None
    # Snapshotted from the current revision's ``extra_mounts`` column.
    # ``VFolderMount`` resolution happens later in the session-creation
    # path; ``EndpointData`` carries the unresolved request entries.
    extra_mounts: Sequence[MountInfoEntry]
    scaling_state: ScalingState = ScalingState.STABLE
    model_definition: ModelDefinition | None = None
    routings: Sequence[RoutingData] = field(default_factory=list)

    @classmethod
    def from_deployment(
        cls,
        info: DeploymentInfo,
        *,
        created_user_email: str | None,
        session_owner_email: str,
        routings: Sequence[RoutingData],
    ) -> Self:
        """The endpoint ``info`` with no revision; ``with_revision`` fills the revision fields."""
        metadata = info.metadata
        return cls(
            id=info.id,
            name=metadata.name,
            image=None,
            domain=metadata.domain,
            project=metadata.project,
            resource_group=metadata.resource_group,
            resource_slots=ResourceSlot({}),
            url=info.network.url,
            model=uuid.UUID(int=0),
            model_definition_path=None,
            model_mount_destination=None,
            created_user_id=metadata.created_user,
            created_user_email=created_user_email,
            session_owner_id=metadata.session_owner,
            session_owner_email=session_owner_email,
            tag=metadata.tag,
            startup_command=None,
            bootstrap_script=None,
            callback_url=None,
            environ=None,
            resource_opts=None,
            replicas=info.replica.replica_count,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            open_to_public=info.network.open_to_public,
            created_at=metadata.created_at,
            destroyed_at=metadata.destroyed_at,
            retries=info.state.retry_count,
            lifecycle_stage=info.state.lifecycle,
            runtime_variant_id=None,
            extra_mounts=[],
            scaling_state=info.state.scaling_state,
            routings=routings,
        )

    def with_revision(self, revision: ModelRevisionData, image: ImageData | None) -> Self:
        """This endpoint with the fields of the revision it serves."""
        mount = revision.model_mount_config
        return dataclasses.replace(
            self,
            image=image,
            resource_slots=revision.resource_config.resource_slot,
            model=mount.vfolder_id or uuid.UUID(int=0),
            model_definition_path=mount.definition_path or None,
            model_mount_destination=mount.mount_destination,
            startup_command=revision.execution.startup_command,
            bootstrap_script=revision.execution.bootstrap_script,
            callback_url=revision.execution.callback_url,
            environ=revision.model_runtime_config.environ,
            resource_opts=revision.resource_config.resource_opts,
            cluster_mode=revision.cluster_config.mode,
            cluster_size=revision.cluster_config.size,
            runtime_variant_id=revision.model_runtime_config.runtime_variant_id,
            extra_mounts=mount.extra_mounts,
            model_definition=revision.model_definition,
        )


@dataclass
class RoutingData(FieldData):
    id: uuid.UUID
    endpoint: uuid.UUID
    session: SessionId | None
    status: RouteStatus
    health_status: RouteHealthStatus
    traffic_ratio: float
    created_at: datetime
    error_data: dict[str, Any]


@dataclass
class EndpointTokenData:
    id: uuid.UUID
    token: str
    endpoint: uuid.UUID
    session_owner: uuid.UUID
    domain: str
    project: uuid.UUID
    created_at: datetime


@dataclass
class EndpointAutoScalingRuleData(FieldData):
    id: uuid.UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: str
    comparator: AutoScalingMetricComparator
    step_size: int
    cooldown_seconds: int
    min_replicas: int
    max_replicas: int
    created_at: datetime
    last_triggered_at: datetime | None
    endpoint: uuid.UUID


@dataclass
class UserData:
    uuid: uuid.UUID
    email: str


@dataclass
class ResourceGroupData:
    wsproxy_addr: str
    wsproxy_api_token: str


@dataclass(frozen=True)
class ModelServiceValidationContext:
    """Data resolved from DB during model service validation."""

    model_vfolder_id: VFolderUUID
    model_folder_host: str
    model_folder_quota_scope_id: QuotaScopeID | None
    model_folder_usage_mode: str
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    owner_uuid: uuid.UUID
    owner_role: UserRole
    group_id: uuid.UUID
    resource_policy: dict[str, Any]
    resource_group: str
    extra_mounts: Sequence[VFolderMount]
    variant_reads_vfolder_config_files: bool


@dataclass
class ModelServicePrepareCtx:
    model_vfolder_id: VFolderUUID
    model_definition_path: str | None
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    owner_uuid: uuid.UUID
    owner_role: UserRole
    group_id: uuid.UUID
    resource_policy: dict[str, Any]
    resource_group: str
    extra_mounts: Sequence[VFolderMount]


@dataclass
class MountOption:
    """Per-vfolder extra mount option."""

    mount_destination: str | None
    type: MountTypes
    permission: MountPermission | None
    subpath: str | None = None

    @classmethod
    def from_dto(cls, dto: MountOptionDTO) -> MountOption:
        """Convert the wire-level :class:`MountOption` DTO into a data-layer dataclass."""
        return cls(
            mount_destination=dto.mount_destination,
            type=dto.type,
            permission=dto.permission,
            subpath=dto.subpath,
        )

    def to_dict(self) -> dict[str, Any]:
        # ``MountTypes`` / ``MountPermission`` are ``StrEnum``s, so the enum
        # instances ``dataclasses.asdict`` returns serialise as their string
        # value under ``json.dumps`` — no manual ``.value`` extraction needed.
        return dataclasses.asdict(self)


@dataclass
class RouteInfo:
    route_id: uuid.UUID
    session_id: uuid.UUID | None
    traffic_ratio: float


@dataclass(frozen=True)
class AppProxyRouteEntry:
    """One (session, kernel host:port) entry pushed to AppProxy.

    Manager builds these from RoutingRow + KernelRow joins so the
    AppProxy coordinator can install them on ``circuit.route_info``
    without needing a manager-side Redis hand-off or a back-channel
    DB read.
    """

    session_id: uuid.UUID
    route_id: uuid.UUID
    kernel_host: str
    kernel_port: int


@dataclass
class ServiceConfig:
    model: str
    model_definition_path: str | None
    model_version: int
    model_mount_destination: str
    extra_mounts: dict[uuid.UUID, MountOption]
    environ: dict[str, str] | None
    resource_group: str
    resources: dict[str, str | int | float] | None
    resource_opts: dict[str, str | int | bool] | None
    vfolder_subpath: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "model_definition_path": self.model_definition_path,
            "model_mount_destination": self.model_mount_destination,
            "vfolder_subpath": self.vfolder_subpath,
            "extra_mounts": {key: value.to_dict() for key, value in self.extra_mounts.items()},
            "environ": self.environ if self.environ is not None else {},
            "scaling_group": self.resource_group,
            "resources": self.resources,
            "resource_opts": self.resource_opts,
        }


@dataclass
class ServiceInfo:
    deployment_id: DeploymentID
    model_vfolder_id: VFolderUUID
    extra_mounts: Sequence[VFolderUUID]
    name: str
    model_definition_path: str | None
    replicas: int
    desired_session_count: int
    active_routes: list[RouteInfo]
    service_endpoint: HttpUrl | None
    is_public: bool
    runtime_variant_id: RuntimeVariantID


@dataclass
class CompactServiceInfo:
    id: uuid.UUID
    name: str
    replicas: int
    desired_session_count: int
    active_route_count: int
    service_endpoint: HttpUrl | None
    is_public: bool


@dataclass
class ServiceSearchItem:
    id: uuid.UUID
    name: str
    replicas: int
    active_route_count: int
    service_endpoint: HttpUrl | None
    open_to_public: bool
    resource_slots: ResourceSlot
    resource_group: str
    routings: Sequence[RoutingData]


@dataclass
class ServiceSearchResult:
    items: list[ServiceSearchItem]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class ErrorInfo:
    session_id: uuid.UUID | None
    error: dict[str, Any]


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Any | None


@dataclass
class RuntimeVariantData:
    name: str
    human_readable_name: str
