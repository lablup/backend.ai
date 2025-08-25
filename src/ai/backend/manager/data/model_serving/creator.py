import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional, override

import yarl
from pydantic import AnyUrl, HttpUrl

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    MountPermission,
    MountTypes,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.data.user.types import UserRole
from ai.backend.manager.types import Creator


@dataclass
class EndpointCreator(Creator):
    name: str
    model_definition_path: Optional[str]
    created_user: uuid.UUID
    session_owner: uuid.UUID
    image: uuid.UUID  # Image row ID
    model: uuid.UUID  # vfolder row ID
    domain: str
    project: uuid.UUID
    resource_group: str  # Resource group row ID which is the name
    resource_slots: Mapping[str, Any]
    replicas: int = 0
    lifecycle_stage: EndpointLifecycle = EndpointLifecycle.CREATED
    tag: Optional[str] = None
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None
    callback_url: Optional[yarl.URL] = None
    environ: Optional[dict[str, str]] = None
    open_to_public: bool = False
    runtime_variant: RuntimeVariant = RuntimeVariant.CUSTOM
    model_mount_destination: str = "/models"
    url: Optional[str] = None
    resource_opts: Optional[dict[str, Any]] = None
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    cluster_size: int = 1
    extra_mounts: list[VFolderMount] = field(default_factory=list)
    retries: int = 0

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "model_definition_path": self.model_definition_path,
            "created_user": self.created_user,
            "session_owner": self.session_owner,
            "image": self.image,
            "model": self.model,
            "domain": self.domain,
            "project": self.project,
            "resource_group": self.resource_group,
            "resource_slots": self.resource_slots,
            "replicas": self.replicas,
            "lifecycle_stage": self.lifecycle_stage,
            "tag": self.tag,
            "startup_command": self.startup_command,
            "bootstrap_script": self.bootstrap_script,
            "callback_url": self.callback_url,
            "environ": self.environ,
            "open_to_public": self.open_to_public,
            "runtime_variant": self.runtime_variant,
            "model_mount_destination": self.model_mount_destination,
            "url": self.url,
            "resource_opts": self.resource_opts,
            "cluster_mode": self.cluster_mode,
            "cluster_size": self.cluster_size,
            "extra_mounts": self.extra_mounts,
        }


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
    extra_mounts: list[VFolderMount]


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
    session_id: Optional[uuid.UUID]
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
    extra_mounts: list[uuid.UUID]
    name: str
    model_definition_path: Optional[str]
    replicas: int
    desired_session_count: int
    active_routes: list[RouteInfo]
    service_endpoint: Optional[HttpUrl]
    is_public: bool
    runtime_variant: RuntimeVariant


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
