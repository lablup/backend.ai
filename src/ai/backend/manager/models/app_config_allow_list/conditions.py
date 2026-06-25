"""Query conditions for app config allow-list rows."""

from __future__ import annotations

import uuid
from collections.abc import Collection, Sequence
from datetime import datetime

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.data.app_config_allow_list.types import AppConfigScopeType
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import make_string_in_factory

__all__ = ("AppConfigAllowListConditions",)


class AppConfigAllowListConditions:
    @staticmethod
    def by_config_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigAllowListRow.config_name.ilike(f"%{spec.value}%")
            else:
                condition = AppConfigAllowListRow.config_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_config_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AppConfigAllowListRow.config_name) == spec.value.lower()
            else:
                condition = AppConfigAllowListRow.config_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_config_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigAllowListRow.config_name.ilike(f"{spec.value}%")
            else:
                condition = AppConfigAllowListRow.config_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_config_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigAllowListRow.config_name.ilike(f"%{spec.value}")
            else:
                condition = AppConfigAllowListRow.config_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_config_name_in = staticmethod(make_string_in_factory(AppConfigAllowListRow.config_name))

    @staticmethod
    def by_ids(ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.id.in_(ids)

        return inner

    # --- scope_type filters ---

    @staticmethod
    def by_scope_type_equals(scope_type: AppConfigScopeType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.scope_type == scope_type

        return inner

    @staticmethod
    def by_scope_type_in(scope_types: Sequence[AppConfigScopeType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.scope_type.in_(list(scope_types))

        return inner

    @staticmethod
    def by_scope_type_not_equals(scope_type: AppConfigScopeType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.scope_type != scope_type

        return inner

    @staticmethod
    def by_scope_type_not_in(scope_types: Sequence[AppConfigScopeType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.scope_type.not_in(list(scope_types))

        return inner

    # --- cursor (created_at-based) pagination ---

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(AppConfigAllowListRow.created_at)
                .where(AppConfigAllowListRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return AppConfigAllowListRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(AppConfigAllowListRow.created_at)
                .where(AppConfigAllowListRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return AppConfigAllowListRow.created_at > subquery

        return inner

    # --- created_at datetime filters ---

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.created_at == dt

        return inner

    # --- updated_at datetime filters ---

    @staticmethod
    def by_updated_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.updated_at < dt

        return inner

    @staticmethod
    def by_updated_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.updated_at > dt

        return inner

    @staticmethod
    def by_updated_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigAllowListRow.updated_at == dt

        return inner
