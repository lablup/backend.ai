"""
Response DTOs for background task v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("BackgroundTaskEventPayloadNode",)


class BgtaskEventTypeDTO(StrEnum):
    """Event type for background task events."""

    UPDATED = "UPDATED"
    DONE = "DONE"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class BackgroundTaskEventPayloadNode(BaseResponseModel):
    """Payload for background task subscription events."""

    task_id: str = Field(description="UUID of the background task.")
    event_type: BgtaskEventTypeDTO = Field(description="Type of the background task event.")
    message: str = Field(description="Human-readable message for this event.")
    current_progress: float | None = Field(
        default=None,
        description="Current progress value. Only populated for UPDATED events.",
    )
    total_progress: float | None = Field(
        default=None,
        description="Total progress value. Only populated for UPDATED events.",
    )
