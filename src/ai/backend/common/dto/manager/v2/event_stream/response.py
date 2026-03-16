"""
Response DTOs for Event Stream domain (v2).

These Node models represent the JSON payloads embedded in the ``data`` field
of Server-Sent Events produced by the session and background task SSE endpoints.

Unlike the v1 models, these use canonical snake_case field names with no camelCase aliases.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "BgtaskCancelledNode",
    "BgtaskDoneNode",
    "BgtaskFailedNode",
    "BgtaskPartialSuccessNode",
    "BgtaskUpdatedNode",
    "SessionEventNode",
    "SessionKernelEventNode",
)


class SessionEventNode(BaseResponseModel):
    """Node model for session lifecycle SSE events.

    Emitted for events such as ``session_enqueued``, ``session_success``,
    ``session_terminated``, ``session_failure``, etc.
    """

    reason: str = Field(default="", description="Reason for the session event")
    session_name: str = Field(default="", description="Session name")
    owner_access_key: str = Field(default="", description="Access key of the session owner")
    session_id: str = Field(default="", description="Session ID")
    exit_code: int | None = Field(default=None, description="Exit code of the session process")


class SessionKernelEventNode(SessionEventNode):
    """Node model for kernel lifecycle SSE events.

    Extends :class:`SessionEventNode` with kernel-specific fields.
    Emitted for events such as ``kernel_started``, ``kernel_terminated``, etc.
    """

    kernel_id: str = Field(default="", description="Kernel ID")
    cluster_role: str = Field(default="main", description="Cluster role of the kernel")
    cluster_idx: int = Field(default=0, description="Cluster index of the kernel")


class BgtaskUpdatedNode(BaseResponseModel):
    """Node model for bgtask_updated SSE event."""

    task_id: str = Field(description="Background task ID")
    message: str = Field(description="Status message")
    current_progress: float = Field(description="Current progress value")
    total_progress: float = Field(description="Total progress value")


class BgtaskDoneNode(BaseResponseModel):
    """Node model for bgtask_done SSE event."""

    task_id: str = Field(description="Background task ID")
    message: str = Field(description="Completion message")


class BgtaskPartialSuccessNode(BaseResponseModel):
    """Node model for bgtask_done SSE event with partial success (includes errors)."""

    task_id: str = Field(description="Background task ID")
    message: str = Field(description="Completion message")
    errors: list[str] = Field(description="List of error messages from partial failures")


class BgtaskCancelledNode(BaseResponseModel):
    """Node model for bgtask_cancelled SSE event."""

    task_id: str = Field(description="Background task ID")
    message: str = Field(description="Cancellation message")


class BgtaskFailedNode(BaseResponseModel):
    """Node model for bgtask_failed SSE event."""

    task_id: str = Field(description="Background task ID")
    message: str = Field(description="Failure message")
