from __future__ import annotations

import enum
from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class SchedulerOps(enum.Enum):
    INCLUDE_AGENTS = "include-agents"
    EXCLUDE_AGENTS = "exclude-agents"


class UpdateManagerStatusRequest(BaseRequestModel):
    """Request body for updating manager status."""

    status: str = Field(description="New manager status")
    force_kill: bool = Field(default=False, description="Force kill running sessions")


class UpdateAnnouncementRequest(BaseRequestModel):
    """Request body for updating announcement."""

    enabled: bool = Field(default=False, description="Whether announcement is enabled")
    message: str | None = Field(default=None, description="Announcement message text")


class SchedulerOpsRequest(BaseRequestModel):
    """Request body for scheduler operations."""

    op: str = Field(description="Scheduler operation type")
    args: Any = Field(description="Operation arguments")
