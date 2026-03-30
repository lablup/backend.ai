"""Response DTOs for Login History DTO v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import LoginAttemptResult

__all__ = (
    "AdminSearchLoginHistoryPayload",
    "LoginHistoryNode",
    "MySearchLoginHistoryPayload",
)


class LoginHistoryNode(BaseResponseModel):
    """Node model representing a login history entry."""

    id: UUID = Field(description="Login history entry ID")
    user_id: UUID = Field(description="UUID of the user who attempted to log in")
    domain_name: str = Field(description="Domain name of the user at the time of the attempt")
    result: LoginAttemptResult = Field(description="Result of the login attempt")
    fail_reason: str | None = Field(
        default=None, description="Detailed reason for the login failure"
    )
    created_at: datetime = Field(description="Timestamp when the login attempt occurred")


class AdminSearchLoginHistoryPayload(BaseResponseModel):
    """Payload for login history search result (admin)."""

    items: list[LoginHistoryNode] = Field(description="Login history list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class MySearchLoginHistoryPayload(BaseResponseModel):
    """Payload for login history search result (current user)."""

    items: list[LoginHistoryNode] = Field(description="Login history list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")
