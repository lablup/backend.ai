from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from ai.backend.common.data.model_deployment.types import (
    LivenessStatus,
    ModelDeploymentStatus,
    ReadinessStatus,
)
from ai.backend.common.types import (
    AutoScalingMetricSource,
    ClusterMode,
    RuntimeVariant,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    ModelRevisionSpec,
    ReplicaSpec,
)


@dataclass
class ModelDeploymentMetadata:
    name: str
    status: ModelDeploymentStatus
    tags: list[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


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
class ModelDeploymentNetworkAccessData:
    endpoint_url: str
    preferred_domain_name: Optional[str] = None
    open_to_public: bool = False
    access_tokens: list[ModelDeploymentAccessTokenData] = field(default_factory=list)


@dataclass
class ClusterConfig:
    mode: ClusterMode
    size: int


@dataclass
class ResourceConfig:
    resource_slots: Mapping[str, Any]
    resource_opts: Optional[Mapping[str, Any]] = None


@dataclass
class ModelRuntimeConfig:
    runtime_variant: RuntimeVariant
    inference_runtime_config: Optional[Mapping[str, Any]] = None
    environ: Optional[dict[str, str]] = None


@dataclass
class ModelRevisionData:
    id: UUID
    name: str
    cluster_config: ClusterConfig
    resource_config: ResourceConfig
    runtime_config: ModelRuntimeConfig


@dataclass
class ModelReplicaData:
    id: UUID
    revision: ModelRevisionSpec
    session_id: Optional[UUID]
    readiness_status: ReadinessStatus
    liveness_status: LivenessStatus
    weight: int
    detail: str
    created_at: datetime
    live_stat: str


@dataclass
class ModelDeploymentData:
    id: UUID
    metadata: DeploymentMetadata
    state: DeploymentState
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revisions: list[ModelRevisionSpec]
