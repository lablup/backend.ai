from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from ai.backend.common.types import AgentSelectionStrategy, SessionTypes


@dataclass
class ScalingGroupStatus:
    """Status information for a scaling group."""

    is_active: bool
    is_public: bool


@dataclass
class ScalingGroupMetadata:
    """Metadata for a scaling group."""

    description: str
    created_at: datetime


@dataclass
class ScalingGroupNetworkConfig:
    """Network configuration for a scaling group."""

    wsproxy_addr: str
    wsproxy_api_token: str
    use_host_network: bool


@dataclass
class ScalingGroupDriverConfig:
    """Driver configuration for a scaling group."""

    name: str
    options: Mapping[str, Any]


@dataclass
class ScalingGroupSchedulerOptions:
    """Scheduler options for a scaling group."""

    allowed_session_types: list[SessionTypes]
    pending_timeout: timedelta
    config: Mapping[str, Any]
    agent_selection_strategy: AgentSelectionStrategy
    agent_selector_config: Mapping[str, Any]
    enforce_spreading_endpoint_replica: bool
    allow_fractional_resource_fragmentation: bool
    route_cleanup_target_statuses: list[str]


@dataclass
class ScalingGroupSchedulerConfig:
    """Scheduler configuration for a scaling group."""

    name: str
    options: ScalingGroupSchedulerOptions


@dataclass
class ScalingGroupData:
    name: str
    status: ScalingGroupStatus
    metadata: ScalingGroupMetadata
    wsproxy: ScalingGroupNetworkConfig
    driver: ScalingGroupDriverConfig
    scheduler: ScalingGroupSchedulerConfig


@dataclass
class ScalingGroupListResult:
    """Result of searching scaling groups."""

    items: list[ScalingGroupData]
    total_count: int
