"""Types for role invitation repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.data.role_invitation.types import RoleInvitationData
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope


@dataclass
class RoleInvitationSearchResult:
    """Result from searching role invitations."""

    items: list[RoleInvitationData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class InviteeSearchScope(SearchScope):
    """Scope for searching invitations addressed to a specific user."""

    invitee_user_id: UUID

    def to_condition(self) -> QueryCondition:
        invitee_user_id = self.invitee_user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.invitee_user_id == invitee_user_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        # Invitee existence is guaranteed by RBAC authentication before reaching here.
        return []


@dataclass(frozen=True)
class InviterSearchScope(SearchScope):
    """Scope for searching invitations sent by a specific user."""

    inviter_user_id: UUID

    def to_condition(self) -> QueryCondition:
        inviter_user_id = self.inviter_user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.inviter_user_id == inviter_user_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        # Inviter existence is guaranteed by RBAC authentication before reaching here.
        return []


@dataclass(frozen=True)
class RoleInvitationSearchScope(SearchScope):
    """Scope for searching invitations for a specific role."""

    role_id: UUID

    def to_condition(self) -> QueryCondition:
        role_id = self.role_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.role_id == role_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        # Role existence is validated by the RBAC permission check before reaching here.
        return []
