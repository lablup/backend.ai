import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional, Self, Sequence

import yarl
from pydantic import HttpUrl

from ai.backend.common.types import (
    AccessKey,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    MountPermission,
    MountTypes,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.endpoint import EndpointAutoScalingRuleRow, EndpointRow
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.user import UserRole


@dataclass
class ValidationResult:
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
    permission: MountPermission

    def to_dict(self) -> dict[str, Any]:
        return {
            "mount_destination": self.mount_destination,
            "type": self.type.value,
            "permission": self.permission.value,
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
    is_authorized: bool
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
    live_stat: dict[str, Any]

    @classmethod
    def from_row(cls, row: Optional[RoutingRow]) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            id=row.id,
            endpoint=row.endpoint,
            session=row.session,
            status=row.status,
            traffic_ratio=row.traffic_ratio,
            created_at=row.created_at,
            error_data=row.error_data,
            live_stat=row.live_stat,
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
    resource_slots: Mapping[str, Any]
    url: str

    model: uuid.UUID
    model_definition_path: str | None
    model_mount_destination: Optional[str]

    created_user: uuid.UUID
    created_user_email: Optional[str]

    session_owner: uuid.UUID
    session_owner_email: str

    tag: Optional[str]

    startup_command: Optional[str]
    bootstrap_script: Optional[str]
    callback_url: Optional[yarl.URL]
    environ: Optional[Mapping[str, Any]]

    name: str

    resource_opts: Optional[Mapping[str, Any]]
    replicas: int
    desired_session_count: int

    cluster_mode: ClusterMode
    cluster_size: int
    open_to_public: bool
    created_at: datetime
    destroyed_at: datetime
    retries: int

    routings: Optional[RoutingData]
    lifecycle_stage: str
    runtime_variant: RuntimeVariant

    @classmethod
    def from_row(cls, row: Optional[EndpointRow]) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            id=row.id,
            image=ImageData.from_row(row.image_row),
            domain=row.domain,
            project=row.project,
            resource_group=row.resource_group,
            resource_slots=row.resource_slots,
            url=row.url,
            model=row.model,
            model_definition_path=row.model_definition_path,
            model_mount_destination=row.model_mount_destination,
            created_user=row.created_user,
            created_user_email=row.created_user_email,
            session_owner=row.session_owner,
            session_owner_email=row.session_owner_email,
            tag=row.tag,
            startup_command=row.startup_command,
            bootstrap_script=row.bootstrap_script,
            callback_url=row.callback_url,
            environ=row.environ,
            name=row.name,
            resource_opts=row.resource_opts,
            replicas=row.replicas,
            desired_session_count=row.desired_session_count,
            cluster_mode=ClusterMode(row.cluster_mode),
            cluster_size=row.cluster_size,
            open_to_public=row.open_to_public,
            created_at=row.created_at,
            destroyed_at=row.destroyed_at,
            retries=row.retries,
            routings=RoutingData.from_row(row.routings),
            lifecycle_stage=row.lifecycle_stage,
            runtime_variant=row.runtime_variant,
        )


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
