"""
Request DTOs for login session management.
Used by Manager REST API endpoints.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "RevokeLoginSessionRequest",
    "UpdateLoginSecurityPolicyRequest",
)


class RevokeLoginSessionRequest(BaseRequestModel):
    """Request to revoke a specific login session."""

    session_id: str = Field(
        description="Unique identifier of the login session to revoke",
    )


class UpdateLoginSecurityPolicyRequest(BaseRequestModel):
    """Request to update the login security policy for a user."""

    max_concurrent_logins: int | None = Field(
        default=None,
        gt=0,
        description="Maximum number of concurrent login sessions allowed; None means unlimited",
    )
