"""Endpoint types for deployment repository."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from ai.backend.common.types import (
    ResourceSlot,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle


@dataclass(frozen=True)
class EndpointConfig:
    """Configuration for an endpoint."""

    image: str
    architecture: str
    resources: ResourceSlot
    environ: dict[str, str]
    mounts: list[VFolderMount]
    scaling_group: str
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None


@dataclass(frozen=True)
class EndpointData:
    """Data representing an endpoint."""

    id: UUID
    name: str
    model_id: UUID
    replicas: int
    desired_replicas: int
    lifecycle_stage: EndpointLifecycle
    runtime_variant: RuntimeVariant
    config: EndpointConfig
    created_at: datetime
    updated_at: datetime
    owner_id: UUID
    domain_id: UUID
    project_id: UUID
    is_public: bool = False
    url: Optional[str] = None
    error_data: Optional[dict[str, str]] = None
