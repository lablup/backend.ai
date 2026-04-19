"""Query conditions for role invitation repository operations."""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.data.role_invitation.types import RoleInvitationState
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.repositories.base import QueryCondition


class RoleInvitationConditions:
    """Query conditions for filtering role invitations."""

    @staticmethod
    def by_id(invitation_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.id == invitation_id

        return inner

    @staticmethod
    def by_state(state: RoleInvitationState) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.state == state

        return inner

    @staticmethod
    def by_state_not(state: RoleInvitationState) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.state != state

        return inner

    @staticmethod
    def by_invitee(invitee_user_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.invitee_user_id == invitee_user_id

        return inner

    @staticmethod
    def by_role(role_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.role_id == role_id

        return inner
