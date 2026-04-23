"""Query conditions and orders for role invitation repository operations."""

from __future__ import annotations

import uuid
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.data.role_invitation.types import RoleInvitationState
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.base.types import QueryOrder


class RoleInvitationOrders:
    """Query orders for role invitations."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleInvitationRow.created_at.asc()
        return RoleInvitationRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleInvitationRow.updated_at.asc()
        return RoleInvitationRow.updated_at.desc()

    @staticmethod
    def state(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleInvitationRow.state.asc()
        return RoleInvitationRow.state.desc()


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

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Default order is created_at DESC, so forward means created_at < cursor's created_at.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RoleInvitationRow.created_at)
                .where(RoleInvitationRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return RoleInvitationRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Default order is created_at DESC, so backward means created_at > cursor's created_at.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RoleInvitationRow.created_at)
                .where(RoleInvitationRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return RoleInvitationRow.created_at > subquery

        return inner
