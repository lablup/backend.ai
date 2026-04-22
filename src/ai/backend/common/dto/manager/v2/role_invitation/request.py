"""
Request DTOs for role invitation v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class CreateRoleInvitationInput(BaseRequestModel):
    """Input for creating role invitations."""

    role_id: UUID = Field(description="Role ID to invite for")
    emails: list[str] = Field(
        min_length=1,
        description="Invitee email addresses",
    )


class SearchRoleInvitationsInput(BaseRequestModel):
    """Pagination search input for role invitations."""

    limit: int | None = None
    offset: int | None = None
