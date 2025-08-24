from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import yarl

from ai.backend.common.types import RuntimeVariant, VFolderMount
from ai.backend.manager.models.endpoint import EndpointLifecycle


@dataclass
class DeploymentMetadata:
    name: str
    domain: str
    project: UUID
    resource_group: str
    created_user: UUID
    session_owner: UUID
    lifecycle_stage: EndpointLifecycle
    retries: int
    created_at: Optional[datetime]
    tag: Optional[str] = None


@dataclass
class MountMetadata:
    model_vfolder_id: UUID
    model_definition_path: str = "/models"
    extra_mounts: list[VFolderMount] = field(default_factory=list)


@dataclass
class ReplicaSpec:
    replica_count: int


@dataclass
class ResourceSpec:
    replicas: int
    cluster_mode: str
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
    image: UUID
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
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revisions: list[ModelRevisionSpec]
