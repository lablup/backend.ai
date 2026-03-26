"""
Response DTOs for scaling group DTO v2.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import PreemptionMode, PreemptionOrder, SchedulerType

__all__ = (
    "PreemptionConfigInfo",
    "ScalingGroupMetadataInfo",
    "ScalingGroupNetworkInfo",
    "ScalingGroupNode",
    "ScalingGroupSchedulerInfo",
    "ScalingGroupStatusInfo",
    "UpdateScalingGroupPayload",
)


class ScalingGroupStatusInfo(BaseResponseModel):
    """Status information for a scaling group."""

    is_active: bool = Field(
        description="Whether the scaling group is active and can accept new sessions."
    )
    is_public: bool = Field(
        description="Whether the scaling group is publicly accessible to all users."
    )


class ScalingGroupMetadataInfo(BaseResponseModel):
    """Metadata for a scaling group."""

    description: str | None = Field(
        default=None,
        description="Human-readable description of the scaling group.",
    )
    created_at: datetime = Field(
        description="Timestamp when the scaling group was created.",
    )


class ScalingGroupNetworkInfo(BaseResponseModel):
    """Network configuration for a scaling group."""

    wsproxy_addr: str | None = Field(
        default=None,
        description="WebSocket proxy address for this scaling group.",
    )
    use_host_network: bool = Field(
        description="Whether to use host network mode for containers in this scaling group.",
    )


class PreemptionConfigInfo(BaseResponseModel):
    """Preemption configuration for a scaling group."""

    preemptible_priority: int = Field(
        description="Priority of preemptible sessions (1=lowest, 10=highest).",
    )
    order: PreemptionOrder = Field(
        description="Tie-breaking order for sessions with the same priority during preemption.",
    )
    mode: PreemptionMode = Field(
        description="How to preempt a session when preemption is triggered.",
    )


class ScalingGroupSchedulerInfo(BaseResponseModel):
    """Scheduler configuration for a scaling group."""

    type: SchedulerType = Field(
        description="Type of scheduler used for session scheduling.",
    )
    preemption: PreemptionConfigInfo = Field(
        description="Preemption configuration for this scaling group.",
    )


class ScalingGroupNode(BaseResponseModel):
    """Node model representing a scaling group entity."""

    name: str = Field(description="Unique name identifying the scaling group.")
    status: ScalingGroupStatusInfo = Field(
        description="Status information including active and public flags.",
    )
    metadata: ScalingGroupMetadataInfo = Field(
        description="Metadata including description and creation timestamp.",
    )
    network: ScalingGroupNetworkInfo = Field(
        description="Network configuration for the scaling group.",
    )
    scheduler: ScalingGroupSchedulerInfo = Field(
        description="Scheduler configuration for the scaling group.",
    )


class UpdateScalingGroupPayload(BaseResponseModel):
    """Payload for scaling group update mutation result."""

    scaling_group: ScalingGroupNode = Field(description="Updated scaling group.")
