"""Types for replica controller."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from ai.backend.common.types import (
    ClusterMode,
    ImageAlias,
    ResourceSlot,
    SessionTypes,
    VFolderMount,
)

from ..types import NetworkConfig, ReplicaStatus


@dataclass(frozen=True)
class ReplicaSpec:
    """Specification for creating replicas (sessions)."""

    endpoint_id: UUID
    image: ImageAlias
    resources: ResourceSlot
    network_config: NetworkConfig
    mounts: list[VFolderMount]
    environ: dict[str, str]
    scaling_group: str
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    cluster_size: int = 1
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None


@dataclass(frozen=True)
class SessionEnqueueSpec:
    """Detailed specification for session enqueue operation."""

    endpoint_id: UUID
    session_name: str
    session_type: SessionTypes
    image: ImageAlias
    resources: ResourceSlot
    mounts: list[VFolderMount]
    environ: dict[str, str]
    scaling_group: str
    cluster_mode: ClusterMode
    cluster_size: int
    network_config: NetworkConfig
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None
    tag: Optional[str] = None


@dataclass(frozen=True)
class ReplicaData:
    """Data representing a replica (session) in deployment."""

    id: UUID
    endpoint_id: UUID
    session_id: UUID
    route_id: Optional[UUID]
    status: ReplicaStatus
    created_at: datetime
    updated_at: datetime
    agent_id: Optional[str] = None
    container_id: Optional[str] = None
