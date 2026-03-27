"""Response DTOs for Login Session DTO v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import LoginSessionStatus

__all__ = (
    "AdminSearchLoginSessionsPayload",
    "LoginSessionNode",
    "MySearchLoginSessionsPayload",
    "RevokeLoginSessionPayload",
)


class LoginSessionNode(BaseResponseModel):
    """Node model representing a login session entry."""

    id: UUID = Field(description="Login session ID")
    user_id: UUID = Field(description="UUID of the user who owns the session")
    access_key: str = Field(description="Access key associated with the session")
    status: LoginSessionStatus = Field(description="Current status of the login session")
    created_at: datetime = Field(description="Timestamp when the session was created")
    last_accessed_at: datetime | None = Field(
        default=None, description="Timestamp when the session was last accessed"
    )
    invalidated_at: datetime | None = Field(
        default=None, description="Timestamp when the session was invalidated"
    )


class AdminSearchLoginSessionsPayload(BaseResponseModel):
    """Payload for login session search result (admin)."""

    items: list[LoginSessionNode] = Field(description="Login session list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class MySearchLoginSessionsPayload(BaseResponseModel):
    """Payload for login session search result (current user)."""

    items: list[LoginSessionNode] = Field(description="Login session list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class RevokeLoginSessionPayload(BaseResponseModel):
    """Payload for login session revocation result."""

    success: bool = Field(description="Whether the revocation was successful")
