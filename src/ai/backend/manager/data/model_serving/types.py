from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

import yarl
from pydantic import BaseModel, Field, HttpUrl

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
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.types import (
    EndpointLifecycle,
    ModelRevisionSpec,
    RouteStatus,
)
from ai.backend.manager.data.image.types import ImageData, ImageIdentifier
from ai.backend.manager.data.user.types import UserRole

# Re-export for backward compatibility
__all__ = [
    "EndpointLifecycle",
    "RouteStatus",
    "EndpointData",
    "RoutingData",
    "EndpointTokenData",
    "EndpointAutoScalingRuleData",
]


@dataclass
class EndpointData:
    id: uuid.UUID
    name: str
    image: Optional[ImageData]
    domain: str
    project: uuid.UUID
    resource_group: str
    resource_slots: ResourceSlot
    url: str
    model: uuid.UUID
    model_definition_path: Optional[str]
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
    resource_opts: Optional[Mapping[str, Any]]
    replicas: int
    cluster_mode: ClusterMode
    cluster_size: int
    open_to_public: bool
    created_at: datetime
    destroyed_at: Optional[datetime]
    retries: int
    lifecycle_stage: EndpointLifecycle
    runtime_variant: RuntimeVariant
    extra_mounts: Sequence[VFolderMount]
    routings: Optional[Sequence["RoutingData"]] = None


@dataclass
class RoutingData:
    id: uuid.UUID
    endpoint: uuid.UUID
    session: Optional[uuid.UUID]
    status: RouteStatus
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
    session_id: Optional[uuid.UUID]
    traffic_ratio: float


@dataclass
class RouteConnectionInfo:
    app: str
    kernel_host: str
    kernel_port: int


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
class RuntimeVariantData:
    name: str
    human_readable_name: str


class ImageEnvironment(BaseModel):
    image: str = Field(
        description="""
        Container image to use for the model service.
        """,
        examples=[
            "myregistry/myimage:latest",
        ],
    )
    architecture: str = Field(
        description="""
        Architecture of the container image.
        """,
        examples=[
            "x86_64",
            "arm64",
        ],
    )


class ModelServiceDefinition(BaseModel):
    environment: Optional[ImageEnvironment] = Field(
        default=None,
        description="""
        Environment in which the model service will run.
        """,
        examples=[
            {
                "image": "myregistry/myimage:latest",
                "architecture": "x86_64",
            }
        ],
    )
    resource_slots: Optional[dict[str, Any]] = Field(
        default=None,
        description="""
        Resource slots used by the model service session.
        """,
        examples=[
            {"cpu": 1, "mem": "2gb"},
        ],
    )
    environ: Optional[dict[str, str]] = Field(
        default=None,
        description="""
        Environment variables to set for the model service.
        """,
        examples=[
            {"MY_ENV_VAR": "value", "ANOTHER_VAR": "another_value"},
        ],
    )

    def override_model_revision(self, model_revision: ModelRevisionSpec) -> ModelRevisionSpec:
        """Override model revision configuration with model service definition values."""
        if self.resource_slots:
            model_revision.resource_spec.resource_slots = self.resource_slots
        if self.environment:
            model_revision.image_identifier = ImageIdentifier(
                canonical=self.environment.image, architecture=self.environment.architecture
            )
        if self.environ:
            if model_revision.execution.environ:
                model_revision.execution.environ.update(self.environ)
            else:
                model_revision.execution.environ = self.environ

        return model_revision

    def override_creator(self, creator: DeploymentCreator) -> DeploymentCreator:
        """Override deployment creator configuration with model service definition values."""
        # Override resource slots if specified
        if self.resource_slots:
            creator.model_revision.resource_spec.resource_slots = self.resource_slots
        if self.environment:
            creator.model_revision.image_identifier = ImageIdentifier(
                canonical=self.environment.image, architecture=self.environment.architecture
            )
        if self.environ:
            if creator.model_revision.execution.environ:
                creator.model_revision.execution.environ.update(self.environ)
            else:
                creator.model_revision.execution.environ = self.environ

        return creator
