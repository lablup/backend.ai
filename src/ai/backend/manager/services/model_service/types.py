import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping, Optional, Self, Sequence, override

import yarl
from pydantic import AnyUrl, HttpUrl

from ai.backend.common.types import (
    AccessKey,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    MountPermission,
    MountTypes,
    ResourceSlot,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.endpoint import EndpointAutoScalingRuleRow, EndpointRow
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.types import Creator, OptionalState, PartialModifier, TriState


@dataclass
class ModelServicePrepareCtx:
    model_id: uuid.UUID
    model_definition_path: Optional[str]
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    owner_uuid: uuid.UUID
    owner_role: UserRole
    group_id: uuid.UUID
    resource_policy: dict
    scaling_group: str
    extra_mounts: Sequence[VFolderMount]


@dataclass
class MountOption:
    mount_destination: Optional[str]
    type: MountTypes
    permission: Optional[MountPermission]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mount_destination": self.mount_destination,
            "type": self.type.value,
            "permission": self.permission.value if self.permission else None,
        }


@dataclass
class RouteInfo:
    route_id: uuid.UUID
    session_id: uuid.UUID
    traffic_ratio: float


@dataclass
class ServiceConfig:
    model: str
    model_definition_path: Optional[str]
    model_version: int
    model_mount_destination: str
    extra_mounts: dict[uuid.UUID, MountOption]
    environ: Optional[dict[str, str]]
    scaling_group: str
    resources: dict[str, str | int]
    resource_opts: dict[str, str | int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "model_definition_path": self.model_definition_path,
            "model_mount_destination": self.model_mount_destination,
            "extra_mounts": {key: value.to_dict() for key, value in self.extra_mounts.items()},
            "environ": self.environ,
            "scaling_group": self.scaling_group,
            "resources": self.resources,
            "resource_opts": self.resource_opts,
        }


@dataclass
class ServiceInfo:
    endpoint_id: uuid.UUID
    model_id: uuid.UUID
    extra_mounts: Sequence[uuid.UUID]
    name: str
    model_definition_path: Optional[str]
    replicas: int
    desired_session_count: int
    active_routes: list[RouteInfo]
    service_endpoint: Optional[HttpUrl]
    is_public: bool
    runtime_variant: RuntimeVariant


@dataclass
class CompactServiceInfo:
    id: uuid.UUID
    name: str
    replicas: int
    desired_session_count: int
    active_route_count: int
    service_endpoint: Optional[HttpUrl]
    is_public: bool


@dataclass
class RequesterCtx:
    is_authorized: Optional[bool]
    user_id: uuid.UUID
    user_role: UserRole
    domain_name: str


@dataclass
class ErrorInfo:
    session_id: Optional[uuid.UUID]
    error: dict[str, Any]


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Optional[Any]


@dataclass
class RoutingData:
    id: uuid.UUID
    endpoint: uuid.UUID
    session: Optional[uuid.UUID]
    status: RouteStatus
    traffic_ratio: float
    created_at: datetime
    error_data: dict[str, Any]

    @classmethod
    def from_row(cls, row: RoutingRow) -> Self:
        return cls(
            id=row.id,
            endpoint=row.endpoint,
            session=row.session,
            status=row.status,
            traffic_ratio=row.traffic_ratio,
            created_at=row.created_at,
            error_data=row.error_data,
        )


@dataclass
class RuntimeVariantData:
    name: str
    human_readable_name: str


@dataclass
class EndpointData:
    id: uuid.UUID
    image: Optional[ImageData]
    domain: str
    project: uuid.UUID
    resource_group: str
    resource_slots: ResourceSlot
    url: str

    model: uuid.UUID
    model_definition_path: str | None
    model_mount_destination: Optional[str]

    created_user_id: uuid.UUID
    created_user_email: Optional[str]

    session_owner_id: uuid.UUID
    session_owner_email: str

    tag: Optional[str]

    startup_command: Optional[str]
    bootstrap_script: Optional[str]
    callback_url: Optional[yarl.URL]
    environ: Optional[Mapping[str, Any]]

    name: str

    resource_opts: Optional[Mapping[str, Any]]
    replicas: int

    cluster_mode: ClusterMode
    cluster_size: int
    open_to_public: bool
    created_at: datetime
    destroyed_at: datetime
    retries: int

    routings: Optional[list[RoutingData]]
    lifecycle_stage: str
    runtime_variant: RuntimeVariant

    @classmethod
    def from_row(cls, row: Optional[EndpointRow]) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            id=row.id,
            image=row.image_row.to_dataclass(),
            domain=row.domain,
            project=row.project,
            resource_group=row.resource_group,
            resource_slots=row.resource_slots,
            url=row.url,
            model=row.model,
            model_definition_path=row.model_definition_path,
            model_mount_destination=row.model_mount_destination,
            created_user_id=row.created_user,
            created_user_email=row.created_user_row.email
            if row.created_user_row is not None
            else None,
            session_owner_id=row.session_owner,
            session_owner_email=row.session_owner_row.email,
            tag=row.tag,
            startup_command=row.startup_command,
            bootstrap_script=row.bootstrap_script,
            callback_url=row.callback_url,
            environ=row.environ,
            name=row.name,
            resource_opts=row.resource_opts,
            replicas=row.replicas,
            cluster_mode=ClusterMode(row.cluster_mode),
            cluster_size=row.cluster_size,
            open_to_public=row.open_to_public,
            created_at=row.created_at,
            destroyed_at=row.destroyed_at,
            retries=row.retries,
            routings=[RoutingData.from_row(routing) for routing in row.routings]
            if row.routings
            else None,
            lifecycle_stage=row.lifecycle_stage.name,
            runtime_variant=row.runtime_variant,
        )


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
class EndpointAutoScalingRuleData:
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
    last_triggered_at: datetime
    endpoint: uuid.UUID

    @classmethod
    def from_row(cls, row: Optional[EndpointAutoScalingRuleRow]) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            id=row.id,
            metric_source=row.metric_source,
            metric_name=row.metric_name,
            threshold=row.threshold,
            comparator=row.comparator,
            step_size=row.step_size,
            cooldown_seconds=row.cooldown_seconds,
            min_replicas=row.min_replicas,
            max_replicas=row.max_replicas,
            created_at=row.created_at,
            last_triggered_at=row.last_triggered_at,
            endpoint=row.endpoint,
        )


