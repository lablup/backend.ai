from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional, Self, Sequence

import yarl

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.data.deployment.types import EndpointLifecycle, RouteStatus
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.user import UserRow

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

    @classmethod
    def from_row(cls, row: UserRow) -> Self:
        return cls(
            uuid=row.uuid,
            email=row.email,
        )


@dataclass
class ScalingGroupData:
    wsproxy_addr: str
    wsproxy_api_token: str
