from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

import yarl
from pydantic import HttpUrl

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.user.types import UserRole
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

if TYPE_CHECKING:
    from ai.backend.manager.data.deployment.types import RouteStatus

__all__ = [
    "EndpointAccessValidationData",
    "EndpointAutoScalingRuleData",
    "EndpointAutoScalingRuleListResult",
    "EndpointData",
    "EndpointLifecycle",
    "EndpointTokenData",
    "RoutingData",
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
    id: uuid.UUID
    name: str
    image: ImageData | None
    domain: str
    project: uuid.UUID
    resource_group: str
    resource_slots: ResourceSlot
    url: str
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
    created_at: datetime
    destroyed_at: datetime | None
    retries: int
    lifecycle_stage: EndpointLifecycle
    runtime_variant: RuntimeVariant
    extra_mounts: Sequence[VFolderMount]
    routings: Sequence[RoutingData] | None = None


@dataclass
class RoutingData:
    id: uuid.UUID
    endpoint: uuid.UUID
    session: uuid.UUID | None
    status: RouteStatus
    traffic_ratio: float
    created_at: datetime | None
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


@dataclass
class EndpointAutoScalingRuleListResult:
    """Search result with total count for endpoint auto scaling rules."""

    items: list[EndpointAutoScalingRuleData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class UserData:
    uuid: uuid.UUID
    email: str


@dataclass
class ScalingGroupData:
    wsproxy_addr: str
    wsproxy_api_token: str


@dataclass
class ModelServicePrepareCtx:
    model_id: uuid.UUID
    model_definition_path: str | None
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    owner_uuid: uuid.UUID
    owner_role: UserRole
    group_id: uuid.UUID
    resource_policy: dict[str, Any]
    scaling_group: str
    extra_mounts: Sequence[VFolderMount]


@dataclass
class MountOption:
    mount_destination: str | None
    type: MountTypes
    permission: MountPermission | None
    subpath: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "mount_destination": self.mount_destination,
            "type": self.type.value,
            "permission": self.permission.value if self.permission else None,
            "subpath": self.subpath if self.subpath else None,
        }
        return result


@dataclass
class RouteInfo:
    route_id: uuid.UUID
    session_id: uuid.UUID | None
    traffic_ratio: float


@dataclass
class RouteConnectionInfo:
    app: str
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
    scaling_group: str
    resources: dict[str, str | int] | None
    resource_opts: dict[str, str | int | bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "model_definition_path": self.model_definition_path,
            "model_mount_destination": self.model_mount_destination,
            "extra_mounts": {key: value.to_dict() for key, value in self.extra_mounts.items()},
            "environ": self.environ if self.environ is not None else {},
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
    model_definition_path: str | None
    replicas: int
    desired_session_count: int
    active_routes: list[RouteInfo]
    service_endpoint: HttpUrl | None
    is_public: bool
    runtime_variant: RuntimeVariant


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
    routings: Sequence[RoutingData] | None


@dataclass
class ServiceSearchResult:
    items: list[ServiceSearchItem]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class RequesterCtx:
    """Deprecated: Use UserData from ai.backend.common.data.user.types instead."""

    is_authorized: bool | None
    user_id: uuid.UUID
    user_role: UserRole
    domain_name: str


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
