import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, Self, Sequence, override

from pydantic import AnyUrl, BaseModel, Field, HttpUrl

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
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.types import ModelRevisionSpec
from ai.backend.manager.data.image.types import ImageIdentifier
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

    def ovrride_model_revision(self, model_revision: ModelRevisionSpec) -> ModelRevisionSpec:
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
