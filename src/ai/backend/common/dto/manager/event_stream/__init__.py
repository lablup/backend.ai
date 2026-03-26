"""
Event Stream DTOs for Manager API.

Covers SSE event parameters and payloads for session lifecycle
and background task progress events from the ``/events`` endpoints.
"""

from ai.backend.common.dto.manager.streaming.types import (
    BackgroundTaskEventParams,
    BgtaskCancelledPayload,
    BgtaskDonePayload,
    BgtaskFailedPayload,
    BgtaskPartialSuccessPayload,
    BgtaskSSEEventName,
    BgtaskUpdatedPayload,
    SessionEventParams,
    SessionEventScope,
)

from .response import (
    SessionEventPayload,
    SessionKernelEventPayload,
)

__all__ = (
    # Enums
    "BgtaskSSEEventName",
    "SessionEventScope",
    # SSE event params
    "BackgroundTaskEventParams",
    "SessionEventParams",
    # SSE event payloads — background task
    "BgtaskCancelledPayload",
    "BgtaskDonePayload",
    "BgtaskFailedPayload",
    "BgtaskPartialSuccessPayload",
    "BgtaskUpdatedPayload",
    # SSE event payloads — session
    "SessionEventPayload",
    "SessionKernelEventPayload",
)
