"""
Response DTOs for login session management.
Used by Manager REST API endpoints.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "LoginSessionItemResponse",
    "ListLoginSessionsResponse",
)


class LoginSessionItemResponse(BaseResponseModel):
    """A single login session entry."""

    id: str = Field(description="Unique identifier of the login session")
    session_token: str = Field(description="Opaque token identifying this session")
    client_ip: str | None = Field(
        default=None,
        description="IP address of the client that created this session",
    )
    created_at: datetime = Field(description="Timestamp when the session was created")
    expired_at: datetime | None = Field(
        default=None,
        description="Timestamp when the session expires; None if it does not expire",
    )
    reason: str | None = Field(
        default=None,
        description="Human-readable reason for the session state (e.g., revocation reason)",
    )


class ListLoginSessionsResponse(BaseResponseModel):
    """Response containing a list of login sessions for the current user."""

    items: list[LoginSessionItemResponse] = Field(
        description="List of active login sessions",
    )
