"""
Response DTOs for Event Stream domain.

These models represent the JSON payloads embedded in the ``data`` field
of Server-Sent Events produced by the ``/events/session`` endpoint.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = (
    "SessionEventPayload",
    "SessionKernelEventPayload",
)


class SessionEventPayload(BaseModel):
    """Payload for session lifecycle SSE events.

    Emitted for events such as ``session_enqueued``, ``session_success``,
    ``session_terminated``, ``session_failure``, etc.
    """

    model_config = ConfigDict(extra="allow")

    reason: str = Field(default="")
    session_name: str = Field(
        default="",
        alias="sessionName",
    )
    owner_access_key: str = Field(
        default="",
        alias="ownerAccessKey",
    )
    session_id: str = Field(
        default="",
        alias="sessionId",
    )
    exit_code: int | None = Field(
        default=None,
        alias="exitCode",
    )


class SessionKernelEventPayload(SessionEventPayload):
    """Payload for kernel lifecycle SSE events.

    Extends :class:`SessionEventPayload` with kernel-specific fields.
    Emitted for events such as ``kernel_started``, ``kernel_terminated``, etc.
    """

    kernel_id: str = Field(
        default="",
        alias="kernelId",
    )
    cluster_role: str = Field(
        default="main",
        alias="clusterRole",
    )
    cluster_idx: int = Field(
        default=0,
        alias="clusterIdx",
    )
