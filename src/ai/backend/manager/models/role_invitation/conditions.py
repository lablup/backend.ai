"""Query conditions and orders for role invitation repository operations."""

from __future__ import annotations

import uuid
from collections.abc import Collection
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.manager.data.role_invitation.types import RoleInvitationState
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.models.user import UserRow


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
    def by_inviter(inviter_user_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.inviter_user_id == inviter_user_id

        return inner

    @staticmethod
    def by_role(role_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.role_id == role_id

        return inner

    @staticmethod
    def by_role_id_filter_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = RoleInvitationRow.role_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_role_id_filter_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = RoleInvitationRow.role_id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

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

    # -- state filter --

    @staticmethod
    def by_state_equals(state: RoleInvitationState) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.state == state

        return inner

    @staticmethod
    def by_state_in(states: Collection[RoleInvitationState]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.state.in_(states)

        return inner

    @staticmethod
    def by_state_not_equals(state: RoleInvitationState) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.state != state

        return inner

    @staticmethod
    def by_state_not_in(states: Collection[RoleInvitationState]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleInvitationRow.state.not_in(states)

        return inner

    # -- nested role filter (EXISTS subquery) --

    @staticmethod
    def exists_role_with_conditions(role_conditions: list[QueryCondition]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(
                RoleRow.id == RoleInvitationRow.role_id,
            )
            for cond in role_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner

    @staticmethod
    def role_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RoleRow.name.ilike(f"%{spec.value}%")
            else:
                condition = RoleRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def role_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(RoleRow.name) == spec.value.lower()
            else:
                condition = RoleRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def role_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RoleRow.name.ilike(f"{spec.value}%")
            else:
                condition = RoleRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def role_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RoleRow.name.ilike(f"%{spec.value}")
            else:
                condition = RoleRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    role_name_in = staticmethod(make_string_in_factory(RoleRow.name))

    # -- nested user filter helpers (for EXISTS subquery) --

    @staticmethod
    def _user_email_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.email.ilike(f"%{spec.value}%")
            else:
                condition = UserRow.email.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def _user_email_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(UserRow.email) == spec.value.lower()
            else:
                condition = UserRow.email == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def _user_email_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.email.ilike(f"{spec.value}%")
            else:
                condition = UserRow.email.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def _user_email_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.email.ilike(f"%{spec.value}")
            else:
                condition = UserRow.email.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    _user_email_in = staticmethod(make_string_in_factory(UserRow.email))

    @staticmethod
    def exists_invitee_with_conditions(
        user_conditions: list[QueryCondition],
    ) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(
                UserRow.uuid == RoleInvitationRow.invitee_user_id,
            )
            for cond in user_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner

    @staticmethod
    def exists_inviter_with_conditions(
        user_conditions: list[QueryCondition],
    ) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(
                UserRow.uuid == RoleInvitationRow.inviter_user_id,
            )
            for cond in user_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner
