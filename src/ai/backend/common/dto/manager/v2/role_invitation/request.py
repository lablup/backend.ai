"""
Request DTOs for role invitation v2.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.role_invitation.types import RoleInvitationStateDTO


class CreateRoleInvitationInput(BaseRequestModel):
    """Input for creating role invitations."""

    role_id: UUID = Field(description="Role ID to invite for")
    emails: list[str] = Field(
        min_length=1,
        description="Invitee email addresses",
    )


class AcceptRoleInvitationInput(BaseRequestModel):
    """Input for accepting a role invitation."""

    invitation_id: UUID = Field(description="Invitation ID to accept")


class RejectRoleInvitationInput(BaseRequestModel):
    """Input for rejecting a role invitation."""

    invitation_id: UUID = Field(description="Invitation ID to reject")


class CancelRoleInvitationInput(BaseRequestModel):
    """Input for canceling a role invitation."""

    invitation_id: UUID = Field(description="Invitation ID to cancel")


class RoleInvitationOrderField(StrEnum):
    """Orderable fields for role invitations."""

    CREATED_AT = "created_at"
    STATE = "state"


class RoleInvitationOrderBy(BaseRequestModel):
    """Order by specification for role invitations."""

    field: RoleInvitationOrderField
    direction: OrderDirection = OrderDirection.DESC


class RoleInvitationStateFilter(BaseRequestModel):
    """Filter for invitation state with equality and membership operators.

    Follows the Strawberry GQL EnumFilter pattern.
    """

    equals: RoleInvitationStateDTO | None = Field(
        default=None, description="Exact match for invitation state."
    )
    in_: list[RoleInvitationStateDTO] | None = Field(
        default=None, alias="in", description="Match any of the provided states."
    )
    not_equals: RoleInvitationStateDTO | None = Field(
        default=None, description="Exclude exact state match."
    )
    not_in: list[RoleInvitationStateDTO] | None = Field(
        default=None, description="Exclude any of the provided states."
    )


class RoleNestedFilter(BaseRequestModel):
    """Nested filter for the role associated with an invitation."""

    name: StringFilter | None = None


RoleNestedFilter.model_rebuild()


class UserNestedFilter(BaseRequestModel):
    """Nested filter for a user (inviter or invitee) of an invitation."""

    email: StringFilter | None = None


UserNestedFilter.model_rebuild()


class RoleInvitationFilter(BaseRequestModel):
    """Filter for role invitations."""

    state: RoleInvitationStateFilter | None = None
    role_id: UUIDFilter | None = None
    role: RoleNestedFilter | None = None
    inviter: UserNestedFilter | None = None
    invitee: UserNestedFilter | None = None
    AND: list[RoleInvitationFilter] | None = None
    OR: list[RoleInvitationFilter] | None = None
    NOT: list[RoleInvitationFilter] | None = None


RoleInvitationFilter.model_rebuild()


class SearchRoleInvitationsInput(BaseRequestModel):
    """Pagination search input for role invitations."""

    filter: RoleInvitationFilter | None = None
    order: list[RoleInvitationOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None
