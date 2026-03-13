from __future__ import annotations

import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class PushSessionEventsRequest(BaseRequestModel):
    """Query parameters for the session events SSE endpoint."""

    session_name: str = Field(
        default="*",
        validation_alias="sessionName",
    )
    owner_access_key: str | None = Field(
        default=None,
        validation_alias="ownerAccessKey",
    )
    session_id: uuid.UUID | None = Field(
        default=None,
        validation_alias="sessionId",
    )
    group_name: str = Field(
        default="*",
        validation_alias="groupName",
    )
    scope: str = Field(default="*")


class PushBackgroundTaskEventsRequest(BaseRequestModel):
    """Query parameters for the background task events SSE endpoint."""

    task_id: uuid.UUID = Field(validation_alias="taskId")
