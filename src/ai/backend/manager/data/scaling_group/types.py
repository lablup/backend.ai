from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from ai.backend.common.types import AgentSelectionStrategy, SessionTypes


class SchedulerType(StrEnum):
    """Scheduler type for session scheduling."""

    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"


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

    def to_json(self) -> dict[str, Any]:
        """Convert scheduler options to JSON-serializable dict."""
        return {
            "allowed_session_types": [st.value for st in self.allowed_session_types],
            "pending_timeout": self.pending_timeout.total_seconds(),
            "config": dict(self.config),
            "agent_selection_strategy": self.agent_selection_strategy.value,
            "agent_selector_config": dict(self.agent_selector_config),
            "enforce_spreading_endpoint_replica": self.enforce_spreading_endpoint_replica,
            "allow_fractional_resource_fragmentation": self.allow_fractional_resource_fragmentation,
            "route_cleanup_target_statuses": self.route_cleanup_target_statuses,
        }


@dataclass
class ScalingGroupSchedulerConfig:
    """Scheduler configuration for a scaling group."""

    name: SchedulerType
    options: ScalingGroupSchedulerOptions


@dataclass
class ScalingGroupData:
    name: str
    status: ScalingGroupStatus
    metadata: ScalingGroupMetadata
    network: ScalingGroupNetworkConfig
    driver: ScalingGroupDriverConfig
    scheduler: ScalingGroupSchedulerConfig


@dataclass
class ScalingGroupListResult:
    """Result of searching scaling groups."""

    items: list[ScalingGroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
