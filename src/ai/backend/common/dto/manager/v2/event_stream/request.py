"""
Request DTOs for event_stream DTO v2.
"""

from __future__ import annotations

import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

from .types import SessionEventScope

__all__ = (
    "BackgroundTaskEventSubscribeInput",
    "SessionEventSubscribeInput",
)


class SessionEventSubscribeInput(BaseRequestModel):
    """Input for subscribing to session SSE events."""

    session_name: str = Field(
        default="*",
        description="Session name filter; '*' means all sessions",
    )
    owner_access_key: str | None = Field(
        default=None,
        description="Owner access key filter",
    )
    session_id: uuid.UUID | None = Field(
        default=None,
        description="Specific session UUID to subscribe to",
    )
    group_name: str = Field(
        default="*",
        description="Group name filter; '*' means all groups",
    )
    scope: SessionEventScope | str = Field(
        default="*",
        description="Event scope; '*' means all scopes",
    )


class BackgroundTaskEventSubscribeInput(BaseRequestModel):
    """Input for subscribing to background task SSE events."""

    task_id: uuid.UUID = Field(
        description="Background task UUID to subscribe to",
    )
