from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel


class ManagerStatusResponse(BaseResponseModel):
    """Response containing manager status information."""

    nodes: list[Any] = Field(description="List of manager node info")
    status: str = Field(description="Current manager status")
    active_sessions: int | None = Field(description="Number of active sessions")


class AnnouncementResponse(BaseResponseModel):
    """Response containing announcement info."""

    enabled: bool = Field(description="Whether announcement is enabled")
    message: str = Field(description="Announcement message")
