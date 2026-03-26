"""
Request DTOs for scaling group DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel

from .types import PreemptionMode, PreemptionOrder, SchedulerType

__all__ = (
    "PreemptionConfigInput",
    "UpdateScalingGroupInput",
)


class PreemptionConfigInput(BaseRequestModel):
    """Input for preemption configuration."""

    preemptible_priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Priority of preemptible sessions (1=lowest, 10=highest). Default is 5.",
    )
    order: PreemptionOrder = Field(
        default=PreemptionOrder.OLDEST,
        description="Order in which sessions are selected for preemption.",
    )
    mode: PreemptionMode = Field(
        default=PreemptionMode.TERMINATE,
        description="Preemption mode (terminate or reschedule).",
    )


class UpdateScalingGroupInput(BaseRequestModel):
    """Input for updating a scaling group. All fields optional for partial update."""

    is_active: bool | None = Field(
        default=None,
        description="Whether the scaling group is active. Leave null to keep existing value.",
    )
    is_public: bool | None = Field(
        default=None,
        description="Whether the scaling group is public. Leave null to keep existing value.",
    )
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Human-readable description. Use SENTINEL to clear, null to keep existing value."
        ),
    )
    wsproxy_addr: str | Sentinel | None = Field(
        default=SENTINEL,
        description="WebSocket proxy address. Use SENTINEL to clear, null to keep existing value.",
    )
    wsproxy_api_token: str | Sentinel | None = Field(
        default=SENTINEL,
        description="WebSocket proxy API token. Use SENTINEL to clear, null to keep existing value.",
    )
    use_host_network: bool | None = Field(
        default=None,
        description="Whether to use host network mode. Leave null to keep existing value.",
    )
    scheduler: SchedulerType | None = Field(
        default=None,
        description="Scheduler type. Leave null to keep existing value.",
    )
    preemption_config: PreemptionConfigInput | None = Field(
        default=None,
        description=(
            "Preemption configuration. When provided, replaces the entire preemption config. "
            "Leave null to keep existing value."
        ),
    )
