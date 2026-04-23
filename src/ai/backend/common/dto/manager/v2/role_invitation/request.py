"""
Request DTOs for role invitation v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import OrderDirection


class CreateRoleInvitationInput(BaseRequestModel):
    """Input for creating role invitations."""

    role_id: UUID = Field(description="Role ID to invite for")
    emails: list[str] = Field(
        min_length=1,
        description="Invitee email addresses",
    )


class RoleInvitationOrderBy(BaseRequestModel):
    """Order by specification for role invitations."""

    field: str
    direction: OrderDirection = OrderDirection.DESC


class SearchRoleInvitationsInput(BaseRequestModel):
    """Pagination search input for role invitations."""

    order: list[RoleInvitationOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None
