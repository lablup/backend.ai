"""
Response DTOs for role invitation v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import RoleInvitationStateDTO

__all__ = (
    "CreateRoleInvitationPayload",
    "RoleInvitationNode",
    "SearchRoleInvitationsPayload",
)


class RoleInvitationNode(BaseResponseModel):
    """Node model representing a role invitation."""

    id: UUID = Field(description="Invitation ID")
    inviter_user_id: UUID | None = Field(default=None, description="Inviter user ID")
    invitee_user_id: UUID = Field(description="Invitee user ID")
    role_id: UUID = Field(description="Role ID")
    state: RoleInvitationStateDTO = Field(description="Invitation state")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class CreateRoleInvitationPayload(BaseResponseModel):
    """Payload for role invitation creation."""

    items: list[RoleInvitationNode] = Field(description="List of created role invitations.")


class SearchRoleInvitationsPayload(BaseResponseModel):
    """Paginated result for role invitation search."""

    items: list[RoleInvitationNode] = Field(description="List of invitation nodes.")
    total_count: int = Field(description="Total number of invitations matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
