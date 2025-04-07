import uuid
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from pydantic import HttpUrl

from ai.backend.common.types import (
    AccessKey,
    MountPermission,
    MountTypes,
    RuntimeVariant,
    VFolderMount,
)
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
