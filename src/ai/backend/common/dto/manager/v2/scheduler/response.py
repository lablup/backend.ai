"""
Response DTOs for scheduler subscription v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInfo

__all__ = (
    "ComputeScheduleKernelResultInfo",
    "ComputeSchedulePayload",
    "SchedulingBroadcastEventPayloadNode",
    "UnschedulableReasonHintInfo",
)


class SchedulingStatusDTO(StrEnum):
    """Scheduling status transitions for session lifecycle."""

    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    PREPARING = "PREPARING"
    PULLING = "PULLING"
    PREPARED = "PREPARED"
    CREATING = "CREATING"
    RUNNING = "RUNNING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class SchedulingBroadcastEventPayloadNode(BaseResponseModel):
    """Payload for scheduling broadcast subscription events."""

    session_id: str = Field(description="UUID of the session being scheduled.")
    status_transition: SchedulingStatusDTO = Field(
        description="Status transition that occurred during session scheduling."
    )
    reason: str = Field(description="Human-readable reason for this status transition.")


class UnschedulableReasonHintInfo(BaseResponseModel):
    """What the caller could change so an unschedulable kernel would fit.

    Populated only when the kernel's ``success`` is False. Surfaces
    the user-actionable subset of the selector's remediation hint.
    """

    required_reduction: list[ResourceSlotEntryInfo] | None = Field(
        default=None,
        description="Subtract these slots to fit the best-fitting node.",
    )


class ComputeScheduleKernelResultInfo(BaseResponseModel):
    """Compute-schedule outcome for a single kernel.

    Results correspond positionally to the requested kernels: the caller
    matches each result to its input by list index. ``reason_hint`` is
    populated only when ``success`` is False.
    """

    requested_slots: list[ResourceSlotEntryInfo] = Field(
        description="Resource slots resolved for this kernel after applying defaults.",
    )
    requested_architecture: str = Field(
        description="Architecture resolved for this kernel.",
    )
    success: bool = Field(
        description="Whether this kernel could be scheduled onto a target node.",
    )
    reason_hint: UnschedulableReasonHintInfo | None = Field(
        default=None,
        description="What to change so the kernel would fit. Null when success is True.",
    )


class ComputeSchedulePayload(BaseResponseModel):
    """Result of a compute-schedule request."""

    results: list[ComputeScheduleKernelResultInfo] = Field(
        description="Per-kernel compute-schedule outcomes, correlated to the request by list index.",
    )
