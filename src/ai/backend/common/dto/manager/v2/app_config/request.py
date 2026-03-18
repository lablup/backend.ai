"""
Request DTOs for App Configuration v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "DeleteDomainConfigInput",
    "DeleteUserConfigInput",
)


class DeleteDomainConfigInput(BaseRequestModel):
    """Input for deleting domain-level app configuration."""

    domain_name: str = Field(description="Domain name whose configuration will be deleted.")


class DeleteUserConfigInput(BaseRequestModel):
    """Input for deleting user-level app configuration."""

    user_id: UUID | None = Field(
        default=None,
        description="User ID whose configuration will be deleted. Defaults to current user.",
    )
