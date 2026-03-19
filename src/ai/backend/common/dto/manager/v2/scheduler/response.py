"""
Response DTOs for scheduler subscription v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("SchedulingBroadcastEventPayloadNode",)


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
