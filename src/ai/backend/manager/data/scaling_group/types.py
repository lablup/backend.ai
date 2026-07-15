from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import ConfigDict, Field, field_serializer, field_validator

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    AgentSelectionStrategy,
    BackendAISchema,
    PreemptionMode,
    PreemptionOrder,
    ResourceSlot,
    SessionTypes,
    SlotQuantity,
)

if TYPE_CHECKING:
    from ai.backend.manager.data.deployment.types import DeploymentOptions
    from ai.backend.manager.data.session.options import DefaultSessionOptions


class SchedulerType(StrEnum):
    """Scheduler type for session scheduling."""

    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"
    FAIR_SHARE = "fair-share"


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


@dataclass(frozen=True)
class PreemptionConfig:
    """Preemption configuration for a scaling group."""

    enabled: bool = False
    preemptible_priority: int = 5
    order: PreemptionOrder = PreemptionOrder.OLDEST
    mode: PreemptionMode = PreemptionMode.TERMINATE
    preemption_min_runtime: timedelta = timedelta(seconds=0)


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
    preemption: PreemptionConfig = dataclasses.field(default_factory=PreemptionConfig)

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
            "preemption": {
                "enabled": self.preemption.enabled,
                "preemptible_priority": self.preemption.preemptible_priority,
                "order": self.preemption.order.value,
                "mode": self.preemption.mode.value,
                "preemption_min_runtime": self.preemption.preemption_min_runtime.total_seconds(),
            },
        }


@dataclass
class ScalingGroupSchedulerConfig:
    """Scheduler configuration for a scaling group."""

    name: SchedulerType
    options: ScalingGroupSchedulerOptions


class FairShareScalingGroupSpec(BackendAISchema):
    """Fair Share calculation configuration for a Resource Group.

    Used for Fair Share metric calculation regardless of the scheduler type.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    half_life_days: int = 7
    """Half-life for exponential decay in days."""

    lookback_days: int = 28
    """Total lookback period in days for usage aggregation."""

    decay_unit_days: int = 1
    """Granularity of decay buckets in days."""

    default_weight: Decimal = Decimal("1.0")
    """Default weight for entities without explicit weight in this scaling group."""

    resource_weights: ResourceSlot = Field(default_factory=ResourceSlot)
    """Weights for each resource type when calculating normalized usage.

    If a resource type is not specified, default weight (1.0) is used.
    Example: ResourceSlot({"cpu": 1.0, "mem": 0.001, "cuda.device": 10.0})
    """

    @field_serializer("resource_weights", mode="plain")
    def serialize_resource_weights(self, value: ResourceSlot) -> dict[str, Any]:
        """Serialize ResourceSlot to dict for JSON compatibility."""
        return {k: str(v) for k, v in value.items()}

    @field_validator("resource_weights", mode="before")
    @classmethod
    def validate_resource_weights(cls, value: Any) -> ResourceSlot:
        """Deserialize dict to ResourceSlot.

        Converts string values to Decimal to avoid BinarySize parsing issues.
        """
        if isinstance(value, ResourceSlot):
            return value
        if isinstance(value, dict):
            # Convert string values to Decimal to bypass BinarySize parsing
            converted = {k: Decimal(v) if isinstance(v, str) else v for k, v in value.items()}
            return ResourceSlot(converted)
        return ResourceSlot()


@dataclass
class ScalingGroupData:
    id: ResourceGroupID
    name: str
    status: ScalingGroupStatus
    metadata: ScalingGroupMetadata
    network: ScalingGroupNetworkConfig
    driver: ScalingGroupDriverConfig
    scheduler: ScalingGroupSchedulerConfig
    fair_share_spec: FairShareScalingGroupSpec
    default_deployment_options: DeploymentOptions
    default_session_options: DefaultSessionOptions


@dataclass
class ScalingGroupListResult:
    """Result of searching scaling groups."""

    items: list[ScalingGroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class ResourceInfo:
    """Resource information for a scaling group.

    Provides aggregated resource metrics:
    - capacity: Sum of available_slots from ALIVE, schedulable agents
    - used: Sum of occupied_slots from kernels in RUNNING/TERMINATING status
    - free: capacity - used
    """

    capacity: list[SlotQuantity]
    """Total available resources from ALIVE, schedulable agents."""

    used: list[SlotQuantity]
    """Currently occupied resources from active kernels."""

    free: list[SlotQuantity]
    """Available resources (capacity - used)."""