@dataclass
class ModelServiceCreator(Creator):
    service_name: str
    replicas: int
    image: str
    runtime_variant: RuntimeVariant
    architecture: str
    group_name: str
    domain_name: str
    cluster_size: int
    cluster_mode: ClusterMode
    open_to_public: bool
    config: ServiceConfig
    sudo_session_enabled: bool
    model_service_prepare_ctx: ModelServicePrepareCtx
    tag: Optional[str] = None
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None
    callback_url: Optional[AnyUrl] = None

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {}


@dataclass
class ImageRef:
    name: str
    registry: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    architecture: OptionalState[str] = field(default_factory=OptionalState[str].nop)


@dataclass
class ExtraMount:
    vfolder_id: OptionalState[uuid.UUID] = field(default_factory=OptionalState[uuid.UUID].nop)
    mount_destination: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    type: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    permission: OptionalState[str] = field(default_factory=OptionalState[str].nop)


@dataclass
class EndpointModifier(PartialModifier):
    resource_slots: OptionalState[ResourceSlot] = field(
        default_factory=OptionalState[ResourceSlot].nop
    )
    resource_opts: TriState[dict[str, Any]] = field(default_factory=TriState[dict[str, Any]].nop)
    cluster_mode: OptionalState[ClusterMode] = field(default_factory=OptionalState[ClusterMode].nop)
    cluster_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    replicas: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    desired_session_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    image: TriState[ImageRef] = field(default_factory=TriState.nop)
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    resource_group: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    model_definition_path: TriState[str] = field(default_factory=TriState[str].nop)
    open_to_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    extra_mounts: OptionalState[list[ExtraMount]] = field(
        default_factory=OptionalState[list[ExtraMount]].nop
    )
    environ: TriState[dict[str, str]] = field(default_factory=TriState[dict[str, str]].nop)
    runtime_variant: OptionalState[RuntimeVariant] = field(
        default_factory=OptionalState[RuntimeVariant].nop
    )

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.resource_slots.update_dict(to_update, "resource_slots")
        self.resource_opts.update_dict(to_update, "resource_opts")
        self.cluster_mode.update_dict(to_update, "cluster_mode")
        self.cluster_size.update_dict(to_update, "cluster_size")
        self.model_definition_path.update_dict(to_update, "model_definition_path")
        self.runtime_variant.update_dict(to_update, "runtime_variant")
        self.resource_group.update_dict(to_update, "resource_group")
        return to_update

    def fields_to_update_require_none_check(self) -> dict[str, Any]:
        # This method is used to update fields that require a check for None values
        to_update: dict[str, Any] = {}
        # The order of replicas and desired_session_count is important
        # as desired_session_count is legacy field and value of replicas need to override it
        self.desired_session_count.update_dict(to_update, "desired_session_count")
        self.replicas.update_dict(to_update, "replicas")
        self.environ.update_dict(to_update, "environ")
        return to_update


@dataclass
class EndpointAutoScalingRuleCreator(Creator):
    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: str
    comparator: AutoScalingMetricComparator
    step_size: int
    cooldown_seconds: int
    min_replicas: Optional[int] = None
    max_replicas: Optional[int] = None

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "metric_source": self.metric_source,
            "metric_name": self.metric_name,
            "threshold": self.threshold,
            "comparator": self.comparator,
            "step_size": self.step_size,
            "cooldown_seconds": self.cooldown_seconds,
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
        }


@dataclass
class EndpointAutoScalingRuleModifier(PartialModifier):
    metric_source: OptionalState[AutoScalingMetricSource] = field(default_factory=OptionalState.nop)
    metric_name: OptionalState[str] = field(default_factory=OptionalState.nop)
    threshold: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    comparator: OptionalState[AutoScalingMetricComparator] = field(
        default_factory=OptionalState.nop
    )
    step_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    cooldown_seconds: OptionalState[int] = field(default_factory=OptionalState.nop)
    min_replicas: TriState[int] = field(default_factory=TriState.nop)
    max_replicas: TriState[int] = field(default_factory=TriState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.metric_source.update_dict(to_update, "metric_source")
        self.metric_name.update_dict(to_update, "metric_name")
        self.threshold.update_dict(to_update, "threshold")
        self.comparator.update_dict(to_update, "comparator")
        self.step_size.update_dict(to_update, "step_size")
        self.cooldown_seconds.update_dict(to_update, "cooldown_seconds")
        self.min_replicas.update_dict(to_update, "min_replicas")
        self.max_replicas.update_dict(to_update, "max_replicas")
        return to_update
