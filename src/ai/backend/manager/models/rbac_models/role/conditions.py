"""Query conditions for role rows."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow

__all__ = ("RoleConditions",)


class RoleConditions:
    """Query conditions for roles."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
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
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
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
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
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
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RoleRow.name.ilike(f"%{spec.value}")
            else:
                condition = RoleRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(RoleRow.name))

    @staticmethod
    def by_sources(sources: list[RoleSource]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.source.in_(sources)

        return inner

    @staticmethod
    def by_source_equals(source: RoleSource) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.source == source

        return inner

    @staticmethod
    def by_source_not_equals(source: RoleSource) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.source != source

        return inner

    @staticmethod
    def by_source_not_in(sources: Collection[RoleSource]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.source.not_in(sources)

        return inner

    @staticmethod
    def by_statuses(statuses: list[RoleStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_equals(status: RoleStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.status == status

        return inner

    @staticmethod
    def by_status_not_equals(status: RoleStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.status != status

        return inner

    @staticmethod
    def by_status_not_in(statuses: Collection[RoleStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.status.not_in(statuses)

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RoleRow.created_at).where(RoleRow.id == cursor_uuid).scalar_subquery()
            )
            return RoleRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RoleRow.created_at).where(RoleRow.id == cursor_uuid).scalar_subquery()
            )
            return RoleRow.created_at > subquery

        return inner

    @staticmethod
    def by_ids(role_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.id.in_(role_ids)

        return inner

    @staticmethod
    def by_assigned_user_id(
        user_conditions: list[QueryCondition],
    ) -> QueryCondition:
        """Match roles whose ``user_roles`` rows satisfy ``user_conditions`` (correlated EXISTS)."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = (
                sa.select(sa.literal(1)).where(UserRoleRow.role_id == RoleRow.id).correlate(RoleRow)
            )
            for cond in user_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner

    @staticmethod
    def by_scope_type_equals(scope_type: EntityType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.scope_type == scope_type

        return inner

    @staticmethod
    def by_scope_type_not_equals(scope_type: EntityType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.scope_type != scope_type

        return inner

    @staticmethod
    def by_scope_type_in(scope_types: Collection[EntityType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.scope_type.in_(list(scope_types))

        return inner

    @staticmethod
    def by_scope_type_not_in(scope_types: Collection[EntityType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.scope_type.not_in(list(scope_types))

        return inner

    @staticmethod
    def by_scope_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = RoleRow.scope_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scope_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = RoleRow.scope_id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_mapped_scope(
        scope_conditions: list[QueryCondition],
    ) -> QueryCondition:
        """Match roles whose scope satisfies every one of ``scope_conditions``."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(*[condition() for condition in scope_conditions])

        return inner
